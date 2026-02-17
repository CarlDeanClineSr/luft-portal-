"""
Storm Phase Analyzer

Analyzes χ (chi) timeseries and classifies observations into storm phases:
PRE, PEAK, POST, UNKNOWN.

This module provides robust storm phase classification based on χ amplitude
relative to the critical boundary (χ ≈ 0.15).
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple


def analyze_storm_phases(
    df: pd.DataFrame,
    chi_boundary_min: float = 0.145,
    chi_boundary_max: float = 0.155,
    min_peak_points: int = 3,
) -> Tuple[Dict[str, Any], pd.DataFrame]:
    """
    Analyze χ timeseries and classify observations into storm phases:
    PRE, PEAK, POST, UNKNOWN.

    Phase logic (single-storm, simple and robust):
      - PEAK:  any point where chi is within [chi_boundary_min, chi_boundary_max]
      - PRE:   points before the first PEAK point
      - POST:  points after the last PEAK point
      - UNKNOWN: NaN / invalid chi

    If no PEAK points exist:
      - All valid points are labeled PRE (quiet period, no storm yet)

    Args:
        df: DataFrame with columns:
             - 'timestamp' (datetime-like or string)
             - 'chi_amplitude' (float)
        chi_boundary_min: lower bound of χ boundary (inclusive)
        chi_boundary_max: upper bound of χ boundary (inclusive)
        min_peak_points: minimum number of PEAK samples to call it a storm

    Returns:
        tuple: (summary, df_with_phases)
            summary: dict with:
              - 'total_obs'
              - 'num_pre'
              - 'num_peak'
              - 'num_post'
              - 'num_unknown'
              - 'pct_pre'
              - 'pct_peak'
              - 'pct_post'
              - 'pct_unknown'
              - 'has_storm'
              - 'first_peak_time'
              - 'last_peak_time'
              - 'chi_boundary_min'
              - 'chi_boundary_max'
            df_with_phases: DataFrame with new 'phase' column
    """

    df = df.copy()

    # Ensure timestamp is datetime
    if 'timestamp' not in df.columns:
        # Try alternate column names
        if 'timestamp_utc' in df.columns:
            df['timestamp'] = df['timestamp_utc']
        else:
            raise ValueError("DataFrame must contain 'timestamp' or 'timestamp_utc' column")

    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

    # Initialize phase column
    df['phase'] = 'UNKNOWN'

    # Handle missing or invalid χ
    # First, ensure chi_amplitude is numeric
    df['chi_amplitude'] = pd.to_numeric(df['chi_amplitude'], errors='coerce')
    chi = df['chi_amplitude']
    valid_mask = chi.notna() & np.isfinite(chi)

    # Detect PEAK points (χ in boundary band)
    peak_mask = (
        valid_mask &
        (chi >= chi_boundary_min) &
        (chi <= chi_boundary_max)
    )

    num_peak_points = peak_mask.sum()

    if num_peak_points >= min_peak_points:
        # We consider this a storm event
        first_peak_idx = df.index[peak_mask][0]
        last_peak_idx = df.index[peak_mask][-1]

        first_peak_time = df.loc[first_peak_idx, 'timestamp']
        last_peak_time = df.loc[last_peak_idx, 'timestamp']

        # Assign PEAK
        df.loc[peak_mask, 'phase'] = 'PEAK'

        # Assign PRE: valid points before first peak
        pre_mask = valid_mask & (df.index < first_peak_idx)
        df.loc[pre_mask, 'phase'] = 'PRE'

        # Assign POST: valid points after last peak
        post_mask = valid_mask & (df.index > last_peak_idx)
        df.loc[post_mask, 'phase'] = 'POST'

        has_storm = True
    else:
        # No clear PEAK: treat all valid points as PRE (quiet period)
        df.loc[valid_mask, 'phase'] = 'PRE'
        has_storm = False
        first_peak_time = None
        last_peak_time = None

    # Aggregate statistics
    total_obs = len(df)
    num_pre = (df['phase'] == 'PRE').sum()
    num_peak = (df['phase'] == 'PEAK').sum()
    num_post = (df['phase'] == 'POST').sum()
    num_unknown = (df['phase'] == 'UNKNOWN').sum()

    def pct(n: int) -> float:
        return float(n) * 100.0 / total_obs if total_obs > 0 else 0.0

    summary = {
        'total_obs': int(total_obs),
        'num_pre': int(num_pre),
        'num_peak': int(num_peak),
        'num_post': int(num_post),
        'num_unknown': int(num_unknown),
        'pct_pre': pct(num_pre),
        'pct_peak': pct(num_peak),
        'pct_post': pct(num_post),
        'pct_unknown': pct(num_unknown),
        'has_storm': bool(has_storm),
        'first_peak_time': first_peak_time.isoformat() if first_peak_time is not None and pd.notna(first_peak_time) else None,
        'last_peak_time': last_peak_time.isoformat() if last_peak_time is not None and pd.notna(last_peak_time) else None,
        'chi_boundary_min': float(chi_boundary_min),
        'chi_boundary_max': float(chi_boundary_max),
    }

    return summary, df
