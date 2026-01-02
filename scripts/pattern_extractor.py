#!/usr/bin/env python3
"""
Pattern Extractor - Find Hidden Numerical Patterns
Searches χ data for ratios matching fundamental constants
Author: LUFT Portal Engine
Date: 2026-01-02
"""

import pandas as pd
import numpy as np
import json
import argparse
import random
from scipy.stats import zscore
from collections import Counter

# Fundamental constants to check against
FUNDAMENTAL_CONSTANTS = {
    'fine_structure': 1/137.035999,
    'pi': np.pi,
    'e': np.e,
    'phi': (1 + np.sqrt(5))/2,  # Golden ratio
    'chi_boundary': 0.15,
    'sqrt_2': np.sqrt(2),
    'sqrt_3': np.sqrt(3),
    'planck_reduced': 1.054571817e-34,  # Normalized
    'electron_mass_ratio': 0.51099906,  # MeV/c^2 normalized
}

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

def find_ratios(chi_values):
    """Calculate all pairwise ratios"""
    ratios = []
    for i in range(len(chi_values)-1):
        if chi_values[i] > 0:
            ratio = chi_values[i+1] / chi_values[i]
            ratios.append(ratio)
    return np.array(ratios)

def match_constants(ratios, tolerance=0.01):
    """Check if ratios match fundamental constants"""
    matches = {}
    
    for name, const in FUNDAMENTAL_CONSTANTS.items():
        matching_ratios = ratios[np.abs(ratios - const) < tolerance]
        if len(matching_ratios) > 0:
            matches[name] = {
                'constant': const,
                'count': len(matching_ratios),
                'mean_ratio': np.mean(matching_ratios),
                'std': np.std(matching_ratios)
            }
    
    return matches

def find_repeating_intervals(times, chi_values, threshold=0.14):
    """Find repeating time intervals at boundary"""
    # Find times when χ crosses threshold
    crossings = times[chi_values > threshold]
    
    if len(crossings) < 2:
        return []
    
    # Remove timezone if present to avoid conversion issues
    if hasattr(crossings, 'dt') and crossings.dt.tz is not None:
        crossings = crossings.dt.tz_localize(None)
    
    # Calculate intervals between crossings (in seconds)
    intervals = np.diff((crossings.values.astype('datetime64[s]')).astype(int))
    
    interval_counts = Counter(intervals)
    
    return interval_counts.most_common(10)

def main():
    parser = argparse.ArgumentParser(description='Extract numerical patterns from χ data')
    parser.add_argument('--input', required=True, help='Input chi_boundary_tracking.jsonl')
    parser.add_argument('--output', required=True, help='Output JSON file')
    args = parser.parse_args()
    
    print("Loading χ data...")
    df = load_chi_data(args.input)
    
    print(f"Loaded {len(df)} observations")
    
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
    
    times = pd.to_datetime(df['timestamp'])
    
    # Find ratios
    print("Calculating ratios...")
    ratios = find_ratios(chi_values)
    
    # Match constants
    print("Matching against fundamental constants...")
    matches = match_constants(ratios)
    
    # Find temporal patterns
    print("Finding repeating intervals...")
    intervals = find_repeating_intervals(times, chi_values)
    
    # Compile results
    results = {
        'total_observations': len(df),
        'total_ratios': len(ratios),
        'constant_matches': matches,
        'repeating_intervals': [
            {'interval_seconds': int(interval), 'count': count}
            for interval, count in intervals
        ],
        'statistics': {
            'chi_mean': float(np.mean(chi_values)),
            'chi_std': float(np.std(chi_values)),
            'chi_max': float(np.max(chi_values)),
            'chi_min': float(np.min(chi_values))
        }
    }
    
    # Save results
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"✅ Results saved to {args.output}")
    
    # Print summary
    print("\n" + "="*50)
    print("PATTERN EXTRACTION SUMMARY")
    print("="*50)
    print(f"Total ratios analyzed: {len(ratios)}")
    print(f"Constant matches found: {len(matches)}")
    if matches:
        print("\nMatches:")
        for name, data in matches.items():
            print(f"  {name}: {data['count']} occurrences (mean={data['mean_ratio']:.6f})")
    
    if intervals:
        print(f"\nTop repeating intervals:")
        for interval, count in intervals[:5]:
            hours = interval / 3600
            print(f"  {hours:.2f} hours: {count} occurrences")

if __name__ == '__main__':
    main()
