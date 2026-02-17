#!/usr/bin/env python3
"""
Cross-Domain Periodicity Detector for LUFT Portal
==================================================

Searches for 0.9-hour (54-minute) periodicity across multiple data sources:
- Solar wind (DSCOVR, OMNI2)
- Particle physics (CERN)
- Gravitational waves (LIGO)
- Radio astronomy (FAST pulsars)

Hypothesis: 0.9 hours is a universal timescale across physics domains

Based on NASA/NOAA paper (arXiv:2512.14462v1) showing 0.9h CME wave packets

Author: Carl Dean Cline Sr.
Date: 2026-01-03
"""

import pandas as pd
import numpy as np
import argparse
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from scipy import signal
from scipy.fft import fft, fftfreq

def load_time_series_data(filepath):
    """Load time series data from various formats"""
    filepath = Path(filepath)
    
    if filepath.suffix == '.csv':
        df = pd.read_csv(filepath)
    elif filepath.suffix == '.json':
        df = pd.read_json(filepath, lines=True)
    else:
        try:
            df = pd.read_csv(filepath)
        except:
            df = pd.read_json(filepath, lines=True)
    
    return df

def detect_periodicity_fft(times, values, target_period_hours=0.9, tolerance=0.2):
    """
    Use FFT to detect periodic signals
    
    Args:
        times: Array of timestamps (datetime)
        values: Array of values
        target_period_hours: Target period to search for (default 0.9h)
        tolerance: Tolerance for period matching (default ±0.2h)
        
    Returns:
        Dictionary with period detection results
    """
    # Convert times to hours from start
    times_dt = pd.to_datetime(times)
    times_sorted = times_dt.sort_values()
    time_hours = (times_dt - times_sorted.iloc[0]).dt.total_seconds() / 3600
    
    # Sort values accordingly
    sort_idx = times_dt.argsort()
    values_sorted = values[sort_idx]
    
    # Remove NaN values
    valid_mask = ~np.isnan(values_sorted)
    time_hours = time_hours[valid_mask].values
    values_sorted = values_sorted[valid_mask]
    
    if len(values_sorted) < 10:
        return None
    
    # Interpolate to uniform sampling if needed
    # Calculate median time step
    time_diffs = np.diff(time_hours)
    median_dt = np.median(time_diffs)
    
    # Create uniform time grid
    time_uniform = np.arange(time_hours[0], time_hours[-1], median_dt)
    values_uniform = np.interp(time_uniform, time_hours, values_sorted)
    
    # Detrend
    values_detrended = signal.detrend(values_uniform)
    
    # Apply FFT
    n = len(values_detrended)
    fft_vals = fft(values_detrended)
    freqs = fftfreq(n, d=median_dt)
    
    # Only look at positive frequencies
    pos_mask = freqs > 0
    freqs_pos = freqs[pos_mask]
    power = np.abs(fft_vals[pos_mask])**2
    
    # Convert frequency to period (hours)
    periods = 1.0 / freqs_pos
    
    # Find peaks in power spectrum
    peak_indices, _ = signal.find_peaks(power, height=np.percentile(power, 90))
    
    if len(peak_indices) == 0:
        return None
    
    # Check if any peaks match target period
    detected_periods = []
    for idx in peak_indices:
        period = periods[idx]
        power_val = power[idx]
        
        # Check if within tolerance of target
        if abs(period - target_period_hours) < tolerance:
            detected_periods.append({
                'period_hours': float(period),
                'power': float(power_val),
                'frequency_hz': float(freqs_pos[idx]),
            })
    
    if detected_periods:
        # Sort by power
        detected_periods.sort(key=lambda x: x['power'], reverse=True)
        return {
            'detected': True,
            'periods': detected_periods,
            'top_period': detected_periods[0]['period_hours'],
            'top_power': detected_periods[0]['power'],
        }
    else:
        return None

def detect_periodicity_autocorr(times, values, target_period_hours=0.9, tolerance=0.2):
    """
    Use autocorrelation to detect periodic signals
    
    Args:
        times: Array of timestamps
        values: Array of values
        target_period_hours: Target period (default 0.9h)
        tolerance: Tolerance for matching (±0.2h)
        
    Returns:
        Dictionary with results
    """
    # Convert and sort
    times_dt = pd.to_datetime(times)
    sort_idx = times_dt.argsort()
    times_sorted = times_dt[sort_idx]
    values_sorted = values[sort_idx]
    
    # Remove NaN
    valid_mask = ~np.isnan(values_sorted)
    times_sorted = times_sorted[valid_mask]
    values_sorted = values_sorted[valid_mask]
    
    if len(values_sorted) < 10:
        return None
    
    # Calculate time differences
    time_hours = (times_sorted - times_sorted.iloc[0]).dt.total_seconds() / 3600
    
    # Interpolate to uniform grid
    median_dt = np.median(np.diff(time_hours))
    time_uniform = np.arange(time_hours.iloc[0], time_hours.iloc[-1], median_dt)
    values_uniform = np.interp(time_uniform, time_hours, values_sorted)
    
    # Detrend
    values_detrended = signal.detrend(values_uniform)
    
    # Compute autocorrelation
    autocorr = np.correlate(values_detrended, values_detrended, mode='full')
    autocorr = autocorr[len(autocorr)//2:]  # Only positive lags
    
    # Normalize
    autocorr = autocorr / autocorr[0]
    
    # Create lag times
    lags = np.arange(len(autocorr)) * median_dt
    
    # Find peaks in autocorrelation
    peak_indices, _ = signal.find_peaks(autocorr, height=0.1)
    
    if len(peak_indices) == 0:
        return None
    
    # Check for target period
    detected = []
    for idx in peak_indices:
        lag_time = lags[idx]
        corr_val = autocorr[idx]
        
        if abs(lag_time - target_period_hours) < tolerance:
            detected.append({
                'lag_hours': float(lag_time),
                'correlation': float(corr_val),
            })
    
    if detected:
        detected.sort(key=lambda x: x['correlation'], reverse=True)
        return {
            'detected': True,
            'lags': detected,
            'top_lag': detected[0]['lag_hours'],
            'top_correlation': detected[0]['correlation'],
        }
    else:
        return None

def analyze_data_source(filepath, source_name):
    """Analyze a single data source for 0.9h periodicity"""
    print(f"\n  Analyzing {source_name}...")
    
    try:
        df = load_time_series_data(filepath)
        print(f"    Loaded {len(df)} observations")
        
        # Find time and value columns
        time_col = None
        value_cols = []
        
        for col in df.columns:
            col_lower = col.lower()
            if 'time' in col_lower or 'date' in col_lower:
                time_col = col
            elif col_lower not in ['time', 'date', 'timestamp']:
                # Consider as potential value column
                if pd.api.types.is_numeric_dtype(df[col]):
                    value_cols.append(col)
        
        if time_col is None:
            print(f"    ⚠️  No time column found")
            return None
        
        if not value_cols:
            print(f"    ⚠️  No numeric value columns found")
            return None
        
        results = {}
        
        # Analyze each value column
        for val_col in value_cols[:5]:  # Limit to first 5 columns
            print(f"      Column: {val_col}")
            
            times = df[time_col]
            values = df[val_col].values
            
            # Try FFT method
            fft_result = detect_periodicity_fft(times, values)
            
            # Try autocorrelation method
            autocorr_result = detect_periodicity_autocorr(times, values)
            
            if fft_result or autocorr_result:
                results[val_col] = {
                    'fft': fft_result,
                    'autocorr': autocorr_result,
                }
                
                if fft_result:
                    print(f"        FFT: {fft_result['top_period']:.2f}h detected")
                if autocorr_result:
                    print(f"        Autocorr: {autocorr_result['top_lag']:.2f}h detected")
        
        if results:
            return {
                'source': source_name,
                'filepath': str(filepath),
                'detected': True,
                'columns_analyzed': list(results.keys()),
                'results': results,
            }
        else:
            print(f"    ❌ No 0.9h periodicity detected")
            return None
            
    except Exception as e:
        print(f"    ❌ Error: {str(e)}")
        return None

def scan_all_sources(data_dir, registry_file=None):
    """Scan all available data sources"""
    data_dir = Path(data_dir)
    
    print("=" * 70)
    print("LUFT Cross-Domain Periodicity Detector")
    print("=" * 70)
    print(f"\nScanning data directory: {data_dir}")
    
    results = []
    
    # Find all time series data files
    patterns = ['*.csv', '*.json']
    
    files_to_scan = []
    for pattern in patterns:
        files_to_scan.extend(list(data_dir.rglob(pattern)))
    
    # Categorize by source
    sources = defaultdict(list)
    
    for filepath in files_to_scan:
        # Determine source from path
        path_str = str(filepath).lower()
        
        if 'dscovr' in path_str or 'solar_wind' in path_str or 'omni' in path_str:
            sources['Solar Wind'].append(filepath)
        elif 'cern' in path_str or 'lhc' in path_str or 'atlas' in path_str:
            sources['CERN/LHC'].append(filepath)
        elif 'ligo' in path_str or 'gw' in path_str or 'gravitational' in path_str:
            sources['LIGO/GW'].append(filepath)
        elif 'fast' in path_str or 'pulsar' in path_str:
            sources['FAST/Pulsars'].append(filepath)
        elif 'maven' in path_str or 'mars' in path_str:
            sources['MAVEN/Mars'].append(filepath)
        elif 'goes' in path_str:
            sources['GOES'].append(filepath)
        elif 'noaa' in path_str:
            sources['NOAA'].append(filepath)
        else:
            sources['Other'].append(filepath)
    
    print(f"\nFound {len(files_to_scan)} data files across {len(sources)} source categories")
    
    for source_name, files in sources.items():
        print(f"\n{source_name}: {len(files)} files")
        
        # Analyze first few files from each source
        for filepath in files[:3]:  # Limit to 3 files per source
            result = analyze_data_source(filepath, source_name)
            if result:
                results.append(result)
    
    return results

def generate_report(results, output_file):
    """Generate markdown report"""
    with open(output_file, 'w') as f:
        f.write("# Cross-Domain 0.9-Hour Periodicity Report\n\n")
        f.write(f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n")
        f.write("**Hypothesis:** 0.9-hour (54-minute) period is a universal timescale across physics domains\n\n")
        f.write("**Based on:** NASA/NOAA paper (arXiv:2512.14462v1) - CME wave packet arrival rate\n\n")
        f.write("---\n\n")
        
        f.write("## Summary\n\n")
        f.write(f"**Total sources analyzed:** {len(results)}\n")
        f.write(f"**Sources with 0.9h detection:** {sum(1 for r in results if r['detected'])}\n\n")
        
        if results:
            f.write("---\n\n")
            f.write("## Detections by Source\n\n")
            
            for result in results:
                f.write(f"### {result['source']}\n\n")
                f.write(f"**File:** `{result['filepath']}`\n\n")
                
                if result['detected']:
                    f.write("✅ **0.9-hour periodicity DETECTED**\n\n")
                    
                    for col, analysis in result['results'].items():
                        f.write(f"#### Column: `{col}`\n\n")
                        
                        if analysis['fft']:
                            fft = analysis['fft']
                            f.write(f"**FFT Analysis:**\n")
                            f.write(f"- Detected period: {fft['top_period']:.3f} hours\n")
                            f.write(f"- Power: {fft['top_power']:.2e}\n\n")
                        
                        if analysis['autocorr']:
                            ac = analysis['autocorr']
                            f.write(f"**Autocorrelation Analysis:**\n")
                            f.write(f"- Detected lag: {ac['top_lag']:.3f} hours\n")
                            f.write(f"- Correlation: {ac['top_correlation']:.3f}\n\n")
                else:
                    f.write("❌ No 0.9-hour periodicity detected\n\n")
                
                f.write("---\n\n")
        
        # Conclusions
        f.write("## Conclusions\n\n")
        
        detection_count = sum(1 for r in results if r['detected'])
        
        if detection_count >= 2:
            f.write("✅ **HYPOTHESIS SUPPORTED:** 0.9-hour periodicity detected across multiple domains\n\n")
            f.write("This suggests a universal timescale that may connect:\n")
            f.write("- Solar wind dynamics\n")
            f.write("- Particle physics processes\n")
            f.write("- Gravitational wave phenomena\n")
            f.write("- Astrophysical timing\n\n")
        elif detection_count == 1:
            f.write("⚠️  **HYPOTHESIS UNCLEAR:** 0.9-hour periodicity detected in one domain only\n\n")
            f.write("More data needed from other sources.\n\n")
        else:
            f.write("❌ **HYPOTHESIS NOT SUPPORTED:** No 0.9-hour periodicity detected\n\n")
            f.write("Possible reasons:\n")
            f.write("- Insufficient data coverage\n")
            f.write("- Period not present in analyzed timeframes\n")
            f.write("- Signal-to-noise ratio too low\n\n")
        
        f.write("---\n\n")
        f.write("*Generated by LUFT Cross-Domain Periodicity Detector*\n")
        f.write("*Carl Dean Cline Sr. - Lincoln, Nebraska, USA*\n")

def main():
    parser = argparse.ArgumentParser(description='Detect 0.9h periodicity across data sources')
    parser.add_argument('--data-dir', default='data', help='Data directory to scan')
    parser.add_argument('--output', required=True, help='Output markdown report')
    parser.add_argument('--json', help='Optional JSON output')
    args = parser.parse_args()
    
    # Scan sources
    results = scan_all_sources(args.data_dir)
    
    # Generate report
    print(f"\nGenerating report: {args.output}")
    generate_report(results, args.output)
    print(f"  ✅ Report saved")
    
    # Save JSON if requested
    if args.json:
        print(f"Saving JSON: {args.json}")
        with open(args.json, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"  ✅ JSON saved")
    
    print("\n" + "=" * 70)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 70)

if __name__ == '__main__':
    main()
