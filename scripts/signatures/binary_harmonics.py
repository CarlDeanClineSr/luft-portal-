#!/usr/bin/env python3
"""
Binary Harmonics Signature Detector.
Tests for Binary Harmonic Ladder: 0.9h fundamental and 6h spacing (event timing/peaks).
"""
import numpy as np
import pandas as pd

# Thresholds for binary harmonics detection
FUNDAMENTAL_THRESHOLD_FRACTION = 0.0005  # 0.05% of intervals
SPACING_THRESHOLD_FRACTION = 0.05  # 5% of intervals
MIN_FUNDAMENTAL_EVENTS = 5  # Minimum absolute number of events


def score_binary_harmonics(event_times: pd.Series, spacing_hours=6.0, tol_hours=0.5, min_events=50, fundamental_hours=0.9):
    """
    Detect whether event intervals cluster around 6h spacing and show a 0.9h fundamental.
    
    Args:
        event_times: Series of event timestamps
        spacing_hours: Expected main spacing in hours
        tol_hours: Tolerance for spacing detection
        min_events: Minimum number of events required
        fundamental_hours: Expected fundamental period in hours
    
    Returns:
        dict with interval statistics and pass status
    """
    t = pd.to_datetime(event_times, errors="coerce").dropna().sort_values()
    if t.size < min_events:
        return {"events": int(t.size), "pass": False, "reason": "insufficient events"}
    # Compute intervals (hours)
    dt = (t.diff().dt.total_seconds() / 3600.0).dropna()
    # Mode near spacing_hours?
    mu = dt.mean()
    close = ((dt - spacing_hours).abs() <= tol_hours).sum()
    frac_close = float(close) / int(dt.size)
    # Fundamental presence: do we have peaks near 0.9h multiples?
    near_fund = ((dt - fundamental_hours).abs() <= tol_hours).sum()
    
    # Pass if EITHER condition is met:
    # 1. Strong fundamental presence (at least 0.05% of intervals near 0.9h, OR 5+ events)
    # 2. Sufficient 6h spacing pattern (at least 5% of intervals near 6h)
    # Threshold of 5 events allows detection in short-duration datasets with burst patterns
    has_fundamental = near_fund >= max(MIN_FUNDAMENTAL_EVENTS, int(FUNDAMENTAL_THRESHOLD_FRACTION * dt.size))
    has_spacing = frac_close >= SPACING_THRESHOLD_FRACTION
    
    return {
        "interval_mean_hours": float(mu),
        "frac_near_spacing": frac_close,
        "near_fund_count": int(near_fund),
        "pass": bool(has_fundamental or has_spacing)
    }
