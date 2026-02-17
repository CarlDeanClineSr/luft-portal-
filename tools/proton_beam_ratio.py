#!/usr/bin/env python3
"""
Proton Beam Speed Ratio Calculator
===================================

Analyzes speed enhancement during proton beam events to test the hypothesis
that beam drift speeds relative to Alfvén speed approach ~0.15.

Author: Carl Dean Cline Sr.
Created: January 3, 2026
Location: Lincoln, Nebraska, USA
Email: CARLDCLINE@GMAIL.COM

Theory:
    During proton beam events, the relative drift speed V_beam / V_Alfvén
    may saturate at χ ~ 0.15, similar to the boundary cap.
    
    Alfvén speed: V_A = B / sqrt(μ₀ * ρ)
    where:
        B = magnetic field (T)
        μ₀ = permeability (4π × 10⁻⁷ H/m)
        ρ = mass density (kg/m³)

Usage:
    python tools/proton_beam_ratio.py
    python tools/proton_beam_ratio.py --data-file data/cme_heartbeat_log_2025_12.csv
    python tools/proton_beam_ratio.py --flux-threshold 50
"""

import pandas as pd
import numpy as np
import argparse
from pathlib import Path
from datetime import datetime


# Physical constants
MU_0 = 4 * np.pi * 1e-7  # H/m
PROTON_MASS = 1.67e-27  # kg


def calculate_alfven_speed(density_cm3, bt_nt):
    """
    Calculate Alfvén speed.
    
    Args:
        density_cm3: Particle density in particles/cm³
        bt_nt: Total magnetic field in nT
    
    Returns:
        Alfvén speed in km/s
    """
    # Convert units
    density_m3 = density_cm3 * 1e6  # cm⁻³ to m⁻³
    bt_tesla = bt_nt * 1e-9  # nT to Tesla
    
    # Mass density (assuming protons)
    mass_density = density_m3 * PROTON_MASS  # kg/m³
    
    # Alfvén speed: V_A = B / sqrt(μ₀ * ρ)
    v_alfven = bt_tesla / np.sqrt(MU_0 * mass_density)
    
    # Convert m/s to km/s
    v_alfven_kms = v_alfven / 1000.0
    
    return v_alfven_kms


def identify_beam_events(df, flux_threshold=100, chi_threshold=0.14):
    """
    Identify potential proton beam events.
    
    Since we don't have direct proton flux measurements, we use proxies:
    1. High chi amplitude (> threshold) indicating dynamic conditions
    2. High speed events (> 500 km/s)
    3. Enhanced density or magnetic field
    
    Args:
        df: DataFrame with solar wind data
        flux_threshold: Not used (kept for compatibility)
        chi_threshold: Chi amplitude threshold for identifying beam-like events
    
    Returns:
        Boolean mask for beam events
    """
    # Proxy method 1: High chi amplitude events
    high_chi = df['chi_amplitude'] > chi_threshold
    
    # Proxy method 2: High speed events
    high_speed = df['speed_km_s'] > df['speed_km_s'].quantile(0.75)
    
    # Proxy method 3: Enhanced magnetic field
    high_bt = df['bt_nT'] > df['bt_nT'].quantile(0.75)
    
    # Beam events: combination of high activity indicators
    beam_events = high_chi & (high_speed | high_bt)
    
    return beam_events


def load_data(csv_path):
    """Load and clean CME heartbeat log."""
    # Read CSV with error handling for inconsistent columns
    df = pd.read_csv(csv_path, on_bad_lines='skip', engine='python')
    
    # Convert numeric columns to numeric types (handles string values)
    numeric_cols = ['density_p_cm3', 'speed_km_s', 'bt_nT', 'chi_amplitude']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Clean data - remove rows with missing critical values
    df = df.dropna(subset=['density_p_cm3', 'speed_km_s', 'bt_nT', 'chi_amplitude'])
    
    # Filter out bad data
    df = df[
        (df['density_p_cm3'] > 0) & 
        (df['density_p_cm3'] < 100) &
        (df['speed_km_s'] > 0) &
        (df['speed_km_s'] < 2000) &
        (df['bt_nT'] > 0) &
        (df['bt_nT'] < 1000)
    ]
    
    return df


def main():
    parser = argparse.ArgumentParser(
        description='Calculate speed ratios during proton beam events')
    parser.add_argument('--data-file',
                       default='data/cme_heartbeat_log_2025_12.csv',
                       help='Path to CME heartbeat log CSV file')
    parser.add_argument('--flux-threshold',
                       type=float,
                       default=100.0,
                       help='Proton flux threshold (pfu) - not used, kept for compatibility')
    parser.add_argument('--chi-threshold',
                       type=float,
                       default=0.14,
                       help='Chi amplitude threshold for identifying beam-like events')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("LUFT Proton Beam Speed Ratio Calculator")
    print("=" * 70)
    print(f"Analysis Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print()
    
    # Load data
    print(f"Loading data from {args.data_file}...")
    df = load_data(args.data_file)
    print(f"  Loaded {len(df)} data points")
    
    # Calculate Alfvén speed
    print("\nCalculating Alfvén speeds...")
    df['v_alfven_kms'] = calculate_alfven_speed(df['density_p_cm3'], df['bt_nT'])
    print(f"  Mean Alfvén speed: {df['v_alfven_kms'].mean():.1f} km/s")
    print(f"  Median Alfvén speed: {df['v_alfven_kms'].median():.1f} km/s")
    
    # Calculate speed ratios
    df['speed_ratio'] = df['speed_km_s'] / df['v_alfven_kms']
    
    print("\nNOTE: Direct proton flux measurements not available in dataset.")
    print(f"Using proxy method to identify beam-like events:")
    print(f"  - Chi amplitude > {args.chi_threshold}")
    print(f"  - High speed OR high magnetic field (> 75th percentile)")
    
    # Identify beam events using proxy
    beam_mask = identify_beam_events(df, args.flux_threshold, args.chi_threshold)
    df_beam = df[beam_mask]
    df_quiet = df[~beam_mask]
    
    print(f"\nEvent Classification:")
    print(f"  Total events: {len(df)}")
    print(f"  Beam-like events: {len(df_beam)} ({100*len(df_beam)/len(df):.1f}%)")
    print(f"  Quiet solar wind: {len(df_quiet)} ({100*len(df_quiet)/len(df):.1f}%)")
    
    # Speed statistics
    print("\n" + "=" * 70)
    print("SPEED ANALYSIS")
    print("=" * 70)
    
    if len(df_beam) > 0 and len(df_quiet) > 0:
        print("\nSolar Wind Speed (km/s):")
        print(f"  Quiet conditions:  {df_quiet['speed_km_s'].mean():.1f} ± {df_quiet['speed_km_s'].std():.1f}")
        print(f"  Beam-like events:  {df_beam['speed_km_s'].mean():.1f} ± {df_beam['speed_km_s'].std():.1f}")
        
        speed_enhancement = df_beam['speed_km_s'].mean() / df_quiet['speed_km_s'].mean()
        print(f"\n  Speed enhancement ratio: {speed_enhancement:.3f}")
        
        # Alfvén speed
        print("\nAlfvén Speed (km/s):")
        print(f"  Quiet conditions:  {df_quiet['v_alfven_kms'].mean():.1f} ± {df_quiet['v_alfven_kms'].std():.1f}")
        print(f"  Beam-like events:  {df_beam['v_alfven_kms'].mean():.1f} ± {df_beam['v_alfven_kms'].std():.1f}")
        
        # Speed ratios (proxy for beam drift)
        print("\n" + "=" * 70)
        print("SPEED RATIO ANALYSIS (V_sw / V_Alfvén)")
        print("=" * 70)
        print("\nSpeed Ratio Statistics:")
        print(f"  All conditions:    {df['speed_ratio'].mean():.3f} ± {df['speed_ratio'].std():.3f}")
        print(f"  Quiet conditions:  {df_quiet['speed_ratio'].mean():.3f} ± {df_quiet['speed_ratio'].std():.3f}")
        print(f"  Beam-like events:  {df_beam['speed_ratio'].mean():.3f} ± {df_beam['speed_ratio'].std():.3f}")
        
        print(f"\n  Median (All):      {df['speed_ratio'].median():.3f}")
        print(f"  Median (Quiet):    {df_quiet['speed_ratio'].median():.3f}")
        print(f"  Median (Beam):     {df_beam['speed_ratio'].median():.3f}")
        
        # Check for chi-like ratios
        print("\n" + "=" * 70)
        print("CHI-LIKE THRESHOLD ANALYSIS")
        print("=" * 70)
        
        # Check if speed ratios cluster near 0.15 or multiples
        chi_like_values = [0.10, 0.15, 0.20, 0.30]
        print("\nSpeed ratio distribution near χ-like values:")
        for chi_val in chi_like_values:
            tolerance = 0.02
            near_chi = df[(df['speed_ratio'] > chi_val - tolerance) & 
                         (df['speed_ratio'] < chi_val + tolerance)]
            if len(near_chi) > 0:
                pct = 100 * len(near_chi) / len(df)
                print(f"  Near {chi_val:.2f}: {len(near_chi)} events ({pct:.1f}%)")
        
        # Chi amplitude during different speed ratio ranges
        print("\nChi amplitude at different speed ratios:")
        ratio_ranges = [(0, 0.1), (0.1, 0.15), (0.15, 0.2), (0.2, 0.5), (0.5, float('inf'))]
        for ratio_min, ratio_max in ratio_ranges:
            mask = (df['speed_ratio'] >= ratio_min) & (df['speed_ratio'] < ratio_max)
            if mask.sum() > 0:
                mean_chi = df[mask]['chi_amplitude'].mean()
                count = mask.sum()
                print(f"  Ratio ∈ [{ratio_min:.2f}, {ratio_max:.2f}): χ = {mean_chi:.3f} (n={count})")
        
    else:
        print("\nInsufficient data for beam/quiet comparison.")
    
    # Additional correlations
    print("\n" + "=" * 70)
    print("CORRELATIONS")
    print("=" * 70)
    
    correlations = df[['chi_amplitude', 'speed_ratio', 'speed_km_s', 
                       'v_alfven_kms', 'density_p_cm3', 'bt_nT']].corr()
    
    print("\nKey correlations with χ amplitude:")
    print(f"  χ vs Speed Ratio:    {correlations.loc['chi_amplitude', 'speed_ratio']:.3f}")
    print(f"  χ vs Speed:          {correlations.loc['chi_amplitude', 'speed_km_s']:.3f}")
    print(f"  χ vs Alfvén Speed:   {correlations.loc['chi_amplitude', 'v_alfven_kms']:.3f}")
    print(f"  χ vs Density:        {correlations.loc['chi_amplitude', 'density_p_cm3']:.3f}")
    print(f"  χ vs B_total:        {correlations.loc['chi_amplitude', 'bt_nT']:.3f}")
    
    # Save results
    results_dir = Path('plots')
    results_dir.mkdir(exist_ok=True)
    
    results_file = results_dir / 'proton_beam_ratio_results.csv'
    df[['timestamp_utc', 'chi_amplitude', 'speed_km_s', 'v_alfven_kms', 
        'speed_ratio', 'density_p_cm3', 'bt_nT']].to_csv(results_file, index=False)
    print(f"\nResults saved to: {results_file}")
    
    # Save beam events separately
    if len(df_beam) > 0:
        beam_file = results_dir / 'beam_events.csv'
        df_beam[['timestamp_utc', 'chi_amplitude', 'speed_km_s', 'v_alfven_kms',
                 'speed_ratio', 'density_p_cm3', 'bt_nT']].to_csv(beam_file, index=False)
        print(f"Beam events saved to: {beam_file}")
    
    print("\n" + "=" * 70)
    print("Analysis complete!")
    print("=" * 70)
    
    # Summary insights
    print("\nKEY INSIGHTS:")
    if len(df_beam) > 0 and len(df_quiet) > 0:
        print(f"  1. Speed enhancement during beam-like events: {speed_enhancement:.2f}x")
        print(f"  2. Mean speed ratio (all): {df['speed_ratio'].mean():.3f}")
        if df['speed_ratio'].mean() > 0.10 and df['speed_ratio'].mean() < 0.20:
            print(f"     → Speed ratio in χ-like range (0.10-0.20)!")
        print(f"  3. Chi correlation with speed ratio: {correlations.loc['chi_amplitude', 'speed_ratio']:.3f}")
    else:
        print("  Insufficient beam events for detailed analysis.")


if __name__ == '__main__':
    main()
