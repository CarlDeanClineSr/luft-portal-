import argparse
import numpy as np
import pandas as pd
from scipy import signal
from scipy.signal import butter, filtfilt
from pathlib import Path
import matplotlib.pyplot as plt
from datetime import datetime
import sys

def bandpass_filter(data, lowcut, highcut, fs, order=4):
    """
    Apply Butterworth bandpass filter to time series data.
    
    Parameters:
    -----------
    data : array-like
        Input time series
    lowcut : float
        Lower cutoff frequency (Hz)
    highcut : float
        Upper cutoff frequency (Hz)
    fs : float
        Sampling frequency (Hz)
    order : int
        Filter order (default: 4)
    
    Returns:
    --------
    filtered_data : ndarray
        Bandpass filtered signal
    """
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    
    # Check for valid frequency range
    if lowcut >= highcut:
        raise ValueError(f"Lower cutoff ({lowcut} Hz) must be less than upper cutoff ({highcut} Hz)")
    if low <= 0 or high >= 1:
        raise ValueError(f"Filter frequencies must be within (0, {nyq} Hz)")
    
    b, a = butter(order, [low, high], btype='band')
    filtered_data = filtfilt(b, a, data)
    
    return filtered_data

def main():
    parser = argparse.ArgumentParser(description="FFT Sideband Detector for χ Time-Series")
    parser.add_argument('--input', required=True, help='Path to χ CSV (timestamp, chi_value)')
    parser.add_argument('--sampling-rate', type=float, default=1.0, help='Sampling rate in Hz (default 1.0 for hourly)')
    parser.add_argument('--threshold', type=float, default=0.05, help='Peak prominence threshold')
    parser.add_argument('--plot-all', action='store_true', help='Generate all diagnostic plots')
    parser.add_argument('--save-report', action='store_true', help='Save text report')
    parser.add_argument('--output-dir', default='results/test_001', help='Output directory')
    parser.add_argument('--bandpass', action='store_true',
                       help='Apply bandpass filter before FFT')
    parser.add_argument('--lowcut', type=float, default=5e-5,
                       help='Bandpass lower cutoff frequency (Hz, default: 5e-5)')
    parser.add_argument('--highcut', type=float, default=5e-4,
                       help='Bandpass upper cutoff frequency (Hz, default: 5e-4)')
    parser.add_argument('--filter-order', type=int, default=4,
                       help='Butterworth filter order (default: 4)')
    args = parser.parse_args()

    # Load data with robust CSV parsing
    try:
        df = pd.read_csv(args.input, 
                         parse_dates=['timestamp_utc'],
                         on_bad_lines='skip',  # Skip malformed lines
                         engine='python')  # Use flexible Python parser
    except Exception as e:
        print(f"Error reading CSV: {e}")
        print("Attempting alternate parsing...")
        df = pd.read_csv(args.input, on_bad_lines='skip', engine='python')
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
    
    print(f"Processing {len(df)} valid data rows")
    
    chi = df[chi_column].values
    times = df['timestamp_utc'].values

    # Apply bandpass filter if requested
    if args.bandpass:
        # Validate filter parameters
        if args.lowcut >= args.highcut:
            print(f"Error: Lower cutoff ({args.lowcut:.2e} Hz) must be less than upper cutoff ({args.highcut:.2e} Hz)")
            print("Proceeding without filter...")
        else:
            print(f"Applying bandpass filter: {args.lowcut:.2e} - {args.highcut:.2e} Hz...")
            try:
                chi = bandpass_filter(chi, 
                                      args.lowcut, 
                                      args.highcut, 
                                      args.sampling_rate,
                                      order=args.filter_order)
                print(f"Filter applied successfully")
            except ValueError as e:
                print(f"Filter error: {e}")
                print("Proceeding without filter...")

    # FFT
    N = len(chi)
    freqs = np.fft.rfftfreq(N, d=1/args.sampling_rate)
    fft = np.fft.rfft(chi - chi.mean())
    power = np.abs(fft)**2

    # Find peaks
    peaks, properties = signal.find_peaks(power, prominence=args.threshold * power.max())
    peak_freqs = freqs[peaks]
    peak_power = power[peaks]

    # Output directory
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Save report
    report = f"""# FFT Sideband Analysis Report
Generated: {datetime.utcnow()}
Input: {args.input}
N: {N} points
Sampling Rate: {args.sampling_rate} Hz
"""
    if args.bandpass:
        report += f"Bandpass Filter: {args.lowcut:.2e} - {args.highcut:.2e} Hz (order {args.filter_order})\n"
    
    report += f"""
Detected Peaks ({len(peaks)}):
"""
    for i, (f, p) in enumerate(zip(peak_freqs, peak_power)):
        report += f"{i+1}. Frequency: {f:.6f} Hz | Power: {p:.2e}\n"

    if args.save_report:
        with open(out_dir / "sideband_report.md", 'w') as f:
            f.write(report)
        print("Report saved.")

    # Plot
    if args.plot_all:
        plt.figure(figsize=(12, 6))
        plt.plot(freqs, power)
        plt.plot(peak_freqs, peak_power, "x", color='red')
        plt.xlabel('Frequency (Hz)')
        plt.ylabel('Power')
        title = 'χ FFT Power Spectrum with Detected Peaks'
        if args.bandpass:
            title += f'\n(Bandpass: {args.lowcut:.2e} - {args.highcut:.2e} Hz)'
        plt.title(title)
        plt.grid(True)
        plt.savefig(out_dir / "fft_spectrum.png", dpi=150)
        plt.close()
        print("Plot saved.")

    # Simple sideband check (carrier near zero, symmetric pairs)
    if len(peaks) >= 3:
        diffs = np.diff(peak_freqs)
        symmetry = np.std(diffs) / np.mean(diffs)
        print(f"Sideband symmetry check: std/mean = {symmetry:.4f} (lower = better symmetry)")

if __name__ == "__main__":
    main()
