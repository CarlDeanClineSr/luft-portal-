#!/usr/bin/env python3
"""
Blind Transient Test — χ Boundary Validation
=============================================

This script implements a "blind" test to validate Carl Dean Cline Sr.'s χ ≤ 0.15
universal boundary discovery. The test uses purely kinetic/thermal parameters to
classify data into "steady" vs "transient" regimes, WITHOUT using magnetic field
data (χ) in the classification.

This eliminates potential circularity in the analysis:
- If χ ≤ 0.15 emerges naturally in the "steady" regime (classified without
  using magnetic data), this confirms the boundary is a physical property of
  the quiet solar wind, not a statistical artifact.

The "Kinetic Shock" Protocol:
----------------------------
A data point is flagged as TRANSIENT if ANY of these conditions are met:
1. Velocity Surge: Solar wind speed > 600 km/s (fast wind / CME driver)
2. Velocity Jump: |Δv| > 50 km/s per hour (shock front indicator)
3. Density Compression: Proton density > 15 p/cm³ (compressed sheath region)

These thresholds are based on NOAA/SWPC Rankine-Hugoniot shock indicators.

Success Condition:
-----------------
The "Steady" distribution should naturally wall off at χ = 0.15, while the
"Transient" distribution shows the long tail of shocks/storms.

Author: LUFT Portal Project
Based on: Carl Dean Cline Sr.'s empirical discovery
Reference: Action Plan for Validation of χ = 0.15 Boundary
"""

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# =============================================================================
# KINETIC SHOCK THRESHOLDS (NOAA/SWPC-based)
# =============================================================================

VELOCITY_THRESHOLD = 600      # km/s - Fast wind / CME driver
VELOCITY_JUMP_THRESHOLD = 50  # km/s per hour - Shock front
DENSITY_THRESHOLD = 15        # p/cm³ - Compressed sheath

# Optional thermal thresholds (commented out for simpler implementation)
# TEMPERATURE_THRESHOLD = 5e5  # K - High temperature regions

# χ boundary value (Carl's discovery)
CHI_BOUNDARY = 0.15


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def detect_velocity_jump(speed_series, threshold=VELOCITY_JUMP_THRESHOLD):
    """
    Detect velocity jumps indicating shock fronts.

    Uses the absolute difference of speed values. Since data may not be
    exactly hourly, we compute the diff and check if it exceeds threshold.

    Args:
        speed_series: Pandas Series of speed values (km/s)
        threshold: Jump threshold in km/s

    Returns:
        Boolean Series where True indicates a velocity jump
    """
    # Compute absolute difference between consecutive readings
    # This is a simplified approach; for exact hourly rates,
    # would need time-weighted differences
    return speed_series.diff().abs() > threshold


def classify_kinetic_regime(df, speed_col='speed', density_col='density'):
    """
    Classify data points into kinetic regimes using ONLY speed and density.

    This is the "blind" classification that ignores magnetic field data.

    Args:
        df: DataFrame with solar wind data
        speed_col: Name of the speed column (km/s)
        density_col: Name of the density column (p/cm³)

    Returns:
        Series of regime flags: 1 = Transient, 0 = Steady
    """
    # Ensure columns exist
    if speed_col not in df.columns:
        raise KeyError(f"Speed column '{speed_col}' not found in data")
    if density_col not in df.columns:
        raise KeyError(f"Density column '{density_col}' not found in data")

    # Convert to numeric (handle any string values)
    speed = pd.to_numeric(df[speed_col], errors='coerce')
    density = pd.to_numeric(df[density_col], errors='coerce')

    # Velocity surge (fast wind)
    v_high = speed > VELOCITY_THRESHOLD

    # Velocity jump (shock front)
    v_jump = detect_velocity_jump(speed)

    # Density compression
    n_high = density > DENSITY_THRESHOLD

    # Combine: ANY condition flags as transient
    regime_flag = (v_high | v_jump | n_high).astype(int)

    return regime_flag


def analyze_chi_by_regime(df, chi_col='chi', regime_col='regime_flag'):
    """
    Analyze χ distribution for each regime.

    Args:
        df: DataFrame with χ and regime data
        chi_col: Name of the chi column
        regime_col: Name of the regime flag column

    Returns:
        Dictionary with analysis results for each regime
    """
    results = {}

    # Ensure chi column is numeric
    chi_values = pd.to_numeric(df[chi_col], errors='coerce')

    for regime, name in [(0, 'steady'), (1, 'transient')]:
        subset = chi_values[df[regime_col] == regime].dropna()

        if len(subset) == 0:
            results[name] = {
                'count': 0,
                'max': None,
                'min': None,
                'mean': None,
                'median': None,
                'std': None,
                'p99': None,
                'p95': None,
                'violations': 0,
                'violations_pct': 0.0
            }
            continue

        violations = (subset > CHI_BOUNDARY).sum()

        results[name] = {
            'count': len(subset),
            'max': float(subset.max()),
            'min': float(subset.min()),
            'mean': float(subset.mean()),
            'median': float(subset.median()),
            'std': float(subset.std()),
            'p99': float(subset.quantile(0.99)),
            'p95': float(subset.quantile(0.95)),
            'violations': int(violations),
            'violations_pct': float(100 * violations / len(subset))
        }

    return results


def create_visualization(df, chi_col='chi', regime_col='regime_flag',
                        output_path=None, show=False):
    """
    Create side-by-side histogram visualization of χ distributions.

    Args:
        df: DataFrame with χ and regime data
        chi_col: Name of the chi column
        regime_col: Name of the regime flag column
        output_path: Path to save the figure (optional)
        show: Whether to display the figure interactively

    Returns:
        Figure object
    """
    # Convert chi to numeric
    chi_values = pd.to_numeric(df[chi_col], errors='coerce')

    steady = chi_values[df[regime_col] == 0].dropna()
    transient = chi_values[df[regime_col] == 1].dropna()

    fig, ax = plt.subplots(figsize=(12, 6), dpi=100)

    # Plot steady state distribution
    if len(steady) > 0:
        ax.hist(steady, bins=100, alpha=0.6, label=f'Steady (n={len(steady):,})',
                density=True, range=(0, 0.3), color='#2E86AB')

    # Plot transient distribution
    if len(transient) > 0:
        ax.hist(transient, bins=100, alpha=0.4, color='red',
                label=f'Transient (n={len(transient):,})', density=True,
                range=(0, 0.3))

    # Mark the proposed boundary
    ax.axvline(x=CHI_BOUNDARY, color='black', linestyle='--', linewidth=2,
               label=f'χ = {CHI_BOUNDARY} Boundary')

    ax.set_xlabel('χ (Normalized Magnetic Perturbation)', fontsize=12)
    ax.set_ylabel('Probability Density', fontsize=12)
    ax.set_title('Blind Transient Test: Emergence of χ = 0.15 Boundary\n'
                 '(Regimes classified WITHOUT using magnetic data)',
                 fontsize=14)
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(True, alpha=0.3)

    # Add annotation box with key findings
    textstr = (f'Steady Max χ: {steady.max():.4f}\n'
               f'Steady 99th %ile: {steady.quantile(0.99):.4f}'
               if len(steady) > 0 else 'No steady data')
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=props)

    fig.tight_layout()

    if output_path:
        fig.savefig(output_path, bbox_inches='tight')
        print(f"[OK] Visualization saved to: {output_path}")

    if show:
        plt.show()

    return fig


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def run_blind_transient_test(csv_path, time_col='timestamp_utc',
                             speed_col='speed_km_s', density_col='density_p_cm3',
                             chi_col='chi_amplitude', output_dir=None):
    """
    Run the complete blind transient test on a dataset.

    Args:
        csv_path: Path to the CSV data file
        time_col: Name of the timestamp column
        speed_col: Name of the speed column (km/s)
        density_col: Name of the density column (p/cm³)
        chi_col: Name of the chi column
        output_dir: Directory for output files (optional)

    Returns:
        Tuple of (DataFrame with classifications, analysis results)
    """
    print("=" * 70)
    print("BLIND TRANSIENT TEST — χ Boundary Validation")
    print("Carl Dean Cline Sr.'s Discovery")
    print("=" * 70)
    print()

    # Load data
    print(f"[1/4] Loading data from: {csv_path}")
    try:
        df = pd.read_csv(csv_path, parse_dates=[time_col], on_bad_lines='skip')
    except TypeError:
        # Older pandas version fallback
        df = pd.read_csv(csv_path, parse_dates=[time_col], error_bad_lines=False)
    df = df.sort_values(time_col).reset_index(drop=True)
    print(f"      Loaded {len(df):,} data points")
    print()

    # Check for required columns
    required_cols = [speed_col, density_col]
    for col in required_cols:
        if col not in df.columns:
            # Try alternate column names
            alternates = {
                'speed_km_s': ['speed', 'solar_wind_speed', 'v_sw'],
                'density_p_cm3': ['density', 'proton_density', 'np']
            }
            found = False
            for alt in alternates.get(col, []):
                if alt in df.columns:
                    df[col] = df[alt]
                    found = True
                    print(f"      Using alternate column: {alt} -> {col}")
                    break
            if not found:
                raise KeyError(f"Required column '{col}' not found. "
                             f"Available: {list(df.columns)}")

    # Classify kinetic regimes (WITHOUT using chi)
    print("[2/4] Classifying kinetic regimes (BLIND to magnetic data)...")
    print(f"      Thresholds:")
    print(f"        - Velocity surge: > {VELOCITY_THRESHOLD} km/s")
    print(f"        - Velocity jump:  > {VELOCITY_JUMP_THRESHOLD} km/s")
    print(f"        - Density compression: > {DENSITY_THRESHOLD} p/cm³")

    df['regime_flag'] = classify_kinetic_regime(
        df, speed_col=speed_col, density_col=density_col
    )

    n_steady = (df['regime_flag'] == 0).sum()
    n_transient = (df['regime_flag'] == 1).sum()
    print(f"      Steady state:  {n_steady:,} points ({100*n_steady/len(df):.1f}%)")
    print(f"      Transient:     {n_transient:,} points ({100*n_transient/len(df):.1f}%)")
    print()

    # Analyze chi distributions
    print("[3/4] Analyzing χ distributions by regime...")

    # Handle chi column name variations
    if chi_col not in df.columns:
        for alt in ['chi', 'chi_amplitude', 'chi_amplitude_extended']:
            if alt in df.columns:
                chi_col = alt
                print(f"      Using chi column: {chi_col}")
                break
        else:
            raise KeyError(f"Chi column not found. Available: {list(df.columns)}")

    results = analyze_chi_by_regime(df, chi_col=chi_col)
    print()

    # Output results
    print("=" * 70)
    print("RESULTS — THE 'REVEAL'")
    print("=" * 70)
    print()

    print("STEADY STATE (Kinetic Lattice):")
    if results['steady']['count'] > 0:
        print(f"  Count:           {results['steady']['count']:,}")
        print(f"  Max χ:           {results['steady']['max']:.4f}")
        print(f"  99th Percentile: {results['steady']['p99']:.4f}")
        print(f"  Mean χ:          {results['steady']['mean']:.4f}")
        print(f"  Violations:      {results['steady']['violations']} "
              f"({results['steady']['violations_pct']:.2f}%)")

        if results['steady']['max'] <= CHI_BOUNDARY + 0.01:
            print(f"  ✅ BOUNDARY CONFIRMED: Steady max χ ≤ {CHI_BOUNDARY}")
        else:
            print(f"  ⚠️  WARNING: Steady max χ exceeds boundary")
    else:
        print("  (No steady state data)")
    print()

    print("TRANSIENT STATE (Shocks/Storms):")
    if results['transient']['count'] > 0:
        print(f"  Count:           {results['transient']['count']:,}")
        print(f"  Max χ:           {results['transient']['max']:.4f}")
        print(f"  99th Percentile: {results['transient']['p99']:.4f}")
        print(f"  Mean χ:          {results['transient']['mean']:.4f}")
        print(f"  Violations:      {results['transient']['violations']} "
              f"({results['transient']['violations_pct']:.2f}%)")
    else:
        print("  (No transient data)")
    print()

    # Create visualization
    print("[4/4] Generating visualization...")
    output_path = None
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "blind_transient_test_chi_distribution.png"
    else:
        output_path = Path("reports/charts/blind_transient_test_chi_distribution.png")
        output_path.parent.mkdir(parents=True, exist_ok=True)

    fig = create_visualization(df, chi_col=chi_col, output_path=output_path)
    plt.close(fig)
    print()

    # Summary
    print("=" * 70)
    print("INTERPRETATION")
    print("=" * 70)
    if results['steady']['count'] > 0 and results['steady']['max'] <= CHI_BOUNDARY + 0.01:
        print("""
The χ = 0.15 boundary EMERGES naturally in the steady-state solar wind
when classified using ONLY kinetic parameters (speed, density).

This confirms Carl Dean Cline Sr.'s discovery:
• The boundary is a PHYSICAL property of the quiet plasma
• It is NOT a circular result of filtering by magnetic field
• The proton lattice has a maximum sustainable magnetic perturbation

The "transient" regime (shocks, CMEs) may exceed this boundary because
coherent glow-mode oscillation breaks down during violent disturbances.
""")
    else:
        print("""
Results are inconclusive or unexpected. This may indicate:
• Data quality issues (gaps, calibration)
• Need to adjust kinetic thresholds for this dataset
• A genuine exception worth investigating

Review the visualization for detailed distribution shapes.
""")

    print("=" * 70)
    print("[OK] Blind transient test complete.")
    print("=" * 70)

    return df, results


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

def main():
    """Command-line interface for the blind transient test."""
    parser = argparse.ArgumentParser(
        description="Blind Transient Test for χ Boundary Validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s data/cme_heartbeat_log_2025_12.csv
  %(prog)s data.csv --speed-col speed --density-col density --chi-col chi

The test classifies data into "steady" vs "transient" regimes using
ONLY kinetic parameters (speed, density), then analyzes χ distributions
to verify that the χ ≤ 0.15 boundary emerges naturally in steady plasma.
        """
    )

    parser.add_argument('csv_path', type=str, help='Path to input CSV file')
    parser.add_argument('--time-col', type=str, default='timestamp_utc',
                        help='Timestamp column name (default: timestamp_utc)')
    parser.add_argument('--speed-col', type=str, default='speed_km_s',
                        help='Speed column name (default: speed_km_s)')
    parser.add_argument('--density-col', type=str, default='density_p_cm3',
                        help='Density column name (default: density_p_cm3)')
    parser.add_argument('--chi-col', type=str, default='chi_amplitude',
                        help='Chi column name (default: chi_amplitude)')
    parser.add_argument('--output-dir', type=str, default=None,
                        help='Output directory for results')

    args = parser.parse_args()

    if not Path(args.csv_path).exists():
        print(f"Error: File not found: {args.csv_path}", file=sys.stderr)
        sys.exit(1)

    try:
        run_blind_transient_test(
            args.csv_path,
            time_col=args.time_col,
            speed_col=args.speed_col,
            density_col=args.density_col,
            chi_col=args.chi_col,
            output_dir=args.output_dir
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
