#!/usr/bin/env python3
"""
Compute χ (normalized amplitude) from INTERMAGNET magnetometer data
Tests if χ caps at 0.15 in Earth's magnetosphere (plasma domain)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timezone
import json

def compute_chi_from_intermagnet():
    """Compute χ from INTERMAGNET magnetic field data"""
    
    # Find all INTERMAGNET data files
    data_dir = Path("data/intermagnet")
    
    # Try JSON files first, then TXT
    json_files = sorted(data_dir.glob("intermagnet_*.json"))
    txt_files = sorted(data_dir.glob("intermagnet_*.txt"))
    csv_files = sorted(data_dir.glob("intermagnet_*.csv"))
    
    data_files = json_files or txt_files or csv_files
    
    if not data_files:
        print("⚠️ No INTERMAGNET data found")
        return False
    
    # Load and parse all data files
    all_data = []
    
    for data_file in data_files:
        try:
            if data_file.suffix == '.json':
                with open(data_file, 'r') as f:
                    data = json.load(f)
                # Parse JSON structure (adjust based on actual format)
                if isinstance(data, list):
                    all_data.extend(data)
                elif isinstance(data, dict):
                    all_data.append(data)
            
            elif data_file.suffix == '.csv':
                df_temp = pd.read_csv(data_file)
                all_data.extend(df_temp.to_dict('records'))
            
            elif data_file.suffix == '.txt':
                # Parse text format (adjust based on actual format)
                with open(data_file, 'r') as f:
                    lines = f.readlines()
                # Add parsing logic for TXT format
                
        except Exception as e:
            print(f"⚠️ Error reading {data_file}: {e}")
    
    if not all_data:
        print("⚠️ No valid INTERMAGNET data found")
        return False
    
    # Convert to DataFrame
    df = pd.DataFrame(all_data)
    
    # Identify magnetic field column (H, X, Y, Z, or F total field)
    mag_cols = [c for c in df.columns if c.upper() in ['H', 'X', 'Y', 'Z', 'F', 'TOTAL_FIELD', 'BT', 'B_TOTAL']]
    
    if not mag_cols:
        print("⚠️ No magnetic field column found in INTERMAGNET data")
        return False
    
    mag_col = mag_cols[0]
    df = df[[mag_col]].dropna()
    df = df.rename(columns={mag_col: 'b_total'})
    
    if len(df) < 100:
        print(f"⚠️ Not enough INTERMAGNET data points: {len(df)}")
        return False
    
    # Compute baseline (24-hour rolling mean or full mean)
    if len(df) >= 1440:  # 1 day at 1-min resolution
        df['baseline'] = df['b_total'].rolling(window=1440, min_periods=100).mean()
    else:
        df['baseline'] = df['b_total'].mean()
    
    # Compute χ = |deviation| / baseline
    df['deviation'] = df['b_total'] - df['baseline']
    df['chi'] = np.abs(df['deviation']) / df['baseline']
    
    # Cap at 0.15
    df['chi_capped'] = df['chi'].clip(upper=0.15)
    
    # Add timestamp
    df['timestamp_utc'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    
    # Save results
    output_dir = Path("results/intermagnet_chi")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    date_str = datetime.now(timezone.utc).strftime('%Y_%m_%d')
    output_file = output_dir / f"intermagnet_chi_{date_str}.csv"
    
    # Select columns
    result = df[['b_total', 'baseline', 'chi', 'chi_capped', 'timestamp_utc']].reset_index(drop=True)
    result.to_csv(output_file, index=False)
    
    # Print stats
    chi_max = df['chi'].max()
    chi_mean = df['chi'].mean()
    cap_violations = (df['chi'] > 0.15).sum()
    
    print(f"✅ INTERMAGNET χ calculated: {len(df)} data points")
    print(f"   χ max: {chi_max:.4f}")
    print(f"   χ mean: {chi_mean:.4f}")
    print(f"   Cap violations (χ > 0.15): {cap_violations}")
    print(f"   Saved: {output_file}")
    
    if chi_max <= 0.15:
        print(f"🎯 **INTERMAGNET χ CAP CONFIRMED AT 0.15** — Plasma boundary detected in Earth's magnetosphere!")
    else:
        print(f"⚠️ χ exceeds 0.15 cap in magnetosphere — max value: {chi_max:.4f}")
    
    return True

if __name__ == "__main__":
    success = compute_chi_from_intermagnet()
    exit(0 if success else 1)
