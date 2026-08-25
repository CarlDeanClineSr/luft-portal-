#!/usr/bin/env python3
"""Download definitive historical DSCOVR telemetry through NASA CDAWeb REST CSV.

No mission variable is addressed by row position. The service returns a JSON
DataResult containing a URL to a generated CSV file; both the descriptor and
CSV bytes are preserved before normalization.

Datasets
--------
* DSCOVR_H0_MAG: B1GSE, B1F1, FLAG1; native one-second definitive MAG.
* DSCOVR_H1_FC: V_GSE, Np, THERMAL_TEMP, DQF; native one-minute FC moments.

The canonical magnetic product retains truthful GSE names. It never renames
GSE components as GSM.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence
from urllib.parse import quote

import numpy as np
import pandas as pd
import requests

BASE_URL = "https://cdaweb.gsfc.nasa.gov/WS/cdasr/1/dataviews/sp_phys/datasets"
MAG_DATASET = "DSCOVR_H0_MAG"
MAG_VARIABLES = ("B1GSE", "B1F1", "FLAG1")
PLASMA_DATASET = "DSCOVR_H1_FC"
PLASMA_VARIABLES = ("V_GSE", "Np", "THERMAL_TEMP", "DQF")
INGEST_PROTOCOL = "CDAWEB-DSCOVR-RESTCSV-1M-v1"
USER_AGENT = "CLINE-L1-Rebuild/1.1 (independent audit; contact CARLDCLINE@GMAIL.COM)"

# Frozen V1 archive inventory: the definitive H1 Faraday-cup archive exposes
# 2016-2019. Paired V1 runs fail closed beyond this boundary instead of
# silently substituting a different spacecraft, propagated product, or clock.
PAIRED_PLASMA_END_EXCLUSIVE = pd.Timestamp("2020-01-01T00:00:00Z")


class DownloadError(RuntimeError):
    """Raised for an unsuccessful or malformed CDAWeb transaction."""


@dataclass(frozen=True)
class IngestConfig:
    magnetic_chunk_days: int = 1
    plasma_chunk_days: int = 7
    magnetic_min_valid_seconds_per_minute: int = 45
    provider_vector_negative_tolerance_nT: float = 0.05
    request_timeout_seconds: int = 180
    max_retries: int = 4
    retry_backoff_seconds: float = 3.0
    strict_magnetic_flag: int = 0
    strict_plasma_flags: tuple[int, ...] = (0,)
    nonfill_plasma_flags: tuple[int, ...] = (0, 1, 2, 3)


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_utc(value: str | datetime | pd.Timestamp) -> pd.Timestamp:
    stamp = pd.Timestamp(value)
    if stamp.tzinfo is None:
        return stamp.tz_localize("UTC")
    return stamp.tz_convert("UTC")


def compact_utc(value: str | datetime | pd.Timestamp) -> str:
    return parse_utc(value).strftime("%Y%m%dT%H%M%SZ")


def iso_utc(value: str | datetime | pd.Timestamp) -> str:
    return parse_utc(value).strftime("%Y-%m-%dT%H:%M:%SZ")


def iter_chunks(start: Any, end: Any, days: int) -> Iterator[tuple[pd.Timestamp, pd.Timestamp]]:
    cursor = parse_utc(start)
    stop = parse_utc(end)
    if cursor >= stop:
        raise ValueError("start must precede end")
    width = pd.Timedelta(days=days)
    while cursor < stop:
        chunk_end = min(cursor + width, stop)
        yield cursor, chunk_end
        cursor = chunk_end


def build_csv_request_url(
    dataset: str,
    variables: Sequence[str],
    start: Any,
    end: Any,
) -> str:
    variable_path = ",".join(quote(name, safe="") for name in variables)
    return (
        f"{BASE_URL}/{quote(dataset, safe='')}/data/"
        f"{compact_utc(start)},{compact_utc(end)}/{variable_path}?format=csv"
    )


def _request_with_retry(
    session: requests.Session,
    url: str,
    *,
    config: IngestConfig,
    accept: str | None = None,
) -> requests.Response:
    headers = {"User-Agent": USER_AGENT}
    if accept:
        headers["Accept"] = accept
    last_error: Exception | None = None
    for attempt in range(1, config.max_retries + 1):
        try:
            response = session.get(url, headers=headers, timeout=config.request_timeout_seconds)
            if response.status_code == 200:
                return response
            if response.status_code not in {429, 500, 502, 503, 504}:
                raise DownloadError(
                    f"CDAWeb HTTP {response.status_code} for {url}: {response.text[:500]}"
                )
            retry_after = response.headers.get("Retry-After")
            delay = float(retry_after) if retry_after else config.retry_backoff_seconds * attempt
            time.sleep(delay)
        except (requests.RequestException, DownloadError) as exc:
            last_error = exc
            if attempt == config.max_retries:
                break
            time.sleep(config.retry_backoff_seconds * attempt)
    raise DownloadError(f"request failed after {config.max_retries} attempts: {url}: {last_error}")


def extract_file_descriptions(payload: Any) -> list[dict[str, Any]]:
    """Extract CDAWeb FileDescription records from mapped JSON variants."""
    if not isinstance(payload, dict):
        raise DownloadError("CDAWeb descriptor response is not a JSON object")

    candidates: Any = payload.get("FileDescription")
    if candidates is None:
        # Some serializers wrap the root object.
        for value in payload.values():
            if isinstance(value, dict) and "FileDescription" in value:
                candidates = value["FileDescription"]
                break
    if candidates is None:
        errors = payload.get("Error") or payload.get("errors") or payload
        raise DownloadError(f"CDAWeb response contains no FileDescription: {errors!r}")
    if isinstance(candidates, dict):
        candidates = [candidates]
    if not isinstance(candidates, list) or not candidates:
        raise DownloadError("CDAWeb FileDescription is empty or malformed")

    result: list[dict[str, Any]] = []
    for item in candidates:
        if not isinstance(item, dict):
            continue
        name = item.get("Name") or item.get("name") or item.get("Url") or item.get("url")
        if name:
            normalized = dict(item)
            normalized["Name"] = name
            result.append(normalized)
    if not result:
        raise DownloadError("CDAWeb FileDescription contains no downloadable Name")
    return result


def fetch_cdaweb_csv(
    dataset: str,
    variables: Sequence[str],
    start: Any,
    end: Any,
    *,
    session: requests.Session | None = None,
    config: IngestConfig | None = None,
) -> tuple[bytes, dict[str, Any]]:
    """Request a generated CDAWeb CSV and return bytes plus provenance."""
    config = config or IngestConfig()
    owned_session = session is None
    session = session or requests.Session()
    request_url = build_csv_request_url(dataset, variables, start, end)
    try:
        descriptor_response = _request_with_retry(
            session, request_url, config=config, accept="application/json"
        )
        descriptor_bytes = descriptor_response.content
        try:
            descriptor_payload = descriptor_response.json()
        except ValueError as exc:
            raise DownloadError(
                f"CDAWeb descriptor was not JSON: {descriptor_response.text[:500]}"
            ) from exc
        descriptions = extract_file_descriptions(descriptor_payload)
        # A subset request ordinarily returns one file. If the server returns
        # more than one, concatenate only when every item is text/csv.
        downloaded: list[bytes] = []
        files: list[dict[str, Any]] = []
        for description in descriptions:
            file_url = str(description["Name"])
            file_response = _request_with_retry(session, file_url, config=config)
            downloaded.append(file_response.content)
            files.append(
                {
                    "url": file_url,
                    "length_reported": description.get("Length"),
                    "length_downloaded": len(file_response.content),
                    "mime_type_reported": description.get("MimeType"),
                    "sha256": sha256_bytes(file_response.content),
                }
            )
        if len(downloaded) == 1:
            csv_bytes = downloaded[0]
        else:
            # Preserve each file in provenance; combine later at the table
            # layer. Byte concatenation here is intentionally rejected because
            # repeated headers would make provenance less clear.
            raise DownloadError(
                f"CDAWeb returned {len(downloaded)} generated files; split the time chunk"
            )
        provenance = {
            "dataset": dataset,
            "variables": list(variables),
            "start": iso_utc(start),
            "end": iso_utc(end),
            "request_url": request_url,
            "descriptor_sha256": sha256_bytes(descriptor_bytes),
            "descriptor": descriptor_payload,
            "files": files,
            "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        }
        return csv_bytes, provenance
    finally:
        if owned_session:
            session.close()


def _clean_column_name(value: Any) -> str:
    text = str(value).strip().strip('"').strip("'")
    text = re.sub(r"\s+", "_", text)
    return text


def read_cdaweb_csv(content: bytes) -> pd.DataFrame:
    """Read a generated CDAWeb CSV, tolerating comment/metadata preambles."""
    text = content.decode("utf-8-sig", errors="replace")
    lines = text.splitlines()
    header_index: int | None = None
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "!", ";")):
            continue
        if "," not in stripped:
            continue
        tokens = [_clean_column_name(token).lower() for token in stripped.split(",")]
        if any(token in {"epoch", "time", "time_tag", "datetime", "utc"} or "epoch" in token for token in tokens):
            header_index = index
            break
    if header_index is None:
        # Fall back to pandas' first non-comment row and let contract checks
        # produce a precise missing-column error.
        frame = pd.read_csv(io.StringIO(text), comment="#")
    else:
        frame = pd.read_csv(io.StringIO("\n".join(lines[header_index:])))
    frame.columns = [_clean_column_name(column) for column in frame.columns]
    return frame


def _find_time_column(frame: pd.DataFrame) -> str:
    lower = {column.lower(): column for column in frame.columns}
    for name in ("epoch", "time_tag", "time", "datetime", "utc"):
        if name in lower:
            return lower[name]
    for column in frame.columns:
        if "epoch" in column.lower() or column.lower().startswith("time"):
            return column
    raise DownloadError(f"no epoch/time column in CDAWeb CSV columns: {list(frame.columns)}")


def _find_scalar_column(frame: pd.DataFrame, base: str) -> str:
    exact = [column for column in frame.columns if column.lower() == base.lower()]
    if exact:
        return exact[0]
    candidates = [
        column
        for column in frame.columns
        if re.sub(r"[^a-z0-9]", "", base.lower())
        == re.sub(r"[^a-z0-9]", "", column.lower())
    ]
    if len(candidates) == 1:
        return candidates[0]
    raise DownloadError(f"scalar variable {base!r} not uniquely found in {list(frame.columns)}")


def _find_vector_columns(frame: pd.DataFrame, base: str) -> tuple[str, str, str]:
    candidates = [column for column in frame.columns if base.lower() in column.lower()]
    if len(candidates) < 3:
        raise DownloadError(f"vector variable {base!r} has fewer than 3 columns: {candidates}")

    def component_score(column: str, component: str) -> int:
        normalized = re.sub(r"[^a-z0-9]", "", column.lower())
        suffixes = {
            "x": ("x", "0", "1"),
            "y": ("y", "1", "2"),
            "z": ("z", "2", "3"),
        }[component]
        score = 0
        for suffix in suffixes:
            if normalized.endswith(suffix):
                score += 10
            if re.search(rf"(?:_|\[|\(|\s){re.escape(suffix)}(?:\]|\)|$)", column.lower()):
                score += 20
        return score

    chosen: list[str] = []
    remaining = list(candidates)
    for component in ("x", "y", "z"):
        ranked = sorted(remaining, key=lambda c: component_score(c, component), reverse=True)
        if ranked and component_score(ranked[0], component) > 0:
            chosen.append(ranked[0])
            remaining.remove(ranked[0])
        else:
            chosen = []
            break
    if len(chosen) == 3:
        return tuple(chosen)  # type: ignore[return-value]

    # CDAWeb commonly emits vector columns in their source component order.
    if len(candidates) == 3:
        return tuple(candidates)  # type: ignore[return-value]
    raise DownloadError(f"vector variable {base!r} is ambiguous: {candidates}")


def normalize_magnetic_csv(raw: pd.DataFrame, config: IngestConfig | None = None) -> pd.DataFrame:
    config = config or IngestConfig()
    time_column = _find_time_column(raw)
    bx_col, by_col, bz_col = _find_vector_columns(raw, "B1GSE")
    magnitude_col = _find_scalar_column(raw, "B1F1")
    flag_col = _find_scalar_column(raw, "FLAG1")

    frame = pd.DataFrame(
        {
            "time_tag": pd.to_datetime(raw[time_column], utc=True, errors="coerce"),
            "bx_gse": pd.to_numeric(raw[bx_col], errors="coerce"),
            "by_gse": pd.to_numeric(raw[by_col], errors="coerce"),
            "bz_gse": pd.to_numeric(raw[bz_col], errors="coerce"),
            "B_provider_nT": pd.to_numeric(raw[magnitude_col], errors="coerce"),
            "quality_flag": pd.to_numeric(raw[flag_col], errors="coerce"),
        }
    )
    frame["B_vector_nT"] = np.sqrt(
        frame["bx_gse"] ** 2 + frame["by_gse"] ** 2 + frame["bz_gse"] ** 2
    )
    # B1F1 is average magnitude; B1GSE is an averaged vector. Equality is not
    # mathematically required. A large negative provider-minus-vector value is
    # the stronger consistency warning because mean(|B|) should not ordinarily
    # be materially below |mean(B)| over the same samples.
    frame["provider_minus_vector_nT"] = frame["B_provider_nT"] - frame["B_vector_nT"]
    frame["provider_below_vector_flag"] = (
        frame["provider_minus_vector_nT"] < -config.provider_vector_negative_tolerance_nT
    )
    finite = frame[["time_tag", "bx_gse", "by_gse", "bz_gse"]].notna().all(axis=1)
    frame["source_quality_pass"] = frame["quality_flag"] == config.strict_magnetic_flag
    frame["quality_pass"] = finite & frame["source_quality_pass"]
    frame["source_dataset"] = MAG_DATASET
    frame["coordinate_frame"] = "GSE"
    frame["ingest_protocol"] = INGEST_PROTOCOL
    return frame.sort_values("time_tag").drop_duplicates("time_tag", keep="last")


def aggregate_magnetic_to_one_minute(
    one_second: pd.DataFrame,
    config: IngestConfig | None = None,
) -> pd.DataFrame:
    config = config or IngestConfig()
    good = one_second.loc[one_second["quality_pass"]].copy()
    if good.empty:
        return pd.DataFrame()
    good = good.set_index("time_tag").sort_index()
    means = good[["bx_gse", "by_gse", "bz_gse"]].resample("1min").mean()
    counts = good["bx_gse"].resample("1min").count().rename("valid_seconds")
    provider = good["B_provider_nT"].resample("1min").mean().rename("provider_bt_mean_nT")
    warnings = good["provider_below_vector_flag"].resample("1min").sum().rename("provider_below_vector_count")
    output = pd.concat([means, provider, counts, warnings], axis=1).reset_index()
    output["coverage_fraction"] = output["valid_seconds"] / 60.0
    output = output.loc[
        output["valid_seconds"] >= config.magnetic_min_valid_seconds_per_minute
    ].copy()
    output["source_dataset"] = MAG_DATASET
    output["coordinate_frame"] = "GSE"
    output["ingest_protocol"] = INGEST_PROTOCOL
    return output.reset_index(drop=True)


def normalize_plasma_csv(raw: pd.DataFrame, config: IngestConfig | None = None) -> pd.DataFrame:
    config = config or IngestConfig()
    time_column = _find_time_column(raw)
    vx_col, vy_col, vz_col = _find_vector_columns(raw, "V_GSE")
    density_col = _find_scalar_column(raw, "Np")
    temperature_col = _find_scalar_column(raw, "THERMAL_TEMP")
    flag_col = _find_scalar_column(raw, "DQF")
    frame = pd.DataFrame(
        {
            "time_tag": pd.to_datetime(raw[time_column], utc=True, errors="coerce"),
            "vx_gse": pd.to_numeric(raw[vx_col], errors="coerce"),
            "vy_gse": pd.to_numeric(raw[vy_col], errors="coerce"),
            "vz_gse": pd.to_numeric(raw[vz_col], errors="coerce"),
            "density": pd.to_numeric(raw[density_col], errors="coerce"),
            "temperature": pd.to_numeric(raw[temperature_col], errors="coerce"),
            "quality_flag": pd.to_numeric(raw[flag_col], errors="coerce"),
        }
    )
    frame["speed"] = np.sqrt(
        frame["vx_gse"] ** 2 + frame["vy_gse"] ** 2 + frame["vz_gse"] ** 2
    )
    finite = frame[["time_tag", "density", "speed"]].notna().all(axis=1)
    physical = (frame["density"] >= 0) & (frame["speed"] >= 0)
    frame["strict_quality_pass"] = frame["quality_flag"].isin(config.strict_plasma_flags)
    frame["nonfill_quality_pass"] = frame["quality_flag"].isin(config.nonfill_plasma_flags)
    frame["quality_pass"] = finite & physical & frame["strict_quality_pass"]
    frame["source_dataset"] = PLASMA_DATASET
    frame["coordinate_frame"] = "GSE"
    frame["ingest_protocol"] = INGEST_PROTOCOL
    return frame.sort_values("time_tag").drop_duplicates("time_tag", keep="last")


def _preserve_transaction(
    root: Path,
    stem: str,
    csv_bytes: bytes,
    provenance: dict[str, Any],
) -> tuple[Path, Path]:
    root.mkdir(parents=True, exist_ok=True)
    csv_path = root / f"{stem}.csv"
    descriptor_path = root / f"{stem}.descriptor.json"
    csv_path.write_bytes(csv_bytes)
    descriptor_path.write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    return csv_path, descriptor_path


def download_magnetic_interval(
    start: Any,
    end: Any,
    output_dir: str | Path,
    *,
    config: IngestConfig | None = None,
    session: requests.Session | None = None,
) -> tuple[Path, dict[str, Any]]:
    config = config or IngestConfig()
    root = Path(output_dir)
    raw_root = root / "raw" / "magnetic"
    session = session or requests.Session()
    minute_frames: list[pd.DataFrame] = []
    chunks: list[dict[str, Any]] = []
    for chunk_start, chunk_end in iter_chunks(start, end, config.magnetic_chunk_days):
        csv_bytes, provenance = fetch_cdaweb_csv(
            MAG_DATASET, MAG_VARIABLES, chunk_start, chunk_end, session=session, config=config
        )
        stem = f"dscovr_h0_mag_{chunk_start:%Y%m%dT%H%M}_{chunk_end:%Y%m%dT%H%M}"
        csv_path, descriptor_path = _preserve_transaction(raw_root, stem, csv_bytes, provenance)
        raw = normalize_magnetic_csv(read_cdaweb_csv(csv_bytes), config)
        minute = aggregate_magnetic_to_one_minute(raw, config)
        minute_frames.append(minute)
        consistency = raw["provider_minus_vector_nT"].dropna()
        chunks.append(
            {
                "start": iso_utc(chunk_start),
                "end": iso_utc(chunk_end),
                "raw_csv": str(csv_path),
                "raw_csv_sha256": sha256_file(csv_path),
                "descriptor": str(descriptor_path),
                "raw_rows": int(len(raw)),
                "source_quality_pass_rows": int(raw["source_quality_pass"].sum()),
                "minute_rows": int(len(minute)),
                "provider_minus_vector": {
                    "median_nT": float(consistency.median()) if len(consistency) else None,
                    "p01_nT": float(consistency.quantile(0.01)) if len(consistency) else None,
                    "minimum_nT": float(consistency.min()) if len(consistency) else None,
                    "negative_warning_rows": int(raw["provider_below_vector_flag"].sum()),
                },
            }
        )
    combined = (
        pd.concat(minute_frames, ignore_index=True)
        .sort_values("time_tag")
        .drop_duplicates("time_tag", keep="last")
    ) if minute_frames else pd.DataFrame()
    canonical_path = root / "canonical" / "dscovr_mag_1m_gse.csv"
    canonical_path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(canonical_path, index=False)
    summary = {
        "dataset": MAG_DATASET,
        "variables": list(MAG_VARIABLES),
        "start": iso_utc(start),
        "end": iso_utc(end),
        "coordinate_frame": "GSE",
        "ingest_protocol": INGEST_PROTOCOL,
        "canonical_path": str(canonical_path),
        "canonical_sha256": sha256_file(canonical_path),
        "canonical_rows": int(len(combined)),
        "chunks": chunks,
    }
    return canonical_path, summary


def download_plasma_interval(
    start: Any,
    end: Any,
    output_dir: str | Path,
    *,
    config: IngestConfig | None = None,
    session: requests.Session | None = None,
) -> tuple[Path, dict[str, Any]]:
    config = config or IngestConfig()
    root = Path(output_dir)
    raw_root = root / "raw" / "plasma"
    session = session or requests.Session()
    strict_frames: list[pd.DataFrame] = []
    nonfill_frames: list[pd.DataFrame] = []
    chunks: list[dict[str, Any]] = []
    for chunk_start, chunk_end in iter_chunks(start, end, config.plasma_chunk_days):
        csv_bytes, provenance = fetch_cdaweb_csv(
            PLASMA_DATASET, PLASMA_VARIABLES, chunk_start, chunk_end, session=session, config=config
        )
        stem = f"dscovr_h1_fc_{chunk_start:%Y%m%dT%H%M}_{chunk_end:%Y%m%dT%H%M}"
        csv_path, descriptor_path = _preserve_transaction(raw_root, stem, csv_bytes, provenance)
        raw = normalize_plasma_csv(read_cdaweb_csv(csv_bytes), config)
        strict_frames.append(raw.loc[raw["quality_pass"]].copy())
        nonfill_frames.append(raw.loc[raw["nonfill_quality_pass"]].copy())
        counts = raw["quality_flag"].value_counts(dropna=False)
        chunks.append(
            {
                "start": iso_utc(chunk_start),
                "end": iso_utc(chunk_end),
                "raw_csv": str(csv_path),
                "raw_csv_sha256": sha256_file(csv_path),
                "descriptor": str(descriptor_path),
                "raw_rows": int(len(raw)),
                "strict_rows": int(raw["quality_pass"].sum()),
                "nonfill_rows": int(raw["nonfill_quality_pass"].sum()),
                "quality_flag_counts": {str(key): int(value) for key, value in counts.items()},
            }
        )

    def combine(frames: list[pd.DataFrame]) -> pd.DataFrame:
        return (
            pd.concat(frames, ignore_index=True)
            .sort_values("time_tag")
            .drop_duplicates("time_tag", keep="last")
        ) if frames else pd.DataFrame()

    strict = combine(strict_frames)
    nonfill = combine(nonfill_frames)
    columns = [
        "time_tag", "density", "speed", "temperature",
        "vx_gse", "vy_gse", "vz_gse", "quality_flag",
        "source_dataset", "coordinate_frame", "ingest_protocol",
    ]
    strict = strict[[column for column in columns if column in strict.columns]]
    nonfill = nonfill[[column for column in columns if column in nonfill.columns]]
    canonical_path = root / "canonical" / "dscovr_plasma_1m_dqf0.csv"
    sensitivity_path = root / "sensitivity" / "dscovr_plasma_1m_dqf0to3.csv"
    canonical_path.parent.mkdir(parents=True, exist_ok=True)
    sensitivity_path.parent.mkdir(parents=True, exist_ok=True)
    strict.to_csv(canonical_path, index=False)
    nonfill.to_csv(sensitivity_path, index=False)
    summary = {
        "dataset": PLASMA_DATASET,
        "variables": list(PLASMA_VARIABLES),
        "start": iso_utc(start),
        "end": iso_utc(end),
        "coordinate_frame": "GSE",
        "ingest_protocol": INGEST_PROTOCOL,
        "strict_quality_rule": f"DQF in {config.strict_plasma_flags}",
        "nonfill_sensitivity_rule": f"DQF in {config.nonfill_plasma_flags}",
        "canonical_path": str(canonical_path),
        "canonical_sha256": sha256_file(canonical_path),
        "canonical_rows": int(len(strict)),
        "sensitivity_path": str(sensitivity_path),
        "sensitivity_sha256": sha256_file(sensitivity_path),
        "sensitivity_rows": int(len(nonfill)),
        "chunks": chunks,
    }
    return canonical_path, summary


def download_interval(
    analysis_start: Any,
    analysis_end: Any,
    output_dir: str | Path,
    *,
    baseline_warmup_hours: int = 24,
    config: IngestConfig | None = None,
) -> dict[str, Any]:
    config = config or IngestConfig()
    analysis_start_ts = parse_utc(analysis_start)
    analysis_end_ts = parse_utc(analysis_end)
    if analysis_end_ts > PAIRED_PLASMA_END_EXCLUSIVE:
        raise DownloadError(
            "CDAWEB-DSCOVR-RESTCSV-1M-v1 paired definitive coverage ends "
            "before 2020; use a magnetic-only DSCOVR run or define a new "
            "source/clock protocol"
        )
    retrieval_start = analysis_start_ts - pd.Timedelta(hours=baseline_warmup_hours)
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    with requests.Session() as session:
        mag_path, mag_summary = download_magnetic_interval(
            retrieval_start, analysis_end_ts, root, config=config, session=session
        )
        plasma_path, plasma_summary = download_plasma_interval(
            retrieval_start, analysis_end_ts, root, config=config, session=session
        )
    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "analysis_start": iso_utc(analysis_start_ts),
        "analysis_end": iso_utc(analysis_end_ts),
        "retrieval_start": iso_utc(retrieval_start),
        "baseline_warmup_hours": baseline_warmup_hours,
        "ingest_protocol": INGEST_PROTOCOL,
        "config": asdict(config),
        "magnetic": mag_summary,
        "plasma": plasma_summary,
        "canonical_files": {"magnetic": str(mag_path), "plasma": str(plasma_path)},
    }
    manifest_path = root / "download_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", required=True, help="analysis start UTC")
    parser.add_argument("--end", required=True, help="analysis end UTC")
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--warmup-hours", type=int, default=24)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = download_interval(
        args.start, args.end, args.outdir, baseline_warmup_hours=args.warmup_hours
    )
    print(json.dumps(manifest["canonical_files"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
