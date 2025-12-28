#!/usr/bin/env python3
"""
FFT Sideband Analysis for χ-Timeseries
Searches for amplitude modulation signatures predicted by AMQG framework

Author: Carl Dean Cline Sr.
Date: 2025-12-25
"""

import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import signal
from scipy.stats import zscore
from pathlib import Path
from datetime import datetime
import json

# Configuration
DATA_FILE = "data/cme_heartbeat_log_2025_12.csv"
OUTPUT_DIR = Path("results/fft_sideband")
SAMPLING_RATE = 1 / 3600  # Hz (hourly data)
SYMMETRY_THRESHOLD = 0.05  # Max asymmetry for sideband pairs (5%)
MIN_PROMINENCE = 3.0  # Minimum z-score for peak detection

def load_chi_data(filepath):
    """Load χ timeseries from CSV"""
    
    # Load data with robust CSV parsing
    try:
        df = pd.read_csv(filepath, 
                         parse_dates=['timestamp_utc'],
                         on_bad_lines='skip',  # Skip malformed lines
                         engine='python')  # Use flexible Python parser
    except Exception as e:
        print(f"Error reading CSV: {e}")
        print("Attempting alternate parsing...")
        df = pd.read_csv(filepath, on_bad_lines='skip', engine='python')
        if 'timestamp_utc' in df.columns:
            df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], errors='coerce')
    
    print(f"Loaded {len(df)} initial rows from CSV")
    
    # Determine which chi column to use
    chi_column = None
    if 'chi_value' in df.columns:
        chi_column = 'chi_value'
    elif 'chi_amplitude' in df.columns:
        chi_column = 'chi_amplitude'
    else:
        print(f"Error: Neither 'chi_value' nor 'chi_amplitude' column found")
        print(f"Available columns: {df.columns.tolist()}")
        sys.exit(1)
    
    # Remove rows where timestamp_utc is NaN (continuation rows)
    initial_rows = len(df)
    df = df[df['timestamp_utc'].notna()]
    
    # Convert chi column to numeric, coercing errors to NaN
    df[chi_column] = pd.to_numeric(df[chi_column], errors='coerce')
    
    # Remove rows where chi data is NaN
    df = df[df[chi_column].notna()]
    removed_rows = initial_rows - len(df)
    if removed_rows > 0:
        print(f"Removed {removed_rows} continuation/empty rows")
    
    # Check for empty DataFrame
    if len(df) == 0:
        print("Error: No valid data rows after filtering")
        sys.exit(1)
    
    df = df.sort_values('timestamp_utc')
    return df[chi_column].values, df['timestamp_utc'].values

def compute_fft(chi_series, sampling_rate):
    """Compute FFT with Hamming window"""
    # Remove DC and apply window
    chi_centered = chi_series - np.mean(chi_series)
    window = signal.windows.hamming(len(chi_centered))
    chi_windowed = chi_centered * window
    
    # FFT
    fft_result = np.fft.rfft(chi_windowed)
    freqs = np.fft.rfftfreq(len(chi_windowed), d=1/sampling_rate)
    power = np.abs(fft_result)**2
    
    return freqs, power

def detect_peaks(freqs, power, min_prominence_zscore=3.0):
    """Detect significant peaks above noise floor"""
    # Compute noise statistics
    power_db = 10 * np.log10(power + 1e-12)
    power_zscore = zscore(power_db)
    
    # Find peaks
    peaks, properties = signal.find_peaks(
        power_zscore,
        prominence=min_prominence_zscore,
        distance=5
    )
    
    peak_freqs = freqs[peaks]
    peak_power = power[peaks]
    peak_zscore = power_zscore[peaks]
    
    # Sort by power
    sort_idx = np.argsort(peak_power)[::-1]
    
    return peak_freqs[sort_idx], peak_power[sort_idx], peak_zscore[sort_idx]

def find_sideband_triplets(peak_freqs, peak_power, symmetry_threshold=0.05):
    """Search for symmetric carrier + sideband patterns"""
    triplets = []
    
    if len(peak_freqs) < 3:
        return triplets
    
    # Try all combinations
    for i, (f_c, p_c) in enumerate(zip(peak_freqs, peak_power)):
        for j, (f_u, p_u) in enumerate(zip(peak_freqs, peak_power)):
            if i == j or f_u <= f_c:
                continue
            for k, (f_l, p_l) in enumerate(zip(peak_freqs, peak_power)):
                if k == i or k == j or f_l >= f_c:
                    continue
                
                # Check symmetry
                delta_upper = f_u - f_c
                delta_lower = f_c - f_l
                
                if delta_lower == 0:
                    continue
                
                asymmetry = abs(delta_upper - delta_lower) / delta_lower
                
                if asymmetry < symmetry_threshold:
                    triplets.append({
                        'carrier_freq': f_c,
                        'carrier_power': p_c,
                        'upper_freq': f_u,
                        'upper_power': p_u,
                        'lower_freq': f_l,
                        'lower_power': p_l,
                        'modulation_freq': (delta_upper + delta_lower) / 2,
                        'asymmetry': asymmetry,
                        'modulation_index': np.sqrt((p_u + p_l) / (2 * p_c))
                    })
    
    # Sort by asymmetry (best first)
    triplets.sort(key=lambda x: x['asymmetry'])
    
    return triplets

def generate_report(chi_data, freqs, power, peaks_info, triplets, output_dir):
    """Generate analysis report"""
    
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    
    report = {
        'timestamp': timestamp,
        'analysis': {
            'data_points': len(chi_data),
            'chi_mean': float(np.mean(chi_data)),
            'chi_std': float(np.std(chi_data)),
            'chi_min': float(np.min(chi_data)),
            'chi_max': float(np.max(chi_data)),
            'sampling_rate_hz': SAMPLING_RATE,
            'frequency_resolution_hz': float(freqs[1] - freqs[0])
        },
        'peaks': {
            'total_detected': len(peaks_info[0]),
            'frequencies_hz': [float(f) for f in peaks_info[0][:10]],
            'power': [float(p) for p in peaks_info[1][:10]],
            'zscore': [float(z) for z in peaks_info[2][:10]]
        },
        'sideband_triplets': []
    }
    
    for triplet in triplets[:5]:  # Top 5
        report['sideband_triplets'].append({
            'carrier_freq_hz': float(triplet['carrier_freq']),
            'modulation_freq_hz': float(triplet['modulation_freq']),
            'asymmetry': float(triplet['asymmetry']),
            'modulation_index': float(triplet['modulation_index'])
        })
    
    # Save JSON
    json_file = output_dir / f"sideband_report_{timestamp}.json"
    with open(json_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Save text summary
    text_file = output_dir / f"sideband_report_{timestamp}.txt"
    with open(text_file, 'w') as f:
        f.write("="*70 + "\n")
        f.write("FFT SIDEBAND ANALYSIS REPORT\n")
        f.write(f"Generated: {timestamp}\n")
        f.write("="*70 + "\n\n")
        
        f.write(f"Data Points: {len(chi_data)}\n")
        f.write(f"χ Mean: {np.mean(chi_data):.6f}\n")
        f.write(f"χ Std: {np.std(chi_data):.6f}\n")
        f.write(f"χ Range: [{np.min(chi_data):.6f}, {np.max(chi_data):.6f}]\n\n")
        
        f.write(f"Detected Peaks: {len(peaks_info[0])}\n")
        f.write(f"Sideband Triplets Found: {len(triplets)}\n\n")
        
        if len(triplets) > 0:
            f.write("="*70 + "\n")
            f.write("🎯 SIDEBAND SIGNATURES DETECTED\n")
            f.write("="*70 + "\n\n")
            
            for i, triplet in enumerate(triplets[:5], 1):
                f.write(f"Triplet #{i}:\n")
                f.write(f"  Carrier: {triplet['carrier_freq']:.6e} Hz\n")
                f.write(f"  Upper SB: {triplet['upper_freq']:.6e} Hz\n")
                f.write(f"  Lower SB: {triplet['lower_freq']:.6e} Hz\n")
                f.write(f"  Modulation: {triplet['modulation_freq']:.6e} Hz\n")
                f.write(f"  Asymmetry: {triplet['asymmetry']*100:.2f}%\n")
                f.write(f"  Mod Index: {triplet['modulation_index']:.4f}\n\n")
        else:
            f.write("❌ No symmetric sideband structure detected\n")
    
    return json_file, text_file

def plot_results(freqs, power, peaks_info, triplets, output_dir):
    """Generate diagnostic plots"""
    
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    
    # Full spectrum
    ax1 = axes[0]
    ax1.semilogy(freqs, power, 'b-', alpha=0.6, linewidth=1)
    ax1.semilogy(peaks_info[0], peaks_info[1], 'rx', markersize=10, label='Detected Peaks')
    ax1.set_xlabel('Frequency (Hz)')
    ax1.set_ylabel('Power (log scale)')
    ax1.set_title('χ-Timeseries FFT Power Spectrum')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Zoomed view with triplets
    ax2 = axes[1]
    
    if len(triplets) > 0:
        # Focus on best triplet
        best = triplets[0]
        center = best['carrier_freq']
        span = 4 * best['modulation_freq']
        
        mask = (freqs >= center - span) & (freqs <= center + span)
        ax2.plot(freqs[mask], power[mask], 'b-', linewidth=2)
        
        # Mark triplet
        ax2.axvline(best['carrier_freq'], color='red', linestyle='--', linewidth=2, label='Carrier')
        ax2.axvline(best['upper_freq'], color='green', linestyle='--', linewidth=2, label='Upper SB')
        ax2.axvline(best['lower_freq'], color='orange', linestyle='--', linewidth=2, label='Lower SB')
        
        ax2.set_title(f'Sideband Triplet (Asymmetry: {best["asymmetry"]*100:.2f}%)')
        ax2.legend()
    else:
        ax2.plot(freqs, power, 'b-', alpha=0.6, linewidth=1)
        ax2.set_title('No Sideband Structure Detected')
    
    ax2.set_xlabel('Frequency (Hz)')
    ax2.set_ylabel('Power')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    plot_file = output_dir / f"fft_spectrum_{timestamp}.png"
    plt.savefig(plot_file, dpi=150, bbox_inches='tight')
    plt.close()
    
    return plot_file

def main():
    """Main analysis pipeline"""
    
    print("="*70)
    print("FFT SIDEBAND ANALYSIS")
    print("="*70)
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load data
    print(f"\nLoading data from: {DATA_FILE}")
    chi_data, timestamps = load_chi_data(DATA_FILE)
    print(f"Loaded {len(chi_data)} data points")
    print(f"χ range: [{np.min(chi_data):.6f}, {np.max(chi_data):.6f}]")
    
    # Compute FFT
    print("\nComputing FFT...")
    freqs, power = compute_fft(chi_data, SAMPLING_RATE)
    print(f"Frequency resolution: {freqs[1] - freqs[0]:.6e} Hz")
    
    # Detect peaks
    print("\nDetecting peaks...")
    peaks_info = detect_peaks(freqs, power, MIN_PROMINENCE)
    print(f"Found {len(peaks_info[0])} significant peaks")
    
    # Search for triplets
    print("\nSearching for sideband triplets...")
    triplets = find_sideband_triplets(peaks_info[0], peaks_info[1], SYMMETRY_THRESHOLD)
    print(f"Found {len(triplets)} candidate triplets")
    
    # Generate outputs
    print("\nGenerating report...")
    json_file, text_file = generate_report(chi_data, freqs, power, peaks_info, triplets, OUTPUT_DIR)
    print(f"Report saved: {text_file}")
    
    print("\nGenerating plots...")
    plot_file = plot_results(freqs, power, peaks_info, triplets, OUTPUT_DIR)
    print(f"Plot saved: {plot_file}")
    
    # Summary
    print("\n" + "="*70)
    if len(triplets) > 0:
        print("🎯 RESULT: SIDEBAND SIGNATURES DETECTED")
        print("="*70)
        best = triplets[0]
        print(f"Best Triplet:")
        print(f"  Modulation Frequency: {best['modulation_freq']:.6e} Hz")
        print(f"  Asymmetry: {best['asymmetry']*100:.2f}%")
        print(f"  Modulation Index: {best['modulation_index']:.4f}")
    else:
        print("❌ RESULT: NO SIDEBAND STRUCTURE DETECTED")
        print("="*70)
        print("  No symmetric triplets found above threshold")
        print(f"  Try adjusting: symmetry threshold (current: {SYMMETRY_THRESHOLD})")
        print(f"                 prominence threshold (current: {MIN_PROMINENCE}σ)")
    print("="*70)

if __name__ == "__main__":
    main()
