#!/usr/bin/env python3
"""
Evaluate a single dataset against all signatures.
Auto-detect schema:
- CSV with [timestamp, value] or [timestamp, chi] → time-series φ computed (Imperial Math)
- Spectrogram CSV with [time_s, freq_hz, amplitude] → whistler gaps + envelope φ
- JSON timeseries → converted on the fly
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from scripts.signatures.chi_boundary import score_chi_boundary
from scripts.signatures.binary_harmonics import score_binary_harmonics
from scripts.signatures.whistler_gaps import score_whistler_gaps
from scripts.signatures.fractal_regulator import score_fractal_regulator
from scripts.signatures.electroweak_bridge import score_electroweak_bridge


def rolling_median(series: pd.Series, window: int = 24) -> pd.Series:
    """Compute rolling median baseline."""
    return pd.to_numeric(series, errors="coerce").rolling(window=window, min_periods=max(1, window // 2)).median()


# Small epsilon to prevent division by zero
EPSILON = 1e-12


def compute_phi(x: pd.Series, base: pd.Series) -> pd.Series:
    """Compute normalized perturbation φ = |x−baseline|/baseline (Imperial Math)."""
    base = base.replace(0, np.nan)
    return (pd.to_numeric(x, errors="coerce") - base).abs() / (base + EPSILON)


def load_csv_generic(p: Path):
    """Load a generic CSV and attempt to identify timestamp and value columns."""
    df = pd.read_csv(p)
    # heuristics for timestamp column
    ts = None
    for c in df.columns:
        if any(k in c.lower() for k in ["timestamp", "time_tag", "time", "date", "epoch"]):
            ts = pd.to_datetime(df[c], errors="coerce")
            break
    # heuristics for value column - expanded list for NOAA and other data sources
    vals = None
    value_cols = [
        "value", "chi", "envelope", "phi", "b_total_nt", "b_total", "anomaly",
        "bt", "bz_gsm", "density", "speed", "temperature", "flow_speed",
        "proton_density", "dst", "kp", "ap",
        # Lightning/amplitude data columns
        "peak_amplitude", "amplitude", "amp", "baseline", "signal"
    ]
    for c in df.columns:
        if c.lower() in value_cols:
            vals = pd.to_numeric(df[c], errors="coerce")
            break
    return ts, vals, df


def load_spectrogram(p: Path):
    """Load a spectrogram CSV with time_s, freq_hz, amplitude columns."""
    df = pd.read_csv(p)
    return df


def evaluate(path: str, curriculum: dict):
    """
    Evaluate a single file against all signatures from the curriculum.
    
    Args:
        path: Path to the data file
        curriculum: Loaded curriculum.yaml configuration
    
    Returns:
        dict with evaluation results for all applicable signatures
    """
    p = Path(path)
    out = {"file": str(p), "status": "unknown"}

    if p.suffix.lower() == ".csv":
        ts, vals, df = load_csv_generic(p)
        
        # Check for spectrogram first (before timeseries) to prioritize whistler detection
        # Files with (time_s, freq_hz, amplitude) were being misdetected as timeseries
        # because load_csv_generic matches time_s as a timestamp column.
        # Spectrogram detection must happen first to ensure proper analysis.
        # Check for exact column names first
        if {"time_s", "freq_hz", "amplitude"}.issubset(df.columns):
            spec = load_spectrogram(p)
            agg = spec.groupby("freq_hz")["amplitude"].mean().reset_index()
            wg_res = score_whistler_gaps(
                agg["freq_hz"].to_numpy(),
                agg["amplitude"].to_numpy(),
                tuple(curriculum["signatures"]["whistler_gaps"]["fractions_of_top"]),
                curriculum["signatures"]["whistler_gaps"]["tolerance"]
            )
            out.update({"status": "analyzed", "whistler_gaps": wg_res})
            return out
        
        # Flexible spectrogram column detection (time/freq/amp variants)
        lower_cols = {c.lower(): c for c in df.columns}
        time_variants = ["time", "time_s", "t"]
        freq_variants = ["freq", "freq_hz", "frequency", "f"]
        amp_variants = ["amp", "amplitude", "a", "power", "magnitude"]
        
        time_col = next((lower_cols[v] for v in time_variants if v in lower_cols), None)
        freq_col = next((lower_cols[v] for v in freq_variants if v in lower_cols), None)
        amp_col = next((lower_cols[v] for v in amp_variants if v in lower_cols), None)
        
        if time_col and freq_col and amp_col:
            # Rename to standard columns and process as spectrogram
            spec = df.rename(columns={time_col: "time_s", freq_col: "freq_hz", amp_col: "amplitude"})
            agg = spec.groupby("freq_hz")["amplitude"].mean().reset_index()
            wg_res = score_whistler_gaps(
                agg["freq_hz"].to_numpy(),
                agg["amplitude"].to_numpy(),
                tuple(curriculum["signatures"]["whistler_gaps"]["fractions_of_top"]),
                curriculum["signatures"]["whistler_gaps"]["tolerance"]
            )
            out.update({"status": "analyzed", "whistler_gaps": wg_res})
            return out
        
        # Timeseries processing (after spectrogram check)
        if ts is not None and vals is not None:
            # φ from 24-sample median baseline
            base = rolling_median(vals, 24)
            phi = compute_phi(vals, base)
            chi_res = score_chi_boundary(
                phi,
                tuple(curriculum["signatures"]["chi_boundary"]["boundary_band"]),
                curriculum["signatures"]["chi_boundary"]["max_allowed"],
                curriculum["signatures"]["chi_boundary"]["max_exceptions"]
            )
            frac_res = score_fractal_regulator(
                phi,
                curriculum["signatures"]["fractal_regulator"]["cap_threshold"],
                curriculum["signatures"]["fractal_regulator"]["tail_p95_max"],
                curriculum["signatures"]["fractal_regulator"]["tail_p99_max"]
            )
            # events from peaks? fallback to timestamps as bursts if envelope present
            bh_res = score_binary_harmonics(
                ts,
                curriculum["signatures"]["binary_harmonics"]["main_spacing_hours"],
                curriculum["signatures"]["binary_harmonics"]["spacing_tolerance_hours"],
                curriculum["signatures"]["binary_harmonics"]["min_events"],
                curriculum["signatures"]["binary_harmonics"]["fundamental_hours"]
            )
            ew_res = score_electroweak_bridge(
                ts,
                curriculum["signatures"]["electroweak_bridge"]["fundamental_hours"],
                curriculum["signatures"]["electroweak_bridge"]["tol_hours"],
                curriculum["signatures"]["electroweak_bridge"]["min_presence_fraction"]
            )
            out.update({
                "status": "analyzed",
                "chi_boundary": chi_res,
                "fractal_regulator": frac_res,
                "binary_harmonics": bh_res,
                "electroweak_bridge": ew_res
            })
            return out

    if p.suffix.lower() == ".json":
        # Try to parse timeseries from JSON
        obj = json.loads(Path(p).read_text())
        if isinstance(obj, list) and obj and isinstance(obj[0], dict):
            df = pd.DataFrame(obj)
        elif isinstance(obj, dict) and "data" in obj and isinstance(obj["data"], list):
            df = pd.DataFrame(obj["data"])
        else:
            return {"file": str(p), "status": "skipped", "reason": "no timeseries JSON"}
        # find timestamps and one numeric column
        ts = None
        for c in df.columns:
            if any(k in c.lower() for k in ["time", "timestamp", "date", "epoch"]):
                ts = pd.to_datetime(df[c], errors="coerce")
                break
        num = None
        for c in df.columns:
            if c.lower() not in ["time", "timestamp", "date", "epoch"] and pd.api.types.is_numeric_dtype(df[c]):
                num = pd.to_numeric(df[c], errors="coerce")
                break
        if ts is not None and num is not None:
            base = rolling_median(num, 24)
            phi = compute_phi(num, base)
            chi_res = score_chi_boundary(
                phi,
                tuple(curriculum["signatures"]["chi_boundary"]["boundary_band"]),
                curriculum["signatures"]["chi_boundary"]["max_allowed"],
                curriculum["signatures"]["chi_boundary"]["max_exceptions"]
            )
            frac_res = score_fractal_regulator(
                phi,
                curriculum["signatures"]["fractal_regulator"]["cap_threshold"],
                curriculum["signatures"]["fractal_regulator"]["tail_p95_max"],
                curriculum["signatures"]["fractal_regulator"]["tail_p99_max"]
            )
            out.update({"status": "analyzed", "chi_boundary": chi_res, "fractal_regulator": frac_res})
            return out

    return {"file": str(p), "status": "skipped", "reason": "unrecognized schema"}
