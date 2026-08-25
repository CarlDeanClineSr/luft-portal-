#!/usr/bin/env python3
"""Data-first plasma transition analysis for the CLINE L1 rebuild.

This module consumes canonical ``chi_B24M`` output and independently measured
plasma quantities. It does not cap chi and does not assume that 0.15 is a
boundary. Its purpose is to measure what the continuous chi distribution
tracks: proton beta, dynamic pressure, Alfven Mach number, kinetic regime, and
spectral behavior.

Protocol dependency
-------------------
Analysis observable: CLINE-L1-B24M-TRAIL-v1
Historical ingest:   CDAWEB-DSCOVR-RESTCSV-1M-v1
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Iterable, Mapping

import numpy as np
import pandas as pd

MU0 = 4.0e-7 * np.pi
KB = 1.380649e-23
M_PROTON = 1.67262192369e-27
EPS = np.finfo(float).tiny
L1_SOURCE_REVIEW_CEILING_NT = 1000.0

COLUMN_CANDIDATES: dict[str, tuple[str, ...]] = {
    "timestamp": ("timestamp_utc", "time_tag", "timestamp", "time", "Epoch"),
    "chi": ("chi_B24M",),
    # Transition analysis consumes canonical magnetic magnitude, not a generic
    # B or terrestrial F column. An explicit override is still checked below.
    "b_nt": ("B_vector_nT", "B_total_nT", "B_nT"),
    "density_cm3": ("density_p_cm3", "density_cm3", "Np", "density"),
    "speed_kms": ("speed_km_s", "speed_kms", "V_km_s", "speed"),
    "temperature_k": ("temperature_K", "thermal_temp_K", "THERMAL_TEMP", "temperature"),
    "regime": ("kinetic_regime", "regime", "regime_flag", "storm_phase"),
    "source_dataset": ("source_dataset",),
    "coordinate_frame": ("coordinate_frame",),
    "ingest_protocol": ("ingest_protocol",),
}


class TransitionInputError(ValueError):
    """Raised when input identity is unsafe for L1 plasma transition analysis."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_columns(
    df: pd.DataFrame,
    overrides: Mapping[str, str] | None = None,
    required: Iterable[str] = ("chi", "b_nt", "density_cm3", "speed_kms", "temperature_k"),
) -> dict[str, str]:
    """Resolve semantic fields by explicit override first, then exact names."""
    overrides = dict(overrides or {})
    resolved: dict[str, str] = {}
    for semantic, candidates in COLUMN_CANDIDATES.items():
        if semantic in overrides:
            column = overrides[semantic]
            if column not in df.columns:
                raise KeyError(f"Override for {semantic!r} points to absent column {column!r}")
            resolved[semantic] = column
            continue
        for candidate in candidates:
            if candidate in df.columns:
                resolved[semantic] = candidate
                break

    missing = [semantic for semantic in required if semantic not in resolved]
    if missing:
        raise KeyError(
            "Missing required canonical measurements: "
            + ", ".join(missing)
            + f". Available columns: {list(df.columns)}"
        )
    return resolved


def _unique_text(df: pd.DataFrame, column: str) -> list[str]:
    if column not in df.columns:
        return []
    return sorted(
        {
            str(value).strip()
            for value in df[column].dropna().unique().tolist()
            if str(value).strip()
        }
    )


def validate_transition_input(
    df: pd.DataFrame,
    columns: Mapping[str, str],
    *,
    review_ceiling_nT: float = L1_SOURCE_REVIEW_CEILING_NT,
) -> dict[str, object]:
    """Fail closed on generic, terrestrial, or wrong-scale magnetic inputs.

    The ceiling is an engineering quarantine threshold. It triggers manual
    source review and never clips, caps, or replaces a measured value.
    """
    raw_columns = {str(column) for column in df.columns}
    if "F" in raw_columns or {"F", "B"}.issubset(raw_columns):
        raise TransitionInputError(
            "terrestrial total-field layout detected (column F); refusing plasma transition analysis"
        )
    if {"B", "baseline", "chi"}.issubset(raw_columns):
        raise TransitionInputError(
            "generic B/baseline/chi layout is not canonical CLINE L1 output"
        )
    if columns.get("chi") != "chi_B24M":
        raise TransitionInputError(
            f"chi source must be exactly 'chi_B24M'; resolved {columns.get('chi')!r}"
        )
    if columns.get("b_nt") in {"B", "F", "bt"}:
        raise TransitionInputError(
            f"generic magnetic column {columns.get('b_nt')!r} is not accepted; use canonical B_vector_nT"
        )

    field = pd.to_numeric(df[columns["b_nt"]], errors="coerce").abs()
    finite = field.replace([np.inf, -np.inf], np.nan).dropna()
    if finite.empty:
        raise TransitionInputError("no finite magnetic magnitudes remain")
    field_max = float(finite.max())
    field_median = float(finite.median())
    field_p99 = float(finite.quantile(0.99))
    if field_max > review_ceiling_nT:
        raise TransitionInputError(
            "magnetic magnitude exceeds the L1 source-review ceiling: "
            f"max={field_max:.6g} nT > {review_ceiling_nT:.6g} nT. "
            "Possible ground magnetometer or wrong instrument; no data were altered."
        )

    datasets = _unique_text(df, columns["source_dataset"]) if "source_dataset" in columns else []
    ground_tokens = ("GROUND", "USGS", "INTERMAGNET", "MAGNETIC_OBSERVATORY")
    if any(any(token in value.upper() for token in ground_tokens) for value in datasets):
        raise TransitionInputError(
            f"terrestrial source_dataset detected: {datasets!r}"
        )

    coordinate_frames = (
        _unique_text(df, columns["coordinate_frame"])
        if "coordinate_frame" in columns
        else []
    )
    if coordinate_frames and not set(coordinate_frames).issubset({"GSE", "GSM"}):
        raise TransitionInputError(
            f"unsupported coordinate frame for L1 transition analysis: {coordinate_frames!r}"
        )

    ingest_protocols = (
        _unique_text(df, columns["ingest_protocol"])
        if "ingest_protocol" in columns
        else []
    )
    return {
        "verdict": "PASS",
        "B_column": columns["b_nt"],
        "B_median_nT": field_median,
        "B_p99_nT": field_p99,
        "B_max_nT": field_max,
        "review_ceiling_nT": float(review_ceiling_nT),
        "source_dataset_values": datasets,
        "coordinate_frame_values": coordinate_frames,
        "ingest_protocol_values": ingest_protocols,
        "chi_column": columns["chi"],
        "chi_used_for_source_identity": False,
        "data_clipped": False,
    }


def compute_proton_beta(b_nt: pd.Series, density_cm3: pd.Series, temperature_k: pd.Series) -> pd.Series:
    """Compute scalar proton beta = thermal pressure / magnetic pressure."""
    b_t = pd.to_numeric(b_nt, errors="coerce") * 1e-9
    n_m3 = pd.to_numeric(density_cm3, errors="coerce") * 1e6
    temp = pd.to_numeric(temperature_k, errors="coerce")
    numerator = 2.0 * MU0 * n_m3 * KB * temp
    denominator = np.square(b_t)
    beta = numerator / denominator.where(denominator > EPS)
    return beta.where((n_m3 > 0) & (temp > 0) & (b_t.abs() > 0))


def compute_dynamic_pressure_npa(density_cm3: pd.Series, speed_kms: pd.Series) -> pd.Series:
    """Compute proton dynamic pressure n*m_p*v^2 in nPa."""
    density = pd.to_numeric(density_cm3, errors="coerce")
    speed = pd.to_numeric(speed_kms, errors="coerce")
    pressure = M_PROTON * (density * 1e6) * np.square(speed * 1e3) * 1e9
    return pressure.where((density >= 0) & (speed >= 0))


def compute_alfven_speed_kms(b_nt: pd.Series, density_cm3: pd.Series) -> pd.Series:
    """Compute Alfven speed from field magnitude and proton number density."""
    b_t = pd.to_numeric(b_nt, errors="coerce").abs() * 1e-9
    n_m3 = pd.to_numeric(density_cm3, errors="coerce") * 1e6
    denominator = np.sqrt(MU0 * n_m3 * M_PROTON)
    va = b_t / denominator.where(denominator > EPS) / 1e3
    return va.where((b_t > 0) & (n_m3 > 0))


def add_derived_metrics(df: pd.DataFrame, columns: Mapping[str, str]) -> pd.DataFrame:
    """Return a copy with independently derived plasma metrics."""
    out = df.copy()
    out["chi_B24M"] = pd.to_numeric(out[columns["chi"]], errors="coerce")
    out["B_used_nT"] = pd.to_numeric(out[columns["b_nt"]], errors="coerce")
    out["density_used_cm3"] = pd.to_numeric(out[columns["density_cm3"]], errors="coerce")
    out["speed_used_km_s"] = pd.to_numeric(out[columns["speed_kms"]], errors="coerce")
    out["temperature_used_K"] = pd.to_numeric(out[columns["temperature_k"]], errors="coerce")

    out["proton_beta"] = compute_proton_beta(
        out["B_used_nT"], out["density_used_cm3"], out["temperature_used_K"]
    )
    out["dynamic_pressure_nPa"] = compute_dynamic_pressure_npa(
        out["density_used_cm3"], out["speed_used_km_s"]
    )
    out["alfven_speed_km_s"] = compute_alfven_speed_kms(
        out["B_used_nT"], out["density_used_cm3"]
    )
    out["alfven_mach"] = out["speed_used_km_s"] / out["alfven_speed_km_s"]

    if "timestamp" in columns:
        out["timestamp_utc"] = pd.to_datetime(out[columns["timestamp"]], utc=True, errors="coerce")
    if "regime" in columns:
        out["kinetic_regime_source"] = out[columns["regime"]].astype("string")
    return out


def rank_correlation(x: pd.Series, y: pd.Series) -> tuple[float, int]:
    """Spearman-style rank correlation using pandas ranks, with pairwise NA removal."""
    paired = pd.DataFrame(
        {"x": pd.to_numeric(x, errors="coerce"), "y": pd.to_numeric(y, errors="coerce")}
    ).dropna()
    if len(paired) < 3:
        return float("nan"), len(paired)
    value = paired["x"].rank(method="average").corr(
        paired["y"].rank(method="average")
    )
    return float(value), len(paired)


def beta_band(beta: pd.Series) -> pd.Categorical:
    bins = [-np.inf, 0.1, 0.3, 1.0, 3.0, np.inf]
    labels = ["beta<0.1", "0.1<=beta<0.3", "0.3<=beta<1", "1<=beta<3", "beta>=3"]
    return pd.cut(beta, bins=bins, labels=labels, right=False, ordered=True)


def summarize_chi_by_group(df: pd.DataFrame, group_column: str) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for group, frame in df.groupby(group_column, observed=True, dropna=False):
        chi = pd.to_numeric(frame["chi_B24M"], errors="coerce").dropna()
        if chi.empty:
            continue
        records.append(
            {
                "group": str(group),
                "n": int(len(chi)),
                "chi_mean": float(chi.mean()),
                "chi_median": float(chi.median()),
                "chi_p90": float(chi.quantile(0.90)),
                "chi_p95": float(chi.quantile(0.95)),
                "chi_p99": float(chi.quantile(0.99)),
                "chi_max": float(chi.max()),
                "fraction_gt_0_15": float((chi > 0.15).mean()),
                "fraction_0_145_to_0_155": float(
                    ((chi >= 0.145) & (chi <= 0.155)).mean()
                ),
            }
        )
    return pd.DataFrame.from_records(records)


def estimate_spectral_slope(
    values: pd.Series | np.ndarray,
    cadence_seconds: float,
    min_period_seconds: float = 5.0 * 60.0,
    max_period_seconds: float = 6.0 * 3600.0,
) -> dict[str, float | int]:
    """Estimate a descriptive log-power/log-frequency slope."""
    series = pd.Series(values, dtype="float64")
    finite_fraction = float(series.notna().mean()) if len(series) else 0.0
    if len(series) < 32 or finite_fraction < 0.80 or cadence_seconds <= 0:
        return {"n": int(len(series)), "finite_fraction": finite_fraction, "slope": float("nan")}

    series = series.interpolate(limit_direction="both")
    data = series.to_numpy(dtype=float)
    data = data - np.mean(data)
    if not np.any(np.isfinite(data)) or np.allclose(data, 0.0):
        return {"n": int(len(data)), "finite_fraction": finite_fraction, "slope": float("nan")}

    window = np.hanning(len(data))
    transformed = np.fft.rfft(data * window)
    frequencies = np.fft.rfftfreq(len(data), d=cadence_seconds)
    power = np.square(np.abs(transformed))

    f_min = 1.0 / max_period_seconds
    f_max = 1.0 / min_period_seconds
    mask = (frequencies >= f_min) & (frequencies <= f_max) & (power > 0)
    if int(mask.sum()) < 8:
        return {"n": int(len(data)), "finite_fraction": finite_fraction, "slope": float("nan")}

    slope, intercept = np.polyfit(
        np.log10(frequencies[mask]), np.log10(power[mask]), 1
    )
    return {
        "n": int(len(data)),
        "finite_fraction": finite_fraction,
        "frequency_min_hz": float(frequencies[mask].min()),
        "frequency_max_hz": float(frequencies[mask].max()),
        "slope": float(slope),
        "intercept": float(intercept),
    }


def infer_cadence_seconds(timestamps: pd.Series) -> float:
    ts = pd.to_datetime(timestamps, utc=True, errors="coerce").dropna().sort_values()
    if len(ts) < 3:
        return float("nan")
    deltas = ts.diff().dt.total_seconds().dropna()
    deltas = deltas[deltas > 0]
    return float(deltas.median()) if not deltas.empty else float("nan")


def correlation_table(df: pd.DataFrame) -> pd.DataFrame:
    records = []
    for measurement in (
        "proton_beta",
        "dynamic_pressure_nPa",
        "alfven_mach",
        "B_used_nT",
        "speed_used_km_s",
    ):
        rho, n = rank_correlation(df["chi_B24M"], df[measurement])
        records.append(
            {"measurement": measurement, "rank_correlation_with_chi": rho, "n": n}
        )
    return pd.DataFrame(records)


def run_analysis(
    input_csv: Path,
    output_dir: Path,
    overrides: Mapping[str, str] | None = None,
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    source = pd.read_csv(input_csv, low_memory=False)
    columns = resolve_columns(source, overrides=overrides)
    source_identity = validate_transition_input(source, columns)
    derived = add_derived_metrics(source, columns)

    # No clipping: preserve every finite chi value from the canonical input.
    input_max = pd.to_numeric(source[columns["chi"]], errors="coerce").max()
    output_max = derived["chi_B24M"].max()
    if (
        pd.notna(input_max)
        and pd.notna(output_max)
        and not np.isclose(input_max, output_max, rtol=0, atol=0)
    ):
        raise RuntimeError("chi_B24M changed during transition analysis; refusing output")

    derived["beta_band"] = beta_band(derived["proton_beta"])
    beta_summary = summarize_chi_by_group(derived, "beta_band")
    correlations = correlation_table(derived)

    regime_summary = pd.DataFrame()
    if "kinetic_regime_source" in derived.columns:
        regime_summary = summarize_chi_by_group(derived, "kinetic_regime_source")

    cadence = infer_cadence_seconds(
        derived.get("timestamp_utc", pd.Series(dtype="datetime64[ns, UTC]"))
    )
    spectral = {
        "cadence_seconds": cadence,
        "chi_B24M": (
            estimate_spectral_slope(derived["chi_B24M"], cadence)
            if np.isfinite(cadence)
            else {}
        ),
        "B_used_nT": (
            estimate_spectral_slope(derived["B_used_nT"], cadence)
            if np.isfinite(cadence)
            else {}
        ),
    }

    derived_path = output_dir / "derived_transition_metrics.csv"
    beta_path = output_dir / "chi_by_beta_band.csv"
    corr_path = output_dir / "chi_rank_correlations.csv"
    regime_path = output_dir / "chi_by_kinetic_regime.csv"
    spectral_path = output_dir / "spectral_slopes.json"
    manifest_path = output_dir / "transition_analysis_manifest.json"

    derived.to_csv(derived_path, index=False)
    beta_summary.to_csv(beta_path, index=False)
    correlations.to_csv(corr_path, index=False)
    if not regime_summary.empty:
        regime_summary.to_csv(regime_path, index=False)
    spectral_path.write_text(
        json.dumps(spectral, indent=2, allow_nan=True), encoding="utf-8"
    )

    manifest: dict[str, object] = {
        "analysis_protocol": "CLINE-L1-B24M-TRAIL-v1",
        "transition_analysis_version": "CLINE-L1-TRANSITIONS-v1.1",
        "input_file": str(input_csv),
        "input_sha256": sha256_file(input_csv),
        "rows": int(len(derived)),
        "resolved_columns": columns,
        "source_identity_guard": source_identity,
        "chi_input_max": None if pd.isna(input_max) else float(input_max),
        "chi_output_max": None if pd.isna(output_max) else float(output_max),
        "chi_clipped": False,
        "outputs": {
            "derived": str(derived_path),
            "beta_summary": str(beta_path),
            "correlations": str(corr_path),
            "regime_summary": str(regime_path) if regime_path.exists() else None,
            "spectral": str(spectral_path),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def parse_overrides(items: list[str]) -> dict[str, str]:
    overrides: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"Column override must be semantic=column, got {item!r}")
        semantic, column = item.split("=", 1)
        if semantic not in COLUMN_CANDIDATES:
            raise ValueError(f"Unknown semantic field {semantic!r}")
        overrides[semantic] = column
    return overrides


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", type=Path, required=True, help="Canonical CLINE L1 result CSV"
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--column",
        action="append",
        default=[],
        metavar="SEMANTIC=COLUMN",
        help="Explicit column override; repeat as needed",
    )
    args = parser.parse_args()
    manifest = run_analysis(args.input, args.output_dir, parse_overrides(args.column))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
