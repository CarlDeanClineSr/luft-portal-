#!/usr/bin/env python3
"""
heartbeat_detector.py
=====================
LUFT Heartbeat Detector — Test any dataset for the 2.4-hour cosmic modulation (χ = 0.055)

Discovered by Carl Dean Cline Sr., Lincoln, Nebraska
November 2025

This script allows anyone to analyze their own data for the universal modulation
signature that appears across quantum, resonance, collider, and cosmic domains.

Usage:
    python heartbeat_detector.py --input data.csv --time-col timestamp --value-col measurement
    python heartbeat_detector.py --demo  # Run with synthetic demonstration data

The script will:
1. Load your time-series data
2. Perform spectral analysis to find the 2.4-hour periodicity
3. Estimate the modulation amplitude (χ)
4. Generate a plot showing the analysis
5. Report whether the cosmic heartbeat signature is detected

Requirements:
    pip install numpy pandas matplotlib

Contact: CARLDCLINE@GMAIL.COM
Repository: https://github.com/CarlDeanClineSr/luft-portal-
"""

import argparse
import sys
from datetime import datetime, timedelta


def check_dependencies():
    """Check if required packages are installed."""
    missing = []
    try:
        import numpy
    except ImportError:
        missing.append("numpy")
    try:
        import pandas
    except ImportError:
        missing.append("pandas")
    
    if missing:
        print("Missing required packages:", ", ".join(missing))
        print("Install with: pip install " + " ".join(missing))
        sys.exit(1)


check_dependencies()

import numpy as np
import pandas as pd


# LUFT Constants
CHI_EXPECTED = 0.055  # Expected modulation amplitude
CHI_TOLERANCE = 0.012  # Tolerance range
OMEGA_HZ = 2 * np.pi * 1e-4  # Frequency in rad/s
PERIOD_HOURS = 2.4  # Period in hours
PERIOD_SECONDS = PERIOD_HOURS * 3600  # Period in seconds (8640s)


def generate_demo_data(hours=48, sample_minutes=2):
    """
    Generate synthetic demonstration data with the LUFT modulation embedded.
    
    Parameters:
        hours: Total duration of synthetic data
        sample_minutes: Sampling interval in minutes
    
    Returns:
        DataFrame with 'timestamp' and 'value' columns
    """
    n_points = int(hours * 60 / sample_minutes)
    timestamps = pd.date_range(
        start=datetime.now() - timedelta(hours=hours),
        periods=n_points,
        freq=f"{sample_minutes}min"
    )
    
    # Time in seconds from start
    t = np.arange(n_points) * sample_minutes * 60
    
    # Base signal with LUFT modulation
    base = 100.0
    chi = CHI_EXPECTED
    omega = 2 * np.pi / PERIOD_SECONDS
    
    # O(t) = O_0 * [1 + χ * cos(Ω*t + φ)]
    modulation = base * (1 + chi * np.cos(omega * t + np.random.uniform(0, 2*np.pi)))
    
    # Add realistic noise
    noise = np.random.normal(0, base * 0.02, n_points)
    values = modulation + noise
    
    return pd.DataFrame({
        'timestamp': timestamps,
        'value': values
    })


def load_data(filepath, time_col, value_col):
    """
    Load data from a CSV file.
    
    Parameters:
        filepath: Path to CSV file
        time_col: Name of timestamp column
        value_col: Name of value column to analyze
    
    Returns:
        DataFrame with parsed timestamps
    """
    try:
        df = pd.read_csv(filepath)
    except FileNotFoundError:
        print(f"Error: File not found: {filepath}")
        print("Please check the file path and try again.")
        sys.exit(1)
    except PermissionError:
        print(f"Error: Permission denied reading file: {filepath}")
        sys.exit(1)
    except pd.errors.EmptyDataError:
        print(f"Error: File is empty: {filepath}")
        sys.exit(1)
    except pd.errors.ParserError as e:
        print(f"Error: Could not parse CSV file: {filepath}")
        print(f"Details: {e}")
        print("Please ensure the file is a valid CSV format.")
        sys.exit(1)
    
    if time_col not in df.columns:
        print(f"Error: Column '{time_col}' not found in data.")
        print(f"Available columns: {list(df.columns)}")
        sys.exit(1)
    
    if value_col not in df.columns:
        print(f"Error: Column '{value_col}' not found in data.")
        print(f"Available columns: {list(df.columns)}")
        sys.exit(1)
    
    # Parse timestamps
    try:
        df[time_col] = pd.to_datetime(df[time_col])
    except (ValueError, TypeError) as e:
        print(f"Error: Could not parse timestamps in column '{time_col}'.")
        print(f"Details: {e}")
        print("Supported formats include: '2025-01-15 12:30:00', '2025-01-15', '01/15/2025', etc.")
        print("Tip: Ensure timestamps are in a consistent, standard format.")
        sys.exit(1)
    df = df.sort_values(time_col).reset_index(drop=True)
    
    return df, time_col, value_col


def compute_sampling_interval(timestamps):
    """Compute median sampling interval in seconds."""
    diffs = np.diff(timestamps.astype(np.int64) // 1e9)
    return np.median(diffs)


def spectral_analysis(values, dt_seconds):
    """
    Perform spectral analysis to find the 2.4-hour modulation.
    
    Parameters:
        values: Time-series values (numpy array)
        dt_seconds: Sampling interval in seconds
    
    Returns:
        Dictionary with spectral analysis results
    """
    n = len(values)
    
    # Remove mean and normalize
    values_centered = values - np.mean(values)
    values_norm = values_centered / np.std(values_centered) if np.std(values_centered) > 0 else values_centered
    
    # FFT
    fft_result = np.fft.rfft(values_norm)
    freqs = np.fft.rfftfreq(n, d=dt_seconds)
    power = np.abs(fft_result) ** 2
    
    # Convert to periods
    with np.errstate(divide='ignore'):
        periods_seconds = 1.0 / freqs
        periods_hours = periods_seconds / 3600
    
    # Find peak near 2.4 hours (search between 1.5 and 4 hours)
    target_period = PERIOD_HOURS
    search_mask = (periods_hours > 1.5) & (periods_hours < 4.0) & np.isfinite(periods_hours)
    
    if not np.any(search_mask):
        return {
            'detected': False,
            'reason': 'Insufficient data span for 2.4-hour analysis'
        }
    
    search_indices = np.where(search_mask)[0]
    peak_idx = search_indices[np.argmax(power[search_mask])]
    
    peak_period = periods_hours[peak_idx]
    peak_power = power[peak_idx]
    
    # Estimate χ amplitude from FFT
    # The modulation amplitude relates to the power spectral density
    total_power = np.sum(power[1:])  # Exclude DC
    mean_values = np.mean(values)
    if total_power > 0 and abs(mean_values) > 1e-10:
        relative_power = peak_power / total_power
        # χ estimated from relative power (simplified relationship)
        chi_estimate = np.sqrt(2 * relative_power) * np.std(values) / abs(mean_values)
        chi_estimate = min(chi_estimate, 1.0)  # Cap at 1.0
    else:
        chi_estimate = 0.0
    
    # Compute uncertainty (simplified)
    chi_uncertainty = chi_estimate * 0.15  # 15% relative uncertainty
    
    # Check if detection is positive
    within_period = abs(peak_period - PERIOD_HOURS) < 0.5  # Within 0.5 hours of expected
    within_chi = abs(chi_estimate - CHI_EXPECTED) <= CHI_TOLERANCE * 2
    
    detected = within_period and within_chi and chi_estimate > 0.01
    
    return {
        'detected': detected,
        'peak_period_hours': peak_period,
        'chi_estimate': chi_estimate,
        'chi_uncertainty': chi_uncertainty,
        'freqs': freqs,
        'power': power,
        'periods_hours': periods_hours
    }


def plot_results(df, time_col, value_col, results, output_path):
    """
    Generate analysis plot.
    
    Parameters:
        df: DataFrame with data
        time_col: Timestamp column name
        value_col: Value column name
        results: Spectral analysis results
        output_path: Path to save plot
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("Note: matplotlib not installed. Skipping plot generation.")
        print("Install with: pip install matplotlib")
        return False
    
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    
    # Top panel: Time series with 2.4-hour markers
    ax1 = axes[0]
    ax1.plot(df[time_col], df[value_col], 'b-', linewidth=0.8, alpha=0.7, label='Data')
    ax1.set_xlabel('Time')
    ax1.set_ylabel(value_col)
    ax1.set_title('Time Series with 2.4-Hour Lattice Markers')
    
    # Add 2.4-hour vertical markers
    t_min = df[time_col].min()
    t_max = df[time_col].max()
    marker_time = t_min
    while marker_time <= t_max:
        ax1.axvline(marker_time, color='gold', linestyle='--', alpha=0.6, linewidth=1)
        marker_time += timedelta(hours=PERIOD_HOURS)
    
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Bottom panel: Power spectrum
    ax2 = axes[1]
    if 'periods_hours' in results and 'power' in results:
        periods = results['periods_hours']
        power = results['power']
        
        # Plot only relevant period range
        mask = (periods > 0.5) & (periods < 12) & np.isfinite(periods)
        ax2.semilogy(periods[mask], power[mask], 'b-', linewidth=1)
        ax2.axvline(PERIOD_HOURS, color='red', linestyle='-', linewidth=2, 
                    label=f'Expected: {PERIOD_HOURS}h')
        
        if results['detected']:
            ax2.axvline(results['peak_period_hours'], color='green', linestyle='--', 
                        linewidth=2, label=f"Detected: {results['peak_period_hours']:.2f}h")
        
        ax2.set_xlabel('Period (hours)')
        ax2.set_ylabel('Power')
        ax2.set_title('Power Spectrum — LUFT Heartbeat Search')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.set_xlim(0.5, 12)
    
    # Add detection result annotation
    if results['detected']:
        result_text = f"DETECTION POSITIVE\nχ = {results['chi_estimate']:.3f} ± {results['chi_uncertainty']:.3f}"
        color = 'green'
    else:
        result_text = "NO DETECTION"
        color = 'red'
    
    fig.text(0.98, 0.98, result_text, transform=fig.transFigure, 
             fontsize=12, verticalalignment='top', horizontalalignment='right',
             bbox=dict(boxstyle='round', facecolor=color, alpha=0.2))
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return True


def print_banner():
    """Print the LUFT banner."""
    print()
    print("=" * 60)
    print("   LUFT HEARTBEAT DETECTOR")
    print("   Test any dataset for the 2.4-hour cosmic modulation")
    print("   χ = 0.055 | Ω = 2π·10⁻⁴ Hz | Period = 2.4 hours")
    print("=" * 60)
    print("   Discovered by Carl Dean Cline Sr., Lincoln, Nebraska")
    print("   Contact: CARLDCLINE@GMAIL.COM")
    print("=" * 60)
    print()


def main():
    parser = argparse.ArgumentParser(
        description="LUFT Heartbeat Detector — Test any dataset for the 2.4-hour cosmic modulation (χ = 0.055)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python heartbeat_detector.py --demo
  python heartbeat_detector.py --input solar_wind.csv --time-col timestamp --value-col density
  python heartbeat_detector.py --input telescope_data.csv --time-col time --value-col flux --output my_analysis.png

Contact: CARLDCLINE@GMAIL.COM
Repository: https://github.com/CarlDeanClineSr/luft-portal-
        """
    )
    
    parser.add_argument('--demo', action='store_true',
                        help='Run with synthetic demonstration data')
    parser.add_argument('--input', '-i', type=str,
                        help='Path to input CSV file')
    parser.add_argument('--time-col', '-t', type=str, default='timestamp',
                        help='Name of timestamp column (default: timestamp)')
    parser.add_argument('--value-col', '-v', type=str, default='value',
                        help='Name of value column to analyze (default: value)')
    parser.add_argument('--output', '-o', type=str, default='heartbeat_analysis.png',
                        help='Output path for analysis plot (default: heartbeat_analysis.png)')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Suppress detailed output')
    
    args = parser.parse_args()
    
    if not args.quiet:
        print_banner()
    
    # Load or generate data
    if args.demo:
        print("Generating synthetic demonstration data (48 hours, 2-min sampling)...")
        df = generate_demo_data(hours=48, sample_minutes=2)
        time_col = 'timestamp'
        value_col = 'value'
        print("Demo data generated with embedded χ = 0.055 modulation.\n")
    elif args.input:
        print(f"Loading data from: {args.input}")
        df, time_col, value_col = load_data(args.input, args.time_col, args.value_col)
        print(f"Data loaded successfully.\n")
    else:
        parser.print_help()
        print("\nError: Please provide --input <file.csv> or use --demo for demonstration.")
        sys.exit(1)
    
    # Data summary
    n_points = len(df)
    t_start = df[time_col].min()
    t_end = df[time_col].max()
    span_hours = (t_end - t_start).total_seconds() / 3600
    dt_seconds = compute_sampling_interval(df[time_col])
    
    print("Data Summary:")
    print(f"  Data points: {n_points}")
    print(f"  Time span: {span_hours:.1f} hours")
    print(f"  Sampling interval: {dt_seconds/60:.1f} minutes")
    print()
    
    # Check if we have enough data
    if span_hours < 4.8:  # Need at least 2 full periods
        print("WARNING: Data span is less than 2 full periods (4.8 hours).")
        print("         Results may be unreliable. Recommend at least 24 hours of data.")
        print()
    
    # Perform spectral analysis
    print("Performing spectral analysis...")
    values = df[value_col].values.astype(float)
    results = spectral_analysis(values, dt_seconds)
    
    # Report results
    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    
    if 'reason' in results:
        print(f"Analysis could not be completed: {results['reason']}")
    else:
        print(f"Peak period detected: {results['peak_period_hours']:.2f} hours")
        print(f"Expected period: {PERIOD_HOURS} hours")
        print()
        print(f"Estimated χ amplitude: {results['chi_estimate']:.3f} ± {results['chi_uncertainty']:.3f}")
        print(f"Expected χ: {CHI_EXPECTED} ± {CHI_TOLERANCE}")
        print()
        
        if results['detected']:
            print("╔══════════════════════════════════════════════════════════╗")
            print("║            DETECTION POSITIVE                            ║")
            print("║  The 2.4-hour LUFT modulation is present in your data!   ║")
            print("╚══════════════════════════════════════════════════════════╝")
            print()
            print("Your data shows the cosmic heartbeat signature.")
            print("The lattice breathes through your measurements.")
        else:
            print("╔══════════════════════════════════════════════════════════╗")
            print("║            NO CLEAR DETECTION                            ║")
            print("╚══════════════════════════════════════════════════════════╝")
            print()
            print("The 2.4-hour modulation was not clearly detected.")
            print("Possible reasons:")
            print("  - Insufficient data duration (need at least 24 hours)")
            print("  - Sampling rate too coarse (need at least 15-minute intervals)")
            print("  - Signal buried in noise (try filtering or averaging)")
            print("  - This dataset may not contain the modulation")
    
    print()
    
    # Generate plot
    if plot_results(df, time_col, value_col, results, args.output):
        print(f"Analysis plot saved to: {args.output}")
    
    print()
    print("=" * 60)
    print("Thank you for testing the LUFT Heartbeat Detector!")
    print("Report your findings: https://github.com/CarlDeanClineSr/luft-portal-")
    print("Contact: CARLDCLINE@GMAIL.COM")
    print("=" * 60)
    print()
    
    # Return exit code based on detection
    return 0 if results.get('detected', False) else 1


if __name__ == "__main__":
    sys.exit(main())
