#!/usr/bin/env python3
"""CLINE L1 magnetic-to-CME reconstruction.

Protocol: CLINE-L1-B24M-TRAIL-v1

This program reads NOAA-style magnetic and plasma telemetry by column name,
validates the supplied magnetic magnitude against the vector components,
computes a prior-only 24-hour median baseline, and preserves all chi values
without clipping.

It deliberately separates:
  * magnetic chi computation;
  * independent kinetic transient classification; and
  * interpretation.

The generated reports contain numerical results only. They do not hard-code a
confirmation or rejection sentence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

PROTOCOL_ID = "CLINE-L1-B24M-TRAIL-v1"
PROTOCOL_VERSION = "1.1.0"


@dataclass(frozen=True)
class ProtocolConfig:
    baseline_hours: int = 24
    cadence_seconds: int = 60
    minimum_coverage_fraction: float = 0.95
    bt_absolute_tolerance_nT: float = 0.02
    plasma_join_tolerance_seconds: int = 90
    speed_lag_minutes: int = 60
    speed_lag_tolerance_seconds: int = 120
    speed_high_km_s: float = 600.0
    density_high_cm3: float = 15.0
    speed_jump_1h_km_s: float = 50.0
    southward_bz_support_nT: float = -10.0
    high_bt_support_nT: float = 15.0
    chi_theoretical: float = 0.15
    chi_band_low: float = 0.145
    chi_band_high: float = 0.155

    @property
    def expected_baseline_samples(self) -> int:
        return int(self.baseline_hours * 3600 / self.cadence_seconds)

    @property
    def minimum_baseline_samples(self) -> int:
        return math.ceil(
            self.expected_baseline_samples * self.minimum_coverage_fraction
        )


class DataContractError(ValueError):
    """Raised when a source does not meet the frozen input contract."""


def sha256_file(path: str | Path) -> str:
    p = Path(path)
    h = hashlib.sha256()
    with p.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_table(path: str | Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Load a CSV or NOAA JSON table without positional field assumptions."""
    p = Path(path)
    suffix = p.suffix.lower()
    raw_rows: int | None = None
    source_header: list[str] | None = None

    if suffix == ".csv":
        df = pd.read_csv(p)
        raw_rows = len(df)
        source_header = [str(c) for c in df.columns]
    elif suffix == ".json":
        with p.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        if not isinstance(payload, list) or not payload:
            raise DataContractError(f"{p}: expected a non-empty JSON list")

        if isinstance(payload[0], list):
            source_header = [str(v) for v in payload[0]]
            df = pd.DataFrame(payload[1:], columns=source_header)
            raw_rows = len(payload) - 1
        elif isinstance(payload[0], dict):
            df = pd.DataFrame(payload)
            source_header = [str(c) for c in df.columns]
            raw_rows = len(df)
        else:
            raise DataContractError(
                f"{p}: expected JSON rows as lists with a header or dictionaries"
            )
    else:
        raise DataContractError(f"{p}: supported formats are .json and .csv")

    metadata = {
        "path": str(p),
        "filename": p.name,
        "sha256": sha256_file(p),
        "size_bytes": p.stat().st_size,
        "raw_rows": int(raw_rows),
        "source_header": source_header,
    }
    return df, metadata


def _parse_and_deduplicate(
    frame: pd.DataFrame,
    required_numeric: Iterable[str],
    optional_numeric: Iterable[str] = (),
) -> tuple[pd.DataFrame, dict[str, int]]:
    df = frame.copy()
    if "time_tag" not in df.columns:
        raise DataContractError("required timestamp column 'time_tag' is absent")

    missing = [c for c in required_numeric if c not in df.columns]
    if missing:
        raise DataContractError(f"required columns absent: {missing}")

    before = len(df)
    df["time_tag"] = pd.to_datetime(df["time_tag"], utc=True, errors="coerce")
    for column in list(required_numeric) + [
        c for c in optional_numeric if c in df.columns
    ]:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    required_for_row = ["time_tag", *required_numeric]
    invalid_mask = df[required_for_row].isna().any(axis=1)
    rejected_invalid = int(invalid_mask.sum())
    df = df.loc[~invalid_mask].copy()

    df = df.sort_values("time_tag")
    duplicated_mask = df.duplicated("time_tag", keep="last")
    removed_duplicates = int(duplicated_mask.sum())
    df = df.loc[~duplicated_mask].reset_index(drop=True)

    audit = {
        "rows_before_cleaning": int(before),
        "rows_rejected_invalid": rejected_invalid,
        "duplicate_timestamps_removed": removed_duplicates,
        "rows_after_cleaning": int(len(df)),
    }
    return df, audit


def load_magnetic(
    path: str | Path,
    config: ProtocolConfig,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    raw, metadata = _load_table(path)

    # The frozen observable is magnetic-field magnitude, which is invariant
    # under rotation, but coordinate labels must remain truthful. Historical
    # CDAWeb DSCOVR data are supplied in GSE while NOAA real-time products are
    # commonly supplied in GSM. Never relabel GSE components as GSM.
    vector_contracts = [
        ("GSM", ("bx_gsm", "by_gsm", "bz_gsm")),
        ("GSE", ("bx_gse", "by_gse", "bz_gse")),
    ]
    complete = [
        (frame, columns)
        for frame, columns in vector_contracts
        if all(column in raw.columns for column in columns)
    ]
    if not complete:
        expected = [list(columns) for _, columns in vector_contracts]
        raise DataContractError(
            f"required magnetic vector absent; expected one complete set from {expected}"
        )
    if len(complete) > 1:
        # Both frames can be legitimate, but silently choosing one would hide a
        # coordinate decision. Require the source to be explicit.
        raise DataContractError(
            "multiple complete magnetic coordinate frames found; provide one frame per input"
        )

    coordinate_frame, required = complete[0]
    optional = ["bt", "lon_gsm", "lat_gsm", "quality_flag"]
    magnetic, cleaning = _parse_and_deduplicate(
        raw,
        required_numeric=required,
        optional_numeric=optional,
    )

    bx_col, by_col, bz_col = required
    magnetic["B_vector_nT"] = np.sqrt(
        magnetic[bx_col] ** 2
        + magnetic[by_col] ** 2
        + magnetic[bz_col] ** 2
    )
    magnetic["bz_context_nT"] = magnetic[bz_col]
    magnetic["coordinate_frame"] = coordinate_frame

    if "bt" in magnetic.columns:
        magnetic["B_provider_nT"] = magnetic["bt"]
        magnetic["bt_abs_error_nT"] = (
            magnetic["B_provider_nT"] - magnetic["B_vector_nT"]
        ).abs()
        magnetic["bt_qc_pass"] = (
            magnetic["bt_abs_error_nT"] <= config.bt_absolute_tolerance_nT
        )
    else:
        magnetic["B_provider_nT"] = np.nan
        magnetic["bt_abs_error_nT"] = np.nan
        magnetic["bt_qc_pass"] = pd.Series(pd.NA, index=magnetic.index, dtype="boolean")

    metadata.update(cleaning)
    metadata["authoritative_magnitude"] = (
        "sqrt(bx_gsm^2 + by_gsm^2 + bz_gsm^2)"
    )
    metadata["provider_bt_used_for"] = "quality-control only"
    metadata["coordinate_frame"] = coordinate_frame
    metadata["field_mapping"] = {
        "timestamp": "time_tag",
        "bx": bx_col,
        "by": by_col,
        "bz": bz_col,
        "coordinate_frame": coordinate_frame,
        "provider_magnitude": "bt" if "bt" in magnetic.columns else None,
    }
    return magnetic, metadata


def load_plasma(path: str | Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    raw, metadata = _load_table(path)
    plasma, cleaning = _parse_and_deduplicate(
        raw,
        required_numeric=["density", "speed"],
        optional_numeric=["temperature"],
    )
    metadata.update(cleaning)
    return plasma, metadata


def cadence_audit(frame: pd.DataFrame, cadence_seconds: int) -> dict[str, Any]:
    if frame.empty:
        return {
            "rows": 0,
            "start_utc": None,
            "end_utc": None,
            "span_seconds": 0.0,
            "median_cadence_seconds": None,
            "max_gap_seconds": None,
            "gaps_over_1p5_cadences": 0,
            "gaps_over_5_minutes": 0,
            "observed_coverage_fraction": None,
        }

    times = frame["time_tag"].sort_values()
    deltas = times.diff().dropna().dt.total_seconds()
    span_seconds = float((times.iloc[-1] - times.iloc[0]).total_seconds())
    expected_rows = int(span_seconds / cadence_seconds) + 1
    return {
        "rows": int(len(frame)),
        "start_utc": times.iloc[0].isoformat(),
        "end_utc": times.iloc[-1].isoformat(),
        "span_seconds": span_seconds,
        "median_cadence_seconds": float(deltas.median()) if len(deltas) else None,
        "max_gap_seconds": float(deltas.max()) if len(deltas) else None,
        "gaps_over_1p5_cadences": int((deltas > 1.5 * cadence_seconds).sum()),
        "gaps_over_5_minutes": int((deltas > 300).sum()),
        "observed_coverage_fraction": (
            float(len(frame) / expected_rows) if expected_rows > 0 else None
        ),
    }


def compute_frozen_baseline(
    magnetic: pd.DataFrame,
    config: ProtocolConfig,
) -> pd.DataFrame:
    """Apply the frozen prior-only 24-hour magnetic median protocol."""
    df = magnetic.copy().sort_values("time_tag").reset_index(drop=True)
    first_time = df["time_tag"].iloc[0]

    indexed = df.set_index("time_tag")
    window = f"{config.baseline_hours}h"
    indexed["baseline_sample_count"] = indexed["B_vector_nT"].rolling(
        window,
        closed="left",
        min_periods=1,
    ).count()
    indexed["B0_trailing_24h_median_nT"] = indexed["B_vector_nT"].rolling(
        window,
        closed="left",
        min_periods=config.minimum_baseline_samples,
    ).median()

    indexed = indexed.reset_index()
    indexed["history_age_seconds"] = (
        indexed["time_tag"] - first_time
    ).dt.total_seconds()
    full_history = indexed["history_age_seconds"] >= config.baseline_hours * 3600
    positive_baseline = indexed["B0_trailing_24h_median_nT"] > 0
    indexed["baseline_valid"] = (
        full_history
        & positive_baseline
        & indexed["B0_trailing_24h_median_nT"].notna()
    )

    indexed["baseline_coverage_fraction"] = (
        indexed["baseline_sample_count"] / config.expected_baseline_samples
    )

    indexed["baseline_status"] = "VALID"
    indexed.loc[~full_history, "baseline_status"] = "WARMUP_LT_24H"
    indexed.loc[
        full_history & indexed["B0_trailing_24h_median_nT"].isna(),
        "baseline_status",
    ] = "INSUFFICIENT_COVERAGE"
    indexed.loc[
        full_history
        & indexed["B0_trailing_24h_median_nT"].notna()
        & ~positive_baseline,
        "baseline_status",
    ] = "NONPOSITIVE_BASELINE"

    indexed["chi_B24M"] = np.nan
    valid = indexed["baseline_valid"]
    indexed.loc[valid, "chi_B24M"] = (
        indexed.loc[valid, "B_vector_nT"]
        - indexed.loc[valid, "B0_trailing_24h_median_nT"]
    ).abs() / indexed.loc[valid, "B0_trailing_24h_median_nT"].abs()

    # No clipping or capping is performed.
    indexed["chi_status"] = "WARMUP_OR_GAP"
    # A tiny numerical epsilon keeps decimal boundary values such as 0.155
    # inside the explicitly inclusive band after binary floating conversion.
    boundary_epsilon = 1e-12
    indexed.loc[
        valid & (indexed["chi_B24M"] < config.chi_band_low - boundary_epsilon),
        "chi_status",
    ] = "BELOW"
    indexed.loc[
        valid
        & (indexed["chi_B24M"] >= config.chi_band_low - boundary_epsilon)
        & (indexed["chi_B24M"] <= config.chi_band_high + boundary_epsilon),
        "chi_status",
    ] = "AT_BOUNDARY"
    indexed.loc[
        valid & (indexed["chi_B24M"] > config.chi_band_high + boundary_epsilon),
        "chi_status",
    ] = "ABOVE_BAND"
    indexed["above_theoretical_0p15"] = (
        valid & (indexed["chi_B24M"] > config.chi_theoretical)
    )
    return indexed


def merge_plasma_and_classify(
    magnetic: pd.DataFrame,
    plasma: pd.DataFrame,
    config: ProtocolConfig,
) -> pd.DataFrame:
    """Join plasma by time and classify kinetics without using chi."""
    base = magnetic.copy().sort_values("time_tag").reset_index(drop=True)
    source = plasma.copy().sort_values("time_tag").reset_index(drop=True)

    join_source = source.rename(columns={"time_tag": "plasma_time_tag"})
    joined = pd.merge_asof(
        base,
        join_source,
        left_on="time_tag",
        right_on="plasma_time_tag",
        direction="nearest",
        tolerance=pd.Timedelta(seconds=config.plasma_join_tolerance_seconds),
    )
    joined["plasma_join_delta_seconds"] = (
        joined["time_tag"] - joined["plasma_time_tag"]
    ).abs().dt.total_seconds()

    # Construct a time-normalized one-hour speed comparison from the plasma
    # timestamps themselves. This avoids treating a one-minute fluctuation as
    # a one-hour jump.
    speed_lag = source[["time_tag", "speed"]].dropna().copy()
    speed_lag = speed_lag.rename(
        columns={"time_tag": "speed_prior_time_tag", "speed": "speed_1h_prior"}
    )
    speed_lag["speed_lag_target_time"] = (
        speed_lag["speed_prior_time_tag"]
        + pd.Timedelta(minutes=config.speed_lag_minutes)
    )
    joined = pd.merge_asof(
        joined.sort_values("time_tag"),
        speed_lag.sort_values("speed_lag_target_time"),
        left_on="time_tag",
        right_on="speed_lag_target_time",
        direction="nearest",
        tolerance=pd.Timedelta(seconds=config.speed_lag_tolerance_seconds),
    )
    joined["speed_lag_alignment_error_seconds"] = (
        joined["time_tag"] - joined["speed_lag_target_time"]
    ).abs().dt.total_seconds()
    joined["speed_jump_1h_km_s"] = (
        joined["speed"] - joined["speed_1h_prior"]
    ).abs()

    joined["kin_speed_high"] = joined["speed"] > config.speed_high_km_s
    joined["kin_density_high"] = joined["density"] > config.density_high_cm3
    joined["kin_speed_jump_1h"] = (
        joined["speed_jump_1h_km_s"] > config.speed_jump_1h_km_s
    )

    kinetic_inputs_valid = joined[
        ["density", "speed", "speed_1h_prior"]
    ].notna().all(axis=1)
    transient = (
        joined["kin_speed_high"]
        | joined["kin_density_high"]
        | joined["kin_speed_jump_1h"]
    ) & kinetic_inputs_valid
    joined["kinetic_regime"] = np.where(
        ~kinetic_inputs_valid,
        "UNCLASSIFIED",
        np.where(transient, "TRANSIENT_KINETIC", "STEADY_KINETIC"),
    )

    # Magnetic fields are retained as supporting context only; they do not
    # determine the blind kinetic regime.
    # Southward Bz support is interpreted only for GSM inputs. GSE Bz is
    # retained as context but is not silently treated as GSM. Older in-memory
    # callers may not yet contain the normalized context columns, so infer
    # them only when the original column labels make the frame unambiguous.
    if "coordinate_frame" not in joined.columns:
        if "bz_gsm" in joined.columns and "bz_gse" not in joined.columns:
            joined["coordinate_frame"] = "GSM"
        elif "bz_gse" in joined.columns and "bz_gsm" not in joined.columns:
            joined["coordinate_frame"] = "GSE"
        else:
            joined["coordinate_frame"] = "UNKNOWN"
    if "bz_context_nT" not in joined.columns:
        joined["bz_context_nT"] = np.nan
        gsm_rows = joined["coordinate_frame"] == "GSM"
        gse_rows = joined["coordinate_frame"] == "GSE"
        if "bz_gsm" in joined.columns:
            joined.loc[gsm_rows, "bz_context_nT"] = joined.loc[gsm_rows, "bz_gsm"]
        if "bz_gse" in joined.columns:
            joined.loc[gse_rows, "bz_context_nT"] = joined.loc[gse_rows, "bz_gse"]

    frame_is_gsm = joined["coordinate_frame"] == "GSM"
    joined["mag_support_southward_bz"] = pd.Series(
        pd.NA, index=joined.index, dtype="boolean"
    )
    joined.loc[frame_is_gsm, "mag_support_southward_bz"] = (
        joined.loc[frame_is_gsm, "bz_context_nT"]
        <= config.southward_bz_support_nT
    )
    joined["mag_support_high_bt"] = (
        joined["B_vector_nT"] >= config.high_bt_support_nT
    )
    return joined


def series_statistics(values: pd.Series, config: ProtocolConfig) -> dict[str, Any]:
    x = pd.to_numeric(values, errors="coerce").dropna()
    if x.empty:
        return {
            "n": 0,
            "mean": None,
            "std": None,
            "min": None,
            "median": None,
            "p90": None,
            "p95": None,
            "p99": None,
            "max": None,
            "above_0p15_count": 0,
            "above_0p15_fraction": None,
            "at_boundary_count": 0,
            "at_boundary_fraction": None,
            "above_band_count": 0,
            "above_band_fraction": None,
        }

    return {
        "n": int(len(x)),
        "mean": float(x.mean()),
        "std": float(x.std(ddof=1)) if len(x) > 1 else 0.0,
        "min": float(x.min()),
        "median": float(x.median()),
        "p90": float(x.quantile(0.90)),
        "p95": float(x.quantile(0.95)),
        "p99": float(x.quantile(0.99)),
        "max": float(x.max()),
        "above_0p15_count": int((x > config.chi_theoretical).sum()),
        "above_0p15_fraction": float((x > config.chi_theoretical).mean()),
        "at_boundary_count": int(
            x.between(config.chi_band_low, config.chi_band_high).sum()
        ),
        "at_boundary_fraction": float(
            x.between(config.chi_band_low, config.chi_band_high).mean()
        ),
        "above_band_count": int((x > config.chi_band_high).sum()),
        "above_band_fraction": float((x > config.chi_band_high).mean()),
    }


def _baseline_sensitivity(
    magnetic: pd.DataFrame,
    config: ProtocolConfig,
    fractions: tuple[float, ...] = (0.80, 0.85, 0.90, 0.95),
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for fraction in fractions:
        trial_config = ProtocolConfig(
            **{
                **asdict(config),
                "minimum_coverage_fraction": fraction,
            }
        )
        trial = compute_frozen_baseline(magnetic, trial_config)
        stats = series_statistics(trial["chi_B24M"], trial_config)
        rows.append(
            {
                "coverage_fraction": fraction,
                "minimum_samples": trial_config.minimum_baseline_samples,
                **stats,
            }
        )
    return rows


def build_summary(
    result: pd.DataFrame,
    magnetic_metadata: dict[str, Any],
    plasma_metadata: dict[str, Any] | None,
    config: ProtocolConfig,
    label: str,
    magnetic_clean: pd.DataFrame,
) -> dict[str, Any]:
    valid = result[result["baseline_valid"]]
    by_regime: dict[str, Any] = {}
    if "kinetic_regime" in result.columns:
        for regime in ["STEADY_KINETIC", "TRANSIENT_KINETIC", "UNCLASSIFIED"]:
            subset = result[
                result["baseline_valid"] & (result["kinetic_regime"] == regime)
            ]
            by_regime[regime] = series_statistics(subset["chi_B24M"], config)

    bt_errors = pd.to_numeric(result["bt_abs_error_nT"], errors="coerce").dropna()
    bt_pass = result["bt_qc_pass"].dropna()
    plasma_matches = (
        int(result["plasma_time_tag"].notna().sum())
        if "plasma_time_tag" in result.columns
        else 0
    )

    source_header = magnetic_metadata.get("source_header") or []
    positional_index_4 = source_header[4] if len(source_header) > 4 else None

    summary = {
        "protocol": {
            "id": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
            "config": asdict(config),
            "expected_baseline_samples": config.expected_baseline_samples,
            "minimum_baseline_samples": config.minimum_baseline_samples,
            "baseline_definition": (
                "median of B_vector_nT over prior (t-24h, t), excluding current sample"
            ),
            "chi_definition": "abs(B_vector_nT - B0) / abs(B0)",
            "clipping": "none",
        },
        "run": {
            "label": label,
            "status": (
                "PRIMARY_STATISTICS_AVAILABLE"
                if int(result["baseline_valid"].sum()) > 0
                else "WARMUP_ONLY_NO_PRIMARY_CHI"
            ),
        },
        "inputs": {
            "magnetic": magnetic_metadata,
            "plasma": plasma_metadata,
        },
        "field_mapping_audit": {
            "source_header": source_header,
            "source_index_4_column": positional_index_4,
            "source_index_6_column": source_header[6] if len(source_header) > 6 else None,
            "canonical_bt_access": "column name 'bt', never row position",
            "authoritative_B": "vector magnitude from bx_gsm/by_gsm/bz_gsm",
        },
        "data_quality": {
            "magnetic_cadence": cadence_audit(
                magnetic_clean, config.cadence_seconds
            ),
            "baseline_status_counts": {
                str(k): int(v)
                for k, v in result["baseline_status"].value_counts().items()
            },
            "bt_consistency": {
                "tested_rows": int(len(bt_errors)),
                "pass_rows": int(bt_pass.astype(bool).sum()) if len(bt_pass) else 0,
                "pass_fraction": (
                    float(bt_pass.astype(bool).mean()) if len(bt_pass) else None
                ),
                "mean_abs_error_nT": float(bt_errors.mean()) if len(bt_errors) else None,
                "p99_abs_error_nT": float(bt_errors.quantile(0.99)) if len(bt_errors) else None,
                "max_abs_error_nT": float(bt_errors.max()) if len(bt_errors) else None,
                "tolerance_nT": config.bt_absolute_tolerance_nT,
            },
            "plasma_join": {
                "matched_rows": plasma_matches,
                "matched_fraction": (
                    float(plasma_matches / len(result)) if len(result) else None
                ),
                "tolerance_seconds": config.plasma_join_tolerance_seconds,
            },
        },
        "results": {
            "all_baseline_valid": series_statistics(valid["chi_B24M"], config),
            "by_kinetic_regime": by_regime,
            "chi_status_counts": {
                str(k): int(v)
                for k, v in result["chi_status"].value_counts().items()
            },
            "kinetic_regime_counts": (
                {
                    str(k): int(v)
                    for k, v in result["kinetic_regime"].value_counts().items()
                }
                if "kinetic_regime" in result.columns
                else {}
            ),
            "baseline_coverage_sensitivity": _baseline_sensitivity(
                magnetic_clean, config
            ),
        },
    }
    return summary


def _fmt(value: Any, digits: int = 6) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.{digits}g}"
    return str(value)


def write_markdown_report(path: Path, summary: dict[str, Any]) -> None:
    protocol = summary["protocol"]
    run = summary["run"]
    quality = summary["data_quality"]
    results = summary["results"]
    overall = results["all_baseline_valid"]
    mapping = summary["field_mapping_audit"]

    lines = [
        f"# CLINE L1 Reconstruction — {run['label']}",
        "",
        f"- Protocol: `{protocol['id']}`",
        f"- Version: `{protocol['version']}`",
        f"- Run status: `{run['status']}`",
        f"- Baseline: {protocol['baseline_definition']}",
        f"- χ: `{protocol['chi_definition']}`",
        f"- Clipping: **{protocol['clipping']}**",
        "",
        "## Field mapping audit",
        "",
        f"- Source header: `{mapping['source_header']}`",
        f"- Source position 4 is `{mapping['source_index_4_column']}`.",
        f"- Source position 6 is `{mapping['source_index_6_column']}`.",
        "- The reconstruction accesses `bt` by name and computes the authoritative magnitude from `bx_gsm`, `by_gsm`, and `bz_gsm`.",
        "",
        "## Input integrity",
        "",
        f"- Magnetic SHA-256: `{summary['inputs']['magnetic']['sha256']}`",
        f"- Magnetic rows after cleaning: `{summary['inputs']['magnetic']['rows_after_cleaning']}`",
        f"- BT/vector QC pass fraction: `{_fmt(quality['bt_consistency']['pass_fraction'])}`",
        f"- Maximum BT/vector absolute error: `{_fmt(quality['bt_consistency']['max_abs_error_nT'])} nT`",
        f"- Baseline status counts: `{quality['baseline_status_counts']}`",
        f"- Plasma matches: `{quality['plasma_join']['matched_rows']}`",
        "",
        "## Primary χ result",
        "",
        f"- Baseline-valid rows: `{overall['n']}`",
        f"- Mean χ: `{_fmt(overall['mean'])}`",
        f"- Median χ: `{_fmt(overall['median'])}`",
        f"- 95th percentile χ: `{_fmt(overall['p95'])}`",
        f"- Maximum χ: `{_fmt(overall['max'])}`",
        f"- χ > 0.15: `{overall['above_0p15_count']}` / `{overall['n']}` (`{_fmt(overall['above_0p15_fraction'])}`)",
        f"- 0.145 ≤ χ ≤ 0.155: `{overall['at_boundary_count']}` / `{overall['n']}` (`{_fmt(overall['at_boundary_fraction'])}`)",
        f"- χ > 0.155: `{overall['above_band_count']}` / `{overall['n']}` (`{_fmt(overall['above_band_fraction'])}`)",
        "",
        "## Independent kinetic split",
        "",
        "The kinetic split uses density, speed, and the absolute speed change over approximately one hour. It does not use χ.",
        "",
    ]

    for regime, stats in results["by_kinetic_regime"].items():
        lines.extend(
            [
                f"### {regime}",
                "",
                f"- Baseline-valid rows: `{stats['n']}`",
                f"- Median χ: `{_fmt(stats['median'])}`",
                f"- Maximum χ: `{_fmt(stats['max'])}`",
                f"- χ > 0.15 fraction: `{_fmt(stats['above_0p15_fraction'])}`",
                f"- Boundary-band fraction: `{_fmt(stats['at_boundary_fraction'])}`",
                "",
            ]
        )

    lines.extend(
        [
            "## Coverage sensitivity audit",
            "",
            "The canonical protocol remains 95% coverage. The following rows show whether the numerical result changes when only the coverage requirement is varied.",
            "",
            "| Coverage | Min samples | Valid n | Median χ | χ > 0.15 fraction | Boundary-band fraction | Max χ |",
            "|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in results["baseline_coverage_sensitivity"]:
        lines.append(
            "| {coverage_fraction:.0%} | {minimum_samples} | {n} | {median} | {above} | {band} | {maxv} |".format(
                coverage_fraction=row["coverage_fraction"],
                minimum_samples=row["minimum_samples"],
                n=row["n"],
                median=_fmt(row["median"]),
                above=_fmt(row["above_0p15_fraction"]),
                band=_fmt(row["at_boundary_fraction"]),
                maxv=_fmt(row["max"]),
            )
        )

    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "This report records what the frozen computation produced. It does not infer a physical mechanism from the distribution. Rows without a complete baseline are retained and explicitly excluded from primary χ statistics.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def make_charts(result: pd.DataFrame, output_dir: Path, config: ProtocolConfig) -> None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return

    valid = result[result["baseline_valid"]].copy()
    if valid.empty:
        return

    fig = plt.figure(figsize=(12, 6))
    ax = fig.add_subplot(111)
    # Points are not connected across telemetry or baseline gaps.
    ax.scatter(valid["time_tag"], valid["chi_B24M"], s=3)
    ax.axhline(config.chi_band_low, linestyle=":", label="0.145")
    ax.axhline(config.chi_theoretical, linestyle="--", label="0.150")
    ax.axhline(config.chi_band_high, linestyle="-.", label="0.155")
    ax.set_title(f"{PROTOCOL_ID}: magnetic χ over time")
    ax.set_xlabel("UTC")
    ax.set_ylabel("χ")
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(output_dir / "chi_timeseries.png", dpi=180)
    plt.close(fig)

    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111)
    ax.hist(valid["chi_B24M"], bins=120)
    ax.axvline(config.chi_band_low, linestyle=":", label="0.145")
    ax.axvline(config.chi_theoretical, linestyle="--", label="0.150")
    ax.axvline(config.chi_band_high, linestyle="-.", label="0.155")
    ax.set_title(f"{PROTOCOL_ID}: magnetic χ distribution")
    ax.set_xlabel("χ")
    ax.set_ylabel("Count")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "chi_histogram.png", dpi=180)
    plt.close(fig)


def run_chain(
    magnetic_path: str | Path,
    plasma_path: str | Path | None,
    output_dir: str | Path,
    label: str,
    config: ProtocolConfig | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    config = config or ProtocolConfig()
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    magnetic, magnetic_metadata = load_magnetic(magnetic_path, config)
    result = compute_frozen_baseline(magnetic, config)

    plasma_metadata: dict[str, Any] | None = None
    if plasma_path:
        plasma, plasma_metadata = load_plasma(plasma_path)
        result = merge_plasma_and_classify(result, plasma, config)
    else:
        result["kinetic_regime"] = "UNCLASSIFIED"

    summary = build_summary(
        result=result,
        magnetic_metadata=magnetic_metadata,
        plasma_metadata=plasma_metadata,
        config=config,
        label=label,
        magnetic_clean=magnetic,
    )

    result.to_csv(out / "cline_l1_rows.csv", index=False)
    (out / "cline_l1_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    write_markdown_report(out / "cline_l1_report.md", summary)
    make_charts(result, out, config)
    return result, summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=f"Run frozen protocol {PROTOCOL_ID}"
    )
    parser.add_argument("--mag", required=True, help="NOAA magnetic JSON/CSV")
    parser.add_argument("--plasma", help="NOAA plasma JSON/CSV")
    parser.add_argument("--outdir", required=True, help="Output directory")
    parser.add_argument("--label", default="CLINE L1 run", help="Run label")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    _, summary = run_chain(
        magnetic_path=args.mag,
        plasma_path=args.plasma,
        output_dir=args.outdir,
        label=args.label,
    )
    overall = summary["results"]["all_baseline_valid"]
    print(f"Protocol: {PROTOCOL_ID}")
    print(f"Run status: {summary['run']['status']}")
    print(f"Baseline-valid rows: {overall['n']}")
    print(f"Median chi: {overall['median']}")
    print(f"Maximum chi: {overall['max']}")
    print(f"chi > 0.15 fraction: {overall['above_0p15_fraction']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
