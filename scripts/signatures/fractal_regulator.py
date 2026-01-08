#!/usr/bin/env python3
"""
Fractal Regulator Signature Detector.
Tests for χ–Fractal Regulator: capped normalized perturbations across scales (tail behavior).
"""
import numpy as np
import pandas as pd


def score_fractal_regulator(phi: pd.Series, cap=0.15, p95_max=0.20, p99_max=0.25):
    """
    Score a time-series for fractal regulator compliance.
    
    Args:
        phi: Normalized perturbation series (φ = |x−baseline|/baseline)
        cap: Cap threshold for counting exceedances
        p95_max: Maximum allowed 95th percentile
        p99_max: Maximum allowed 99th percentile
    
    Returns:
        dict with percentile values, over_cap_count, and pass status
    """
    phi = pd.to_numeric(phi, errors="coerce").dropna()
    total = int(phi.size) or 1
    p95 = float(np.nanpercentile(phi, 95)) if total else np.nan
    p99 = float(np.nanpercentile(phi, 99)) if total else np.nan
    over = int((phi > cap).sum())
    return {
        "phi_p95": p95,
        "phi_p99": p99,
        "over_cap_count": over,
        "pass": (p95 <= p95_max and p99 <= p99_max)
    }
