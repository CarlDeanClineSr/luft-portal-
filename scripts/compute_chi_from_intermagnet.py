#!/usr/bin/env python3
"""
Compute χ from INTERMAGNET CSV data
Uses 24-hour rolling median baseline, handles missing data

Usage:
    python scripts/compute_chi_from_intermagnet.py \
        --input data/intermagnet_csv/dou_20260106.csv \
        --output data/intermagnet_chi_calculations_20260106_dou.csv
"""

import argparse
import pandas as pd
import numpy as np


def compute_chi(df, baseline_window_hours=24):
    """
    Compute χ = |ΔB / B_baseline| for each timestamp
    
    Args:
        df: DataFrame with columns [timestamp, B_total]
        baseline_window_hours:  Rolling median window size (default 24 hours)
    
    Returns:
        DataFrame with added columns [B_baseline, delta_B, chi]
    """
    # Handle missing values (forward fill, then backward fill)
    df['B_total'] = df['B_total'].ffill().bfill()
    
    # Calculate rolling baseline (24-hour window = 1440 minutes)
    window_size = baseline_window_hours * 60
    df['B_baseline'] = df['B_total'].rolling(
        window=window_size, 
        min_periods=1, 
        center=True
    ).median()
    
    # Calculate perturbation
    df['delta_B'] = (df['B_total'] - df['B_baseline']).abs()
    
    # Calculate χ (normalized perturbation)
    df['chi'] = df['delta_B'] / df['B_baseline']
    
    # Replace inf/nan with 0 (edge cases where baseline ≈ 0)
    df['chi'] = df['chi'].replace([np.inf, -np.inf], 0).fillna(0)
    
    return df


if __name__ == '__main__': 
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='Input CSV with B_total column')
    parser.add_argument('--output', required=True, help='Output CSV with chi calculations')
    parser.add_argument('--baseline-hours', type=int, default=24, help='Baseline window (hours)')
    args = parser.parse_args()
    
    # Load data
    df = pd.read_csv(args.input, parse_dates=['timestamp'])
    
    # Compute χ
    df = compute_chi(df, baseline_window_hours=args.baseline_hours)
    
    # Save results
    df.to_csv(args.output, index=False)
    
    # Print stats
    chi_max = df['chi'].max()
    chi_mean = df['chi'].mean()
    chi_median = df['chi'].median()
    violations = (df['chi'] > 0.15).sum()
    
    print(f"📊 χ Statistics ({len(df)} points):")
    print(f"   χ_max:     {chi_max:.6f}")
    print(f"   χ_mean:   {chi_mean:.6f}")
    print(f"   χ_median: {chi_median:.6f}")
    print(f"   Violations (χ > 0.15): {violations}")
    print(f"✅ Saved → {args.output}")
