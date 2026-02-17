#!/usr/bin/env python3
"""
Imperial Physics Observatory: Calculate Chi Across All Missions
Processes daily harvest data and calculates chi for all measurements
"""

import pandas as pd
import numpy as np
import argparse
from pathlib import Path
import glob

def calculate_chi(B_measured, B_baseline):
    """Calculate chi parameter"""
    delta_B = np.abs(B_measured - B_baseline)
    chi = delta_B / B_baseline
    return chi

def process_mission_data(filepath, baseline=5.0):
    """Process a single mission's data file"""
    df = pd.read_csv(filepath)
    
    # Determine total field column
    if 'Bt' in df.columns:
        B_total = df['Bt']
    elif 'BGSE' in df.columns:
        B_total = df['BGSE']
    elif 'BFIELD' in df.columns:
        B_total = df['BFIELD']
    else:
        # Calculate from components if available
        if all(col in df.columns for col in ['Bx_gse', 'By_gse', 'Bz_gse']):
            B_total = np.sqrt(df['Bx_gse']**2 + df['By_gse']**2 + df['Bz_gse']**2)
        else:
            return pd.DataFrame()
    
    # Calculate chi
    df['B_total'] = B_total
    df['B_baseline'] = baseline
    df['chi'] = calculate_chi(B_total, baseline)
    
    # Flag boundary conditions
    df['chi_at_boundary'] = (df['chi'] >= 0.14) & (df['chi'] <= 0.16)
    df['chi_violation'] = df['chi'] > 0.16
    
    df['chi_status'] = 'BELOW'
    df.loc[df['chi_at_boundary'], 'chi_status'] = 'AT_BOUNDARY'
    df.loc[df['chi_violation'], 'chi_status'] = 'VIOLATION'
    
    return df[['timestamp', 'mission', 'B_total', 'B_baseline', 'chi', 'chi_status']]

def main():
    parser = argparse.ArgumentParser(description='Calculate chi across all missions')
    parser.add_argument('--input_dir', required=True, help='Input directory with daily mission data')
    parser.add_argument('--output', required=True, help='Output CSV file')
    parser.add_argument('--baseline', type=float, default=5.0, help='Baseline field (nT)')
    
    args = parser.parse_args()
    
    # Find all mission data files
    input_path = Path(args.input_dir)
    csv_files = list(input_path.glob('**/*.csv'))
    
    print(f"Processing {len(csv_files)} mission data files...")
    
    all_data = []
    for filepath in csv_files:
        print(f"  Processing: {filepath.name}")
        df = process_mission_data(filepath, args.baseline)
        if len(df) > 0:
            all_data.append(df)
    
    if all_data:
        # Combine all missions
        combined = pd.concat(all_data, ignore_index=True)
        
        # Sort by timestamp
        combined = combined.sort_values('timestamp')
        
        # Save
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        combined.to_csv(args.output, index=False)
        
        print(f"\nCombined chi data saved: {args.output}")
        print(f"  Total measurements: {len(combined):,}")
        print(f"  At boundary: {(combined['chi_status'] == 'AT_BOUNDARY').sum():,}")
        print(f"  Violations: {(combined['chi_status'] == 'VIOLATION').sum():,}")
        print(f"  Max chi: {combined['chi'].max():.4f}")
    else:
        print("\nNo data processed")

if __name__ == '__main__':
    main()
