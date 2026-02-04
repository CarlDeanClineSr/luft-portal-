#!/usr/bin/env python3
"""
Imperial Physics Observatory: Nuclear Test Chi Correlation
Correlates nuclear test dates with chi spike events (1945-1992)
"""

import pandas as pd
import argparse
from datetime import timedelta
from pathlib import Path

def load_test_data(test_db_path):
    """Load nuclear test database"""
    df = pd.read_csv(test_db_path)
    df['date'] = pd.to_datetime(df['date'])
    return df

def load_chi_data(chi_db_path):
    """Load historical chi measurements"""
    df = pd.read_csv(chi_db_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

def correlate_tests_with_chi(tests_df, chi_df, max_delay_days=30, chi_threshold=0.15):
    """
    For each nuclear test, find chi spikes within max_delay_days
    
    Args:
        tests_df: DataFrame with nuclear test data (date, test_name, yield_kt, location)
        chi_df: DataFrame with chi measurements (timestamp, chi, source)
        max_delay_days: Maximum days after test to search for correlation
        chi_threshold: Minimum chi value to consider anomalous
        
    Returns:
        DataFrame with correlation results
    """
    results = []
    
    for _, test in tests_df.iterrows():
        window_start = test['date']
        window_end = test['date'] + timedelta(days=max_delay_days)
        
        # Find chi spikes in window
        spikes = chi_df[
            (chi_df['timestamp'] >= window_start) &
            (chi_df['timestamp'] <= window_end) &
            (chi_df['chi'] > chi_threshold)
        ]
        
        for _, spike in spikes.iterrows():
            delay = (spike['timestamp'] - test['date']).days
            results.append({
                'test_date': test['date'],
                'test_name': test.get('test_name', 'UNKNOWN'),
                'test_yield_kt': test.get('yield_kt', None),
                'test_location': test.get('location', 'UNKNOWN'),
                'spike_date': spike['timestamp'],
                'spike_chi': spike['chi'],
                'spike_source': spike.get('source', 'UNKNOWN'),
                'delay_days': delay,
                'correlation_strength': spike['chi'] / (delay + 1)  # Weight by immediacy
            })
    
    return pd.DataFrame(results)

def main():
    parser = argparse.ArgumentParser(description='Correlate nuclear tests with chi spikes')
    parser.add_argument('--test_db', required=True, help='Path to nuclear test database CSV')
    parser.add_argument('--chi_db', required=True, help='Path to historical chi data CSV')
    parser.add_argument('--output', required=True, help='Output correlation CSV path')
    parser.add_argument('--max_delay', type=int, default=30, help='Max delay days (default: 30)')
    parser.add_argument('--chi_threshold', type=float, default=0.15, help='Chi threshold (default: 0.15)')
    
    args = parser.parse_args()
    
    print(f"Loading nuclear test database: {args.test_db}")
    tests_df = load_test_data(args.test_db)
    print(f"  Loaded {len(tests_df)} nuclear tests")
    
    print(f"Loading chi historical data: {args.chi_db}")
    chi_df = load_chi_data(args.chi_db)
    print(f"  Loaded {len(chi_df)} chi measurements")
    
    print(f"Correlating tests with chi spikes (max delay: {args.max_delay} days, threshold: {args.chi_threshold})")
    results_df = correlate_tests_with_chi(tests_df, chi_df, args.max_delay, args.chi_threshold)
    print(f"  Found {len(results_df)} correlations")
    
    # Ensure output directory exists
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    
    # Save results
    results_df.to_csv(args.output, index=False)
    print(f"Results saved to: {args.output}")
    
    # Print summary statistics
    if len(results_df) > 0:
        print("\nCorrelation Summary:")
        print(f"  Average delay: {results_df['delay_days'].mean():.1f} days")
        print(f"  Median delay: {results_df['delay_days'].median():.1f} days")
        print(f"  Max chi spike: {results_df['spike_chi'].max():.4f}")
        print(f"  Tests with correlations: {results_df['test_name'].nunique()}")

if __name__ == '__main__':
    main()
