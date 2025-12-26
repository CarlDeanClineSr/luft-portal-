#!/usr/bin/env python3
"""
Compute χ (normalized amplitude) from INTERMAGNET magnetic field data
Tests if χ caps at 0.15 in geomagnetic domain
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

def compute_chi_from_intermagnet():
    """Compute χ from INTERMAGNET magnetic field strength data"""
    
    # Find all INTERMAGNET CSV files
    data_dir = Path("data/intermagnet")
    csv_files = sorted(data_dir.glob("intermagnet_*. csv"))
    
    if not csv_files:
        print("⚠️ No INTERMAGNET data found")
        return False
    
    # Load and combine all data
    all_data = []
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            # Look for magnetic field columns (B_total, Bx, By, Bz, or similar)
            if any(col in df.columns for col in ['B_total', 'Bx', 'By', 'Bz', 'F']):
                all_data.append(df)
        except Exception as e:
            print(f"⚠️ Error reading {csv_file}: {e}")
    
    if not all_data:
        print("⚠️ No valid INTERMAGNET data found")
        return False
    
    # Combine all data
    combined = pd.concat(all_data, ignore_index=True)
    
    # Compute total field if components exist
    if 'B_total' in combined.columns:
        combined['field_strength'] = combined['B_total']
    elif all(col in combined.columns for col in ['Bx', 'By', 'Bz']):
        combined['field_strength'] = np.sqrt(
            combined['Bx']**2 + combined['By']**2 + combined['Bz']**2
        )
    elif 'F' in combined.columns:
        combined['field_strength'] = combined['F']
    else:
        print("⚠️ No recognizable magnetic field columns found")
        return False
    
    combined['field_strength'] = pd.to_numeric(combined['field_strength'], errors='coerce')
    combined = combined.dropna(subset=['field_strength'])
    
    if len(combined) < 10:
        print(f"⚠️ Not enough INTERMAGNET data points: {len(combined)}")
        return False
    
    # Compute baseline (30-day rolling mean)
    if len(combined) >= 720:  # 30 days * 24 hours
        combined['baseline'] = combined['field_strength'].rolling(window=720, min_periods=10).mean()
    else:
        combined['baseline'] = combined['field_strength'].mean()
    
    # Compute χ = |deviation| / baseline
    combined['deviation'] = combined['field_strength'] - combined['baseline']
    combined['chi'] = np.abs(combined['deviation']) / combined['baseline']
    
    # Cap at 0.15
    combined['chi_capped'] = combined['chi'].clip(upper=0.15)
    
    # Add timestamp
    if 'timestamp' not in combined.columns:
        combined['timestamp_utc'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    else:
        combined['timestamp_utc'] = combined['timestamp']
    
    # Save results
    output_dir = Path("results/intermagnet_chi")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    month_str = datetime.utcnow().strftime('%Y_%m')
    output_file = output_dir / f"intermagnet_chi_{month_str}. csv"
    
    # Select columns
    result = combined[['timestamp_utc', 'field_strength', 'baseline', 'chi', 'chi_capped']]
    result.to_csv(output_file, index=False)
    
    # Print stats
    chi_max = combined['chi'].max()
    chi_mean = combined['chi'].mean()
    cap_violations = (combined['chi'] > 0.15).sum()
    
    print(f"✅ INTERMAGNET χ calculated: {len(combined)} data points")
    print(f"   χ max: {chi_max:.4f}")
    print(f"   χ mean: {chi_mean:.4f}")
    print(f"   Cap violations (χ > 0.15): {cap_violations}")
    print(f"   Saved: {output_file}")
    
    if chi_max <= 0.15:
        print(f"🎯 **INTERMAGNET χ CAP CONFIRMED AT 0.15** — Universal boundary in magnetic data!")
    
    return True

if __name__ == "__main__":
    success = compute_chi_from_intermagnet()
    exit(0 if success else 1)
