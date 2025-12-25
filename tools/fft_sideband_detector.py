import argparse
import numpy as np
import pandas as pd
from scipy import signal
from pathlib import Path
import matplotlib.pyplot as plt
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description="FFT Sideband Detector for χ Time-Series")
    parser.add_argument('--input', required=True, help='Path to χ CSV (timestamp, chi_value)')
    parser.add_argument('--sampling-rate', type=float, default=1.0, help='Sampling rate in Hz (default 1.0 for hourly)')
    parser.add_argument('--threshold', type=float, default=0.05, help='Peak prominence threshold')
    parser.add_argument('--plot-all', action='store_true', help='Generate all diagnostic plots')
    parser.add_argument('--save-report', action='store_true', help='Save text report')
    parser.add_argument('--output-dir', default='results/test_001', help='Output directory')
    args = parser.parse_args()

    # Load data
    df = pd.read_csv(args.input, parse_dates=['timestamp_utc'])
    chi = df['chi_value'].values
    times = df['timestamp_utc'].values

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
        plt.title('χ FFT Power Spectrum with Detected Peaks')
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
