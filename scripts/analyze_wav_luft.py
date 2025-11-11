#!/usr/bin/env python3
"""
LUFT WAV Analyzer - Process audio files and generate spectrograms for 7,468 Hz validation
Usage: python scripts/analyze_wav_luft.py <path_to_wav_file>
"""

import sys
import os
import wave
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from pathlib import Path
import csv
from datetime import datetime

# Target frequency for LUFT validation
TARGET_FREQ = 7468  # Hz


def load_wav(filepath):
    """Load WAV file and return audio data and sample rate."""
    try:
        with wave.open(filepath, 'rb') as wav_file:
            # Get WAV file parameters
            n_channels = wav_file.getnchannels()
            sampwidth = wav_file.getsampwidth()
            framerate = wav_file.getframerate()
            n_frames = wav_file.getnframes()
            
            # Read audio data
            audio_data = wav_file.readframes(n_frames)
            
            # Convert to numpy array
            if sampwidth == 1:
                dtype = np.uint8
                audio_array = np.frombuffer(audio_data, dtype=dtype)
                audio_array = (audio_array - 128) / 128.0
            elif sampwidth == 2:
                dtype = np.int16
                audio_array = np.frombuffer(audio_data, dtype=dtype)
                audio_array = audio_array / 32768.0
            elif sampwidth == 4:
                dtype = np.int32
                audio_array = np.frombuffer(audio_data, dtype=dtype)
                audio_array = audio_array / 2147483648.0
            else:
                raise ValueError(f"Unsupported sample width: {sampwidth}")
            
            # Handle stereo by averaging channels
            if n_channels == 2:
                audio_array = audio_array.reshape(-1, 2).mean(axis=1)
            elif n_channels > 2:
                audio_array = audio_array.reshape(-1, n_channels).mean(axis=1)
            
            return audio_array, framerate, n_frames / framerate
    except Exception as e:
        print(f"Error loading WAV file: {e}")
        sys.exit(1)


def generate_spectrogram(audio_data, sample_rate, output_path):
    """Generate and save spectrogram image."""
    # Calculate spectrogram
    # Use appropriate window size for frequency resolution around 7,468 Hz
    nperseg = min(4096, len(audio_data) // 4)  # Window size
    frequencies, times, Sxx = signal.spectrogram(
        audio_data,
        fs=sample_rate,
        nperseg=nperseg,
        noverlap=nperseg // 2
    )
    
    # Create figure
    plt.figure(figsize=(12, 8))
    
    # Plot spectrogram with log scale for power
    plt.pcolormesh(times, frequencies, 10 * np.log10(Sxx + 1e-10), 
                   shading='gouraud', cmap='viridis')
    plt.ylabel('Frequency (Hz)')
    plt.xlabel('Time (s)')
    plt.title(f'LUFT Signal Spectrogram - Target: {TARGET_FREQ} Hz')
    plt.colorbar(label='Power (dB)')
    
    # Add horizontal line at target frequency
    plt.axhline(y=TARGET_FREQ, color='r', linestyle='--', linewidth=2, 
                label=f'{TARGET_FREQ} Hz Target')
    plt.legend(loc='upper right')
    
    # Set y-axis limits to focus on relevant frequency range
    max_freq = min(sample_rate / 2, TARGET_FREQ * 2)
    plt.ylim([0, max_freq])
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"Spectrogram saved to: {output_path}")
    return frequencies, times, Sxx


def find_peaks(audio_data, sample_rate, output_path, n_peaks=10):
    """Find peak frequencies in the audio signal and save to CSV."""
    # Compute FFT
    fft_data = np.fft.rfft(audio_data)
    fft_freqs = np.fft.rfftfreq(len(audio_data), 1/sample_rate)
    fft_magnitude = np.abs(fft_data)
    
    # Find peaks in the frequency domain
    peak_indices, properties = signal.find_peaks(
        fft_magnitude,
        height=np.max(fft_magnitude) * 0.01,  # Threshold at 1% of max
        distance=int(len(fft_freqs) * 10 / sample_rate)  # Minimum 10 Hz separation
    )
    
    # Sort peaks by magnitude
    sorted_indices = peak_indices[np.argsort(fft_magnitude[peak_indices])[::-1]]
    
    # Take top N peaks
    top_peaks = sorted_indices[:min(n_peaks, len(sorted_indices))]
    
    # Create peak data
    peak_data = []
    for idx in top_peaks:
        freq = fft_freqs[idx]
        magnitude = fft_magnitude[idx]
        power_db = 20 * np.log10(magnitude + 1e-10)
        
        # Calculate distance from target frequency
        distance_from_target = abs(freq - TARGET_FREQ)
        
        peak_data.append({
            'frequency_hz': freq,
            'magnitude': magnitude,
            'power_db': power_db,
            'distance_from_target_hz': distance_from_target
        })
    
    # Sort by frequency for output
    peak_data.sort(key=lambda x: x['magnitude'], reverse=True)
    
    # Save to CSV
    with open(output_path, 'w', newline='') as csvfile:
        fieldnames = ['frequency_hz', 'magnitude', 'power_db', 'distance_from_target_hz']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(peak_data)
    
    print(f"Peak data saved to: {output_path}")
    
    # Print summary to console
    print(f"\nTop {len(peak_data)} frequency peaks detected:")
    print(f"{'Frequency (Hz)':<15} {'Magnitude':<15} {'Power (dB)':<15} {'Δ from {TARGET_FREQ} Hz':<20}")
    print("-" * 70)
    for peak in peak_data:
        print(f"{peak['frequency_hz']:<15.2f} {peak['magnitude']:<15.2f} "
              f"{peak['power_db']:<15.2f} {peak['distance_from_target_hz']:<20.2f}")
    
    # Check if target frequency is detected
    closest_peak = min(peak_data, key=lambda x: x['distance_from_target_hz'])
    print(f"\nClosest peak to {TARGET_FREQ} Hz:")
    print(f"  Frequency: {closest_peak['frequency_hz']:.2f} Hz")
    print(f"  Distance: {closest_peak['distance_from_target_hz']:.2f} Hz")
    if closest_peak['distance_from_target_hz'] < 50:  # Within 50 Hz
        print(f"  ✓ Target frequency {TARGET_FREQ} Hz detected!")
    else:
        print(f"  ⚠ Target frequency {TARGET_FREQ} Hz not clearly detected")
    
    return peak_data


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/analyze_wav_luft.py <path_to_wav_file>")
        print("Example: python scripts/analyze_wav_luft.py ./recordings/sample.wav")
        sys.exit(1)
    
    wav_path = sys.argv[1]
    
    # Check if file exists
    if not os.path.exists(wav_path):
        print(f"Error: File not found: {wav_path}")
        sys.exit(1)
    
    # Create results directory if it doesn't exist
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    
    # Get base filename
    base_name = Path(wav_path).stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Define output paths
    spectrogram_path = results_dir / f"{base_name}_spectrogram_{timestamp}.png"
    peaks_csv_path = results_dir / f"{base_name}_peaks_{timestamp}.csv"
    
    print(f"=" * 70)
    print(f"LUFT WAV Analyzer - 7,468 Hz Signal Validation")
    print(f"=" * 70)
    print(f"Input file: {wav_path}")
    print(f"Target frequency: {TARGET_FREQ} Hz")
    print()
    
    # Load WAV file
    print("Loading WAV file...")
    audio_data, sample_rate, duration = load_wav(wav_path)
    print(f"  Sample rate: {sample_rate} Hz")
    print(f"  Duration: {duration:.2f} seconds")
    print(f"  Samples: {len(audio_data)}")
    print()
    
    # Generate spectrogram
    print("Generating spectrogram...")
    generate_spectrogram(audio_data, sample_rate, spectrogram_path)
    print()
    
    # Find peaks
    print("Analyzing frequency peaks...")
    find_peaks(audio_data, sample_rate, peaks_csv_path)
    print()
    
    print("=" * 70)
    print("Analysis complete!")
    print(f"Results saved to: {results_dir}")
    print("=" * 70)


if __name__ == "__main__":
    main()
