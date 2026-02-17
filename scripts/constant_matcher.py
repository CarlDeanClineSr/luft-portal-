#!/usr/bin/env python3
"""
Constant Matcher - Cross-check χ Values Against Fundamental Constants
Searches for matches between χ data and fundamental physics constants
Author: LUFT Portal Engine
Date: 2026-01-02
"""

import pandas as pd
import numpy as np
import json
import argparse
import random

def load_chi_data(filepath):
    """Load χ boundary tracking data"""
    # Try to load as JSONL first
    if filepath.endswith('.jsonl'):
        df = pd.read_json(filepath, lines=True)
    # Try to load as CSV
    elif filepath.endswith('.csv'):
        df = pd.read_csv(filepath)
    else:
        # Try JSONL by default, fall back to CSV
        try:
            df = pd.read_json(filepath, lines=True)
        except (ValueError, json.JSONDecodeError):
            df = pd.read_csv(filepath)
    return df

def load_constants(filepath):
    """Load fundamental constants from JSON"""
    with open(filepath, 'r') as f:
        constants = json.load(f)
    return constants

def find_constant_matches(chi_values, constants, tolerance=0.01):
    """Find χ values that match fundamental constants"""
    matches = []
    
    for chi in chi_values:
        for name, value in constants.items():
            if abs(chi - value) < tolerance:
                matches.append({
                    'chi_value': float(chi),
                    'constant_name': name,
                    'constant_value': float(value),
                    'difference': float(abs(chi - value))
                })
    
    return matches

def find_ratio_matches(chi_values, constants, tolerance=0.01, max_samples=1000):
    """Find ratios between χ values that match constants"""
    matches = []
    
    # Limit the number of comparisons for large datasets
    n = len(chi_values)
    if n > max_samples:
        # Sample indices randomly
        indices = random.sample(range(n), max_samples)
        chi_sample = chi_values[indices]
    else:
        chi_sample = chi_values
    
    # Calculate pairwise ratios for sample
    for i in range(len(chi_sample)):
        for j in range(i+1, min(i+100, len(chi_sample))):  # Limit inner loop
            if chi_sample[j] > 0:
                ratio = chi_sample[i] / chi_sample[j]
                
                # Check against constants
                for name, value in constants.items():
                    if abs(ratio - value) < tolerance:
                        matches.append({
                            'chi_1': float(chi_sample[i]),
                            'chi_2': float(chi_sample[j]),
                            'ratio': float(ratio),
                            'constant_name': name,
                            'constant_value': float(value),
                            'difference': float(abs(ratio - value))
                        })
    
    return matches

def main():
    parser = argparse.ArgumentParser(description='Match χ data against fundamental constants')
    parser.add_argument('--chi-data', required=True, help='Input chi_boundary_tracking.jsonl')
    parser.add_argument('--constants', required=True, help='Input fundamental_constants.json')
    parser.add_argument('--output', required=True, help='Output text file')
    args = parser.parse_args()
    
    print("Loading χ data...")
    df = load_chi_data(args.chi_data)
    
    # Extract χ values - try different column names
    if 'chi' in df.columns:
        chi_values = df['chi'].values
    elif 'chi_amplitude' in df.columns:
        chi_values = df['chi_amplitude'].values
    elif 'chi_mean' in df.columns:
        chi_values = df['chi_mean'].values
    else:
        print("Error: Could not find chi data column (tried 'chi', 'chi_amplitude', 'chi_mean')")
        print(f"Available columns: {list(df.columns)}")
        return
    
    print(f"Loaded {len(chi_values)} χ observations")
    
    print("Loading fundamental constants...")
    constants = load_constants(args.constants)
    
    print(f"Loaded {len(constants)} fundamental constants")
    
    # Find direct matches
    print("Finding direct value matches...")
    direct_matches = find_constant_matches(chi_values, constants)
    
    # Find ratio matches
    print("Finding ratio matches...")
    ratio_matches = find_ratio_matches(chi_values, constants)
    
    # Write results
    with open(args.output, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write("FUNDAMENTAL CONSTANT MATCHING RESULTS\n")
        f.write("=" * 70 + "\n\n")
        
        f.write(f"Total χ observations: {len(chi_values)}\n")
        f.write(f"Total constants checked: {len(constants)}\n\n")
        
        f.write("-" * 70 + "\n")
        f.write("DIRECT VALUE MATCHES\n")
        f.write("-" * 70 + "\n")
        
        if direct_matches:
            for match in direct_matches:
                f.write(f"\nχ = {match['chi_value']:.6f}\n")
                f.write(f"  Matches: {match['constant_name']} = {match['constant_value']:.6f}\n")
                f.write(f"  Difference: {match['difference']:.6e}\n")
        else:
            f.write("\nNo direct matches found.\n")
        
        f.write("\n" + "-" * 70 + "\n")
        f.write("RATIO MATCHES\n")
        f.write("-" * 70 + "\n")
        
        if ratio_matches:
            for match in ratio_matches:
                f.write(f"\nχ₁ = {match['chi_1']:.6f}, χ₂ = {match['chi_2']:.6f}\n")
                f.write(f"  Ratio: {match['ratio']:.6f}\n")
                f.write(f"  Matches: {match['constant_name']} = {match['constant_value']:.6f}\n")
                f.write(f"  Difference: {match['difference']:.6e}\n")
        else:
            f.write("\nNo ratio matches found.\n")
        
        f.write("\n" + "=" * 70 + "\n")
    
    print(f"✅ Results saved to {args.output}")
    
    # Print summary
    print("\n" + "="*50)
    print("CONSTANT MATCHING SUMMARY")
    print("="*50)
    print(f"Direct matches: {len(direct_matches)}")
    print(f"Ratio matches: {len(ratio_matches)}")
    
    if direct_matches:
        print("\nDirect matches found:")
        for match in direct_matches[:5]:  # Show first 5
            print(f"  χ={match['chi_value']:.6f} ≈ {match['constant_name']}={match['constant_value']:.6f}")
    
    if ratio_matches:
        print("\nRatio matches found:")
        for match in ratio_matches[:5]:  # Show first 5
            print(f"  χ₁/χ₂={match['ratio']:.6f} ≈ {match['constant_name']}={match['constant_value']:.6f}")

if __name__ == '__main__':
    main()
