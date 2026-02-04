#!/usr/bin/env python3
"""
Imperial Physics Observatory: Historical Chi Calculation
Calculate chi parameter from historical magnetometer data
"""

import pandas as pd
import numpy as np
import argparse
from pathlib import Path

def calculate_baseline(distance_au=1.0):
    """
    Calculate baseline magnetic field strength at given distance from Sun
    
    Args:
        distance_au: Distance from Sun in AU
        
    Returns:
        Baseline field strength in nT
    """
    # Parker spiral baseline at 1 AU
    B_baseline_1au = 5.0  # nT (typical quiet solar wind)
    
    # Inverse square law
    B_baseline = B_baseline_1au / (distance_au ** 2)
    
    return B_baseline

def calculate_chi(B_measured, B_baseline):
    """
    Calculate chi parameter
    
    Args:
        B_measured: Measured total field strength (nT)
        B_baseline: Baseline field strength (nT)
        
    Returns:
        Chi parameter (dimensionless)
    """
    delta_B = np.abs(B_measured - B_baseline)
    chi = delta_B / B_baseline
    return chi

def process_magnetometer_data(df, baseline_field=5.0):
    """
    Process magnetometer data and calculate chi
    
    Args:
        df: DataFrame with magnetometer measurements (X, Y, Z, F columns)
        baseline_field: Baseline field strength in nT
        
    Returns:
        DataFrame with chi calculations added
    """
    # Calculate total field if not present
    if 'F' not in df.columns:
        if all(col in df.columns for col in ['X', 'Y', 'Z']):
            df['F'] = np.sqrt(df['X']**2 + df['Y']**2 + df['Z']**2)
        else:
            raise ValueError("Need either F column or X,Y,Z columns")
    
    # Calculate chi
    df['B_baseline'] = baseline_field
    df['chi'] = calculate_chi(df['F'], df['B_baseline'])
    
    # Flag boundary violations
    df['chi_at_boundary'] = (df['chi'] >= 0.15) & (df['chi'] <= 0.16)
    df['chi_violation'] = df['chi'] > 0.16
    
    # Status
    df['chi_status'] = 'BELOW'
    df.loc[df['chi_at_boundary'], 'chi_status'] = 'AT_BOUNDARY'
    df.loc[df['chi_violation'], 'chi_status'] = 'VIOLATION'
    
    return df

def main():
    parser = argparse.ArgumentParser(description='Calculate chi from historical magnetometer data')
    parser.add_argument('--input', required=True, help='Input CSV path (magnetometer data)')
    parser.add_argument('--output', required=True, help='Output CSV path (with chi calculations)')
    parser.add_argument('--baseline', type=float, default=5.0, help='Baseline field in nT (default: 5.0)')
    
    args = parser.parse_args()
    
    print(f"Loading magnetometer data: {args.input}")
    df = pd.read_csv(args.input)
    print(f"  Loaded {len(df)} records")
    
    print(f"Calculating chi (baseline: {args.baseline} nT)")
    df = process_magnetometer_data(df, args.baseline)
    
    # Ensure output directory exists
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    
    # Save results
    df.to_csv(args.output, index=False)
    print(f"Results saved to: {args.output}")
    
    # Print summary
    print("\nChi Summary:")
    print(f"  Mean chi: {df['chi'].mean():.4f}")
    print(f"  Max chi: {df['chi'].max():.4f}")
    print(f"  At boundary: {df['chi_at_boundary'].sum()} records")
    print(f"  Violations: {df['chi_violation'].sum()} records")

if __name__ == '__main__':
    main()
