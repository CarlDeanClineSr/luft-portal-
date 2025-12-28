#!/usr/bin/env python3
"""
FFT Graviton Sideband Detector for LUFT χ-Timeseries
====================================================

Author: Carl Dean Cline Sr. (with Copilot assistance)
Date: 2025-12-27
Version: 1.0
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import signal
from scipy.stats import norm
import json
from datetime import datetime
import os

INPUT_FILE = 'data/cme_heartbeat_log_2025_12.csv'
CHI_COLUMN = 'chi_amplitude'
TIME_COLUMN = 'timestamp_utc'
OUTPUT_DIR = 'results'
SAMPLING_INTERVAL_HOURS = 1.0
MIN_PROMINENCE = 0.01

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 70)
print("LUFT GRAVITON SIDEBAND DETECTOR")
print("=" * 70)
print(f"\nLoading data from: {INPUT_FILE}")

# Load data with robust CSV parsing
try:
    df = pd.read_csv(INPUT_FILE, 
                     parse_dates=[TIME_COLUMN],
                     on_bad_lines='skip',  # Skip malformed lines
                     engine='python')  # Use flexible Python parser
except Exception as e:
    print(f"Error reading CSV: {e}")
    print("Attempting alternate parsing...")
    df = pd.read_csv(INPUT_FILE, on_bad_lines='skip', engine='python')
    if TIME_COLUMN in df.columns:
        df[TIME_COLUMN] = pd.to_datetime(df[TIME_COLUMN], errors='coerce')

print(f"Loaded {len(df)} initial rows")

# Remove rows where timestamp_utc is NaN (continuation rows)
initial_rows = len(df)
df = df[df[TIME_COLUMN].notna()]

# Convert chi column to numeric, coercing errors to NaN
df[CHI_COLUMN] = pd.to_numeric(df[CHI_COLUMN], errors='coerce')

# Remove rows where chi data is NaN
df = df[df[CHI_COLUMN].notna()]
removed_rows = initial_rows - len(df)
if removed_rows > 0:
    print(f"Removed {removed_rows} continuation/empty rows")

# Check for empty DataFrame
if len(df) == 0:
    print("Error: No valid data rows after filtering")
    exit(1)

print(f"Processing {len(df)} valid data rows")

chi = df[CHI_COLUMN].values
timestamps = pd.to_datetime(df[TIME_COLUMN])

print(f"Extracted {len(chi)} χ observations")
print(f"Date range: {timestamps.min()} to {timestamps.max()}")
print(f"χ range: {chi.min():.4f} to {chi.max():.4f}")
print(f"χ = 0.15 count: {(chi == 0.15).sum()} observations")

print(f"\nComputing FFT (N = {len(chi)} points)...")

chi_detrended = chi - np.mean(chi)
window = np.hanning(len(chi_detrended))
chi_windowed = chi_detrended * window

fft = np.fft.fft(chi_windowed)
freqs = np.fft.fftfreq(len(chi), d=SAMPLING_INTERVAL_HOURS)

power = np.abs(fft)**2
power_single_sided = power[: len(power)//2]
freqs_single_sided = freqs[:len(freqs)//2]

print(f"FFT computed")
print(f"Frequency resolution: {freqs[1] - freqs[0]:.6f} cycles/hour")

print(f"\nDetecting peaks...")

peaks, properties = signal.find_peaks(
    power_single_sided,
    prominence=MIN_PROMINENCE * np.max(power_single_sided),
    distance=5
)

print(f"Detected {len(peaks)} peaks")

if len(peaks) == 0:
    print("No peaks detected.  Exiting.")
    exit(1)

peak_powers = power_single_sided[peaks]
peak_order = np.argsort(peak_powers)[::-1]
peaks_sorted = peaks[peak_order]

print(f"\nTop {min(5, len(peaks))} peaks:")
for i, peak_idx in enumerate(peaks_sorted[:5]):
    freq = freqs_single_sided[peak_idx]
    power_val = power_single_sided[peak_idx]
    period = 1/freq if freq > 0 else np.inf
    print(f"  Peak {i+1}: f = {freq:.6f} cycles/hr | T = {period:.2f} hr | Power = {power_val:.2e}")

print(f"\nTesting for symmetric sidebands...")

sideband_detected = False
carrier_freq = None
upper_sideband_freq = None
lower_sideband_freq = None
modulation_freq = None
symmetry_error = None

if len(peaks) >= 3:
    carrier_idx = peaks_sorted[0]
    carrier_freq = freqs_single_sided[carrier_idx]
    carrier_power = power_single_sided[carrier_idx]
    
    print(f"\nCarrier (strongest peak): f = {carrier_freq:.6f} cycles/hr")
    
    other_peaks = peaks_sorted[1:]
    
    upper_candidates = [p for p in other_peaks if freqs_single_sided[p] > carrier_freq]
    lower_candidates = [p for p in other_peaks if freqs_single_sided[p] < carrier_freq]
    
    if len(upper_candidates) > 0 and len(lower_candidates) > 0:
        upper_idx = upper_candidates[0]
        lower_idx = lower_candidates[0]
        
        upper_sideband_freq = freqs_single_sided[upper_idx]
        lower_sideband_freq = freqs_single_sided[lower_idx]
        
        delta_upper = upper_sideband_freq - carrier_freq
        delta_lower = carrier_freq - lower_sideband_freq
        
        avg_delta = (delta_upper + delta_lower) / 2
        symmetry_error = abs(delta_upper - delta_lower) / avg_delta if avg_delta > 0 else 1.0
        
        modulation_freq = avg_delta
        
        print(f"Upper sideband: f = {upper_sideband_freq:.6f} cycles/hr (delta = +{delta_upper:.6f})")
        print(f"Lower sideband: f = {lower_sideband_freq:.6f} cycles/hr (delta = -{delta_lower:.6f})")
        print(f"Symmetry error: {symmetry_error*100:.2f}%")
        print(f"Modulation frequency: {modulation_freq:.6f} cycles/hr (T = {1/modulation_freq:.2f} hr)")
        
        if symmetry_error < 0.05:
            sideband_detected = True
            print(f"\nSYMMETRIC SIDEBANDS DETECTED!")
            print(f"Graviton amplitude modulation signature CONFIRMED")
        else:
            print(f"\nSidebands NOT symmetric (error = {symmetry_error*100:.2f}% > 5%)")
    else:
        print(f"\nInsufficient sideband peaks")
else:
    print(f"\nInsufficient peaks (need >= 3)")

print(f"\nStatistical significance test...")

mask_peaks = np.ones(len(power_single_sided), dtype=bool)
mask_peaks[peaks] = False
noise_floor = np.median(power_single_sided[mask_peaks])

carrier_snr = None
carrier_zscore = None
carrier_pvalue = None

if carrier_freq is not None:
    carrier_snr = power_single_sided[peaks_sorted[0]] / noise_floor
    print(f"Carrier SNR:  {carrier_snr:.2f}")
    
    carrier_zscore = (power_single_sided[peaks_sorted[0]] - noise_floor) / np.std(power_single_sided[mask_peaks])
    carrier_pvalue = 1 - norm. cdf(carrier_zscore)
    
    print(f"Carrier Z-score: {carrier_zscore:.2f}")
    print(f"Carrier p-value: {carrier_pvalue:.2e}")
    
    if carrier_pvalue < 0.001:
        print(f"Carrier peak is statistically significant (p < 0.001)")

print(f"\nSaving results to {OUTPUT_DIR}/...")

results = {
    'timestamp': datetime.utcnow().isoformat(),
    'input_file': INPUT_FILE,
    'n_observations': int(len(chi)),
    'chi_min': float(chi.min()),
    'chi_max': float(chi. max()),
    'chi_mean': float(chi.mean()),
    'chi_std': float(chi.std()),
    'chi_cap_count': int((chi == 0.15).sum()),
    'n_peaks_detected': int(len(peaks)),
    'sideband_detected': bool(sideband_detected),
    'carrier_frequency_cycles_per_hour': float(carrier_freq) if carrier_freq is not None else None,
    'upper_sideband_frequency':  float(upper_sideband_freq) if upper_sideband_freq is not None else None,
    'lower_sideband_frequency': float(lower_sideband_freq) if lower_sideband_freq is not None else None,
    'modulation_frequency': float(modulation_freq) if modulation_freq is not None else None,
    'symmetry_error_percent': float(symmetry_error * 100) if symmetry_error is not None else None,
    'carrier_snr': float(carrier_snr) if carrier_snr is not None else None,
    'carrier_zscore': float(carrier_zscore) if carrier_zscore is not None else None,
    'carrier_pvalue': float(carrier_pvalue) if carrier_pvalue is not None else None,
}

with open(f'{OUTPUT_DIR}/graviton_sideband_analysis.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"Results saved to {OUTPUT_DIR}/graviton_sideband_analysis.json")

print(f"\nGenerating plot...")

fig, axes = plt.subplots(2, 1, figsize=(14, 10))

ax1 = axes[0]
ax1.plot(freqs_single_sided, power_single_sided, 'b-', linewidth=0.5, label='Power Spectrum')
ax1.plot(freqs_single_sided[peaks], power_single_sided[peaks], 'rx', markersize=10, markeredgewidth=2, label=f'Detected Peaks (n={len(peaks)})')

if sideband_detected:
    ax1.axvline(carrier_freq, color='green', linestyle='--', linewidth=2, label='Carrier')
    ax1.axvline(upper_sideband_freq, color='orange', linestyle='--', linewidth=2, label='Upper Sideband')
    ax1.axvline(lower_sideband_freq, color='purple', linestyle='--', linewidth=2, label='Lower Sideband')

ax1.axhline(noise_floor, color='gray', linestyle=':', linewidth=1, label='Noise Floor')
ax1.set_xlabel('Frequency (cycles/hour)', fontsize=12)
ax1.set_ylabel('Power', fontsize=12)
ax1.set_title('FFT Power Spectrum of χ Timeseries - Graviton Sideband Search', fontsize=14, fontweight='bold')
ax1.legend(loc='upper right')
ax1.grid(True, alpha=0.3)
ax1.set_yscale('log')

ax2 = axes[1]
if carrier_freq is not None and modulation_freq is not None: 
    zoom_width = 10 * modulation_freq
    zoom_center = carrier_freq
    zoom_mask = (freqs_single_sided >= zoom_center - zoom_width) & (freqs_single_sided <= zoom_center + zoom_width)
    
    ax2.plot(freqs_single_sided[zoom_mask], power_single_sided[zoom_mask], 'b-', linewidth=1.5)
    
    ax2.axvline(carrier_freq, color='green', linestyle='--', linewidth=2, label='Carrier')
    if sideband_detected:
        ax2.axvline(upper_sideband_freq, color='orange', linestyle='--', linewidth=2, label='Upper Sideband')
        ax2.axvline(lower_sideband_freq, color='purple', linestyle='--', linewidth=2, label='Lower Sideband')
    
    ax2.set_xlabel('Frequency (cycles/hour)', fontsize=12)
    ax2.set_ylabel('Power', fontsize=12)
    ax2.set_title(f'Zoomed View:  Carrier at {carrier_freq:.6f} cycles/hr', fontsize=12, fontweight='bold')
    ax2.legend(loc='upper right')
    ax2.grid(True, alpha=0.3)
    ax2.set_yscale('log')
else:
    ax2.text(0.5, 0.5, 'No carrier detected', ha='center', va='center', fontsize=14, transform=ax2.transAxes)
    ax2.axis('off')

plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/chi_fft_spectrum.png', dpi=300, bbox_inches='tight')
print(f"Plot saved to {OUTPUT_DIR}/chi_fft_spectrum.png")

print("\n" + "=" * 70)
print("ANALYSIS COMPLETE")
print("=" * 70)

if sideband_detected:
    print("\nGRAVITON SIDEBAND SIGNATURE DETECTED!")
    print(f"  Carrier:  {carrier_freq:.6f} cycles/hr")
    print(f"  Modulation: {modulation_freq:.6f} cycles/hr")
    print(f"  Symmetry error: {symmetry_error*100:.2f}% (< 5% threshold)")
    print(f"\n  This is evidence of amplitude-modulated quantum gravity")
else:
    print("\nNo symmetric sidebands detected")
    print(f"  χ = 0.15 remains a plasma boundary")

print("\n" + "=" * 70)
