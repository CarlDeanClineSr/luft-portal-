import argparse
import numpy as np
import pandas as pd
from scipy.signal import find_peaks
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description="FFT Sideband Detector for χ Time-Series")
    parser.add_argument('--input', default='data/cme_heartbeat_log_2025_12.csv', help='Path to χ CSV')
    parser.add_argument('--column', default='chi_amplitude', help='Column name for χ values')
    parser.add_argument('--sampling-hours', type=float, default=1.0, help='Sampling interval in hours')
    parser.add_argument('--threshold', type=float, default=0.05, help='Peak prominence threshold (fraction of max)')
    parser.add_argument('--output-dir', default='results/fft_sideband', help='Output directory')
    args = parser.parse_args()

    # Load data
    df = pd.read_csv(args.input, parse_dates=['timestamp_utc'])
    chi = df[args.column].dropna().values
    N = len(chi)

    if N < 100:
        print("Not enough data points for reliable FFT.")
        return

    # Sampling rate
    fs = 1.0 / (args.sampling_hours * 3600)  # Hz

    # FFT
    fft = np.fft.rfft(chi - chi.mean())
    freqs = np.fft.rfftfreq(N, d=args.sampling_hours * 3600)
    power = np.abs(fft)**2

    # Find peaks
    peaks, properties = find_peaks(power, prominence=args.threshold * power.max())
    peak_freqs = freqs[peaks]
    peak_power = power[peaks]

    # Output directory
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Report
    report = f"""# FFT Sideband Analysis Report
Generated: {datetime.utcnow()}

Input File: {args.input}
Data Points: {N}
Sampling: {args.sampling_hours} hours ({fs:.2e} Hz)

Detected Peaks ({len(peaks)}):
"""
    for i, (f, p) in enumerate(zip(peak_freqs, peak_power)):
        report += f"{i+1}. Frequency: {f:.6f} Hz ({1/f/3600:.2f} hours period) | Power: {p:.2e}\n"

    # Symmetry check (if >2 peaks)
    if len(peaks) >= 3:
        diffs = np.diff(peak_freqs)
        symmetry = np.std(diffs) / np.mean(diffs) if np.mean(diffs) > 0 else np.inf
        report += f"\nSideband Symmetry Check: std/mean = {symmetry:.4f} (lower = better symmetry)\n"
        if symmetry < 0.1:
            report += "→ Strong symmetric sideband pattern detected!\n"
        elif symmetry < 0.3:
            report += "→ Moderate symmetry — possible AM signature.\n"
        else:
            report += "→ No clear symmetry.\n"

    report_path = out_dir / "sideband_report.md"
    with open(report_path, 'w') as f:
        f.write(report)
    print(f"Report saved: {report_path}")

    # Plot
    plt.figure(figsize=(12, 6))
    plt.plot(freqs, power, label='Power Spectrum')
    plt.plot(peak_freqs, peak_power, "x", color='red', label='Detected Peaks')
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Power')
    plt.title('χ FFT Sideband Search')
    plt.grid(True)
    plt.legend()
    plot_path = out_dir / "fft_spectrum.png"
    plt.savefig(plot_path, dpi=150)
    plt.close()
    print(f"Plot saved: {plot_path}")

if __name__ == "__main__":
    main()
