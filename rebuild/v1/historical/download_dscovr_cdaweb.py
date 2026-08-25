#!/usr/bin/env python3
"""Download definitive historical DSCOVR telemetry from NASA CDAWeb.

The downloader keeps coordinate labels truthful:

* ``DSCOVR_H0_MAG`` supplies one-second GSE magnetic vectors ``B1GSE``.
* ``DSCOVR_H1_FC`` supplies one-minute proton velocity ``V_GSE`` and density ``Np``.

Magnetic data are fetched one day at a time, quality-checked at one second,
and reduced to one-minute arithmetic means. The canonical magnetic CSV uses
``bx_gse/by_gse/bz_gse``; it is never relabeled as GSM.

Network access is required when this program runs. It is designed for Colab or
a local Python environment, not for import-time network access.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator

import numpy as np
import pandas as pd

MAG_DATASET = "DSCOVR_H0_MAG"
MAG_VARIABLES = ["B1GSE", "B1F1", "FLAG1"]
PLASMA_DATASET = "DSCOVR_H1_FC"
PLASMA_VARIABLES = ["V_GSE", "Np", "THERMAL_TEMP", "DQF"]
INGEST_PROTOCOL = "CDAWEB-DSCOVR-1M-MEAN-v1"


class DownloadError(RuntimeError):
    """Raised for a failed or malformed CDAWeb retrieval."""


@dataclass(frozen=True)
class IngestConfig:
    magnetic_chunk_days: int = 1
    plasma_chunk_days: int = 7
    magnetic_min_valid_seconds_per_minute: int = 45
    one_second_bt_tolerance_nT: float = 0.02
    strict_magnetic_flag: int = 0
    strict_plasma_flag: int = 0


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_utc(value: str | datetime) -> pd.Timestamp:
    stamp = pd.Timestamp(value)
    if stamp.tzinfo is None:
        stamp = stamp.tz_localize("UTC")
    else:
        stamp = stamp.tz_convert("UTC")
    return stamp


def iso_z(value: str | datetime | pd.Timestamp) -> str:
    return parse_utc(value).strftime("%Y-%m-%dT%H:%M:%SZ")


def iter_chunks(
    start: str | datetime,
    end: str | datetime,
    days: int,
) -> Iterator[tuple[pd.Timestamp, pd.Timestamp]]:
    cursor = parse_utc(start)
    stop = parse_utc(end)
    if cursor >= stop:
        raise ValueError("start must precede end")
    delta = pd.Timedelta(days=days)
    while cursor < stop:
        chunk_end = min(cursor + delta, stop)
        yield cursor, chunk_end
        cursor = chunk_end


def _values(dataset: Any, name: str) -> np.ndarray:
    try:
        value = dataset[name]
    except Exception as exc:
        raise DownloadError(f"CDAWeb result is missing variable {name!r}") from exc
    if hasattr(value, "values"):
        value = value.values
    return np.asarray(value)


def _epochs(dataset: Any) -> pd.DatetimeIndex:
    for name in ("Epoch", "epoch", "time", "Time"):
        try:
            values = _values(dataset, name)
            parsed = pd.to_datetime(values, utc=True, errors="coerce")
            if len(parsed):
                return pd.DatetimeIndex(parsed)
        except DownloadError:
            continue
    raise DownloadError("CDAWeb result contains no recognized epoch coordinate")


def _flatten_scalar(values: np.ndarray, expected: int, name: str) -> np.ndarray:
    array = np.asarray(values)
    array = np.squeeze(array)
    if array.ndim != 1 or len(array) != expected:
        raise DownloadError(
            f"variable {name} has shape {np.asarray(values).shape}; expected ({expected},)"
        )
    return array


def _vector3(values: np.ndarray, expected: int, name: str) -> np.ndarray:
    array = np.asarray(values)
    array = np.squeeze(array)
    if array.ndim != 2:
        raise DownloadError(
            f"variable {name} has shape {np.asarray(values).shape}; expected a 2-D vector"
        )
    if array.shape == (3, expected):
        array = array.T
    if array.shape != (expected, 3):
        raise DownloadError(
            f"variable {name} has shape {np.asarray(values).shape}; expected ({expected}, 3)"
        )
    return array


def magnetic_frame_from_arrays(
    epochs: Any,
    b_gse: Any,
    *,
    provider_magnitude: Any | None = None,
    quality_flag: Any | None = None,
    config: IngestConfig | None = None,
) -> pd.DataFrame:
    """Normalize one-second magnetic arrays without changing the frame label."""
    config = config or IngestConfig()
    times = pd.to_datetime(epochs, utc=True, errors="coerce")
    n = len(times)
    vectors = _vector3(np.asarray(b_gse), n, "B1GSE").astype(float)

    frame = pd.DataFrame(
        {
            "time_tag": times,
            "bx_gse": vectors[:, 0],
            "by_gse": vectors[:, 1],
            "bz_gse": vectors[:, 2],
        }
    )
    frame["B_vector_nT"] = np.linalg.norm(vectors, axis=1)

    if provider_magnitude is not None:
        provider = _flatten_scalar(np.asarray(provider_magnitude), n, "B1F1").astype(float)
        frame["B_provider_nT"] = provider
        frame["bt_abs_error_nT"] = np.abs(provider - frame["B_vector_nT"])
        frame["bt_qc_pass"] = (
            frame["bt_abs_error_nT"] <= config.one_second_bt_tolerance_nT
        )
    else:
        frame["B_provider_nT"] = np.nan
        frame["bt_abs_error_nT"] = np.nan
        frame["bt_qc_pass"] = pd.Series(pd.NA, index=frame.index, dtype="boolean")

    if quality_flag is not None:
        flag = _flatten_scalar(np.asarray(quality_flag), n, "FLAG1")
        frame["quality_flag"] = pd.to_numeric(flag, errors="coerce")
        frame["source_quality_pass"] = (
            frame["quality_flag"] == config.strict_magnetic_flag
        )
    else:
        frame["quality_flag"] = np.nan
        frame["source_quality_pass"] = True

    finite = frame[["time_tag", "bx_gse", "by_gse", "bz_gse"]].notna().all(axis=1)
    frame["quality_pass"] = finite & frame["source_quality_pass"]
    return frame.sort_values("time_tag").drop_duplicates("time_tag", keep="last")


def aggregate_magnetic_to_one_minute(
    one_second: pd.DataFrame,
    *,
    config: IngestConfig | None = None,
) -> pd.DataFrame:
    """Reduce quality-passing one-second GSE vectors to one-minute means."""
    config = config or IngestConfig()
    good = one_second.loc[one_second["quality_pass"]].copy()
    if good.empty:
        return pd.DataFrame(
            columns=[
                "time_tag",
                "bx_gse",
                "by_gse",
                "bz_gse",
                "provider_bt_mean_nT",
                "valid_seconds",
                "coverage_fraction",
                "source_dataset",
                "ingest_protocol",
            ]
        )

    good = good.set_index("time_tag").sort_index()
    means = good[["bx_gse", "by_gse", "bz_gse"]].resample("1min").mean()
    counts = good["bx_gse"].resample("1min").count().rename("valid_seconds")
    provider = good["B_provider_nT"].resample("1min").mean().rename("provider_bt_mean_nT")
    out = pd.concat([means, provider, counts], axis=1).reset_index()
    out["coverage_fraction"] = out["valid_seconds"] / 60.0
    out = out.loc[
        out["valid_seconds"] >= config.magnetic_min_valid_seconds_per_minute
    ].copy()
    out["source_dataset"] = MAG_DATASET
    out["coordinate_frame"] = "GSE"
    out["ingest_protocol"] = INGEST_PROTOCOL
    # Deliberately do not call provider_bt_mean_nT ``bt``: magnitude of the
    # mean vector and mean of the magnitudes are not identical operations.
    return out.reset_index(drop=True)


def plasma_frame_from_arrays(
    epochs: Any,
    velocity_gse: Any,
    density: Any,
    *,
    temperature: Any | None = None,
    quality_flag: Any | None = None,
    config: IngestConfig | None = None,
) -> pd.DataFrame:
    """Normalize one-minute Faraday-cup arrays and retain quality metadata."""
    config = config or IngestConfig()
    times = pd.to_datetime(epochs, utc=True, errors="coerce")
    n = len(times)
    velocity = _vector3(np.asarray(velocity_gse), n, "V_GSE").astype(float)
    density_values = _flatten_scalar(np.asarray(density), n, "Np").astype(float)

    frame = pd.DataFrame(
        {
            "time_tag": times,
            "vx_gse": velocity[:, 0],
            "vy_gse": velocity[:, 1],
            "vz_gse": velocity[:, 2],
            "density": density_values,
        }
    )
    frame["speed"] = np.linalg.norm(velocity, axis=1)

    if temperature is not None:
        frame["temperature"] = _flatten_scalar(
            np.asarray(temperature), n, "THERMAL_TEMP"
        ).astype(float)
    else:
        frame["temperature"] = np.nan

    if quality_flag is not None:
        flag = _flatten_scalar(np.asarray(quality_flag), n, "DQF")
        frame["quality_flag"] = pd.to_numeric(flag, errors="coerce")
        frame["source_quality_pass"] = (
            frame["quality_flag"] == config.strict_plasma_flag
        )
    else:
        frame["quality_flag"] = np.nan
        frame["source_quality_pass"] = True

    finite = frame[["time_tag", "density", "speed"]].notna().all(axis=1)
    physical = (frame["density"] >= 0) & (frame["speed"] >= 0)
    frame["quality_pass"] = finite & physical & frame["source_quality_pass"]
    frame["source_dataset"] = PLASMA_DATASET
    frame["coordinate_frame"] = "GSE"
    frame["ingest_protocol"] = INGEST_PROTOCOL
    return frame.sort_values("time_tag").drop_duplicates("time_tag", keep="last")


def _cdas_client() -> tuple[Any, Any]:
    try:
        from cdasws.cdasws import CdasWs
        from cdasws.datarepresentation import DataRepresentation
    except ImportError as exc:
        raise DownloadError(
            "historical download requires: pip install cdasws cdflib xarray"
        ) from exc
    return CdasWs(), DataRepresentation


def _get_xarray(
    cdas: Any,
    representation: Any,
    dataset: str,
    variables: list[str],
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> Any:
    metadata, data = cdas.get_data(
        dataset,
        variables,
        iso_z(start),
        iso_z(end),
        dataRepresentation=representation.XARRAY,
    )
    if data is None:
        raise DownloadError(
            f"CDAWeb returned no data for {dataset} {iso_z(start)} to {iso_z(end)}; metadata={metadata!r}"
        )
    return data


def _write_csv_gz(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, compression="gzip")


def _mag_qc(frame: pd.DataFrame, config: IngestConfig) -> dict[str, Any]:
    errors = pd.to_numeric(frame["bt_abs_error_nT"], errors="coerce").dropna()
    source_good = frame["source_quality_pass"].fillna(False).astype(bool)
    tested = frame.loc[source_good, "bt_qc_pass"].dropna()
    return {
        "rows": int(len(frame)),
        "source_quality_pass_rows": int(source_good.sum()),
        "bt_tested_rows": int(len(tested)),
        "bt_pass_rows": int(tested.astype(bool).sum()) if len(tested) else 0,
        "bt_pass_fraction": float(tested.astype(bool).mean()) if len(tested) else None,
        "mean_abs_error_nT": float(errors.mean()) if len(errors) else None,
        "p99_abs_error_nT": float(errors.quantile(0.99)) if len(errors) else None,
        "max_abs_error_nT": float(errors.max()) if len(errors) else None,
        "tolerance_nT": config.one_second_bt_tolerance_nT,
    }


def download_magnetic_interval(
    start: str | datetime,
    end: str | datetime,
    output_dir: str | Path,
    *,
    config: IngestConfig | None = None,
    cdas: Any | None = None,
    representation: Any | None = None,
) -> tuple[Path, dict[str, Any]]:
    config = config or IngestConfig()
    root = Path(output_dir)
    raw_dir = root / "raw" / "magnetic"
    if cdas is None or representation is None:
        cdas, representation = _cdas_client()

    minute_frames: list[pd.DataFrame] = []
    chunk_records: list[dict[str, Any]] = []
    for chunk_start, chunk_end in iter_chunks(start, end, config.magnetic_chunk_days):
        data = _get_xarray(
            cdas, representation, MAG_DATASET, MAG_VARIABLES, chunk_start, chunk_end
        )
        raw = magnetic_frame_from_arrays(
            _epochs(data),
            _values(data, "B1GSE"),
            provider_magnitude=_values(data, "B1F1"),
            quality_flag=_values(data, "FLAG1"),
            config=config,
        )
        chunk_name = f"dscovr_h0_mag_{chunk_start:%Y%m%dT%H%M}_{chunk_end:%Y%m%dT%H%M}.csv.gz"
        raw_path = raw_dir / chunk_name
        _write_csv_gz(raw, raw_path)
        minute = aggregate_magnetic_to_one_minute(raw, config=config)
        minute_frames.append(minute)
        chunk_records.append(
            {
                "start": iso_z(chunk_start),
                "end": iso_z(chunk_end),
                "raw_path": str(raw_path),
                "raw_sha256": sha256_file(raw_path),
                "raw_rows": int(len(raw)),
                "minute_rows": int(len(minute)),
                "qc": _mag_qc(raw, config),
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
        "variables": MAG_VARIABLES,
        "start": iso_z(start),
        "end": iso_z(end),
        "coordinate_frame": "GSE",
        "ingest_protocol": INGEST_PROTOCOL,
        "canonical_path": str(canonical_path),
        "canonical_sha256": sha256_file(canonical_path),
        "canonical_rows": int(len(combined)),
        "chunks": chunk_records,
    }
    return canonical_path, summary


def download_plasma_interval(
    start: str | datetime,
    end: str | datetime,
    output_dir: str | Path,
    *,
    config: IngestConfig | None = None,
    cdas: Any | None = None,
    representation: Any | None = None,
) -> tuple[Path, dict[str, Any]]:
    config = config or IngestConfig()
    root = Path(output_dir)
    raw_dir = root / "raw" / "plasma"
    if cdas is None or representation is None:
        cdas, representation = _cdas_client()

    clean_frames: list[pd.DataFrame] = []
    chunk_records: list[dict[str, Any]] = []
    for chunk_start, chunk_end in iter_chunks(start, end, config.plasma_chunk_days):
        data = _get_xarray(
            cdas,
            representation,
            PLASMA_DATASET,
            PLASMA_VARIABLES,
            chunk_start,
            chunk_end,
        )
        raw = plasma_frame_from_arrays(
            _epochs(data),
            _values(data, "V_GSE"),
            _values(data, "Np"),
            temperature=_values(data, "THERMAL_TEMP"),
            quality_flag=_values(data, "DQF"),
            config=config,
        )
        chunk_name = f"dscovr_h1_fc_{chunk_start:%Y%m%dT%H%M}_{chunk_end:%Y%m%dT%H%M}.csv.gz"
        raw_path = raw_dir / chunk_name
        _write_csv_gz(raw, raw_path)
        clean = raw.loc[raw["quality_pass"]].copy()
        clean_frames.append(clean)
        chunk_records.append(
            {
                "start": iso_z(chunk_start),
                "end": iso_z(chunk_end),
                "raw_path": str(raw_path),
                "raw_sha256": sha256_file(raw_path),
                "raw_rows": int(len(raw)),
                "quality_pass_rows": int(raw["quality_pass"].sum()),
                "quality_flag_counts": {
                    str(k): int(v)
                    for k, v in raw["quality_flag"].value_counts(dropna=False).items()
                },
            }
        )

    combined = (
        pd.concat(clean_frames, ignore_index=True)
        .sort_values("time_tag")
        .drop_duplicates("time_tag", keep="last")
    ) if clean_frames else pd.DataFrame()
    columns = [
        "time_tag",
        "density",
        "speed",
        "temperature",
        "vx_gse",
        "vy_gse",
        "vz_gse",
        "quality_flag",
        "source_dataset",
        "coordinate_frame",
        "ingest_protocol",
    ]
    combined = combined[[c for c in columns if c in combined.columns]]
    canonical_path = root / "canonical" / "dscovr_plasma_1m.csv"
    canonical_path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(canonical_path, index=False)
    summary = {
        "dataset": PLASMA_DATASET,
        "variables": PLASMA_VARIABLES,
        "start": iso_z(start),
        "end": iso_z(end),
        "coordinate_frame": "GSE",
        "ingest_protocol": INGEST_PROTOCOL,
        "quality_rule": f"DQF == {config.strict_plasma_flag}",
        "canonical_path": str(canonical_path),
        "canonical_sha256": sha256_file(canonical_path),
        "canonical_rows": int(len(combined)),
        "chunks": chunk_records,
    }
    return canonical_path, summary


def download_interval(
    analysis_start: str | datetime,
    analysis_end: str | datetime,
    output_dir: str | Path,
    *,
    baseline_warmup_hours: int = 24,
    config: IngestConfig | None = None,
) -> dict[str, Any]:
    """Download an interval plus prior baseline history for both instruments."""
    config = config or IngestConfig()
    analysis_start_ts = parse_utc(analysis_start)
    analysis_end_ts = parse_utc(analysis_end)
    retrieval_start = analysis_start_ts - pd.Timedelta(hours=baseline_warmup_hours)
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)

    cdas, representation = _cdas_client()
    mag_path, mag_summary = download_magnetic_interval(
        retrieval_start,
        analysis_end_ts,
        root,
        config=config,
        cdas=cdas,
        representation=representation,
    )
    plasma_path, plasma_summary = download_plasma_interval(
        retrieval_start,
        analysis_end_ts,
        root,
        config=config,
        cdas=cdas,
        representation=representation,
    )
    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "analysis_start": iso_z(analysis_start_ts),
        "analysis_end": iso_z(analysis_end_ts),
        "retrieval_start": iso_z(retrieval_start),
        "baseline_warmup_hours": baseline_warmup_hours,
        "ingest_protocol": INGEST_PROTOCOL,
        "config": asdict(config),
        "magnetic": mag_summary,
        "plasma": plasma_summary,
        "canonical_files": {
            "magnetic": str(mag_path),
            "plasma": str(plasma_path),
        },
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
        args.start,
        args.end,
        args.outdir,
        baseline_warmup_hours=args.warmup_hours,
    )
    print(json.dumps(manifest["canonical_files"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
