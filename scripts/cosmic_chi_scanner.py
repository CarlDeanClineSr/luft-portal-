#!/usr/bin/env python3
"""
COSMIC CHI SCANNER
Target: Detect the 0.15 Vacuum Saturation Limit in Stellar Flux
Logic: If a star dims by exactly 15%, it is not dust. It is the Lattice.

Loads standard light curve data (Time, Flux/Mag).
Supports ASAS-SN and Kepler formats.

Usage:
    python scripts/cosmic_chi_scanner.py --file tabbys_star_2011.csv
"""

import pandas as pd
import numpy as np
import argparse


def load_light_curve(filepath):
    """
    Loads standard light curve data (Time, Flux/Mag).
    Supports ASAS-SN and Kepler formats.
    """
    try:
        df = pd.read_csv(filepath)
        # Normalize headers (handle different data sources)
        cols = [c.lower() for c in df.columns]
        df.columns = cols
        
        # Map to standard 'time' and 'flux'
        if 'mag' in df.columns:
            # Convert Magnitude to Flux if needed (Flux = 10^(-0.4 * Mag))
            # Or analyze Mag dip directly if normalized
            df['flux'] = 10**(-0.4 * df['mag'])
        
        return df
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None


def compute_stellar_chi(df):
    """
    Applies the Cline Transform to Stellar Data.
    """
    # 1. Establish the Baseline (Vacuum Tension of the Quiet Star)
    # We use a median filter to remove the "dips" from the baseline calculation
    df['flux_baseline'] = df['flux'].rolling(window=50, center=True).median().bfill()
    
    # 2. Calculate the Perturbation (The Dip)
    # How far did the vacuum pull the light down?
    df['delta_flux'] = np.abs(df['flux'] - df['flux_baseline'])
    
    # 3. Calculate Chi (The Universal Ratio)
    # Chi = Dip / Baseline
    df['chi'] = df['delta_flux'] / df['flux_baseline']
    
    return df


def scan_for_lattice_lock(df, tolerance=0.01):
    """
    Hunts for the 0.15 'Hard Deck'.
    """
    # Filter for significant dips (ignore noise < 0.05)
    dips = df[df['chi'] > 0.05]
    
    # Check for the 0.15 Lock
    # We look for dips that 'bottom out' at 0.14 - 0.16
    locked_dips = dips[(dips['chi'] >= (0.15 - tolerance)) & (dips['chi'] <= (0.15 + tolerance))]
    
    if not locked_dips.empty:
        print(f"--- DETECTED LATTICE LOCK ---")
        print(f"Count: {len(locked_dips)} data points locked at 0.15")
        print(f"Max Chi: {locked_dips['chi'].max():.4f}")
        print(f"Timestamps: {locked_dips['time'].values[:5]} ...")
        return True
    else:
        print("No Lattice Lock detected in this sector.")
        return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='COSMIC CHI SCANNER - Detect 0.15 Vacuum Saturation in Stellar Flux')
    parser.add_argument('--file', required=True, help='Path to light curve CSV file')
    parser.add_argument('--tolerance', type=float, default=0.01, help='Tolerance for 0.15 lock detection (default: 0.01)')
    args = parser.parse_args()
    
    # Execute
    data = load_light_curve(args.file)
    if data is not None:
        data = compute_stellar_chi(data)
        scan_for_lattice_lock(data, tolerance=args.tolerance)
