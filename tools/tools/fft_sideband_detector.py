#!/usr/bin/env python3
"""
FFT Sideband Detector
Analyzes chi amplitude time series data to detect sidebands in frequency domain.
"""

import argparse
import pandas as pd
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt
import sys

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Detect sidebands in chi amplitude time series using FFT analysis'
    )
    parser.add_argument('input', help='Input CSV file with chi amplitude data')
    parser.add_argument('-o', '--output', help='Output plot file (optional)')
    parser.add_argument('--window', default='hann', 
                       choices=['hann', 'hamming', 'blackman', 'bartlett'],
                       help='Window function for FFT (default: hann)')
    parser.add_argument('--detrend', action='store_true',
                       help='Remove linear trend before FFT')
    parser.add_argument('--show', action='store_true',
                       help='Display plot interactively')
    return parser.parse_args()

def load_data(filepath):
    """
    Load chi amplitude data from CSV file. 
    Handles multi-row format where continuation rows exist.
    """
    # Read CSV, handling multi-row format
    try:
        df = pd.read_csv(filepath, 
                         parse_dates=['timestamp_utc'],
                         on_bad_lines='skip',  # Skip malformed lines
                         engine='python')  # Use Python engine for flexibility
    except Exception as e:
        print(f"Error reading CSV: {e}")
        print("Attempting alternate parsing...")
        # Fallback: read without date parsing
        df = pd.read_csv(filepath, on_bad_lines='skip', engine='python')
        if 'timestamp_utc' in df.columns:
            df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], errors='coerce')
    
    # Remove rows where chi_amplitude is NaN or empty
    if 'chi_amplitude' in df.columns:
        initial_rows = len(df)
        df = df[df['chi_amplitude'].notna()]
        df = df[df['chi_amplitude'] != '']
        removed_rows = initial_rows - len(df)
        if removed_rows > 0:
            print(f"Removed {removed_rows} rows with missing chi_amplitude values")
    else:
        print("Warning: 'chi_amplitude' column not found in data")
        print(f"Available columns: {df.columns. tolist()}")
        sys.exit(1)
    
    return df

def compute_fft(data, sampling_rate, window_func='hann', detrend=False):
    """
    Compute FFT of the input signal.
    
    Parameters:
    -----------
    data : array-like
        Input time series data
    sampling_rate : float
        Sampling rate in Hz
    window_func : str
        Window function to apply
    detrend : bool
        Whether to remove linear trend
    
    Returns: 
    --------
    freqs :  ndarray
        Frequency bins
    power : ndarray
        Power spectral density
    """
    # Convert to numpy array and ensure float type
    signal_data = np.array(data, dtype=float)
    
    # Remove trend if requested
    if detrend:
        signal_data = signal.detrend(signal_data, type='linear')
    
    # Apply window function
    if window_func == 'hann':
        window = np.hanning(len(signal_data))
    elif window_func == 'hamming':
        window = np.hamming(len(signal_data))
    elif window_func == 'blackman': 
        window = np.blackman(len(signal_data))
    elif window_func == 'bartlett':
        window = np. bartlett(len(signal_data))
    else:
        window = np.ones(len(signal_data))
    
    windowed_signal = signal_data * window
    
    # Compute FFT
    fft_vals = np.fft.rfft(windowed_signal)
    freqs = np.fft. rfftfreq(len(signal_data), 1/sampling_rate)
    
    # Compute power spectral density
    power = np.abs(fft_vals) ** 2
    
    return freqs, power

def detect_sidebands(freqs, power, threshold_factor=3.0):
    """
    Detect significant peaks (potential sidebands) in the spectrum.
    
    Parameters:
    -----------
    freqs : ndarray
        Frequency bins
    power : ndarray
        Power spectral density
    threshold_factor : float
        Threshold as multiple of median power
    
    Returns:
    --------
    peaks : ndarray
        Indices of detected peaks
    peak_freqs : ndarray
        Frequencies of detected peaks
    peak_powers : ndarray
        Power values at peaks
    """
    # Calculate threshold
    median_power = np.median(power)
    threshold = median_power * threshold_factor
    
    # Find peaks above threshold
    peaks, properties = signal.find_peaks(power, height=threshold)
    
    peak_freqs = freqs[peaks]
    peak_powers = power[peaks]
    
    return peaks, peak_freqs, peak_powers

def plot_results(freqs, power, peak_freqs, peak_powers, output_file=None, show=False):
    """
    Plot the power spectrum with detected sidebands.
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Plot power spectrum
    ax.semilogy(freqs, power, 'b-', linewidth=0.5, label='Power Spectrum')
    
    # Mark detected peaks
    if len(peak_freqs) > 0:
        ax.semilogy(peak_freqs, peak_powers, 'r*', markersize=10, 
                   label=f'Detected Sidebands ({len(peak_freqs)})')
    
    ax.set_xlabel('Frequency (Hz)')
    ax.set_ylabel('Power')
    ax.set_title('FFT Sideband Detection')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=150)
        print(f"Plot saved to {output_file}")
    
    if show: 
        plt.show()
    
    plt.close()

def main():
    """Main execution function."""
    args = parse_arguments()
    
    print(f"Loading data from {args.input}...")
    df = load_data(args.input)
    
    if len(df) == 0:
        print("Error:  No valid data rows found after filtering")
        sys.exit(1)
    
    print(f"Loaded {len(df)} data points")
    
    # Extract chi amplitude data
    chi_amplitude = df['chi_amplitude'].values
    
    # Estimate sampling rate from timestamps if available
    if 'timestamp_utc' in df.columns and pd.api. types.is_datetime64_any_dtype(df['timestamp_utc']):
        time_diffs = df['timestamp_utc'].diff().dt.total_seconds()
        median_interval = time_diffs.median()
        sampling_rate = 1.0 / median_interval if median_interval > 0 else 1.0
        print(f"Estimated sampling rate: {sampling_rate:.6f} Hz (interval: {median_interval:.2f} s)")
    else:
        sampling_rate = 1.0  # Default to 1 Hz if timestamps unavailable
        print(f"Warning: Could not determine sampling rate, using default: {sampling_rate} Hz")
    
    # Compute FFT
    print(f"Computing FFT with {args.window} window...")
    freqs, power = compute_fft(chi_amplitude, sampling_rate, 
                               window_func=args.window, 
                               detrend=args.detrend)
    
    # Detect sidebands
    print("Detecting sidebands...")
    peaks, peak_freqs, peak_powers = detect_sidebands(freqs, power)
    
    print(f"\nDetected {len(peak_freqs)} significant sidebands:")
    for i, (freq, pwr) in enumerate(zip(peak_freqs, peak_powers)):
        print(f"  {i+1}.  Frequency: {freq:.6f} Hz, Power: {pwr:. 2e}")
    
    # Plot results
    if args.output or args.show:
        print("\nGenerating plot...")
        plot_results(freqs, power, peak_freqs, peak_powers, 
                    output_file=args.output, show=args.show)
    
    print("\nAnalysis complete.")

if __name__ == '__main__':
    main()
