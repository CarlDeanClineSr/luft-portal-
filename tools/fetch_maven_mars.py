#!/usr/bin/env python3
"""
Fetch MAVEN Mars Plasma Data via CDAWeb API

This script retrieves MAVEN MAG (magnetometer) data from NASA's CDAWeb service,
calculates the chi (χ) parameter for magnetic field stability analysis,
and saves results for the LUFT portal system.

Data Source: CDAWeb - https://cdaweb.gsfc.nasa.gov/
Dataset: MVN_MAG_L2-SUNSTATE-1SEC (MAVEN Magnetometer Sun-State 1 Second)
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
import numpy as np
import pandas as pd

# Output directory
OUTPUT_DIR = Path("data/maven_mars")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def validate_csv_file(filepath):
    """Check if a local CSV is valid (not an HTML error page)."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            first_chunk = f.read(500).lower()
            if any(tag in first_chunk for tag in ['<html', '<!doctype', '<head', '<body', 'page not found']):
                print(f"ERROR: {filepath} contains HTML, not CSV data")
                return False
            if any(msg in first_chunk for msg in ['404', 'error 404', 'not found']):
                print(f"ERROR: {filepath} contains error text")
                return False
        return True
    except Exception as e:
        print(f"ERROR: Cannot validate {filepath}: {e}")
        return False

def calculate_chi(B_mag, baseline_percentile=10):
    """
    Calculate χ (chi) parameter: relative deviation from baseline magnetic field.
    
    χ = |B - B_baseline| / B_baseline
    
    Args:
        B_mag: Array of magnetic field magnitudes
        baseline_percentile: Percentile to use for baseline (default: 10th percentile)
    
    Returns:
        Array of χ values
    """
    # Calculate baseline as low percentile of field strength (quiet conditions)
    B_baseline = np.nanpercentile(B_mag, baseline_percentile)
    
    # Avoid division by zero
    if B_baseline == 0:
        B_baseline = np.nanmean(B_mag) if not np.all(np.isnan(B_mag)) else 1.0
    
    # Calculate chi
    chi = np.abs(B_mag - B_baseline) / B_baseline
    
    return chi, B_baseline

def fetch_maven_cdaweb(start_date, end_date):
    """
    Fetch MAVEN data from CDAWeb using the cdasws library.
    
    Args:
        start_date: Start datetime
        end_date: End datetime
    
    Returns:
        DataFrame with columns: time, Bx, By, Bz, B_mag, chi
    """
    try:
        from cdasws import CdasWs
    except ImportError:
        print("ERROR: cdasws library not installed")
        print("Install with: pip install cdasws cdflib xarray")
        return None
    
    print(f"Connecting to CDAWeb...")
    cdas = CdasWs()
    
    # MAVEN MAG dataset
    dataset = 'MVN_MAG_L2-SUNSTATE-1SEC'
    variables = ['OB_B']  # OB_B contains [Bx, By, Bz] in MSO coordinates
    
    # Format dates for CDAWeb API
    start_str = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    end_str = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    print(f"Requesting MAVEN data from {start_str} to {end_str}")
    print(f"Dataset: {dataset}")
    
    try:
        # Get data from CDAWeb
        # Returns tuple: (status_dict, xarray_dataset)
        result = cdas.get_data(dataset, variables, start_str, end_str)
        
        if not result or len(result) < 2:
            print("WARNING: Invalid response from CDAWeb")
            return None
        
        # Extract xarray dataset (second element of tuple)
        xr_dataset = result[1]
        
        # Check if we have data
        if xr_dataset is None or 'OB_B' not in xr_dataset:
            print("WARNING: No OB_B data in response")
            return None
        
        # Extract OB_B DataArray (shape: [time, 3] for [Bx, By, Bz])
        ob_b = xr_dataset['OB_B']
        
        # Get epoch (time) coordinate
        if 'epoch' not in ob_b.coords:
            print("WARNING: No epoch coordinate in data")
            return None
        
        epoch = ob_b.coords['epoch']
        
        # Convert to numpy arrays
        ob_b_values = ob_b.values  # Shape: (n_times, 3)
        epoch_values = epoch.values  # Shape: (n_times,)
        
        if len(ob_b_values) == 0:
            print("WARNING: No data points in response")
            return None
        
        # Create DataFrame
        records = []
        for i in range(len(epoch_values)):
            bx, by, bz = ob_b_values[i]
            b_mag = np.sqrt(bx**2 + by**2 + bz**2)
            
            records.append({
                'time': pd.Timestamp(epoch_values[i]),
                'Bx': float(bx),
                'By': float(by),
                'Bz': float(bz),
                'B_mag': float(b_mag)
            })
        
        df = pd.DataFrame(records)
        
        # Calculate chi
        chi_values, baseline = calculate_chi(df['B_mag'].values)
        df['chi'] = chi_values
        df['B_baseline'] = baseline
        
        print(f"✓ Retrieved {len(df)} MAVEN records")
        print(f"  Time range: {df['time'].min()} to {df['time'].max()}")
        print(f"  B_mag range: {df['B_mag'].min():.2f} - {df['B_mag'].max():.2f} nT")
        print(f"  B_baseline: {baseline:.2f} nT")
        print(f"  χ range: {df['chi'].min():.4f} - {df['chi'].max():.4f}")
        print(f"  Records with χ ≤ 0.15: {(df['chi'] <= 0.15).sum()} ({(df['chi'] <= 0.15).sum()/len(df)*100:.1f}%)")
        
        return df
        
    except Exception as e:
        print(f"ERROR fetching data from CDAWeb: {e}")
        import traceback
        traceback.print_exc()
        return None

def save_results(df, date_str):
    """Save MAVEN results to CSV and summary JSON"""
    if df is None or len(df) == 0:
        print("No data to save")
        return False
    
    # Save CSV
    csv_file = OUTPUT_DIR / f"maven_mag_{date_str}.csv"
    df.to_csv(csv_file, index=False)
    print(f"✓ Saved CSV: {csv_file}")
    
    # Create summary JSON
    summary = {
        'date': date_str,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'dataset': 'MVN_MAG_L2-SUNSTATE-1SEC',
        'records': len(df),
        'time_range': {
            'start': str(df['time'].min()),
            'end': str(df['time'].max())
        },
        'B_field': {
            'min': float(df['B_mag'].min()),
            'max': float(df['B_mag'].max()),
            'mean': float(df['B_mag'].mean()),
            'baseline': float(df['B_baseline'].iloc[0])
        },
        'chi': {
            'min': float(df['chi'].min()),
            'max': float(df['chi'].max()),
            'mean': float(df['chi'].mean()),
            'median': float(df['chi'].median()),
            'records_below_015': int((df['chi'] <= 0.15).sum()),
            'percent_below_015': float((df['chi'] <= 0.15).sum() / len(df) * 100)
        }
    }
    
    # Save summary JSON
    json_file = OUTPUT_DIR / f"maven_summary_{date_str}.json"
    with open(json_file, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"✓ Saved summary: {json_file}")
    
    return True

def main():
    """Main execution function"""
    print("=" * 70)
    print("MAVEN Mars Plasma Data Ingestion")
    print("=" * 70)
    
    # Fetch yesterday's data (full day)
    end = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    start = end - timedelta(days=1)
    date_str = start.strftime('%Y%m%d')
    
    print(f"Target date: {date_str}")
    print()
    
    # Fetch data from CDAWeb
    df = fetch_maven_cdaweb(start, end)
    
    if df is None:
        print()
        print("⚠ WARNING: Could not fetch MAVEN data from CDAWeb")
        print("Possible reasons:")
        print("  - Dataset may not be available for this date")
        print("  - CDAWeb service may be temporarily unavailable")
        print("  - Network connectivity issues")
        print()
        print("This is expected behavior - exiting gracefully")
        sys.exit(0)
    
    # Save results
    success = save_results(df, date_str)
    
    if success:
        print()
        print("=" * 70)
        print("✓ MAVEN data ingestion completed successfully")
        print("=" * 70)
        sys.exit(0)
    else:
        print()
        print("⚠ WARNING: Could not save results")
        sys.exit(0)

if __name__ == "__main__":
    main()
