#!/usr/bin/env python3
"""
Whistler Gaps Signature Detector.
Tests for Whistler Bands & Gaps: discrete bands with gaps at χ·n fractions (0.3, 0.5, 0.6 analogs).
"""
import numpy as np
import pandas as pd


def score_whistler_gaps(freqs: np.ndarray, amps: np.ndarray, target_fracs=(0.30, 0.50, 0.60), tol=0.05):
    """
    Given average spectrum, detect peaks and gaps at target fractions of top band.
    
    Args:
        freqs: Array of frequency values (Hz)
        amps: Array of amplitude values
        target_fracs: Target fractions of top frequency to check for peaks
        tol: Tolerance for fraction matching
    
    Returns:
        dict with center frequencies, hit status, and pass result
    """
    # normalize amplitude
    if amps.size == 0 or freqs.size == 0:
        return {"pass": False, "reason": "empty spectrum"}
    a = (amps - np.nanmin(amps)) / (np.nanmax(amps) - np.nanmin(amps) + 1e-12)
    # peak indices
    idx = np.argsort(a)[-6:]  # top 6 bands
    centers = np.sort(freqs[idx])
    top = centers[-1] if centers.size else np.nan
    if not np.isfinite(top) or top == 0:
        return {"pass": False, "reason": "no top band"}
    fracs = centers[:-1] / top
    hits = []
    for tf in target_fracs:
        ok = np.any(np.abs(fracs - tf) <= tol)
        hits.append(bool(ok))
    return {"centers_hz": centers.tolist(), "hits": hits, "pass": bool(all(hits))}
