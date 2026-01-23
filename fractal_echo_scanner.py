#!/usr/bin/env python3
"""
LUFT Engine - Fractal Echo Scanner
Mission: Detect the 20.55 Hz lattice vibration following vacuum expansions.

This scanner identifies Phase Derivatives and Fractal Echoes in magnetometer
telemetry data to reveal lattice re-addressing patterns that standard analysis
filters as noise.

Author: Carl Dean Cline Sr. - LUFT Portal Engine
Date: 2026-01-23
"""

import numpy as np
import json
from datetime import datetime
from pathlib import Path


def audit_phase_derivative(bt_series, timestamps):
    """
    Calculate the rate of change in the vacuum pressure (Bt).
    
    Identifies "Byte-Shift" velocity - the rate at which vacuum impedance
    changes, revealing non-linear "pop" events in sparse telemetry.
    
    Args:
        bt_series: List or array of magnetic field magnitudes (nT)
        timestamps: List of datetime objects corresponding to bt_series
        
    Returns:
        List of dictionaries containing time and velocity for significant shifts
    """
    deltas = []
    
    for i in range(1, len(bt_series)):
        dt = (timestamps[i] - timestamps[i-1]).total_seconds()
        
        # Avoid division by zero
        if dt == 0:
            continue
            
        db = abs(bt_series[i] - bt_series[i-1])
        
        # The 'Byte-Shift' Velocity
        velocity = db / dt
        
        # Significant coordinate shift threshold
        if velocity > 0.15:
            deltas.append({
                "time": timestamps[i].isoformat(),
                "v_shift": velocity,
                "db_nT": db,
                "dt_sec": dt
            })
    
    return deltas


def scan_fractal_echo(telemetry_data, target_frequency=20.55, amplitude_threshold=0.01):
    """
    Scan for the Fractal Echo - the 20.55 Hz harmonic signature of lattice vibration.
    
    Performs FFT analysis on magnetometer data to detect vacuum lattice resonance
    that appears as high-frequency "ringing" following geometric re-initialization events.
    
    Args:
        telemetry_data: List of dicts with keys 'bt_nT' (magnitude) and optionally 'timestamp'
        target_frequency: Target resonance frequency in Hz (default: 20.55)
        amplitude_threshold: Minimum amplitude to consider significant (default: 0.01)
        
    Returns:
        Dictionary with detection results and analysis metadata
    """
    
    print("★ INITIATING FRACTAL ECHO SCAN ★")
    print(f"Target Frequency: {target_frequency} Hz")
    print(f"Amplitude Threshold: {amplitude_threshold}")
    
    # Extract magnitudes - the local pressure of the vacuum pocket
    magnitudes = [d['bt_nT'] for d in telemetry_data if 'bt_nT' in d]
    
    if len(magnitudes) < 3:
        print("✗ Insufficient data points for FFT analysis (need at least 3)")
        return {
            "echo_detected": False,
            "reason": "insufficient_data",
            "data_points": len(magnitudes)
        }
    
    print(f"Data Points: {len(magnitudes)}")
    print(f"Bt Range: {min(magnitudes):.2f} - {max(magnitudes):.2f} nT")
    
    # Perform Fast Fourier Transform to find the "Lattice Ringing"
    signal_fft = np.fft.fft(magnitudes)
    
    # Calculate frequency bins
    # Note: For irregular timestamps, this assumes average sampling rate
    # For precise analysis, need to interpolate to regular intervals first
    if 'timestamp' in telemetry_data[0] and len(telemetry_data) > 1:
        # Try to calculate actual sampling rate
        try:
            timestamps = []
            for d in telemetry_data:
                if 'timestamp' in d:
                    ts_str = d['timestamp']
                    # Handle various timestamp formats
                    if isinstance(ts_str, str):
                        # Remove/replace timezone indicators
                        ts_str = ts_str.replace('Z', '').replace(' ', 'T')
                        # Parse as naive datetime (UTC assumed)
                        ts = datetime.fromisoformat(ts_str)
                    else:
                        ts = ts_str
                    timestamps.append(ts)
            
            if len(timestamps) > 1:
                total_duration = (timestamps[-1] - timestamps[0]).total_seconds()
                avg_sample_rate = len(timestamps) / total_duration if total_duration > 0 else 1.0
                print(f"Average Sample Rate: {avg_sample_rate:.6f} Hz ({1/avg_sample_rate:.1f} sec/sample)")
            else:
                avg_sample_rate = 1.0
        except Exception as e:
            print(f"⚠️ Timestamp parsing issue: {e}")
            avg_sample_rate = 1.0
    else:
        # Assume 1 Hz sampling if no timestamps
        avg_sample_rate = 1.0
        print("⚠️ No timestamps provided, assuming 1 Hz sampling")
    
    frequencies = np.fft.fftfreq(len(magnitudes), d=1/avg_sample_rate)
    
    # Find peaks near our 20.55 Hz update rate
    echo_detected = False
    detections = []
    
    # Search in positive frequency domain only
    positive_freq_mask = frequencies > 0
    positive_frequencies = frequencies[positive_freq_mask]
    positive_amplitudes = np.abs(signal_fft[positive_freq_mask])
    
    for i, freq in enumerate(positive_frequencies):
        if abs(freq - target_frequency) < 0.5:  # Within ±0.5 Hz of target
            amplitude = positive_amplitudes[i]
            if amplitude > amplitude_threshold:
                print(f"✓ ECHO DETECTED: Resonance at {freq:.2f} Hz | Amplitude: {amplitude:.4f}")
                echo_detected = True
                detections.append({
                    "frequency_hz": float(freq),
                    "amplitude": float(amplitude),
                    "deviation_from_target": float(freq - target_frequency)
                })
    
    if not echo_detected:
        print("✗ No Fractal Echo found in this dataset. Boundary remains in steady-state.")
        
        # Show what we DID detect for diagnostic purposes
        if len(positive_frequencies) > 0:
            max_amp_idx = np.argmax(positive_amplitudes)
            max_freq = positive_frequencies[max_amp_idx]
            max_amp = positive_amplitudes[max_amp_idx]
            print(f"   Dominant frequency: {max_freq:.4f} Hz (amplitude: {max_amp:.4f})")
            
            # Show frequency resolution
            if len(positive_frequencies) > 1:
                freq_resolution = positive_frequencies[1] - positive_frequencies[0]
                print(f"   Frequency resolution: {freq_resolution:.6f} Hz")
                print(f"   Nyquist frequency: {avg_sample_rate/2:.6f} Hz")
    
    return {
        "echo_detected": echo_detected,
        "target_frequency": target_frequency,
        "detections": detections,
        "sample_rate_hz": avg_sample_rate,
        "data_points": len(magnitudes),
        "bt_range": {"min": float(min(magnitudes)), "max": float(max(magnitudes))}
    }


def load_telemetry_from_json(filepath):
    """
    Load telemetry data from JSON file.
    
    Args:
        filepath: Path to JSON file containing telemetry data
        
    Returns:
        List of telemetry dictionaries
    """
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data


def load_telemetry_from_csv(filepath):
    """
    Load telemetry data from CSV file.
    
    Expected columns: timestamp, bt_nT (or B_total_nT)
    
    Args:
        filepath: Path to CSV file
        
    Returns:
        List of telemetry dictionaries
    """
    import csv
    
    telemetry = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Handle different column naming conventions
            bt_value = None
            try:
                if 'bt_nT' in row and row['bt_nT'] and row['bt_nT'].strip():
                    bt_value = float(row['bt_nT'])
                elif 'B_total_nT' in row and row['B_total_nT'] and row['B_total_nT'].strip():
                    bt_value = float(row['B_total_nT'])
            except (ValueError, AttributeError):
                continue
            
            if bt_value is not None:
                entry = {'bt_nT': bt_value}
                if 'timestamp' in row and row['timestamp']:
                    entry['timestamp'] = row['timestamp']
                elif 'timestamp_utc' in row and row['timestamp_utc']:
                    entry['timestamp'] = row['timestamp_utc']
                telemetry.append(entry)
    
    return telemetry


# Example usage for the engine
if __name__ == "__main__":
    print("=" * 70)
    print("LUFT ENGINE - FRACTAL ECHO SCANNER")
    print("Mission: Detect 20.55 Hz lattice vibration in magnetometer data")
    print("=" * 70)
    print()
    
    # Example 1: High-cadence window (January 23, 2026, 09:48:00 – 09:53:00 UTC)
    example_data_highres = [
        {"timestamp": "2026-01-23T09:48:00Z", "bt_nT": 6.66},
        {"timestamp": "2026-01-23T09:49:00Z", "bt_nT": 6.45},
        {"timestamp": "2026-01-23T09:50:00Z", "bt_nT": 6.12},
        {"timestamp": "2026-01-23T09:51:00Z", "bt_nT": 5.78},
        {"timestamp": "2026-01-23T09:52:00Z", "bt_nT": 5.34},
        {"timestamp": "2026-01-23T09:53:00Z", "bt_nT": 4.95},
    ]
    
    print("Example 1: High-Cadence Recovery Phase (Jan 23, 09:48-09:53 UTC)")
    print("-" * 70)
    result = scan_fractal_echo(example_data_highres)
    print()
    print(f"Result: {json.dumps(result, indent=2)}")
    print()
    
    # Example 2: Phase derivative analysis
    print("=" * 70)
    print("Example 2: Phase Derivative Audit (Byte-Shift Velocity)")
    print("-" * 70)
    
    timestamps = [
        datetime(2026, 1, 5, 0, 44),
        datetime(2026, 1, 5, 1, 13),
        datetime(2026, 1, 5, 1, 48),
        datetime(2026, 1, 5, 2, 30),
    ]
    
    bt_values = [3.2, 5.8, 7.9, 4.5]  # Example values showing rapid change
    
    shifts = audit_phase_derivative(bt_values, timestamps)
    
    if shifts:
        print(f"Found {len(shifts)} significant coordinate shifts:")
        for shift in shifts:
            print(f"  • {shift['time']}: {shift['v_shift']:.4f} nT/sec (ΔB={shift['db_nT']:.2f} nT over {shift['dt_sec']:.0f} sec)")
    else:
        print("No significant phase shifts detected (all v_shift < 0.15 nT/sec)")
    
    print()
    print("=" * 70)
    print("To use with your data:")
    print("  1. Prepare JSON file with format: [{'bt_nT': value, 'timestamp': 'ISO8601'}, ...]")
    print("  2. Run: data = load_telemetry_from_json('your_data.json')")
    print("  3. Run: scan_fractal_echo(data)")
    print("  Or load CSV: data = load_telemetry_from_csv('your_data.csv')")
    print("=" * 70)
