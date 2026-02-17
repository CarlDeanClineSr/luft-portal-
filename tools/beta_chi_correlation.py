#!/usr/bin/env python3
"""
Beta vs Chi Correlation Analyzer
=================================

Calculates plasma beta (β) and correlates it with chi (χ) amplitude to test
the hypothesis that χ ~ 0.15 corresponds to a critical β threshold.

Author: Carl Dean Cline Sr.
Created: January 3, 2026
Location: Lincoln, Nebraska, USA
Email: CARLDCLINE@GMAIL.COM

Theory:
    Plasma beta β = (n * k_B * T) / (B² / 2μ₀)
    where:
        n = particle density (particles/m³)
        k_B = Boltzmann constant (1.38e-23 J/K)
        T = temperature (K)
        B = magnetic field magnitude (T)
        μ₀ = permeability of free space (4π × 10⁻⁷ H/m)

Usage:
    python tools/beta_chi_correlation.py
    python tools/beta_chi_correlation.py --data-file data/cme_heartbeat_log_2025_12.csv
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import argparse
from datetime import datetime


# Physical constants
K_BOLTZMANN = 1.38e-23  # J/K
MU_0 = 4 * np.pi * 1e-7  # H/m (permeability of free space)
PROTON_MASS = 1.67e-27  # kg


def calculate_beta(density_cm3, temperature_k, bt_nt):
    """
    Calculate plasma beta.
    
    Args:
        density_cm3: Particle density in particles/cm³
        temperature_k: Temperature in Kelvin
        bt_nt: Total magnetic field in nT
    
    Returns:
        Plasma beta (dimensionless)
    """
    # Convert units
    density_m3 = density_cm3 * 1e6  # cm⁻³ to m⁻³
    bt_tesla = bt_nt * 1e-9  # nT to Tesla
    
    # Calculate plasma pressure
    plasma_pressure = density_m3 * K_BOLTZMANN * temperature_k
    
    # Calculate magnetic pressure
    magnetic_pressure = (bt_tesla ** 2) / (2 * MU_0)
    
    # Beta = plasma pressure / magnetic pressure
    beta = plasma_pressure / magnetic_pressure
    
    return beta


def load_heartbeat_data(csv_path):
    """Load CME heartbeat log with chi amplitude data."""
    # Read CSV with error handling for inconsistent columns
    df = pd.read_csv(csv_path, on_bad_lines='skip', engine='python')
    
    # Convert numeric columns to numeric types (handles string values)
    numeric_cols = ['density_p_cm3', 'bt_nT', 'chi_amplitude', 'speed_km_s']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Clean the data - remove rows with missing critical values
    df = df.dropna(subset=['density_p_cm3', 'bt_nT', 'chi_amplitude'])
    
    # Filter out bad data
    df = df[
        (df['density_p_cm3'] > 0) & 
        (df['density_p_cm3'] < 100) &
        (df['bt_nT'] > 0) &
        (df['bt_nT'] < 1000) &
        (df['chi_amplitude'] > 0) &
        (df['chi_amplitude'] < 1.0)
    ]
    
    return df


def load_plasma_data_with_temperature(plasma_dir='data/noaa_solarwind'):
    """
    Load NOAA plasma data files which contain temperature.
    Merge with heartbeat data if needed.
    """
    plasma_dir = Path(plasma_dir)
    
    if not plasma_dir.exists():
        return None
    
    # Find all plasma CSV files
    plasma_files = sorted(plasma_dir.glob('noaa_plasma_*.csv'))
    
    if not plasma_files:
        return None
    
    # Load and concatenate all plasma files
    dfs = []
    for f in plasma_files:
        try:
            df = pd.read_csv(f)
            if 'temperature' in df.columns:
                dfs.append(df)
        except Exception as e:
            print(f"Warning: Could not load {f}: {e}")
    
    if not dfs:
        return None
    
    plasma_df = pd.concat(dfs, ignore_index=True)
    plasma_df['time_tag'] = pd.to_datetime(plasma_df['time_tag'])
    
    return plasma_df


def merge_heartbeat_with_temperature(heartbeat_df, plasma_df):
    """
    Merge heartbeat data with plasma temperature data.
    """
    if plasma_df is None:
        return None
    
    heartbeat_df['timestamp_utc'] = pd.to_datetime(heartbeat_df['timestamp_utc'])
    
    # Remove timezone from plasma data for merge compatibility
    plasma_df['time_tag'] = pd.to_datetime(plasma_df['time_tag']).dt.tz_localize(None)
    
    # Merge on nearest timestamp (within 5 minutes)
    merged = pd.merge_asof(
        heartbeat_df.sort_values('timestamp_utc'),
        plasma_df.sort_values('time_tag'),
        left_on='timestamp_utc',
        right_on='time_tag',
        direction='nearest',
        tolerance=pd.Timedelta('5min'),
        suffixes=('', '_plasma')
    )
    
    return merged


def main():
    parser = argparse.ArgumentParser(description='Analyze beta vs chi correlation')
    parser.add_argument('--data-file', 
                       default='data/cme_heartbeat_log_2025_12.csv',
                       help='Path to CME heartbeat log CSV file')
    parser.add_argument('--output-plot',
                       default='plots/beta_chi_scatter.png',
                       help='Output plot filename')
    parser.add_argument('--temperature',
                       type=float,
                       default=100000.0,
                       help='Default temperature in K (if not available in data)')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("LUFT Beta vs Chi Correlation Analyzer")
    print("=" * 70)
    print(f"Analysis Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print()
    
    # Load heartbeat data
    print(f"Loading heartbeat data from {args.data_file}...")
    df = load_heartbeat_data(args.data_file)
    print(f"  Loaded {len(df)} data points")
    
    # Try to load temperature data
    print("\nAttempting to load temperature data from NOAA plasma files...")
    plasma_df = load_plasma_data_with_temperature()
    
    if plasma_df is not None:
        print(f"  Found {len(plasma_df)} plasma measurements with temperature")
        merged_df = merge_heartbeat_with_temperature(df, plasma_df)
        
        if merged_df is not None and 'temperature' in merged_df.columns:
            df = merged_df[merged_df['temperature'].notna()].copy()
            print(f"  Successfully merged {len(df)} points with temperature data")
        else:
            print("  Merge failed, using default temperature")
            df['temperature'] = args.temperature
    else:
        print(f"  No temperature data found, using default: {args.temperature} K")
        df['temperature'] = args.temperature
    
    # Calculate beta
    print("\nCalculating plasma beta...")
    df['beta'] = calculate_beta(df['density_p_cm3'], df['temperature'], df['bt_nT'])
    
    # Count invalid values before filtering
    invalid_count = (~np.isfinite(df['beta'])).sum()
    total_before = len(df)
    
    # Remove any inf or nan values
    df = df[np.isfinite(df['beta'])]
    print(f"  Valid beta calculations: {len(df)}")
    if invalid_count > 0:
        print(f"  Filtered out {invalid_count} invalid/infinite beta values ({100*invalid_count/total_before:.1f}%)")
    
    # Calculate correlation
    print("\nCorrelation Analysis:")
    correlation = df[['chi_amplitude', 'beta']].corr().iloc[0, 1]
    print(f"  χ vs β Pearson correlation: {correlation:.3f}")
    
    # Statistics
    print("\nBeta Statistics:")
    print(f"  Mean β: {df['beta'].mean():.3f}")
    print(f"  Median β: {df['beta'].median():.3f}")
    print(f"  Std β: {df['beta'].std():.3f}")
    print(f"  Min β: {df['beta'].min():.3f}")
    print(f"  Max β: {df['beta'].max():.3f}")
    
    print("\nChi Statistics:")
    print(f"  Mean χ: {df['chi_amplitude'].mean():.3f}")
    print(f"  Median χ: {df['chi_amplitude'].median():.3f}")
    print(f"  Std χ: {df['chi_amplitude'].std():.3f}")
    
    # Check for chi ~ 0.15 at specific beta ranges
    print("\nChi amplitude at different beta ranges:")
    beta_ranges = [(0, 0.1), (0.1, 0.2), (0.2, 0.5), (0.5, 1.0), (1.0, 10.0), (10.0, float('inf'))]
    for beta_min, beta_max in beta_ranges:
        mask = (df['beta'] >= beta_min) & (df['beta'] < beta_max)
        if mask.sum() > 0:
            mean_chi = df[mask]['chi_amplitude'].mean()
            count = mask.sum()
            print(f"  β ∈ [{beta_min:.1f}, {beta_max:.1f}): χ = {mean_chi:.3f} (n={count})")
    
    # Create scatter plot
    print(f"\nGenerating scatter plot...")
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Create scatter with color based on chi value
    scatter = ax.scatter(df['beta'], df['chi_amplitude'], 
                        c=df['chi_amplitude'], cmap='viridis',
                        alpha=0.5, s=20, edgecolors='none')
    
    # Add chi = 0.15 reference line
    ax.axhline(y=0.15, color='red', linestyle='--', linewidth=2, 
              label='χ = 0.15 (Critical Boundary)', alpha=0.8)
    
    # Add potential critical beta line if pattern emerges
    # Check if chi clusters near 0.15
    chi_near_015 = df[(df['chi_amplitude'] > 0.14) & (df['chi_amplitude'] < 0.16)]
    if len(chi_near_015) > 10:
        critical_beta = chi_near_015['beta'].median()
        ax.axvline(x=critical_beta, color='orange', linestyle='--', linewidth=2,
                  label=f'β (χ≈0.15) = {critical_beta:.2f}', alpha=0.8)
    
    ax.set_xscale('log')
    ax.set_xlabel('Plasma β (log scale)', fontsize=12)
    ax.set_ylabel('χ Amplitude', fontsize=12)
    ax.set_title(f'Plasma β vs χ Amplitude\nCorrelation: {correlation:.3f}', 
                fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle=':')
    ax.legend(fontsize=10, loc='best')
    
    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax, label='χ Amplitude')
    
    # Add text box with statistics
    stats_text = f'n = {len(df)}\nMean β: {df["beta"].mean():.2f}\nMedian β: {df["beta"].median():.2f}'
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
           verticalalignment='top', bbox=dict(boxstyle='round', 
           facecolor='wheat', alpha=0.8), fontsize=9)
    
    plt.tight_layout()
    
    # Save plot
    output_path = Path(args.output_plot)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"  Plot saved to: {output_path}")
    
    # Save results to CSV
    results_file = output_path.parent / 'beta_chi_results.csv'
    df[['timestamp_utc', 'chi_amplitude', 'beta', 'density_p_cm3', 
        'temperature', 'bt_nT', 'speed_km_s']].to_csv(results_file, index=False)
    print(f"  Results saved to: {results_file}")
    
    print("\n" + "=" * 70)
    print("Analysis complete!")
    print("=" * 70)


if __name__ == '__main__':
    main()
