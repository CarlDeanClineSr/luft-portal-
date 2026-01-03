#!/usr/bin/env python3
"""
Energy Balance Calculator (σ_R) for LUFT Portal
================================================

Calculates energy equipartition parameter:
  σ_R = (E_kinetic - E_magnetic) / (E_kinetic + E_magnetic)

When σ_R ≈ 0 (equipartition) → Hypothesis: χ ≈ 0.15

Based on Solar Orbiter paper (arXiv:2512.20098v1)

Author: Carl Dean Cline Sr.
Date: 2026-01-03
"""

import pandas as pd
import numpy as np
import argparse
import json
from pathlib import Path
from datetime import datetime

def calculate_kinetic_energy_density(density, velocity):
    """
    Calculate kinetic energy density: E_k = 0.5 * ρ * v²
    
    Args:
        density: Plasma density in particles/cm³
        velocity: Solar wind velocity in km/s
        
    Returns:
        Kinetic energy density in appropriate units
    """
    # Convert to SI units
    m_p = 1.67e-27  # Proton mass in kg
    density_si = density * 1e6  # Convert from /cm³ to /m³
    velocity_si = velocity * 1e3  # Convert from km/s to m/s
    
    # E_k = 0.5 * m * n * v²
    return 0.5 * m_p * density_si * velocity_si**2

def calculate_magnetic_energy_density(magnetic_field):
    """
    Calculate magnetic energy density: E_m = B² / (2μ₀)
    
    Args:
        magnetic_field: Magnetic field strength in nT
        
    Returns:
        Magnetic energy density in appropriate units
    """
    mu_0 = 4 * np.pi * 1e-7  # Permeability of free space
    B_si = magnetic_field * 1e-9  # Convert from nT to T
    
    return B_si**2 / (2 * mu_0)

def calculate_sigma_r(kinetic_energy, magnetic_energy):
    """
    Calculate σ_R = (E_k - E_m) / (E_k + E_m)
    
    Args:
        kinetic_energy: Kinetic energy density
        magnetic_energy: Magnetic energy density
        
    Returns:
        σ_R value (dimensionless)
    """
    total = kinetic_energy + magnetic_energy
    if total == 0:
        return np.nan
    
    return (kinetic_energy - magnetic_energy) / total

def load_cme_heartbeat_data(filepath):
    """Load CME heartbeat log data"""
    if filepath.endswith('.csv'):
        df = pd.read_csv(filepath)
    elif filepath.endswith('.json'):
        df = pd.read_json(filepath, lines=True)
    else:
        # Try CSV first, then JSON
        try:
            df = pd.read_csv(filepath)
        except:
            df = pd.read_json(filepath, lines=True)
    
    return df

def process_data(df):
    """Calculate σ_R for all observations"""
    results = []
    
    # Expected column names (adjust as needed)
    # density: proton_density, n_p, density
    # velocity: speed, velocity, v_sw
    # magnetic field: bt, b_total, |b|
    # chi: chi, chi_amplitude
    
    # Find column names
    density_col = None
    velocity_col = None
    bt_col = None
    chi_col = None
    
    for col in df.columns:
        col_lower = col.lower()
        if 'density' in col_lower or col_lower in ['n_p', 'np']:
            density_col = col
        elif 'speed' in col_lower or 'velocity' in col_lower or col_lower in ['v_sw', 'vsw']:
            velocity_col = col
        elif 'bt' in col_lower or 'b_total' in col_lower or col_lower == '|b|':
            bt_col = col
        elif 'chi' in col_lower:
            chi_col = col
    
    if not all([density_col, velocity_col, bt_col]):
        print("Warning: Could not identify all required columns")
        print(f"Available columns: {list(df.columns)}")
        print(f"Found: density={density_col}, velocity={velocity_col}, bt={bt_col}")
        return pd.DataFrame()
    
    print(f"Using columns: density={density_col}, velocity={velocity_col}, bt={bt_col}, chi={chi_col}")
    
    for idx, row in df.iterrows():
        try:
            density = row[density_col]
            velocity = row[velocity_col]
            bt = row[bt_col]
            
            # Skip invalid data
            if pd.isna(density) or pd.isna(velocity) or pd.isna(bt):
                continue
            if density <= 0 or velocity <= 0 or bt <= 0:
                continue
            
            # Calculate energies
            E_k = calculate_kinetic_energy_density(density, velocity)
            E_m = calculate_magnetic_energy_density(bt)
            
            # Calculate σ_R
            sigma_r = calculate_sigma_r(E_k, E_m)
            
            result = {
                'timestamp': row.get('timestamp', row.get('time', idx)),
                'density': density,
                'velocity': velocity,
                'bt': bt,
                'E_kinetic': E_k,
                'E_magnetic': E_m,
                'sigma_r': sigma_r,
            }
            
            # Add chi if available
            if chi_col:
                result['chi'] = row.get(chi_col, np.nan)
            
            results.append(result)
            
        except Exception as e:
            # Skip problematic rows
            continue
    
    return pd.DataFrame(results)

def analyze_results(df):
    """Analyze relationship between σ_R and χ"""
    analysis = {
        'total_observations': len(df),
        'sigma_r_stats': {
            'mean': float(df['sigma_r'].mean()),
            'median': float(df['sigma_r'].median()),
            'std': float(df['sigma_r'].std()),
            'min': float(df['sigma_r'].min()),
            'max': float(df['sigma_r'].max()),
        }
    }
    
    # Check for equipartition (σ_R ≈ 0)
    equipartition_threshold = 0.1
    equipartition_mask = abs(df['sigma_r']) < equipartition_threshold
    analysis['equipartition_count'] = int(equipartition_mask.sum())
    analysis['equipartition_percentage'] = float(equipartition_mask.sum() / len(df) * 100)
    
    # If chi data available, analyze correlation
    if 'chi' in df.columns:
        chi_available = df['chi'].notna()
        
        # Check chi values during equipartition
        equipartition_chi = df[equipartition_mask & chi_available]['chi']
        
        if len(equipartition_chi) > 0:
            analysis['equipartition_chi_stats'] = {
                'mean': float(equipartition_chi.mean()),
                'median': float(equipartition_chi.median()),
                'std': float(equipartition_chi.std()),
                'min': float(equipartition_chi.min()),
                'max': float(equipartition_chi.max()),
            }
            
            # Check if χ ≈ 0.15 during equipartition
            chi_015_mask = (equipartition_chi >= 0.14) & (equipartition_chi <= 0.16)
            analysis['equipartition_chi_near_015_count'] = int(chi_015_mask.sum())
            analysis['equipartition_chi_near_015_percentage'] = float(
                chi_015_mask.sum() / len(equipartition_chi) * 100
            )
            
            # Correlation coefficient
            correlation = df[chi_available]['sigma_r'].corr(df[chi_available]['chi'])
            analysis['sigma_r_chi_correlation'] = float(correlation)
    
    return analysis

def main():
    parser = argparse.ArgumentParser(description='Calculate energy balance (σ_R) from solar wind data')
    parser.add_argument('--input', required=True, help='Input data file (CSV or JSON)')
    parser.add_argument('--output', required=True, help='Output CSV file')
    parser.add_argument('--analysis', help='Output analysis JSON file')
    args = parser.parse_args()
    
    print("=" * 70)
    print("LUFT Energy Balance Calculator (σ_R)")
    print("=" * 70)
    print()
    
    # Load data
    print(f"Loading data from {args.input}...")
    df = load_cme_heartbeat_data(args.input)
    print(f"  Loaded {len(df)} observations")
    
    # Process data
    print("Calculating energy densities and σ_R...")
    results_df = process_data(df)
    
    if len(results_df) == 0:
        print("❌ Error: No valid results generated")
        return
    
    print(f"  Processed {len(results_df)} valid observations")
    
    # Save results
    print(f"Saving results to {args.output}...")
    results_df.to_csv(args.output, index=False)
    print("  ✅ Saved")
    
    # Analyze
    print("\nAnalyzing results...")
    analysis = analyze_results(results_df)
    
    # Print summary
    print("\n" + "=" * 70)
    print("ANALYSIS SUMMARY")
    print("=" * 70)
    print(f"Total observations: {analysis['total_observations']}")
    print(f"\nσ_R Statistics:")
    print(f"  Mean:   {analysis['sigma_r_stats']['mean']:.4f}")
    print(f"  Median: {analysis['sigma_r_stats']['median']:.4f}")
    print(f"  Std:    {analysis['sigma_r_stats']['std']:.4f}")
    print(f"  Range:  [{analysis['sigma_r_stats']['min']:.4f}, {analysis['sigma_r_stats']['max']:.4f}]")
    
    print(f"\nEquipartition (|σ_R| < 0.1):")
    print(f"  Count: {analysis['equipartition_count']}")
    print(f"  Percentage: {analysis['equipartition_percentage']:.2f}%")
    
    if 'equipartition_chi_stats' in analysis:
        print(f"\nχ During Equipartition:")
        print(f"  Mean:   {analysis['equipartition_chi_stats']['mean']:.4f}")
        print(f"  Median: {analysis['equipartition_chi_stats']['median']:.4f}")
        print(f"  Range:  [{analysis['equipartition_chi_stats']['min']:.4f}, {analysis['equipartition_chi_stats']['max']:.4f}]")
        
        print(f"\nχ ≈ 0.15 During Equipartition:")
        print(f"  Count: {analysis['equipartition_chi_near_015_count']}")
        print(f"  Percentage: {analysis['equipartition_chi_near_015_percentage']:.2f}%")
        
        print(f"\nCorrelation:")
        print(f"  σ_R vs χ: {analysis['sigma_r_chi_correlation']:.4f}")
        
        # Hypothesis test
        if analysis['equipartition_chi_stats']['mean'] >= 0.14 and analysis['equipartition_chi_stats']['mean'] <= 0.16:
            print("\n🎯 HYPOTHESIS SUPPORTED: χ ≈ 0.15 during equipartition (σ_R ≈ 0)")
        else:
            print(f"\n⚠️  HYPOTHESIS UNCLEAR: χ mean during equipartition is {analysis['equipartition_chi_stats']['mean']:.4f}")
    
    # Save analysis
    if args.analysis:
        print(f"\nSaving analysis to {args.analysis}...")
        with open(args.analysis, 'w') as f:
            json.dump(analysis, f, indent=2)
        print("  ✅ Saved")
    
    print("\n" + "=" * 70)
    print("✅ COMPLETE")
    print("=" * 70)

if __name__ == '__main__':
    main()
