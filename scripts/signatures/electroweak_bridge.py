#!/usr/bin/env python3
"""
Electroweak Bridge Signature Detector.
Tests for Electroweak–MHD Bridge: presence of 0.9h packets and scale-consistent modulation.
"""
import numpy as np
import pandas as pd


def score_electroweak_bridge(times: pd.Series, fundamental_hours=0.9, tol_hours=0.3, min_presence_frac=0.10):
    """
    Check for presence of ~0.9h packet modulation in a sequence of burst timestamps.
    
    Args:
        times: Series of burst/event timestamps
        fundamental_hours: Expected fundamental period in hours
        tol_hours: Tolerance for fundamental detection
        min_presence_frac: Minimum fraction of intervals near fundamental
    
    Returns:
        dict with near_0p9h_frac and pass status
    """
    t = pd.to_datetime(times, errors="coerce").dropna().sort_values()
    if t.size < 10:
        return {"pass": False, "reason": "insufficient bursts"}
    dt = (t.diff().dt.total_seconds() / 3600.0).dropna()
    near = ((dt - fundamental_hours).abs() <= tol_hours).sum()
    frac = float(near) / int(dt.size)
    return {"near_0p9h_frac": frac, "pass": bool(frac >= min_presence_frac)}
