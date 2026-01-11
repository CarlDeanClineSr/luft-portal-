#!/usr/bin/env python3
"""
ingest_psp_data.py
==================
Parker Solar Probe (PSP) Data Ingestion Pipeline for χ ≤ 0.15 Boundary Validation.

Discovered by Carl Dean Cline Sr., Lincoln, Nebraska
January 2026

This script fetches and processes PSP data to validate the χ = 0.15 boundary
near the Sun, where conditions differ dramatically from 1 AU norms:
- Electron temperature T_e often exceeds proton T_p by factors of 2–10+
- Beta is low (magnetic pressure dominates)
- Reconnection and switchbacks are frequent
- Turbulence cascades are "pristine" (less evolved)

Uses pyspedas (CDAWeb-backed) to fetch:
- FIELDS MAG L2 RTN (vector B, high-res survey ~0.87s)
- SWEAP SPC L3 moments (proton density n_p, velocity V, thermal speed)

Outputs a 1-minute resampled CSV ready for chi_calculator.py.

Dependencies:
    pip install pyspedas pytplot pandas numpy

Usage:
    python scripts/ingest_psp_data.py --start 2025-12-10 --end 2025-12-25
    python scripts/ingest_psp_data.py --demo

Contact: CARLDCLINE@GMAIL.COM
Repository: https://github.com/CarlDeanClineSr/luft-portal-
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


# PSP Data Constants
DEFAULT_OUTPUT_DIR = 'data/psp'
RESAMPLE_CADENCE = '1T'  # 1-minute cadence for chi_calculator compatibility
MERGE_TOLERANCE_SECONDS = 30


def check_pyspedas_available():
    """Check if pyspedas is available and import it."""
    try:
        import pyspedas
        import pyspedas.psp
        from pytplot import get_data
        return True
    except ImportError:
        return False


def ingest_psp_perihelion(start_date='2025-12-10', end_date='2025-12-20', output_dir=DEFAULT_OUTPUT_DIR):
    """
    Download and process PSP MAG (RTN) and SPC (moments) data for a perihelion window.
    
    Computes |B|, proton density n_p, |V| magnitude.
    Saves 1-minute resampled CSV for chi_calculator.py.
    
    Args:
        start_date: Start date string 'YYYY-MM-DD'
        end_date: End date string 'YYYY-MM-DD'
        output_dir: Output directory for CSV files
    
    Returns:
        filepath: Path to the saved CSV file, or None if data unavailable
    
    Note:
        Adjust dates for specific encounters:
        - Encounter 26 (Dec 2025): ~Dec 13-18
        - Encounter 25 (Sep 2025): ~Sep 10-20 (fully public)
    """
    # Import pyspedas here to allow module-level checks
    import pyspedas.psp
    from pytplot import get_data, tplot_names
    
    trange = [start_date, end_date]
    
    print(f"\n{'=' * 60}")
    print("   PSP DATA INGESTION")
    print(f"   Period: {start_date} to {end_date}")
    print(f"{'=' * 60}\n")
    
    # Fetch FIELDS MAG L2 RTN (survey mode, high cadence)
    print("Fetching FIELDS MAG L2 RTN data...")
    try:
        mag_vars = pyspedas.psp.fields(trange=trange, datatype='mag_rtn', level='l2', time_clip=True)
        print(f"  MAG variables loaded: {mag_vars}")
    except Exception as e:
        print(f"  ✗ Error fetching MAG data: {e}")
        mag_vars = []
    
    # Fetch SWEAP SPC L3 ion moments (n_p, V_rtn, T_p etc.)
    print("\nFetching SWEAP SPC L3 ion moments data...")
    try:
        spc_vars = pyspedas.psp.spc(trange=trange, datatype='np_mom', level='l3i', time_clip=True)
        print(f"  SPC variables loaded: {spc_vars}")
    except Exception as e:
        print(f"  ✗ Error fetching SPC data: {e}")
        spc_vars = []
    
    # List available tplot variables for debugging
    available_vars = tplot_names()
    print(f"\nAvailable tplot variables: {available_vars}")
    
    # Extract MAG data
    mag_df = None
    mag_var_candidates = [
        'psp_fld_l2_mag_RTN',
        'psp_fld_l2_mag_rtn',
        'psp_fld_mag_rtn',
    ]
    
    for var_name in mag_var_candidates:
        if var_name in available_vars:
            try:
                result = get_data(var_name)
                if result is not None:
                    mag_time, mag_rtn = result
                    # Compute B magnitude using linalg.norm for robustness
                    B_mag = np.linalg.norm(mag_rtn, axis=1)
                    
                    mag_df = pd.DataFrame({
                        'time': mag_time,
                        'B_mag': B_mag
                    })
                    # Convert time (Unix seconds) to datetime
                    mag_df['time'] = pd.to_datetime(mag_df['time'], unit='s')
                    print(f"  ✓ Extracted MAG data from {var_name}: {len(mag_df)} points")
                    break
            except Exception as e:
                print(f"  ✗ Could not extract from {var_name}: {e}")
    
    if mag_df is None:
        print("  ⚠ No MAG data extracted")
    
    # Extract SPC data (density and velocity)
    spc_df = None
    density_candidates = ['psp_spc_np', 'psp_spc_n_p', 'psp_spc_np_moment']
    velocity_candidates = ['psp_spc_vel', 'psp_spc_vp', 'psp_spc_vp_moment']
    
    spc_np = None
    spc_vel = None
    spc_time = None
    
    # Try to get density
    for var_name in density_candidates:
        if var_name in available_vars:
            try:
                result = get_data(var_name)
                if result is not None:
                    spc_time, spc_np = result
                    print(f"  ✓ Found density data in {var_name}")
                    break
            except Exception as e:
                print(f"  ✗ Could not extract from {var_name}: {e}")
    
    # Try to get velocity
    for var_name in velocity_candidates:
        if var_name in available_vars:
            try:
                result = get_data(var_name)
                if result is not None:
                    spc_time_v, spc_vel = result
                    print(f"  ✓ Found velocity data in {var_name}")
                    break
            except Exception as e:
                print(f"  ✗ Could not extract from {var_name}: {e}")
    
    # Build SPC DataFrame if we have at least density
    if spc_np is not None and spc_time is not None:
        spc_df = pd.DataFrame({
            'time': spc_time,
            'n_p': spc_np
        })
        
        if spc_vel is not None:
            # Compute velocity magnitude using linalg.norm for robustness
            if spc_vel.ndim > 1:
                V_mag = np.linalg.norm(spc_vel, axis=1)
            else:
                # 1D array: take absolute value (could be scalar speed)
                V_mag = np.abs(spc_vel)
            spc_df['V_mag'] = V_mag
        
        spc_df['time'] = pd.to_datetime(spc_df['time'], unit='s')
        print(f"  ✓ Extracted SPC data: {len(spc_df)} points")
    else:
        print("  ⚠ No SPC data extracted")
    
    # Check if we have any data to work with
    if mag_df is None and spc_df is None:
        print("\n✗ No data available for the requested time range.")
        print("  This may be because:")
        print("  - Data for this period hasn't been publicly released yet")
        print("  - CDAWeb downlink is still in progress")
        print("  Try an earlier encounter (e.g., 2025-09-10 to 2025-09-20 for Encounter 25)")
        return None
    
    # Merge datasets
    print("\nMerging datasets...")
    if mag_df is not None and spc_df is not None:
        # Merge on nearest time (high-res MAG dominates)
        df = pd.merge_asof(
            mag_df.sort_values('time'),
            spc_df.sort_values('time'),
            on='time',
            tolerance=pd.Timedelta(f'{MERGE_TOLERANCE_SECONDS}s')
        )
        print(f"  ✓ Merged MAG + SPC: {len(df)} points")
    elif mag_df is not None:
        df = mag_df.copy()
        print(f"  ✓ Using MAG data only: {len(df)} points")
    else:
        df = spc_df.copy()
        print(f"  ✓ Using SPC data only: {len(df)} points")
    
    # Resample to 1-minute median (robust to gaps/bursts, matches DSCOVR style)
    print(f"\nResampling to {RESAMPLE_CADENCE} cadence...")
    df.set_index('time', inplace=True)
    df_resampled = df.resample(RESAMPLE_CADENCE).median()
    
    # Drop NaNs and ensure positive values for B_mag and n_p
    # (velocity magnitude is already positive by definition)
    df_resampled = df_resampled.dropna()
    positive_cols = [c for c in ['B_mag', 'n_p'] if c in df_resampled.columns]
    if positive_cols:
        df_resampled = df_resampled[(df_resampled[positive_cols] > 0).all(axis=1)]
    
    print(f"  ✓ Resampled to {len(df_resampled)} points")
    
    if len(df_resampled) == 0:
        print("\n✗ No valid data after resampling.")
        return None
    
    # Save to CSV
    os.makedirs(output_dir, exist_ok=True)
    filename = f"psp_merged_{start_date}_{end_date}.csv"
    filepath = os.path.join(output_dir, filename)
    df_resampled.to_csv(filepath)
    
    print(f"\n{'=' * 60}")
    print("   PSP DATA INGESTION COMPLETE")
    print(f"{'=' * 60}")
    print(f"Saved {len(df_resampled)} points to {filepath}")
    print(f"\nColumns: {list(df_resampled.columns)}")
    if 'B_mag' in df_resampled.columns:
        print(f"  B_mag range: {df_resampled['B_mag'].min():.2f} - {df_resampled['B_mag'].max():.2f} nT")
    if 'n_p' in df_resampled.columns:
        print(f"  n_p range: {df_resampled['n_p'].min():.2f} - {df_resampled['n_p'].max():.2f} p/cm³")
    if 'V_mag' in df_resampled.columns:
        print(f"  V_mag range: {df_resampled['V_mag'].min():.1f} - {df_resampled['V_mag'].max():.1f} km/s")
    
    print(f"\n💡 Next step: Run chi_calculator.py on this data:")
    print(f"   python chi_calculator.py --file {filepath}")
    print(f"{'=' * 60}\n")
    
    return filepath


def generate_demo_data(output_dir=DEFAULT_OUTPUT_DIR):
    """
    Generate synthetic PSP-like data for testing the ingestion pipeline.
    
    Note: This demo data is for testing the pipeline interface only.
    Real PSP data from CDAWeb should be used for actual χ ≤ 0.15 validation.
    """
    print("\n🎲 Generating demo PSP data for testing...")
    print("   (Note: Use real PSP data via pyspedas to validate Carl's discovery)")
    
    # Create 48 hours of synthetic data
    times = pd.date_range('2025-12-15 00:00:00', periods=2880, freq='1min')
    
    # Near-Sun conditions: higher B field (~100-500 nT at ~10 solar radii)
    # Strong radial component, elevated density
    B_baseline = 200.0  # nT - typical near perihelion
    n_baseline = 50.0   # p/cm³ - elevated near Sun
    V_baseline = 300.0  # km/s - slower near Sun
    
    t_hours = np.arange(len(times)) / 60.0
    
    # Simulate switchbacks (sharp B reversals)
    switchback = 30.0 * np.sin(2 * np.pi * t_hours / 0.5)  # 30-minute period
    
    # Long-period variations
    long_var = 50.0 * np.sin(2 * np.pi * t_hours / 24)
    
    # Small noise
    noise = np.random.normal(0, 5.0, len(times))
    
    B_mag = B_baseline + long_var + switchback * 0.3 + noise
    B_mag = np.maximum(B_mag, 50.0)
    
    # Density with correlated variations
    n_p = n_baseline + 20.0 * np.sin(2 * np.pi * t_hours / 12) + np.random.normal(0, 5.0, len(times))
    n_p = np.maximum(n_p, 5.0)
    
    # Velocity with variations
    V_mag = V_baseline + 50.0 * np.sin(2 * np.pi * t_hours / 8) + np.random.normal(0, 20.0, len(times))
    V_mag = np.maximum(V_mag, 100.0)
    
    df = pd.DataFrame({
        'B_mag': B_mag,
        'n_p': n_p,
        'V_mag': V_mag
    }, index=times)
    df.index.name = 'time'
    
    # Save
    os.makedirs(output_dir, exist_ok=True)
    filename = "psp_demo_2025-12-15_2025-12-17.csv"
    filepath = os.path.join(output_dir, filename)
    df.to_csv(filepath)
    
    print(f"✓ Demo PSP data saved to: {filepath}")
    print(f"  Generated 48 hours of synthetic near-Sun conditions")
    print(f"  B_mag: {df['B_mag'].min():.1f} - {df['B_mag'].max():.1f} nT")
    print(f"  n_p: {df['n_p'].min():.1f} - {df['n_p'].max():.1f} p/cm³")
    print(f"  V_mag: {df['V_mag'].min():.1f} - {df['V_mag'].max():.1f} km/s")
    
    return filepath


def main():
    parser = argparse.ArgumentParser(
        description="PSP Data Ingestion Pipeline for χ ≤ 0.15 Boundary Validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch Encounter 26 (Dec 2025) data - partial/public by mid-Jan 2026
  python scripts/ingest_psp_data.py --start 2025-12-10 --end 2025-12-25

  # Fetch earlier encounter (fully public)
  python scripts/ingest_psp_data.py --start 2025-09-10 --end 2025-09-20

  # Generate demo data for testing
  python scripts/ingest_psp_data.py --demo

Near-Sun Validation Context:
  PSP provides the ultimate falsification arena for the χ = 0.15 boundary.
  Near the Sun (R < 20 solar radii), conditions differ from 1 AU:
  - T_e >> T_p (reverse of cooler solar wind)
  - Low beta (magnetic pressure dominates)
  - Frequent reconnection and switchbacks
  - Pristine turbulence cascades

  If χ holds tight (zero violations, attractor ~0.145-0.155):
    The claim goes nuclear—χ is truly scale-invariant.
  If χ shifts (e.g., χ_max > 0.15):
    Points to temperature/mass-ratio dependence (huge learning!).

Contact: CARLDCLINE@GMAIL.COM
Repository: https://github.com/CarlDeanClineSr/luft-portal-
        """
    )
    
    parser.add_argument('--start', type=str, default='2025-12-10',
                        help='Start date YYYY-MM-DD (default: 2025-12-10)')
    parser.add_argument('--end', type=str, default='2025-12-25',
                        help='End date YYYY-MM-DD (default: 2025-12-25)')
    parser.add_argument('--output-dir', type=str, default=DEFAULT_OUTPUT_DIR,
                        help=f'Output directory for CSV files (default: {DEFAULT_OUTPUT_DIR})')
    parser.add_argument('--demo', action='store_true',
                        help='Generate demo data for testing (no pyspedas required)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("   PARKER SOLAR PROBE (PSP) DATA INGESTION")
    print("   χ ≤ 0.15 Universal Boundary Near-Sun Validation")
    print("   Carl Dean Cline Sr.'s Discovery")
    print("=" * 60)
    
    if args.demo:
        print("\n⚠️  DEMO MODE: Generating synthetic PSP data")
        print("   Use --start/--end flags with pyspedas for real data")
        filepath = generate_demo_data(args.output_dir)
        if filepath:
            print(f"\n💡 Ready for chi_calculator.py:")
            print(f"   python chi_calculator.py --file {filepath}")
        return 0
    
    # Check pyspedas availability
    if not check_pyspedas_available():
        print("\n❌ pyspedas is not installed.")
        print("   Install with: pip install pyspedas pytplot")
        print("   Or use --demo flag for testing without pyspedas")
        return 1
    
    # Run ingestion
    filepath = ingest_psp_perihelion(args.start, args.end, args.output_dir)
    
    if filepath:
        print(f"\n💡 Ready for chi_calculator.py:")
        print(f"   python chi_calculator.py --file {filepath}")
        return 0
    else:
        print("\n⚠️  No data retrieved. Try:")
        print("   - An earlier time range (data may not be public yet)")
        print("   - Check CDAWeb for data availability")
        print("   - Use --demo for testing the pipeline")
        return 1


if __name__ == "__main__":
    sys.exit(main())
