#!/usr/bin/env python3
"""
Generic analysis for any numeric time series:
- Rolling median baseline
- Normalized perturbation phi = |x - baseline| / baseline
- Basic stats, band occupancy, maxima
- Optional spectral density (FFT/periodogram)
"""
from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd
from scipy.signal import welch


def rolling_median(series: pd.Series, window_hours: int) -> pd.Series:
    # For hourly cadence data, window_hours equals number of samples
    return series.rolling(window=window_hours, min_periods=max(1, window_hours // 2)).median()


def compute_phi(series: pd.Series, baseline: pd.Series) -> pd.Series:
    eps = 1e-12
    # For baseline values near zero, use epsilon to avoid division issues
    # Don't replace legitimate zeros with NaN; instead use safe division
    base_safe = baseline.where(baseline.abs() > eps, eps)
    return (series - baseline).abs() / base_safe.abs()


def summarize(series: pd.Series, phi: pd.Series) -> Dict[str, Any]:
    s = series.dropna()
    p = phi.dropna()
    total = int(len(p))
    return {
        "points": total,
        "value_min": float(np.nanmin(s)) if total else np.nan,
        "value_max": float(np.nanmax(s)) if total else np.nan,
        "phi_mean": float(np.nanmean(p)) if total else np.nan,
        "phi_max": float(np.nanmax(p)) if total else np.nan,
        "phi_p95": float(np.nanpercentile(p, 95)) if total else np.nan,
        "band_0p145_0p155_pct": float(((p >= 0.145) & (p <= 0.155)).sum()) / total * 100.0 if total else 0.0,
        "over_0p15_count": int((p > 0.15).sum()) if total else 0,
    }


def spectral_density(series: pd.Series, fs_hz: float = 1.0/3600.0) -> Tuple[np.ndarray, np.ndarray]:
    """
    Welch PSD for evenly sampled series; default fs assumes hourly data.
    
    Args:
        series: Time series data
        fs_hz: Sampling frequency in Hz (default: 1/3600 = hourly cadence).
               This assumption may vary across datasets; caller should verify
               data cadence and adjust accordingly.
    
    Returns:
        (freqs, psd): Frequency array and power spectral density.
                      Returns empty arrays if series has < 256 points.
    """
    x = series.dropna().values
    if len(x) < 256:
        return np.array([]), np.array([])
    freqs, psd = welch(x, fs=fs_hz, nperseg=min(1024, len(x)))
    return freqs, psd
