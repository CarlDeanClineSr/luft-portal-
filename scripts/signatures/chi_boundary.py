#!/usr/bin/env python3
"""
Chi Boundary Signature Detector.
Tests for Causality Precursor Law: χ = A_IC / 3 — boundary band occupancy and no-breach proof.
"""
import numpy as np
import pandas as pd


def score_chi_boundary(phi: pd.Series, boundary_band=(0.145, 0.155), cap=0.15, max_exceptions=0):
    """
    Score a time-series for chi boundary compliance.
    
    Args:
        phi: Normalized perturbation series (φ = |x−baseline|/baseline)
        boundary_band: Tuple of (lower, upper) bounds for the boundary region
        cap: Maximum allowed value (hard ceiling)
        max_exceptions: Maximum number of allowed exceptions above the cap
    
    Returns:
        dict with band_pct, over_cap_count, and pass status
    """
    phi = pd.to_numeric(phi, errors="coerce").dropna()
    total = int(phi.size)
    if total == 0:
        return {"band_pct": np.nan, "over_cap_count": 0, "pass": True, "reason": "no data"}
    band_pct = float(((phi >= boundary_band[0]) & (phi <= boundary_band[1])).sum()) / total * 100.0
    over_cap = int((phi > cap).sum())
    return {
        "band_pct": band_pct,
        "over_cap_count": over_cap,
        "pass": bool(over_cap <= max_exceptions)
    }
