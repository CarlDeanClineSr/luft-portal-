#!/usr/bin/env python3
"""
fetch_psp_encounter17.py
========================
Parker Solar Probe (PSP) Multi-Encounter Data Fetcher for χ ≤ 0.15 Validation

This script downloads PSP FIELDS MAG L2 data for specific encounters (17-20)
and formats it for chi_calculator.py validation.

Discovered by Carl Dean Cline Sr., Lincoln, Nebraska
January 2026

Encounter Timeline:
- Encounter 17: Sep 2023, Perihelion 2023-09-27, ~0.08 AU
- Encounter 18: Dec 2023, Perihelion 2023-12-29, ~0.08 AU  
- Encounter 19: Mar 2024, Perihelion 2024-03-30, ~0.08 AU
- Encounter 20: Jun 2024, Perihelion 2024-06-30, ~0.08 AU

Dependencies:
    pip install pyspedas pandas numpy (or cdasws as fallback)

Usage:
    python fetch_psp_encounter17.py --encounter 17
    python fetch_psp_encounter17.py --encounter 18 --output-dir data/psp

Contact: CARLDCLINE@GMAIL.COM
Repository: https://github.com/CarlDeanClineSr/luft-portal-
"""

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

# Check for data fetching libraries
try:
    import pyspedas
    from pytplot import get_data, del_data
    PYSPEDAS_AVAILABLE = True
except ImportError:
    PYSPEDAS_AVAILABLE = False

try:
    from cdasws import CdasWs
    CDASWS_AVAILABLE = True
except ImportError:
    CDASWS_AVAILABLE = False

# Encounter definitions (perihelion date ± 5 days for comprehensive coverage)
ENCOUNTERS = {
    17: {
        'perihelion': '2023-09-27',
        'start': '2023-09-22',
        'end': '2023-10-02',
        'info': 'Sep 2023, Perihelion 2023-09-27, ~0.08 AU'
    },
    18: {
        'perihelion': '2023-12-29',
        'start': '2023-12-24',
        'end': '2024-01-03',
        'info': 'Dec 2023, Perihelion 2023-12-29, ~0.08 AU'
    },
    19: {
        'perihelion': '2024-03-30',
        'start': '2024-03-25',
        'end': '2024-04-04',
        'info': 'Mar 2024, Perihelion 2024-03-30, ~0.08 AU'
    },
    20: {
        'perihelion': '2024-06-30',
        'start': '2024-06-25',
        'end': '2024-07-05',
        'info': 'Jun 2024, Perihelion 2024-06-30, ~0.08 AU'
    }
}

DEFAULT_OUTPUT_DIR = 'data/psp'
RESAMPLE_CADENCE = '1min'


def fetch_psp_mag_pyspedas(start_date, end_date, encounter_num):
    """
    Fetch PSP MAG data using pyspedas.
    
    Args:
        start_date: Start date string 'YYYY-MM-DD'
        end_date: End date string 'YYYY-MM-DD'
        encounter_num: Encounter number for naming
    
    Returns:
        DataFrame with timestamp, B_R, B_T, B_N columns
    """
    if not PYSPEDAS_AVAILABLE:
        return None
    
    print(f"\nFetching PSP MAG data using pyspedas...")
    print(f"  Period: {start_date} to {end_date}")
    
    try:
        # Fetch FIELDS MAG L2 RTN data
        trange = [start_date, end_date]
        vars_loaded = pyspedas.psp.fields(
            trange=trange,
            datatype='mag_RTN',
            level='l2',
            time_clip=True,
            notplot=True
        )
        
        if not vars_loaded:
            print("  ⚠ No variables loaded from pyspedas")
            return None
        
        print(f"  ✓ Loaded variables: {vars_loaded}")
        
        # Get the magnetic field data
        # Variable name is typically 'psp_fld_l2_mag_RTN'
        mag_var = None
        for var in vars_loaded:
            if 'mag_RTN' in var or 'mag_rtn' in var:
                mag_var = var
                break
        
        if not mag_var:
            print(f"  ⚠ Could not find MAG RTN variable in {vars_loaded}")
            return None
        
        print(f"  ✓ Using variable: {mag_var}")
        
        # Extract data using pytplot
        data = get_data(mag_var)
        
        if data is None:
            print("  ⚠ No data returned from get_data")
            return None
        
        # data is typically (times, values) where values has shape (n, 3) for RTN
        times, mag_rtn = data
        
        # Convert times to datetime (using timezone-aware fromtimestamp for Python 3.12+)
        times_dt = [datetime.fromtimestamp(t, tz=timezone.utc) for t in times]
        
        # Create DataFrame
        df = pd.DataFrame({
            'timestamp': times_dt,
            'B_R': mag_rtn[:, 0],  # Radial component
            'B_T': mag_rtn[:, 1],  # Tangential component
            'B_N': mag_rtn[:, 2]   # Normal component
        })
        
        print(f"  ✓ Loaded {len(df):,} data points")
        
        # Clean up pytplot data
        del_data(mag_var)
        
        return df
        
    except Exception as e:
        print(f"  ✗ Error fetching with pyspedas: {e}")
        import traceback
        traceback.print_exc()
        return None


def fetch_psp_mag_cdasws(start_date, end_date, encounter_num):
    """
    Fetch PSP MAG data using cdasws (fallback).
    
    Args:
        start_date: Start date string 'YYYY-MM-DD'
        end_date: End date string 'YYYY-MM-DD'
        encounter_num: Encounter number for naming
    
    Returns:
        DataFrame with timestamp, B_R, B_T, B_N columns
    """
    if not CDASWS_AVAILABLE:
        return None
    
    print(f"\nFetching PSP MAG data using cdasws...")
    print(f"  Period: {start_date} to {end_date}")
    
    try:
        cdas = CdasWs()
        
        # PSP FIELDS MAG L2 RTN dataset
        dataset = 'PSP_FLD_L2_MAG_RTN'
        variables = ['psp_fld_l2_mag_RTN']
        
        trange = [f"{start_date}T00:00:00Z", f"{end_date}T23:59:59Z"]
        
        print(f"  Fetching from {dataset}...")
        status, data = cdas.get_data(dataset, variables, trange[0], trange[1])
        
        if status != 0 or data is None:
            print(f"  ⚠ No data returned (status={status})")
            return None
        
        print(f"  ✓ Data retrieved")
        
        # Convert to DataFrame
        if hasattr(data, 'to_dataframe'):
            df_raw = data.to_dataframe().reset_index()
            
            # Find time column
            time_col = None
            for col in df_raw.columns:
                if 'epoch' in col.lower() or 'time' in col.lower():
                    time_col = col
                    break
            
            if not time_col:
                print("  ⚠ Could not find time column")
                return None
            
            # Find MAG RTN column
            mag_col = None
            for col in df_raw.columns:
                if 'mag_rtn' in col.lower() or 'mag_RTN' in col:
                    mag_col = col
                    break
            
            if not mag_col:
                print("  ⚠ Could not find MAG RTN column")
                return None
            
            # Extract components
            times = df_raw[time_col]
            mag_data = df_raw[mag_col]
            
            # mag_data should be array-like with 3 components
            if hasattr(mag_data.iloc[0], '__len__'):
                B_R = mag_data.apply(lambda x: x[0] if hasattr(x, '__len__') and len(x) >= 3 else np.nan)
                B_T = mag_data.apply(lambda x: x[1] if hasattr(x, '__len__') and len(x) >= 3 else np.nan)
                B_N = mag_data.apply(lambda x: x[2] if hasattr(x, '__len__') and len(x) >= 3 else np.nan)
            else:
                print("  ⚠ MAG data format unexpected")
                return None
            
            df = pd.DataFrame({
                'timestamp': times,
                'B_R': B_R,
                'B_T': B_T,
                'B_N': B_N
            })
            
            print(f"  ✓ Processed {len(df):,} data points")
            return df
        
        else:
            print("  ⚠ Data format not supported")
            return None
        
    except Exception as e:
        print(f"  ✗ Error fetching with cdasws: {e}")
        import traceback
        traceback.print_exc()
        return None


def fetch_psp_encounter(encounter_num, output_dir=DEFAULT_OUTPUT_DIR):
    """
    Fetch PSP data for a specific encounter and save to CSV.
    
    Args:
        encounter_num: Encounter number (17, 18, 19, or 20)
        output_dir: Output directory for CSV files
    
    Returns:
        filepath: Path to the saved CSV file, or None if fetch failed
    """
    if encounter_num not in ENCOUNTERS:
        print(f"❌ Error: Encounter {encounter_num} not defined")
        print(f"Available encounters: {list(ENCOUNTERS.keys())}")
        return None
    
    encounter = ENCOUNTERS[encounter_num]
    start_date = encounter['start']
    end_date = encounter['end']
    
    print("=" * 70)
    print(f"PSP ENCOUNTER {encounter_num} DATA FETCH")
    print("=" * 70)
    print(f"Info: {encounter['info']}")
    print(f"Date range: {start_date} to {end_date}")
    print("=" * 70)
    
    # Check what's available
    if not PYSPEDAS_AVAILABLE and not CDASWS_AVAILABLE:
        print("\n❌ Error: Neither pyspedas nor cdasws is installed")
        print("Install with:")
        print("  pip install pyspedas  (recommended)")
        print("  pip install cdasws    (fallback)")
        return None
    
    # Try pyspedas first (preferred), then cdasws
    df = None
    
    if PYSPEDAS_AVAILABLE:
        print("\nUsing pyspedas (NASA official Python package)...")
        df = fetch_psp_mag_pyspedas(start_date, end_date, encounter_num)
    
    if df is None and CDASWS_AVAILABLE:
        print("\nFalling back to cdasws...")
        df = fetch_psp_mag_cdasws(start_date, end_date, encounter_num)
    
    if df is None:
        print("\n❌ Failed to fetch data from both pyspedas and cdasws")
        print("This could mean:")
        print("  - Network connectivity issues")
        print("  - NASA CDAWeb service unavailable")
        print("  - Data not yet available for this time range")
        return None
    
    # Validate data
    df = df.dropna()
    if len(df) == 0:
        print("\n❌ No valid data after filtering NaN values")
        return None
    
    # Resample to 1-minute cadence for consistency
    print(f"\nResampling to {RESAMPLE_CADENCE} cadence...")
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.set_index('timestamp')
    df_resampled = df.resample(RESAMPLE_CADENCE).mean()
    df_resampled = df_resampled.dropna()
    
    print(f"  ✓ Resampled to {len(df_resampled):,} points")
    
    if len(df_resampled) == 0:
        print("\n❌ No valid data after resampling")
        return None
    
    # Save to CSV
    os.makedirs(output_dir, exist_ok=True)
    filename = f"psp_encounter{encounter_num}_mag.csv"
    filepath = os.path.join(output_dir, filename)
    
    df_resampled.to_csv(filepath)
    
    print("\n" + "=" * 70)
    print("DATA FETCH COMPLETE")
    print("=" * 70)
    print(f"Saved {len(df_resampled):,} points to {filepath}")
    print(f"\nMagnetic field statistics (RTN coordinates):")
    print(f"  B_R: {df_resampled['B_R'].min():.2f} to {df_resampled['B_R'].max():.2f} nT")
    print(f"  B_T: {df_resampled['B_T'].min():.2f} to {df_resampled['B_T'].max():.2f} nT")
    print(f"  B_N: {df_resampled['B_N'].min():.2f} to {df_resampled['B_N'].max():.2f} nT")
    print(f"  |B|: {np.sqrt(df_resampled['B_R']**2 + df_resampled['B_T']**2 + df_resampled['B_N']**2).mean():.2f} nT (mean)")
    print("\n💡 Next step:")
    print(f"  python chi_calculator.py --file {filepath} --time-col timestamp --bx B_R --by B_T --bz B_N")
    print("=" * 70 + "\n")
    
    return filepath


def main():
    parser = argparse.ArgumentParser(
        description="Fetch PSP data for specific encounters (17-20) for χ ≤ 0.15 validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fetch_psp_encounter17.py --encounter 17
  python fetch_psp_encounter17.py --encounter 18 --output-dir data/psp

Encounters:
  17: Sep 2023, Perihelion 2023-09-27, ~0.08 AU
  18: Dec 2023, Perihelion 2023-12-29, ~0.08 AU
  19: Mar 2024, Perihelion 2024-03-30, ~0.08 AU
  20: Jun 2024, Perihelion 2024-06-30, ~0.08 AU

Data Source:
  NASA Parker Solar Probe FIELDS MAG L2 RTN
  Via pyspedas (preferred) or cdasws (fallback)

Contact: CARLDCLINE@GMAIL.COM
Repository: https://github.com/CarlDeanClineSr/luft-portal-
        """
    )
    
    parser.add_argument('--encounter', type=int, required=True,
                        choices=[17, 18, 19, 20],
                        help='Encounter number to fetch (17, 18, 19, or 20)')
    parser.add_argument('--output-dir', type=str, default=DEFAULT_OUTPUT_DIR,
                        help=f'Output directory for CSV files (default: {DEFAULT_OUTPUT_DIR})')
    
    args = parser.parse_args()
    
    filepath = fetch_psp_encounter(args.encounter, args.output_dir)
    
    if filepath:
        print(f"✅ Success! Data saved to: {filepath}")
        return 0
    else:
        print(f"❌ Failed to fetch data for Encounter {args.encounter}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
