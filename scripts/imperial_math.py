#!/usr/bin/env python3
import numpy as np
import pandas as pd

def rolling_median(series: pd.Series, window_hours: int) -> pd.Series:
    return series.rolling(window=window_hours, min_periods=max(1, window_hours//2), center=False).median()

def compute_chi(b_series: pd.Series, baseline: pd.Series) -> pd.Series:
    eps = 1e-12
    base = baseline.replace(0, np.nan)
    chi = (b_series - base).abs() / (base + eps)
    return chi
