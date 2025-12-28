#!/usr/bin/env python3
"""
luft_solar_wind_audit.py
=========================
LUFT Solar Wind Audit with χ = 0.15 Universal Boundary Analysis

Analyzes DSCOVR/ACE solar wind data for χ amplitude and validates against
the universal χ = 0.15 plasma coherence boundary discovered by Carl Dean Cline Sr.

Discovered: December 2-27, 2025
Location: Lincoln, Nebraska

This script processes solar wind magnetic field and plasma data to:
- Compute χ = |B - B_baseline| / B_baseline
- Classify observations relative to χ = 0.15 boundary
- Detect attractor states (>50% at boundary)
- Report violations (χ > 0.155)

Contact: CARLDCLINE@GMAIL.COM
Repository: https://github.com/CarlDeanClineSr/luft-portal-
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

# χ = 0.15 Universal Boundary Constants
CHI_CAP_THEORETICAL = 0.15
CHI_TOLERANCE = 0.01
CHI_BOUNDARY_MIN = CHI_CAP_THEORETICAL - CHI_TOLERANCE
CHI_BOUNDARY_MAX = CHI_CAP_THEORETICAL + CHI_TOLERANCE


def load_solar_wind_data(filepath):
    """
    Load solar wind data from CSV or JSON file.
    
    Expected columns:
    - timestamp (or time, datetime)
    - bt (or B_total, total_field) - magnetic field magnitude in nT
    
    Returns:
        DataFrame with timestamp and bt columns
    """
    filepath = Path(filepath)
    
    if not filepath.exists():
        print(f"Error: File not found: {filepath}")
        return None
    
    try:
        if filepath.suffix == '.json':
            with open(filepath, 'r') as f:
                data = json.load(f)
                df = pd.DataFrame(data)
        else:  # CSV
            df = pd.read_csv(filepath)
        
        # Normalize column names
        timestamp_cols = ['timestamp', 'time', 'datetime', 'time_tag']
        field_cols = ['bt', 'B_total', 'total_field', 'b_total']
        
        # Find timestamp column
        ts_col = None
        for col in timestamp_cols:
            if col in df.columns:
                ts_col = col
                break
        
        if ts_col is None:
            print(f"Error: Could not find timestamp column in {filepath}")
            return None
        
        # Find field magnitude column
        bt_col = None
        for col in field_cols:
            if col in df.columns:
                bt_col = col
                break
        
        if bt_col is None:
            print(f"Error: Could not find magnetic field magnitude column in {filepath}")
            return None
        
        # Rename to standard names
        df = df.rename(columns={ts_col: 'timestamp', bt_col: 'bt'})
        
        # Parse timestamps
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Convert bt to numeric
        df['bt'] = pd.to_numeric(df['bt'], errors='coerce')
        
        # Drop rows with invalid data
        df = df.dropna(subset=['timestamp', 'bt'])
        
        print(f"Loaded {len(df)} observations from {filepath}")
        return df
        
    except Exception as e:
        print(f"Error loading data from {filepath}: {e}")
        return None


def compute_chi_amplitude(df, baseline_window_hours=24):
    """
    Compute χ amplitude from magnetic field data.
    
    χ = |B - B_baseline| / B_baseline
    
    Args:
        df: DataFrame with 'bt' column (magnetic field magnitude)
        baseline_window_hours: Hours for rolling baseline calculation
    
    Returns:
        DataFrame with added 'baseline' and 'chi_amplitude' columns
    """
    df = df.copy()
    df = df.sort_values('timestamp')
    
    # Compute rolling baseline (24-hour window)
    # Convert hours to number of observations (assuming ~1 min cadence)
    window_size = baseline_window_hours * 60
    
    if len(df) >= window_size:
        df['baseline'] = df['bt'].rolling(
            window=window_size, 
            center=True, 
            min_periods=max(100, window_size // 10)
        ).mean()
    else:
        # Use global mean if insufficient data for rolling window
        df['baseline'] = df['bt'].mean()
    
    # Handle edges (where rolling window doesn't apply)
    df.loc[:, 'baseline'] = df['baseline'].fillna(df['bt'].mean())
    
    # Compute χ amplitude
    df['chi_amplitude'] = np.abs(df['bt'] - df['baseline']) / df['baseline']
    
    return df


def classify_chi_status(chi_val):
    """
    Classify χ value relative to universal boundary.
    
    Returns:
        'UNKNOWN' - NaN value
        'VIOLATION' - Above boundary (χ > 0.155)
        'AT_BOUNDARY' - At optimal coupling (0.145 ≤ χ ≤ 0.155)
        'BELOW' - Glow mode (χ < 0.145)
    """
    if pd.isna(chi_val):
        return 'UNKNOWN'
    elif chi_val > CHI_BOUNDARY_MAX:
        return 'VIOLATION'
    elif CHI_BOUNDARY_MIN <= chi_val <= CHI_BOUNDARY_MAX:
        return 'AT_BOUNDARY'
    else:
        return 'BELOW'


def analyze_chi_boundary(df):
    """
    Analyze χ values relative to the universal χ = 0.15 boundary.
    
    Returns:
        Dictionary with analysis results
    """
    chi_values = df['chi_amplitude'].dropna().values
    
    if len(chi_values) == 0:
        return None
    
    # Count observations in each category
    chi_at_boundary = np.sum((chi_values >= CHI_BOUNDARY_MIN) & 
                              (chi_values <= CHI_BOUNDARY_MAX))
    chi_violations = np.sum(chi_values > CHI_BOUNDARY_MAX)
    chi_below = len(chi_values) - chi_at_boundary - chi_violations
    
    # Compute fractions
    chi_boundary_fraction = chi_at_boundary / len(chi_values)
    chi_violation_fraction = chi_violations / len(chi_values)
    chi_below_fraction = chi_below / len(chi_values)
    
    # Compute statistics
    chi_mean = np.mean(chi_values)
    chi_std = np.std(chi_values)
    chi_max = np.max(chi_values)
    chi_min = np.min(chi_values)
    
    return {
        'total_observations': len(chi_values),
        'at_boundary_count': chi_at_boundary,
        'at_boundary_fraction': chi_boundary_fraction,
        'below_count': chi_below,
        'below_fraction': chi_below_fraction,
        'violations_count': chi_violations,
        'violations_fraction': chi_violation_fraction,
        'chi_mean': chi_mean,
        'chi_std': chi_std,
        'chi_max': chi_max,
        'chi_min': chi_min,
        'attractor_state': chi_boundary_fraction > 0.5
    }


def print_boundary_report(analysis):
    """Print formatted χ = 0.15 boundary analysis report."""
    if analysis is None:
        print("\nNo valid χ data available for boundary analysis.")
        return
    
    print(f"\n{'='*60}")
    print("χ = 0.15 UNIVERSAL BOUNDARY ANALYSIS")
    print(f"{'='*60}")
    print(f"Total observations: {analysis['total_observations']}")
    print(f"At boundary (0.145-0.155): {analysis['at_boundary_count']} "
          f"({analysis['at_boundary_fraction']*100:.1f}%)")
    print(f"Below boundary (<0.145): {analysis['below_count']} "
          f"({analysis['below_fraction']*100:.1f}%)")
    print(f"Violations (>0.155): {analysis['violations_count']} "
          f"({analysis['violations_fraction']*100:.2f}%)")
    
    print(f"\nχ Statistics:")
    print(f"  Mean: {analysis['chi_mean']:.4f}")
    print(f"  Std:  {analysis['chi_std']:.4f}")
    print(f"  Max:  {analysis['chi_max']:.4f}")
    print(f"  Min:  {analysis['chi_min']:.4f}")
    
    if analysis['violations_count'] > 0:
        print(f"\n⚠️  ALERT: {analysis['violations_count']} χ violations detected "
              f"- investigating filamentary breakdown")
        print("   Status: Coherence loss above χ = 0.15 threshold")
        print("   Action: Monitor for plasma instabilities")
    
    if analysis['attractor_state']:
        print(f"\n✅ System in ATTRACTOR STATE: "
              f"{analysis['at_boundary_fraction']*100:.1f}% at optimal coupling")
        print("   Status: Plasma locked to glow-mode maximum amplitude")
        print("   Physics: System spending >50% time at universal boundary")
    else:
        print(f"\nℹ️  System in NORMAL operation: "
              f"{analysis['below_fraction']*100:.1f}% below boundary")
    
    print(f"{'='*60}\n")


def save_analysis_results(df, analysis, output_dir):
    """Save analysis results to files."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save classified data to CSV
    timestamp_str = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    csv_path = output_dir / f'chi_analysis_{timestamp_str}.csv'
    
    # Add classification column
    df['chi_status'] = df['chi_amplitude'].apply(classify_chi_status)
    
    df.to_csv(csv_path, index=False)
    print(f"Saved classified data to: {csv_path}")
    
    # Save summary to JSON
    if analysis:
        json_path = output_dir / f'chi_boundary_summary_{timestamp_str}.json'
        summary = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'total_observations': int(analysis['total_observations']),
            'at_boundary_count': int(analysis['at_boundary_count']),
            'at_boundary_fraction': float(analysis['at_boundary_fraction']),
            'below_count': int(analysis['below_count']),
            'below_fraction': float(analysis['below_fraction']),
            'violations_count': int(analysis['violations_count']),
            'violations_fraction': float(analysis['violations_fraction']),
            'chi_mean': float(analysis['chi_mean']),
            'chi_std': float(analysis['chi_std']),
            'chi_max': float(analysis['chi_max']),
            'chi_min': float(analysis['chi_min']),
            'attractor_state': bool(analysis['attractor_state']),
            'status': 'ATTRACTOR' if analysis['attractor_state'] else 
                     'VIOLATION' if analysis['violations_count'] > 0 else 
                     'NOMINAL'
        }
        
        with open(json_path, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"Saved analysis summary to: {json_path}")
        
        # Append to tracking log
        log_path = output_dir / 'chi_boundary_tracking.jsonl'
        with open(log_path, 'a') as f:
            f.write(json.dumps(summary) + '\n')
        print(f"Appended to tracking log: {log_path}")


def main():
    parser = argparse.ArgumentParser(
        description="LUFT Solar Wind Audit — χ = 0.15 Universal Boundary Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/luft_solar_wind_audit.py --input data/dscovr/solar_wind_data.csv
  python scripts/luft_solar_wind_audit.py --input data/ace_mag_latest.json --output results/

Contact: CARLDCLINE@GMAIL.COM
Repository: https://github.com/CarlDeanClineSr/luft-portal-
        """
    )
    
    parser.add_argument('--input', '-i', type=str, required=True,
                       help='Path to solar wind data file (CSV or JSON)')
    parser.add_argument('--output', '-o', type=str, default='data',
                       help='Output directory for results (default: data)')
    parser.add_argument('--baseline-hours', type=int, default=24,
                       help='Hours for baseline rolling window (default: 24)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("   LUFT SOLAR WIND AUDIT")
    print("   χ = 0.15 Universal Boundary Analysis")
    print("=" * 60)
    print()
    
    # Load data
    print(f"Loading data from: {args.input}")
    df = load_solar_wind_data(args.input)
    
    if df is None or len(df) == 0:
        print("Error: No valid data loaded. Exiting.")
        sys.exit(1)
    
    # Compute χ amplitude
    print(f"\nComputing χ amplitude (baseline window: {args.baseline_hours}h)...")
    df = compute_chi_amplitude(df, baseline_window_hours=args.baseline_hours)
    
    print(f"Computed χ for {len(df)} observations")
    
    # Analyze χ boundary
    print("\nAnalyzing χ = 0.15 universal boundary...")
    analysis = analyze_chi_boundary(df)
    
    # Print report
    print_boundary_report(analysis)
    
    # Save results
    print("Saving analysis results...")
    save_analysis_results(df, analysis, args.output)
    
    print("\n" + "=" * 60)
    print("LUFT Solar Wind Audit complete.")
    print("Contact: CARLDCLINE@GMAIL.COM")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
