#!/usr/bin/env python3
"""
Compute χ (normalized amplitude) from USGS earthquake data
Tests if χ caps at 0.15 in seismic domain
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json

def compute_chi_from_usgs():
    """Compute χ from USGS earthquake magnitude data"""
    
    # Find all USGS JSON files
    data_dir = Path("data/usgs_quakes")
    json_files = sorted(data_dir.glob("usgs_quakes_*.json"))
    
    if not json_files: 
        print("⚠️ No USGS data found")
        return False
    
    # Load and combine all earthquake events
    all_events = []
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                if 'features' in data:
                    for feature in data['features']:
                        props = feature.get('properties', {})
                        if 'mag' in props and props['mag'] is not None: 
                            all_events.append({
                                'time': props.get('time'),
                                'magnitude': props['mag'],
                                'depth':  props.get('depth'),
                                'place': props.get('place')
                            })
        except Exception as e:
            print(f"⚠️ Error reading {json_file}: {e}")
    
    if not all_events:
        print("⚠️ No valid USGS earthquake data found")
        return False
    
    # Convert to DataFrame
    df = pd. DataFrame(all_events)
    df['magnitude'] = pd.to_numeric(df['magnitude'], errors='coerce')
    df = df.dropna(subset=['magnitude'])
    df = df.sort_values('time')
    
    if len(df) < 10:
        print(f"⚠️ Not enough USGS data points: {len(df)}")
        return False
    
    # Compute baseline (30-day rolling mean of magnitudes)
    if len(df) >= 100: 
        df['baseline'] = df['magnitude'].rolling(window=100, min_periods=10).mean()
    else:
        df['baseline'] = df['magnitude']. mean()
    
    # Compute χ = |deviation| / baseline
    df['deviation'] = df['magnitude'] - df['baseline']
    df['chi'] = np.abs(df['deviation']) / df['baseline']
    
    # Cap at 0.15
    df['chi_capped'] = df['chi'].clip(upper=0.15)
    
    # Add timestamp
    df['timestamp_utc'] = pd.to_datetime(df['time'], unit='ms').dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Save results
    output_dir = Path("results/usgs_chi")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    month_str = datetime. utcnow().strftime('%Y_%m')
    output_file = output_dir / f"usgs_chi_{month_str}.csv"
    
    # Select columns
    result = df[['timestamp_utc', 'magnitude', 'baseline', 'chi', 'chi_capped', 'depth', 'place']]
    result.to_csv(output_file, index=False)
    
    # Print stats
    chi_max = df['chi'].max()
    chi_mean = df['chi'].mean()
    cap_violations = (df['chi'] > 0.15).sum()
    
    print(f"✅ USGS χ calculated: {len(df)} earthquake events")
    print(f"   χ max: {chi_max:.4f}")
    print(f"   χ mean:  {chi_mean:.4f}")
    print(f"   Cap violations (χ > 0.15): {cap_violations}")
    print(f"   Saved: {output_file}")
    
    if chi_max <= 0.15:
        print(f"🎯 **USGS χ CAP CONFIRMED AT 0.15** — Universal boundary in seismic data!")
    
    return True

if __name__ == "__main__": 
    success = compute_chi_from_usgs()
    exit(0 if success else 1)
