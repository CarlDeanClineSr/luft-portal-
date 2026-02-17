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

Uses cdasws (NASA CDAWeb Services) to fetch:
- FIELDS MAG L2 RTN (vector B, high-res survey ~0.87s)
- SWEAP SPC L3 moments (proton density n_p, velocity V, thermal speed)

Outputs a 1-minute resampled CSV ready for chi_calculator.py.

Dependencies:
    pip install cdasws pandas numpy xarray

Usage:
    python scripts/ingest_psp_data.py --start 2025-09-10 --end 2025-09-20
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
RESAMPLE_CADENCE = '1min'  # 1-minute cadence for chi_calculator compatibility
MERGE_TOLERANCE_SECONDS = 30

# Check for cdasws availability
try:
    from cdasws import CdasWs
    CDASWS_AVAILABLE = True
except ImportError:
    CDASWS_AVAILABLE = False


def check_cdasws_available():
    """Check if cdasws is available."""
    return CDASWS_AVAILABLE


def ingest_psp_perihelion(start_date='2025-09-10', end_date='2025-09-20', output_dir=DEFAULT_OUTPUT_DIR):
    """
    Download and process PSP MAG (RTN) and SPC (moments) data for a perihelion window.
    
    Uses cdasws (NASA CDAWeb Services) for direct data access.
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
    if not CDASWS_AVAILABLE:
        print("❌ cdasws is not installed. Install with: pip install cdasws")
        return None
    
    cdas = CdasWs()
    trange = [f"{start_date}T00:00:00Z", f"{end_date}T23:59:59Z"]
    
    print(f"\n{'=' * 60}")
    print("   PSP DATA INGESTION (cdasws)")
    print(f"   Period: {start_date} to {end_date}")
    print(f"{'=' * 60}\n")
    
    # MAG RTN L2 (high res or survey)
    mag_dataset = 'PSP_FLD_L2_MAG_RTN'
    mag_vars = ['psp_fld_l2_mag_RTN']
    
    print(f"Fetching MAG data from {mag_dataset}...")
    mag_data = None
    try:
        status_mag, mag_data = cdas.get_data(mag_dataset, mag_vars, trange[0], trange[1])
        if status_mag != 0 or mag_data is None:
            print(f"  ⚠ No MAG data for {mag_dataset} (status={status_mag})")
            mag_data = None
        else:
            print(f"  ✓ MAG data retrieved")
    except Exception as e:
        print(f"  ✗ Error fetching MAG data: {e}")
        mag_data = None
    
    # SWEAP SPC L3 ion moments
    spc_dataset = 'PSP_SWP_SPC_L3I'
    spc_np_var = ['np_moment']
    spc_vp_var = ['vp_moment_RTN']
    
    print(f"\nFetching SPC data from {spc_dataset}...")
    spc_np_data = None
    spc_vp_data = None
    
    try:
        status_np, spc_np_data = cdas.get_data(spc_dataset, spc_np_var, trange[0], trange[1])
        if status_np != 0 or spc_np_data is None:
            print(f"  ⚠ No density data (status={status_np})")
            spc_np_data = None
        else:
            print(f"  ✓ Density data retrieved")
    except Exception as e:
        print(f"  ✗ Error fetching density data: {e}")
    
    try:
        status_vp, spc_vp_data = cdas.get_data(spc_dataset, spc_vp_var, trange[0], trange[1])
        if status_vp != 0 or spc_vp_data is None:
            print(f"  ⚠ No velocity data (status={status_vp})")
            spc_vp_data = None
        else:
            print(f"  ✓ Velocity data retrieved")
    except Exception as e:
        print(f"  ✗ Error fetching velocity data: {e}")
    
    # Check if we have any data
    if mag_data is None and spc_np_data is None:
        print("\n✗ No data available for the requested time range.")
        print("  This may be because:")
        print("  - Data for this period hasn't been publicly released yet")
        print("  - CDAWeb downlink is still in progress")
        print("  - Dataset names may need adjustment")
        print("  Try listing datasets with cdas.get_datasets('Parker')")
        return None
    
    # Process MAG data to DataFrame
    mag_df = None
    if mag_data is not None:
        try:
            if hasattr(mag_data, 'to_dataframe'):
                mag_xr_df = mag_data.to_dataframe().reset_index()
                # Find the epoch/time column
                time_col = None
                for col in mag_xr_df.columns:
                    if 'epoch' in col.lower() or 'time' in col.lower():
                        time_col = col
                        break
                
                if time_col:
                    # Get B_RTN data and compute magnitude
                    b_col = None
                    for col in mag_xr_df.columns:
                        if 'mag_rtn' in col.lower() or 'b_rtn' in col.lower():
                            b_col = col
                            break
                    
                    if b_col:
                        mag_df = pd.DataFrame({'time': mag_xr_df[time_col]})
                        b_data = mag_xr_df[b_col]
                        if hasattr(b_data.iloc[0], '__len__'):
                            mag_df['B_mag'] = b_data.apply(lambda x: np.sqrt(np.sum(np.array(x)**2)) if hasattr(x, '__len__') else np.nan)
                        else:
                            mag_df['B_mag'] = np.abs(b_data)
                        print(f"  ✓ Processed MAG data: {len(mag_df)} points")
        except Exception as e:
            print(f"  ✗ Error processing MAG data: {e}")
    
    # Process SPC data to DataFrame
    spc_df = None
    if spc_np_data is not None:
        try:
            if hasattr(spc_np_data, 'to_dataframe'):
                spc_xr_df = spc_np_data.to_dataframe().reset_index()
                # Find the epoch/time column
                time_col = None
                for col in spc_xr_df.columns:
                    if 'epoch' in col.lower() or 'time' in col.lower():
                        time_col = col
                        break
                
                if time_col:
                    # Get density column
                    np_col = None
                    for col in spc_xr_df.columns:
                        if 'np' in col.lower() or 'density' in col.lower():
                            np_col = col
                            break
                    
                    if np_col:
                        spc_df = pd.DataFrame({
                            'time': spc_xr_df[time_col],
                            'n_p': spc_xr_df[np_col]
                        })
                        print(f"  ✓ Processed density data: {len(spc_df)} points")
        except Exception as e:
            print(f"  ✗ Error processing density data: {e}")
    
    # Add velocity magnitude if available
    if spc_vp_data is not None and spc_df is not None:
        try:
            if hasattr(spc_vp_data, 'to_dataframe'):
                vp_xr_df = spc_vp_data.to_dataframe().reset_index()
                # Find velocity column
                vp_col = None
                for col in vp_xr_df.columns:
                    if 'vp' in col.lower() or 'velocity' in col.lower():
                        vp_col = col
                        break
                
                if vp_col:
                    v_data = vp_xr_df[vp_col]
                    if hasattr(v_data.iloc[0], '__len__'):
                        v_mag = v_data.apply(lambda x: np.sqrt(np.sum(np.array(x)**2)) if hasattr(x, '__len__') else np.nan)
                    else:
                        v_mag = np.abs(v_data)
                    spc_df['V_mag'] = v_mag.values
                    print(f"  ✓ Added velocity magnitude")
        except Exception as e:
            print(f"  ✗ Error processing velocity data: {e}")
    
    # Merge datasets
    print("\nMerging datasets...")
    if mag_df is not None and spc_df is not None:
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
    elif spc_df is not None:
        df = spc_df.copy()
        print(f"  ✓ Using SPC data only: {len(df)} points")
    else:
        print("\n✗ No data available after processing.")
        return None
    
    # Resample to 1-minute median (robust to gaps/bursts, matches DSCOVR style)
    print(f"\nResampling to {RESAMPLE_CADENCE} cadence...")
    df.set_index('time', inplace=True)
    cols_to_resample = [c for c in ['B_mag', 'n_p', 'V_mag'] if c in df.columns]
    df_resampled = df[cols_to_resample].resample(RESAMPLE_CADENCE).median()
    
    # Drop NaNs and ensure positive values for B_mag and n_p
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
    print("   (Note: Use real PSP data via cdasws to validate Carl's discovery)")
    
    # Create 48 hours of synthetic data
    times = pd.date_range('2025-09-15 00:00:00', periods=2880, freq='1min')
    
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
    
    # Small noise (use reproducible random numbers)
    rng = np.random.default_rng(42)
    noise = rng.normal(0, 5.0, len(times))
    
    B_mag = B_baseline + long_var + switchback * 0.3 + noise
    B_mag = np.maximum(B_mag, 50.0)
    
    # Density with correlated variations
    n_p = n_baseline + 20.0 * np.sin(2 * np.pi * t_hours / 12) + rng.normal(0, 5.0, len(times))
    n_p = np.maximum(n_p, 5.0)
    
    # Velocity with variations
    V_mag = V_baseline + 50.0 * np.sin(2 * np.pi * t_hours / 8) + rng.normal(0, 20.0, len(times))
    V_mag = np.maximum(V_mag, 100.0)
    
    df = pd.DataFrame({
        'B_mag': B_mag,
        'n_p': n_p,
        'V_mag': V_mag
    }, index=times)
    df.index.name = 'time'
    
    # Save
    os.makedirs(output_dir, exist_ok=True)
    filename = "psp_demo_2025-09-15_2025-09-17.csv"
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
  # Fetch Encounter 25 (Sep 2025) data - fully public
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
    
    parser.add_argument('--start', type=str, default='2025-09-10',
                        help='Start date YYYY-MM-DD (default: 2025-09-10)')
    parser.add_argument('--end', type=str, default='2025-09-20',
                        help='End date YYYY-MM-DD (default: 2025-09-20)')
    parser.add_argument('--output-dir', type=str, default=DEFAULT_OUTPUT_DIR,
                        help=f'Output directory for CSV files (default: {DEFAULT_OUTPUT_DIR})')
    parser.add_argument('--demo', action='store_true',
                        help='Generate demo data for testing (no cdasws required)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("   PARKER SOLAR PROBE (PSP) DATA INGESTION")
    print("   χ ≤ 0.15 Universal Boundary Near-Sun Validation")
    print("   Carl Dean Cline Sr.'s Discovery")
    print("   Using cdasws (NASA CDAWeb Services)")
    print("=" * 60)
    
    if args.demo:
        print("\n⚠️  DEMO MODE: Generating synthetic PSP data")
        print("   Use --start/--end flags with cdasws for real data")
        filepath = generate_demo_data(args.output_dir)
        if filepath:
            print(f"\n💡 Ready for chi_calculator.py:")
            print(f"   python chi_calculator.py --file {filepath}")
        return 0
    
    # Check cdasws availability
    if not check_cdasws_available():
        print("\n❌ cdasws is not installed.")
        print("   Install with: pip install cdasws")
        print("   Or use --demo flag for testing without cdasws")
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
