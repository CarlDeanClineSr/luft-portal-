#!/usr/bin/env python3
"""
Compute χ = |B - B_baseline| / B_baseline for historical geomagnetic storms.
Uses USGS archived magnetometer data.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timezone
import requests
from pathlib import Path
import sys

HISTORICAL_STORMS = {
    'quebec_1989': {
        'start': '1989-03-13T00:00:00Z',
        'end': '1989-03-14T23:59:59Z',
        'station': 'FRD',  # Fredericksburg was active during 1989
        'name': '1989 Quebec Blackout'
    },
    'apollo_1972': {
        'start': '1972-08-04T00:00:00Z',
        'end': '1972-08-05T23:59:59Z',
        'station': 'HON',  # Honolulu data available
        'name': '1972 Apollo-Era Storm'
    },
    'may_2024': {
        'start': '2024-05-10T00:00:00Z',
        'end': '2024-05-12T23:59:59Z',
        'station': 'BOU',  # Boulder, recent data
        'name': '2024 May G5 Storm'
    }
}

def fetch_storm_data(storm_config):
    """Fetch magnetometer data for a historical storm."""
    url = 'https://geomag.usgs.gov/ws/data/'
    
    # Build URL with query parameters
    url_full = (
        f"{url}"
        f"?id={storm_config['station']}"
        f"&starttime={storm_config['start']}"
        f"&endtime={storm_config['end']}"
        f"&elements=F"  # Total field
        f"&sampling_period=60"
        f"&format=json"
    )
    
    try:
        print(f"   Fetching data from USGS API...")
        response = requests.get(url_full, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        # Parse USGS format
        if not data or 'times' not in data or 'values' not in data:
            return None
        
        times = data.get('times', [])
        # Extract F values
        f_values = []
        if len(data.get('values', [])) > 0:
            f_values = data['values'][0].get('values', [])
        
        if not times or not f_values:
            return None
        
        # Create DataFrame
        df = pd.DataFrame({
            'time': times,
            'F': f_values
        })
        
        return df
        
    except Exception as e:
        print(f"   Error: {str(e)}")
        return None

def compute_chi(df):
    """Compute χ = |B - B_baseline| / B_baseline."""
    if df is None or len(df) < 100:
        return None
    
    df['B'] = pd.to_numeric(df['F'], errors='coerce')
    df = df.dropna(subset=['B'])
    
    if len(df) < 100:
        return None
    
    # Compute 24-hour rolling mean baseline (or use full mean if insufficient data)
    if len(df) >= 1440:  # 24 hours at 1-minute resolution
        baseline = df['B'].rolling(window=1440, center=True, min_periods=100).mean()
    else:
        baseline = df['B'].mean()
    
    df['baseline'] = baseline
    df['chi'] = np.abs(df['B'] - df['baseline']) / df['baseline']
    
    return df

def analyze_all_storms():
    """Analyze χ for all historical storms."""
    results = []
    
    print(f"Analyzing {len(HISTORICAL_STORMS)} historical geomagnetic storms...")
    print()
    
    for storm_id, config in HISTORICAL_STORMS.items():
        print(f"Analyzing: {config['name']}")
        print(f"  Station: {config['station']}")
        print(f"  Period: {config['start']} to {config['end']}")
        
        df = fetch_storm_data(config)
        if df is None:
            print(f"  ⚠️ No data available")
            print()
            continue
        
        print(f"  Retrieved {len(df)} data points")
        
        df = compute_chi(df)
        if df is None:
            print(f"  ⚠️ Insufficient data for χ calculation")
            print()
            continue
        
        max_chi = df['chi'].max()
        mean_chi = df['chi'].mean()
        violations = len(df[df['chi'] > 0.15])
        
        print(f"  Max χ: {max_chi:.4f}")
        print(f"  Mean χ: {mean_chi:.4f}")
        print(f"  Violations (χ > 0.15): {violations}")
        
        results.append({
            'storm': config['name'],
            'station': config['station'],
            'max_chi': max_chi,
            'mean_chi': mean_chi,
            'violations': violations,
            'total_obs': len(df)
        })
        
        # Save data
        output_dir = Path('results/historical_storms')
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f'{storm_id}_chi.csv'
        df.to_csv(output_path, index=False)
        print(f"  ✅ Saved: {output_path}")
        print()
    
    if results:
        # Save summary
        summary = pd.DataFrame(results)
        summary_path = Path('results/historical_storms/summary.csv')
        summary.to_csv(summary_path, index=False)
        
        print(f"✅ Historical storm analysis complete")
        print()
        print(summary.to_string(index=False))
        return True
    else:
        print(f"⚠️ No storm data could be analyzed")
        return False

if __name__ == '__main__':
    success = analyze_all_storms()
    sys.exit(0 if success else 1)
