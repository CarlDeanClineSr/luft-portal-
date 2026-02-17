#!/usr/bin/env python3
import numpy as np
import pandas as pd

# Small epsilon to prevent division by zero in chi calculations
EPSILON = 1e-12

def rolling_median(series: pd.Series, window_hours: int) -> pd.Series:
    return series.rolling(window=window_hours, min_periods=max(1, window_hours//2), center=False).median()

def compute_chi(b_series: pd.Series, baseline: pd.Series) -> pd.Series:
    base = baseline.replace(0, np.nan)
    chi = (b_series - base).abs() / (base + EPSILON)
    return chi


# --- LUFT IMPERIAL MATH CORE ---
# Derived from your lesson: The 0.15 Boundary is the Governor.

def compute_luft_metrics(df):
    """
    Applies the Cline Transform to raw magnetic data.
    
    Args:
        df: DataFrame with a datetime index and a 'B' column containing magnetic field data
        
    Returns:
        DataFrame with additional columns:
            - B_baseline: 24-hour rolling median (The Vacuum Tension)
            - delta_B: Absolute perturbation from baseline
            - chi: Universal ratio (delta_B / B_baseline)
            - status: Classification based on 0.15 boundary
    """
    # 1. Calculate the Rolling Baseline (The Vacuum Tension)
    df['B_baseline'] = df['B'].rolling('24h').median()
    
    # 2. Calculate the Delta (The Perturbation)
    df['delta_B'] = np.abs(df['B'] - df['B_baseline'])
    
    # 3. Calculate Chi (The Universal Ratio)
    # Add small epsilon to prevent division by zero
    df['chi'] = df['delta_B'] / (df['B_baseline'] + EPSILON)
    
    # 4. Status Classifier (The Regulator)
    # We define a tight tolerance for "Locking" based on your 90.48% finding
    tolerance = 0.01 
    
    conditions = [
        (np.abs(df['chi'] - 0.15) <= tolerance),  # Locked at Boundary
        (df['chi'] < (0.15 - tolerance)),         # Recovery / Below
        (df['chi'] > (0.15 + tolerance))          # Precursor / Violation
    ]
    choices = ['AT_BOUNDARY', 'BELOW', 'PRECURSOR_MODE']
    
    df['status'] = np.select(conditions, choices, default='UNCERTAIN')
    
    return df


def generate_storm_report(df):
    """
    Generates the text report confirming the Fractal Regulation.
    
    Args:
        df: DataFrame with computed luft metrics (must have 'status' column)
        
    Returns:
        None (prints report to stdout)
    """
    latest = df.tail(21) # Based on your "21 entries" window
    
    boundary_count = latest[latest['status'] == 'AT_BOUNDARY'].shape[0]
    total = latest.shape[0]
    lock_percentage = (boundary_count / total) * 100
    
    print(f"--- LUFT SYSTEM STATE REPORT ---")
    print(f"Boundary Lock: {lock_percentage:.2f}% (Target: >90% during drive)")
    
    if lock_percentage > 90:
        print("STATUS: FRACTAL REGULATION ACTIVE. System is dumping entropy.")
    else:
        print("STATUS: UNSTABLE / PRECURSOR BUILDUP.")
