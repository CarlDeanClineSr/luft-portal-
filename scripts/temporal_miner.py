#!/usr/bin/env python3
"""
Temporal Miner - Find Repeating Time Patterns
Searches χ data for periodic temporal patterns
Author: LUFT Portal Engine
Date: 2026-01-02
"""

import pandas as pd
import numpy as np
import json
import argparse
from scipy.signal import find_peaks
from collections import Counter

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

def find_temporal_patterns(times, chi_values, threshold=0.14):
    """Find peaks and calculate inter-peak intervals"""
    # Find peaks in χ time series
    peaks, properties = find_peaks(chi_values, height=threshold)
    
    if len(peaks) < 2:
        return [], []
    
    # Get peak times
    peak_times = times[peaks]
    
    # Remove timezone if present to avoid conversion issues
    if hasattr(peak_times, 'dt') and peak_times.dt.tz is not None:
        peak_times = peak_times.dt.tz_localize(None)
    
    # Calculate intervals between peaks (in seconds)
    intervals = np.diff((peak_times.values.astype('datetime64[s]')).astype(int))
    
    # Count interval frequencies
    interval_counts = Counter(intervals)
    
    return peaks, interval_counts.most_common(20)

def analyze_periodicity(intervals):
    """Check if intervals show periodicity"""
    if len(intervals) < 3:
        return None
    
    # Calculate statistics
    interval_array = np.array([item[0] for item in intervals])
    counts = np.array([item[1] for item in intervals])
    
    # Weighted mean
    mean_interval = np.average(interval_array, weights=counts)
    
    # Check for harmonics (multiples of base frequency)
    harmonics = []
    for interval, count in intervals:
        if count > 1:
            ratio = interval / mean_interval
            if abs(ratio - round(ratio)) < 0.1:  # Within 10% of integer multiple
                harmonics.append({
                    'interval_seconds': int(interval),
                    'interval_hours': interval / 3600,
                    'count': count,
                    'harmonic': int(round(ratio))
                })
    
    return {
        'mean_interval_seconds': float(mean_interval),
        'mean_interval_hours': float(mean_interval / 3600),
        'harmonics': harmonics
    }

def main():
    parser = argparse.ArgumentParser(description='Mine temporal patterns from χ data')
    parser.add_argument('--input', required=True, help='Input chi_boundary_tracking.jsonl')
    parser.add_argument('--output', required=True, help='Output CSV file')
    args = parser.parse_args()
    
    print("Loading χ data...")
    df = load_chi_data(args.input)
    
    print(f"Loaded {len(df)} observations")
    
    # Extract χ values and times - try different column names
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
    
    # Find temporal patterns
    print("Finding temporal patterns...")
    peaks, interval_counts = find_temporal_patterns(times, chi_values)
    
    print(f"Found {len(peaks)} peaks above threshold")
    
    # Analyze periodicity
    print("Analyzing periodicity...")
    periodicity = analyze_periodicity(interval_counts)
    
    # Prepare output DataFrame
    results_data = []
    for interval, count in interval_counts:
        results_data.append({
            'interval_seconds': interval,
            'interval_hours': interval / 3600,
            'interval_days': interval / 86400,
            'count': count
        })
    
    results_df = pd.DataFrame(results_data)
    
    # Save to CSV
    results_df.to_csv(args.output, index=False)
    print(f"✅ Results saved to {args.output}")
    
    # Print summary
    print("\n" + "="*50)
    print("TEMPORAL PATTERN SUMMARY")
    print("="*50)
    print(f"Total peaks found: {len(peaks)}")
    print(f"Unique intervals: {len(interval_counts)}")
    
    if interval_counts:
        print("\nTop 10 repeating intervals:")
        for interval, count in interval_counts[:10]:
            hours = interval / 3600
            days = interval / 86400
            print(f"  {hours:.2f} hours ({days:.2f} days): {count} occurrences")
    
    if periodicity and periodicity['harmonics']:
        print(f"\nMean interval: {periodicity['mean_interval_hours']:.2f} hours")
        print("\nHarmonic patterns detected:")
        for harmonic in periodicity['harmonics']:
            print(f"  {harmonic['interval_hours']:.2f} hours (×{harmonic['harmonic']}): {harmonic['count']} occurrences")

if __name__ == '__main__':
    main()
