#!/usr/bin/env python3
"""
parse_omni2.py
Parse OMNIWeb OMNI2 fixed-width annual ASCII files into pandas DataFrame. 
Handles 56-word format, replaces fill values with NaN, builds datetime index. 

Usage: 
  python parse_omni2.py --input data/omni2_2025.txt --output data/omni2_parsed_2025.csv

Dependencies:
  pip install pandas numpy
"""

import pandas as pd
import numpy as np
import argparse
from pathlib import Path

# OMNI2 format: 56 words per line
# FORMAT(2I4,I3,I5,2I3,2I4,14F6.1,F9.0,F6.1,F6.0,2F6.1,F6.3,F6.2,
#        F9.0,F6.1,F6.0,2F6.1,F6.3,2F7.2,F6.1,I3,I4,I6,I5,F10.2,5F9.2,I3,I4,2F6.1,2I6,F5.1,F9.6,F7.4)

# Column widths (sum = line length)
WIDTHS = [
    4, 4, 3, 5, 3, 3, 4, 4,  # words 1-8:  YEAR, DOY, HR, Bartels, IMF_SC_ID, PLA_SC_ID, IMF_PTS, PLA_PTS
    6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6,  # words 9-22: B fields + sigmas (F6.1 each)
    9, 6, 6, 6, 6, 6,  # words 23-28: T(F9.0), Np(F6.1), V(F6.0), phi(F6.1), theta(F6.1), Na/Np(F6.3)
    6,  # word 29: Flow pressure (F6.2)
    9, 6, 6, 6, 6, 6,  # words 30-35: sigma-T, sigma-n, sigma-V, sigma-phi, sigma-theta, sigma-ratio
    7, 7, 6,  # words 36-38: E-field(F7.2), beta(F7.2), Ma(F6.1)
    3, 4, 6, 5,  # words 39-42: Kp*10(I3), R(I4), Dst(I6), AE(I5)
    10, 9, 9, 9, 9, 9,  # words 43-48: Proton fluxes (F10.2, 5*F9.2)
    3, 4, 6, 6, 6, 6, 5, 9, 7  # words 49-57: Msph_flag(I3), ap(I4), F10.7(F6.1), PCN(F6.1), AL/AU(I6), Mms(F5.1), Lya(F9.6), QI(F7.4)
]

# Parameter names (57 words)
PARAM_NAMES = [
    'YEAR', 'DOY', 'HR', 'Bartels', 'IMF_SC_ID', 'PLA_SC_ID', 'IMF_PTS', 'PLA_PTS',
    'B_scalar', 'B_mag', 'B_lat', 'B_lon', 'Bx_GSE', 'By_GSE', 'Bz_GSE', 'By_GSM', 'Bz_GSM',
    'sigma_B_scalar', 'sigma_B', 'sigma_Bx', 'sigma_By', 'sigma_Bz',
    'T_proton', 'Np', 'V', 'phi_V', 'theta_V', 'Na_Np',
    'Flow_pressure',
    'sigma_T', 'sigma_n', 'sigma_V', 'sigma_phi_V', 'sigma_theta_V', 'sigma_Na_Np',
    'E_field', 'Plasma_beta', 'Alfven_Mach',
    'Kp', 'Sunspot_R', 'Dst', 'AE',
    'Prot_flux_1MeV', 'Prot_flux_2MeV', 'Prot_flux_4MeV', 'Prot_flux_10MeV', 'Prot_flux_30MeV', 'Prot_flux_60MeV',
    'Msph_flag', 'ap', 'F10_7', 'PCN', 'AL', 'AU', 'Mms', 'Lyman_alpha', 'QI'
]

# Fill values (per OMNI2 documentation)
FILL_VALUES = {
    'B_scalar': 999.9, 'B_mag': 999.9, 'B_lat': 999.9, 'B_lon': 999.9,
    'Bx_GSE': 999.9, 'By_GSE': 999.9, 'Bz_GSE': 999.9, 'By_GSM': 999.9, 'Bz_GSM': 999.9,
    'sigma_B_scalar': 999.9, 'sigma_B':  999.9, 'sigma_Bx': 999.9, 'sigma_By':  999.9, 'sigma_Bz': 999.9,
    'T_proton': 9999999., 'Np': 999.9, 'V': 9999., 'phi_V': 999.9, 'theta_V': 999.9, 'Na_Np': 9.999,
    'Flow_pressure': 99.99,
    'sigma_T': 9999999., 'sigma_n': 999.9, 'sigma_V': 9999., 'sigma_phi_V': 999.9, 'sigma_theta_V': 999.9, 'sigma_Na_Np': 9.999,
    'E_field': 999.99, 'Plasma_beta': 999.99, 'Alfven_Mach': 999.9,
    'Kp': 99, 'Sunspot_R': 999, 'Dst': 99999, 'AE': 9999,
    'Prot_flux_1MeV': 999999.99, 'Prot_flux_2MeV': 99999.99, 'Prot_flux_4MeV': 99999.99,
    'Prot_flux_10MeV': 99999.99, 'Prot_flux_30MeV': 99999.99, 'Prot_flux_60MeV': 99999.99,
    'ap': 999, 'F10_7': 999.9, 'PCN': 999.9, 'AL': 99999, 'AU': 99999, 'Mms': 99.9, 'Lyman_alpha': 0.999999, 'QI': 9.9999
}

def parse_omni2(input_file: Path) -> pd.DataFrame:
    """Parse OMNI2 fixed-width ASCII file."""
    print(f"[INFO] Reading {input_file}...")
    
    # Check if file exists
    if not input_file.exists():
        raise FileNotFoundError(f"OMNI2 data file not found: {input_file}")
    
    # Check if file is empty
    if input_file.stat().st_size == 0:
        raise ValueError(f"OMNI2 data file is empty: {input_file}")
    
    # Check if file contains HTML (common error from failed downloads)
    with open(input_file, 'r') as f:
        first_line = f.readline().strip()
        if first_line.startswith('<') or 'html' in first_line.lower() or '<!doctype' in first_line.lower():
            raise ValueError(
                f"OMNI2 data file appears to contain HTML instead of data: {input_file}\n"
                f"This usually indicates a failed download from OMNIWeb. "
                f"Please check the source URL and try downloading again."
            )
    
    # Read fixed-width (pandas read_fwf handles widths automatically if we give it column specs)
    # We'll use read_fwf with widths (manual specification)
    try:
        df = pd.read_fwf(input_file, widths=WIDTHS, header=None, na_values=[])
    except Exception as e:
        raise ValueError(f"Failed to read OMNI2 data file {input_file}: {e}")
    
    # Assign column names
    df.columns = PARAM_NAMES[: len(df.columns)]  # Handle cases where file has fewer columns
    
    # Replace fill values with NaN
    for col, fill_val in FILL_VALUES. items():
        if col in df.columns:
            df[col] = df[col].replace(fill_val, np.nan)
    
    # Build datetime index from YEAR, DOY, HR
    try:
        df['datetime'] = pd.to_datetime(
            df['YEAR'].astype(int).astype(str) + df['DOY'].astype(int).astype(str).str.zfill(3),
            format='%Y%j'
        ) + pd.to_timedelta(df['HR'].astype(int), unit='h')
    except (ValueError, TypeError) as e:
        raise ValueError(
            f"Failed to parse datetime columns in OMNI2 file {input_file}. "
            f"The file may be corrupted or contain invalid data. "
            f"Error: {e}"
        )
    
    df = df.set_index('datetime').sort_index()
    
    # Drop redundant time columns
    df = df.drop(columns=['YEAR', 'DOY', 'HR'], errors='ignore')
    
    print(f"[INFO] Parsed {len(df)} records from {df.index.min()} to {df.index.max()}")
    return df

def main():
    parser = argparse. ArgumentParser(description="Parse OMNIWeb OMNI2 ASCII data")
    parser.add_argument('--input', type=Path, required=True, help="Input OMNI2 ASCII file (e.g., omni2_2025.txt)")
    parser.add_argument('--output', type=Path, required=True, help="Output CSV file (e.g., omni2_parsed_2025.csv)")
    args = parser.parse_args()
    
    df = parse_omni2(args.input)
    
    # Save to CSV
    args.output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output)
    print(f"[OK] Saved parsed data to {args.output}")

if __name__ == "__main__":
    main()
