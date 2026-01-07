#!/usr/bin/env python3
"""
Convert IAGA-2002 INTERMAGNET format to CSV for chi_calculator.py
Handles 99999.00 (missing data marker) properly

Usage: 
    python scripts/convert_iaga2002_to_csv.py \
        --input data/intermagnet_raw/dou_20260106.min \
        --output data/intermagnet_csv/dou_20260106.csv
"""

import argparse
import pandas as pd
import numpy as np


def convert_iaga2002(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    data = []
    started = False
    
    for line in lines:
        # Detect data section start
        if 'DATE' in line and 'TIME' in line and 'DOY' in line:
            started = True
            continue
        
        # Parse data lines
        if started and line.strip() and not line.startswith('#') and not line.startswith('|'):
            parts = line.split()
            if len(parts) >= 7:
                try:
                    date = parts[0]
                    time = parts[1]
                    timestamp = f"{date} {time}"
                    
                    # Parse magnetic field components (handle 99999.00 = missing)
                    x = float(parts[3]) if parts[3] != '99999.00' else np.nan
                    y = float(parts[4]) if parts[4] != '99999.00' else np.nan
                    z = float(parts[5]) if parts[5] != '99999.00' else np.nan
                    f_val = float(parts[6]) if parts[6] != '99999.00' else np.nan
                    
                    data.append({
                        'timestamp': timestamp,
                        'Bx': x,
                        'By': y,
                        'Bz': z,
                        'B_total': f_val
                    })
                except (ValueError, IndexError):
                    continue
    
    if data:
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.to_csv(output_file, index=False)
        print(f"✅ Converted {input_file} → {output_file} ({len(df)} rows)")
    else:
        print(f"⚠️  No valid data parsed from {input_file}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='Input IAGA-2002 file')
    parser.add_argument('--output', required=True, help='Output CSV file')
    args = parser.parse_args()
    
    convert_iaga2002(args.input, args.output)
