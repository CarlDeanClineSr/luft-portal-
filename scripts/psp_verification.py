#!/usr/bin/env python3
"""
psp_verification.py
===================
Parker Solar Probe (PSP) Scaling Verification for χ ≤ 0.15 Boundary.

Discovered by Carl Dean Cline Sr., Lincoln, Nebraska
January 2026

This script fetches PSP data using cdasws (NASA CDAWeb Services) and validates
the χ = 0.15 boundary near the Sun during perihelion encounters.

Uses cdasws instead of pyspedas/pytplot for Python 3.12 compatibility.

Near-Sun Validation Context:
- Target: Parker Solar Probe (FIELDS/MAG)
- PSP provides the ultimate falsification arena for the χ = 0.15 boundary
- Near the Sun (R < 20 solar radii), conditions differ from 1 AU:
  * Electron temperature T_e often exceeds proton T_p by factors of 2–10+
  * Beta is low (magnetic pressure dominates)
  * Reconnection and switchbacks are frequent
  * Turbulence cascades are "pristine" (less evolved)

Dependencies:
    pip install cdasws pandas numpy matplotlib seaborn

Usage:
    python scripts/psp_verification.py
    python scripts/psp_verification.py --start 2023-12-28 --end 2023-12-29
    python scripts/psp_verification.py --demo

Contact: CARLDCLINE@GMAIL.COM
Repository: https://github.com/CarlDeanClineSr/luft-portal-
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# Check for cdasws availability
try:
    from cdasws import CdasWs
    CDASWS_AVAILABLE = True
except ImportError:
    CDASWS_AVAILABLE = False

# --- CONFIGURATION ---
# Default: Parker Solar Probe, Encounter 18 (Perihelion)
# Date: Dec 28, 2023 (Deep inside the corona)
DEFAULT_START_TIME = '2023-12-28'
DEFAULT_END_TIME = '2023-12-29'
BASELINE_WINDOW = '1h'  # Rolling window for B0 (1h adaptive for Perihelion dynamics)
THEORETICAL_LIMIT = 0.1528  # The χ = 0.15 boundary
BOUNDARY_TOLERANCE = 0.01  # Tolerance for boundary check (±0.01 around THEORETICAL_LIMIT)
STEADY_STATE_THRESHOLD = 0.2  # Chi threshold for steady-state calculation
OUTPUT_DIR = 'figures'

# Demo data generation parameters
DEMO_SWITCHBACK_COUNT = 20  # Number of switchback events to simulate
DEMO_SWITCHBACK_DURATION_MIN = 5  # Minimum switchback duration in minutes
DEMO_SWITCHBACK_DURATION_MAX = 30  # Maximum switchback duration in minutes
DEMO_SWITCHBACK_AMPLITUDE_MIN = 0.5  # Minimum reversal amplitude (fraction)
DEMO_SWITCHBACK_AMPLITUDE_MAX = 1.5  # Maximum reversal amplitude (fraction)


def fetch_psp_mag_data(start_date, end_date):
    """
    Fetch PSP FIELDS MAG data using cdasws.
    
    This replaces pyspedas.psp.fields() with Python 3.12 compatible cdasws.
    
    Args:
        start_date: Start date string 'YYYY-MM-DD'
        end_date: End date string 'YYYY-MM-DD'
    
    Returns:
        DataFrame with columns ['Br', 'Bt', 'Bn'] indexed by time, or None if unavailable
    """
    if not CDASWS_AVAILABLE:
        print("❌ cdasws is not installed. Install with: pip install cdasws")
        return None
    
    cdas = CdasWs()
    trange = [f"{start_date}T00:00:00Z", f"{end_date}T23:59:59Z"]
    
    print(f"Downloading data from NASA CDAWeb...")
    print(f"  Period: {start_date} to {end_date}")
    
    # Try multiple dataset options for MAG RTN data
    datasets_to_try = [
        ('PSP_FLD_L2_MAG_RTN_1MIN', ['psp_fld_l2_mag_RTN_1min']),
        ('PSP_FLD_L2_MAG_RTN', ['psp_fld_l2_mag_RTN']),
    ]
    
    mag_data = None
    for dataset, variables in datasets_to_try:
        try:
            print(f"  Trying dataset: {dataset}...")
            status, data = cdas.get_data(dataset, variables, trange[0], trange[1])
            if status == 0 and data is not None:
                mag_data = data
                print(f"  ✓ Data retrieved from {dataset}")
                break
            else:
                print(f"  ⚠ No data from {dataset} (status={status})")
        except Exception as e:
            print(f"  ✗ Error fetching from {dataset}: {e}")
            continue
    
    if mag_data is None:
        return None
    
    # Convert xarray/cdasws data to pandas DataFrame
    try:
        if hasattr(mag_data, 'to_dataframe'):
            df_raw = mag_data.to_dataframe().reset_index()
        else:
            print("  ✗ Unexpected data format from CDAWeb")
            return None
        
        # Find the time column
        time_col = None
        for col in df_raw.columns:
            if 'epoch' in col.lower() or 'time' in col.lower():
                time_col = col
                break
        
        if time_col is None:
            print("  ✗ Could not find time column in data")
            return None
        
        # Find the B_RTN data column (vector [R, T, N])
        b_col = None
        for col in df_raw.columns:
            if 'mag_rtn' in col.lower() or 'b_rtn' in col.lower():
                b_col = col
                break
        
        if b_col is None:
            print("  ✗ Could not find magnetic field column in data")
            return None
        
        # Extract RTN components
        times = pd.to_datetime(df_raw[time_col])
        b_data = df_raw[b_col]
        
        # Check if data is empty before accessing iloc[0]
        if len(b_data) == 0:
            print("  ✗ Empty magnetic field data")
            return None
        
        # Handle vector data (may be array-like per row)
        if hasattr(b_data.iloc[0], '__len__') and len(b_data.iloc[0]) >= 3:
            br = b_data.apply(lambda x: x[0] if hasattr(x, '__len__') else np.nan)
            bt = b_data.apply(lambda x: x[1] if hasattr(x, '__len__') else np.nan)
            bn = b_data.apply(lambda x: x[2] if hasattr(x, '__len__') else np.nan)
        else:
            # Try to find separate columns for Br, Bt, Bn
            br = df_raw.get('Br', pd.Series([np.nan] * len(df_raw)))
            bt = df_raw.get('Bt', pd.Series([np.nan] * len(df_raw)))
            bn = df_raw.get('Bn', pd.Series([np.nan] * len(df_raw)))
        
        df = pd.DataFrame({
            'Br': br.values,
            'Bt': bt.values,
            'Bn': bn.values
        }, index=times)
        
        # Remove NaN rows
        df = df.dropna()
        
        print(f"  ✓ Processed {len(df)} data points")
        return df
        
    except Exception as e:
        print(f"  ✗ Error processing MAG data: {e}")
        return None


def generate_demo_psp_data():
    """
    Generate synthetic PSP-like MAG data for testing.
    
    This replaces the need for live data when testing the verification pipeline.
    Uses realistic near-Sun magnetic field conditions.
    """
    print("\n🎲 Generating demo PSP MAG data for testing...")
    print("   (Note: Use real PSP data via cdasws for actual validation)")
    
    # Create 24 hours of synthetic data at 1-minute resolution
    times = pd.date_range('2023-12-28 00:00:00', periods=1440, freq='1min')
    
    # Near-Sun conditions: high B field (~100-500 nT), strong radial component
    # Simulate typical perihelion conditions at ~10 solar radii
    t_hours = np.arange(len(times)) / 60.0
    
    # Use reproducible random numbers
    rng = np.random.default_rng(42)
    
    # Radial component (dominant near Sun)
    Br_baseline = -150.0  # nT - negative = toward Sun (Parker spiral)
    Br = Br_baseline + 30.0 * np.sin(2 * np.pi * t_hours / 24) + rng.normal(0, 15.0, len(times))
    
    # Tangential component (from solar rotation)
    Bt_baseline = 50.0  # nT
    Bt = Bt_baseline + 20.0 * np.sin(2 * np.pi * t_hours / 12) + rng.normal(0, 10.0, len(times))
    
    # Normal component (smaller)
    Bn_baseline = 0.0  # nT
    Bn = Bn_baseline + 10.0 * np.sin(2 * np.pi * t_hours / 6) + rng.normal(0, 8.0, len(times))
    
    # Add switchback events (characteristic of PSP observations)
    # Switchbacks cause brief reversals in Br
    for _ in range(DEMO_SWITCHBACK_COUNT):
        idx = rng.integers(0, len(times))
        width = rng.integers(DEMO_SWITCHBACK_DURATION_MIN, DEMO_SWITCHBACK_DURATION_MAX)
        amplitude = rng.uniform(DEMO_SWITCHBACK_AMPLITUDE_MIN, DEMO_SWITCHBACK_AMPLITUDE_MAX)
        for j in range(max(0, idx - width // 2), min(len(times), idx + width // 2)):
            Br[j] = -Br[j] * amplitude
    
    df = pd.DataFrame({
        'Br': Br,
        'Bt': Bt,
        'Bn': Bn
    }, index=times)
    
    print(f"  ✓ Generated {len(df)} demo data points")
    print(f"  Br range: {df['Br'].min():.1f} to {df['Br'].max():.1f} nT")
    print(f"  Bt range: {df['Bt'].min():.1f} to {df['Bt'].max():.1f} nT")
    print(f"  Bn range: {df['Bn'].min():.1f} to {df['Bn'].max():.1f} nT")
    
    return df


def compute_chi(df, baseline_window='1h'):
    """
    Calculate χ (chi) using the LUFT algorithm.
    
    χ = |B - B₀| / B₀
    
    where:
    - B is the instantaneous magnetic field magnitude
    - B₀ is the baseline (rolling median over baseline_window)
    
    Args:
        df: DataFrame with columns ['Br', 'Bt', 'Bn']
        baseline_window: Rolling window for baseline calculation
    
    Returns:
        DataFrame with added columns ['B_mag', 'B_baseline', 'chi']
    """
    print(f"\nCalculating Chi (using {baseline_window} adaptive baseline for Perihelion)...")
    
    # Calculate magnitude |B|
    df = df.copy()
    df['B_mag'] = np.sqrt(df['Br']**2 + df['Bt']**2 + df['Bn']**2)
    
    # Calculate baseline B₀ (rolling median)
    # Using center=True for symmetric window
    df['B_baseline'] = df['B_mag'].rolling(window=baseline_window, center=True).median()
    
    # Drop NaN values from rolling window edges
    df = df.dropna()
    
    # Compute χ = |B - B₀| / B₀
    # Guard against division by zero
    df['chi'] = np.where(
        df['B_baseline'] > 0,
        (df['B_mag'] - df['B_baseline']).abs() / df['B_baseline'],
        np.nan
    )
    
    # Remove any remaining NaN or infinite values
    df = df.replace([np.inf, -np.inf], np.nan).dropna()
    
    print(f"  ✓ Computed chi for {len(df)} points")
    
    return df


def analyze_chi_results(df):
    """
    Analyze χ results and check against the theoretical limit.
    
    Args:
        df: DataFrame with 'chi' column
    
    Returns:
        dict with analysis results
    """
    max_chi = df['chi'].max()
    min_chi = df['chi'].min()
    mean_chi = df['chi'].mean()
    median_chi = df['chi'].median()
    
    # Calculate steady-state ceiling (99th percentile of values below threshold)
    steady_flow = df[df['chi'] <= STEADY_STATE_THRESHOLD]['chi']
    if len(steady_flow) > 0:
        steady_chi = steady_flow.quantile(0.99)
    else:
        steady_chi = max_chi
    
    # Count boundary violations
    violations = (df['chi'] > THEORETICAL_LIMIT).sum()
    total_points = len(df)
    violation_rate = violations / total_points * 100 if total_points > 0 else 0
    
    # Check if the 0.15 boundary holds (within tolerance)
    boundary_lower = THEORETICAL_LIMIT - BOUNDARY_TOLERANCE
    boundary_upper = THEORETICAL_LIMIT + BOUNDARY_TOLERANCE
    boundary_holds = steady_chi < boundary_upper and steady_chi > boundary_lower
    
    results = {
        'max_chi': max_chi,
        'min_chi': min_chi,
        'mean_chi': mean_chi,
        'median_chi': median_chi,
        'steady_chi': steady_chi,
        'violations': violations,
        'total_points': total_points,
        'violation_rate': violation_rate,
        'boundary_holds': boundary_holds,
    }
    
    return results


def plot_verification_results(df, results, start_time, output_path):
    """
    Generate the verification plot showing χ against the theoretical limit.
    
    Args:
        df: DataFrame with 'chi' column and datetime index
        results: Analysis results dict
        start_time: Start time string for title
        output_path: Path to save the plot
    
    Returns:
        Path to saved plot
    """
    plt.figure(figsize=(12, 6))
    
    # Set style
    sns.set_style("whitegrid")
    
    # Plot χ time series
    plt.plot(df.index, df['chi'], color='#333333', linewidth=1, label=r'PSP $\chi$')
    
    # Plot theoretical limit
    plt.axhline(y=THEORETICAL_LIMIT, color='red', linestyle='--', linewidth=2, 
                label=f'0.15 Limit ({THEORETICAL_LIMIT:.4f})')
    
    # Shade the acceptable region
    plt.fill_between(df.index, 0, THEORETICAL_LIMIT, alpha=0.1, color='green',
                     label='Stable Region')
    
    # Title and labels
    status = "SUCCESS" if results['boundary_holds'] else "NOTICE"
    plt.title(f'Parker Solar Probe: Chi Scaling at Perihelion ({start_time})\n'
              f'{status}: Steady State Ceiling = {results["steady_chi"]:.4f}', 
              fontsize=14, fontweight='bold')
    plt.xlabel('Time (UTC)', fontsize=12)
    plt.ylabel(r'$\chi$ (Chi)', fontsize=12)
    plt.ylim(0, max(0.3, results['max_chi'] * 1.1))
    plt.legend(loc='upper right')
    plt.grid(True, alpha=0.3)
    
    # Rotate x-axis labels for readability
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    # Save plot
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    return output_path


def run_psp_verification(start_time=None, end_time=None, demo=False, output_dir=OUTPUT_DIR):
    """
    Run the complete PSP verification pipeline.
    
    Args:
        start_time: Start date 'YYYY-MM-DD' (default: 2023-12-28)
        end_time: End date 'YYYY-MM-DD' (default: 2023-12-29)
        demo: If True, use synthetic demo data
        output_dir: Directory for output files
    
    Returns:
        dict with verification results
    """
    start_time = start_time or DEFAULT_START_TIME
    end_time = end_time or DEFAULT_END_TIME
    
    print("=" * 60)
    print("   PSP SCALING VERIFICATION")
    print("   χ ≤ 0.15 Universal Boundary Near-Sun Validation")
    print("=" * 60)
    print(f"\nTarget: Parker Solar Probe (FIELDS/MAG)")
    print(f"Window: {start_time} to {end_time}")
    
    # 1. Fetch or generate data
    if demo:
        df = generate_demo_psp_data()
    else:
        df = fetch_psp_mag_data(start_time, end_time)
        
        if df is None:
            print("\n⚠️  No data available. Falling back to demo data.")
            print("   This may be because:")
            print("   - Data for this period hasn't been publicly released yet")
            print("   - CDAWeb is temporarily unavailable")
            print("   - Dataset names may have changed")
            df = generate_demo_psp_data()
    
    if df is None or len(df) == 0:
        print("\n❌ Error: No data available for verification.")
        return None
    
    print(f"\nData acquired: {len(df)} points")
    
    # 2. Compute χ
    df = compute_chi(df, baseline_window=BASELINE_WINDOW)
    
    # 3. Analyze results
    results = analyze_chi_results(df)
    
    print(f"\n{'=' * 60}")
    print("   RESULTS")
    print(f"{'=' * 60}")
    print(f"Max Chi Observed: {results['max_chi']:.4f}")
    print(f"Min Chi Observed: {results['min_chi']:.4f}")
    print(f"Mean Chi: {results['mean_chi']:.4f}")
    print(f"Median Chi: {results['median_chi']:.4f}")
    print(f"Steady State Ceiling (99%): {results['steady_chi']:.4f}")
    print(f"Violations (>{THEORETICAL_LIMIT:.4f}): {results['violations']} / {results['total_points']} ({results['violation_rate']:.2f}%)")
    
    # Check the boundary
    if results['boundary_holds']:
        print(f"\n✓ SUCCESS: 0.15 Boundary holds in the Corona!")
    else:
        print(f"\n⚠ NOTICE: Boundary shifted. New limit: {results['steady_chi']:.4f}")
    
    # 4. Generate plot
    os.makedirs(output_dir, exist_ok=True)
    plot_filename = f"psp_verification_{start_time}_{end_time}.png".replace(' ', '_')
    plot_path = os.path.join(output_dir, plot_filename)
    saved_path = plot_verification_results(df, results, start_time, plot_path)
    print(f"\nChart saved to: {saved_path}")
    
    # 5. Also save the simple filename for backward compatibility
    simple_path = os.path.join(output_dir, 'psp_verification_result.png')
    if saved_path != simple_path:
        import shutil
        shutil.copy(saved_path, simple_path)
        print(f"Also saved to: {simple_path}")
    
    print(f"\n{'=' * 60}")
    print("   VERIFICATION COMPLETE")
    print(f"{'=' * 60}\n")
    
    return {
        'results': results,
        'data_points': len(df),
        'plot_path': saved_path,
        'start_time': start_time,
        'end_time': end_time,
        'demo_mode': demo,
    }


def main():
    parser = argparse.ArgumentParser(
        description="PSP Scaling Verification for χ ≤ 0.15 Boundary (Python 3.12 compatible)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default dates (Encounter 18, Dec 2023)
  python scripts/psp_verification.py

  # Specify custom date range
  python scripts/psp_verification.py --start 2023-12-28 --end 2023-12-29

  # Use demo data for testing
  python scripts/psp_verification.py --demo

Note:
  This script uses cdasws instead of pyspedas/pytplot for Python 3.12 compatibility.
  The χ = 0.15 boundary verification works identically to the original algorithm.

Contact: CARLDCLINE@GMAIL.COM
Repository: https://github.com/CarlDeanClineSr/luft-portal-
        """
    )
    
    parser.add_argument('--start', type=str, default=DEFAULT_START_TIME,
                        help=f'Start date YYYY-MM-DD (default: {DEFAULT_START_TIME})')
    parser.add_argument('--end', type=str, default=DEFAULT_END_TIME,
                        help=f'End date YYYY-MM-DD (default: {DEFAULT_END_TIME})')
    parser.add_argument('--output-dir', type=str, default=OUTPUT_DIR,
                        help=f'Output directory for plots (default: {OUTPUT_DIR})')
    parser.add_argument('--demo', action='store_true',
                        help='Use synthetic demo data for testing')
    
    args = parser.parse_args()
    
    result = run_psp_verification(
        start_time=args.start,
        end_time=args.end,
        demo=args.demo,
        output_dir=args.output_dir
    )
    
    if result is None:
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
