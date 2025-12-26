#!/usr/bin/env python3
"""
Compute χ (normalized amplitude) from Oulu Cosmic Ray data
Tests if χ caps at 0.15 in non-plasma domain
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

def compute_chi_from_oulu():
    """Compute χ from Oulu cosmic ray neutron monitor data"""
    
    # Find all Oulu CSV files
    data_dir = Path("data/oulu_cr")
    csv_files = sorted(data_dir.glob("oulu_cr_*.csv"))
    
    if not csv_files:
        print("⚠️ No Oulu data found")
        return False
    
    # Load and combine all data
    all_data = []
    for csv_file in csv_files:
        try: 
            df = pd.read_csv(csv_file)
            if 'neutron_count' in df.columns:
                all_data.append(df)
        except Exception as e:
            print(f"⚠️ Error reading {csv_file}: {e}")
    
    if not all_data: 
        print("⚠️ No valid Oulu data found")
        return False
    
    # Combine all data
    combined = pd.concat(all_data, ignore_index=True)
    combined['neutron_count'] = pd.to_numeric(combined['neutron_count'], errors='coerce')
    combined = combined.dropna(subset=['neutron_count'])
    
    if len(combined) < 10:
        print(f"⚠️ Not enough Oulu data points: {len(combined)}")
        return False
    
    # Compute baseline (30-day rolling mean, or full mean if < 30 days)
    if len(combined) >= 720:  # 30 days * 24 hours
        combined['baseline'] = combined['neutron_count'].rolling(window=720, min_periods=10).mean()
    else:
        combined['baseline'] = combined['neutron_count']. mean()
    
    # Compute χ = |deviation| / baseline
    combined['deviation'] = combined['neutron_count'] - combined['baseline']
    combined['chi'] = np.abs(combined['deviation']) / combined['baseline']
    
    # Cap at 0.15 (test if natural cap exists)
    combined['chi_capped'] = combined['chi'].clip(upper=0.15)
    
    # Add timestamp
    combined['timestamp_utc'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    
    # Save results
    output_dir = Path("results/oulu_chi")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    month_str = datetime.utcnow().strftime('%Y_%m')
    output_file = output_dir / f"oulu_chi_{month_str}.csv"
    
    # Select columns
    result = combined[['year', 'month', 'neutron_count', 'baseline', 'chi', 'chi_capped', 'timestamp_utc']]
    result.to_csv(output_file, index=False)
    
    # Print stats
    chi_max = combined['chi']. max()
    chi_mean = combined['chi'].mean()
    cap_violations = (combined['chi'] > 0.15).sum()
    
    print(f"✅ Oulu χ calculated:  {len(combined)} data points")
    print(f"   χ max: {chi_max:. 4f}")
    print(f"   χ mean: {chi_mean:.4f}")
    print(f"   Cap violations (χ > 0.15): {cap_violations}")
    print(f"   Saved:  {output_file}")
    
    if chi_max <= 0.15:
        print(f"🎯 **OULU χ CAP CONFIRMED AT 0.15** — Universal boundary detected!")
    
    return True

if __name__ == "__main__":
    success = compute_chi_from_oulu()
    exit(0 if success else 1)
