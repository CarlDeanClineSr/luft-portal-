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
    
    # Find all Oulu TXT files (not CSV)
    data_dir = Path("data/oulu_cr")
    txt_files = sorted(data_dir.glob("oulu_cr_*.txt"))
    
    if not txt_files:
        print("⚠️ No Oulu data found")
        return False
    
    # Load and parse all TXT files
    all_data = []
    for txt_file in txt_files:
        try: 
            with open(txt_file, 'r') as f:
                lines = f.readlines()
            
            # Parse data lines (skip headers and comments)
            for line in lines: 
                if line.startswith('+') or line.startswith('Year') or line.startswith('References') or len(line. strip()) == 0:
                    continue
                if line.strip().startswith('[') or line.strip().startswith('The monthly'):
                    continue
                
                parts = line.split()
                if len(parts) >= 2 and parts[0]. isdigit():
                    year = int(parts[0])
                    # Monthly values (columns 1-12)
                    for month_idx, val in enumerate(parts[1:13], start=1):
                        if val.strip() != '-':
                            try:
                                modulation = float(val)
                                all_data.append({
                                    'year':  year,
                                    'month': month_idx,
                                    'modulation_mv': modulation
                                })
                            except ValueError:
                                continue
        except Exception as e:
            print(f"⚠️ Error reading {txt_file}: {e}")
    
    if not all_data:
        print("⚠️ No valid Oulu data found")
        return False
    
    # Convert to DataFrame
    df = pd. DataFrame(all_data)
    df = df.sort_values(['year', 'month'])
    
    if len(df) < 10:
        print(f"⚠️ Not enough Oulu data points:  {len(df)}")
        return False
    
    # Compute baseline (30-month rolling mean or full mean)
    if len(df) >= 360:
        df['baseline'] = df['modulation_mv'].rolling(window=360, min_periods=10).mean()
    else:
        df['baseline'] = df['modulation_mv'].mean()
    
    # Compute χ = |deviation| / baseline
    df['deviation'] = df['modulation_mv'] - df['baseline']
    df['chi'] = np.abs(df['deviation']) / df['baseline']
    
    # Cap at 0.15
    df['chi_capped'] = df['chi']. clip(upper=0.15)
    
    # Add timestamp
    df['timestamp_utc'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    
    # Save results
    output_dir = Path("results/oulu_chi")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    month_str = datetime.utcnow().strftime('%Y_%m')
    output_file = output_dir / f"oulu_chi_{month_str}. csv"
    
    # Select columns
    result = df[['year', 'month', 'modulation_mv', 'baseline', 'chi', 'chi_capped', 'timestamp_utc']]
    result. to_csv(output_file, index=False)
    
    # Print stats
    chi_max = df['chi']. max()
    chi_mean = df['chi'].mean()
    cap_violations = (df['chi'] > 0.15).sum()
    
    print(f"✅ Oulu χ calculated:  {len(df)} data points")
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
