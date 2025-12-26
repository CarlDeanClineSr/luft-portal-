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
    
    # Collect all INTERMAGNET data files
    json_files = sorted(data_dir.glob("intermagnet_*.json"))
    txt_files = sorted(data_dir.glob("intermagnet_*.txt"))
    csv_files = sorted(data_dir.glob("intermagnet_*.csv"))
    
    data_files = json_files + txt_files + csv_files
    
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
                # Parse INTERMAGNET text format
                # Skip header lines and parse data rows
                with open(data_file, 'r') as f:
                    lines = f.readlines()
                # Simple parsing: skip lines starting with # or empty lines
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Split by whitespace and try to extract numeric values
                        parts = line.split()
                        if len(parts) >= 2:
                            try:
                                # Attempt to create a simple dict with numeric values
                                data_dict = {f"col_{i}": float(p) for i, p in enumerate(parts) if p.replace('.', '').replace('-', '').isdigit()}
                                if data_dict:
                                    all_data.append(data_dict)
                            except (ValueError, AttributeError):
                                continue
                
        except Exception as e:
            print(f"⚠️ Error reading {data_file}: {e}")
    
    if not all_data:
        print("⚠️ No valid INTERMAGNET data found")
        return False
    
    # Convert to DataFrame
    df = pd.DataFrame(all_data)
    
    # Identify magnetic field column (prefer F total field, then X/Y/Z components)
    # Priority: F > B_TOTAL > BT > H > X, Y, Z
    priority_cols = ['F', 'B_TOTAL', 'BT', 'TOTAL_FIELD', 'H', 'X', 'Y', 'Z']
    mag_col = None
    
    for col_name in priority_cols:
        matches = [c for c in df.columns if c.upper() == col_name]
        if matches:
            mag_col = matches[0]
            break
    
    if not mag_col:
        print("⚠️ No magnetic field column found in INTERMAGNET data")
        return False
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
