#!/usr/bin/env python3
"""
merge_omni_heartbeat.py
Merges CME heartbeat log (DSCOVR-derived χ, density, speed, Bz) with OMNIWeb data.
Fills gaps where DSCOVR has blanks, appends extra drivers (pressure, beta, Mach, E-field, QI).
Recomputes χ with better-quality OMNIWeb data where available.

Usage:
  python merge_omni_heartbeat. py \\
    --heartbeat data/cme_heartbeat_log_2025_12.csv \\
    --omni data/omni2_parsed_2025.csv \\
    --output data/extended_heartbeat_log_2025.csv

Dependencies:
  pip install pandas numpy
"""

import pandas as pd
import numpy as np
import argparse
from pathlib import Path

def compute_chi(row):
    """
    Compute χ amplitude using Carl's formula (from Dec 2025 logs):
    χ = min(0.15, 0.0012 * (speed - 350) * (10 / density)^0.3)
    
    Inputs:  row['density'] (p/cm³), row['speed'] (km/s)
    Output: χ amplitude (dimensionless, capped at 0.15)
    """
    if pd.isna(row['density']) or pd.isna(row['speed']) or row['density'] <= 0:
        return np.nan
    modulation = (row['speed'] - 350) * (10 / row['density'])**0.3
    return min(0.15, max(0.0, 0.0012 * modulation))

def merge_data(heartbeat_file: Path, omni_file: Path) -> pd.DataFrame:
    """Merge heartbeat log with OMNIWeb data."""
    print(f"[INFO] Loading heartbeat log:  {heartbeat_file}")
    hb = pd.read_csv(heartbeat_file, parse_dates=['timestamp_utc']).set_index('timestamp_utc')
    
    print(f"[INFO] Loading OMNIWeb data: {omni_file}")
    omni = pd.read_csv(omni_file, parse_dates=['datetime']).set_index('datetime')
    
    # Rename OMNIWeb columns to match heartbeat schema (or keep both for comparison)
    omni_subset = omni[[
        'Np', 'V', 'Bz_GSM', 'Flow_pressure', 'Plasma_beta', 'Alfven_Mach', 'Mms', 'E_field', 'QI'
    ]].rename(columns={
        'Np': 'density_omni', 'V': 'speed_omni', 'Bz_GSM': 'Bz_omni'
    })
    
    # Outer join (keep all timestamps from both sources)
    merged = hb.join(omni_subset, how='outer')
    
    # Gap-filling logic:  if heartbeat density/speed/Bz are NaN, use OMNIWeb values
    merged['density'] = merged['density']. fillna(merged['density_omni'])
    merged['speed'] = merged['speed'].fillna(merged['speed_omni'])
    merged['Bz'] = merged. get('Bz', merged. get('Bz_omni')).fillna(merged['Bz_omni'])
    
    # Recompute χ with potentially better-quality merged data
    merged['chi_amplitude_extended'] = merged.apply(compute_chi, axis=1)
    
    # Keep original χ for comparison (if it exists in heartbeat)
    if 'chi_amplitude' in hb.columns:
        merged['chi_amplitude_original'] = hb['chi_amplitude']
    
    print(f"[INFO] Merged dataset spans {merged.index.min()} to {merged.index.max()}")
    print(f"[INFO] Total records: {len(merged)}")
    print(f"[INFO] Records with density:  {merged['density'].notna().sum()}")
    print(f"[INFO] Records with χ (extended): {merged['chi_amplitude_extended'].notna().sum()}")
    
    return merged

def main():
    parser = argparse.ArgumentParser(description="Merge CME heartbeat log with OMNIWeb data")
    parser.add_argument('--heartbeat', type=Path, required=True, help="Input heartbeat CSV")
    parser.add_argument('--omni', type=Path, required=True, help="Input parsed OMNIWeb CSV")
    parser.add_argument('--output', type=Path, required=True, help="Output merged CSV")
    args = parser.parse_args()
    
    merged = merge_data(args.heartbeat, args.omni)
    
    # Save
    args.output.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(args.output)
    print(f"[OK] Saved merged data to {args.output}")

if __name__ == "__main__":
    main()
