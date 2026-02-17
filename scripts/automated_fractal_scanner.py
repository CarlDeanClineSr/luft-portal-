#!/usr/bin/env python3
"""
Fractal Echo Scanner - Automated Runner

This script is designed to be run by GitHub Actions every 15 minutes.
It fetches the latest magnetometer data and runs the Fractal Echo Scanner.

Author: Carl Dean Cline Sr.
Date: 2026-01-23
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fractal_echo_scanner import (
    scan_fractal_echo,
    audit_phase_derivative,
    load_telemetry_from_csv
)


def get_latest_data(hours_back=24):
    """
    Load the most recent magnetometer data.
    
    Args:
        hours_back: How many hours of recent data to analyze
        
    Returns:
        List of telemetry data points
    """
    data_file = Path(__file__).parent.parent / "data" / "cme_heartbeat_log_2026_01.csv"
    
    if not data_file.exists():
        print(f"⚠️ Primary data file not found: {data_file}")
        return []
    
    print(f"📂 Loading data from: {data_file.name}")
    all_data = load_telemetry_from_csv(data_file)
    
    if not all_data:
        return []
    
    # Filter to recent data
    cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
    
    recent_data = []
    for d in all_data:
        if 'timestamp' in d:
            try:
                ts_str = d['timestamp'].replace(' ', 'T').replace('Z', '')
                # Parse as naive datetime (UTC assumed from data source)
                ts = datetime.fromisoformat(ts_str)
                if ts >= cutoff_time:
                    recent_data.append(d)
            except (ValueError, AttributeError):
                continue
    
    if recent_data:
        print(f"✅ Loaded {len(recent_data)} recent data points (last {hours_back} hours)")
        return recent_data
    else:
        print(f"⚠️ No recent data found in last {hours_back} hours, using all available")
        return all_data[-100:] if len(all_data) > 100 else all_data


def save_scan_result(result, output_dir="data/fractal_echo_scans"):
    """
    Save scan results to JSON file.
    
    Args:
        result: Dictionary containing scan results
        output_dir: Directory to save results
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    result_file = output_path / f"scan_result_{timestamp}.json"
    
    with open(result_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"💾 Results saved to: {result_file}")
    
    # Update latest result symlink/reference
    latest_file = output_path / "latest_result.json"
    with open(latest_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    return result_file


def main():
    """Main execution function for automated scanner."""
    
    print("=" * 80)
    print("FRACTAL ECHO SCANNER - AUTOMATED RUN")
    print(f"Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("=" * 80)
    print()
    
    # Get latest data
    data = get_latest_data(hours_back=48)  # Last 48 hours
    
    if not data:
        print("❌ No data available for scanning")
        return 1
    
    # Run the scan
    print()
    print("=" * 80)
    print("INITIATING FRACTAL ECHO SCAN")
    print("=" * 80)
    
    result = scan_fractal_echo(data, target_frequency=20.55, amplitude_threshold=0.01)
    
    print()
    print("=" * 80)
    print("SCAN RESULTS SUMMARY")
    print("=" * 80)
    
    if result['echo_detected']:
        print("✓ FRACTAL ECHO DETECTED!")
        print()
        for detection in result['detections']:
            print(f"  • Frequency: {detection['frequency_hz']:.2f} Hz")
            print(f"    Amplitude: {detection['amplitude']:.4f}")
            print(f"    Deviation: {detection['deviation_from_target']:.4f} Hz")
        print()
        print("⚠️ ALERT: Lattice vibration signature found!")
        print("   Recommend immediate cross-reference with:")
        print("   - Starlink fleet magnetometer data")
        print("   - Ground VLF station records")
        print("   - MMS/THEMIS burst mode telemetry")
    else:
        print("✗ No Fractal Echo detected")
        print(f"   Sample rate: {result['sample_rate_hz']:.6f} Hz")
        print(f"   Nyquist frequency: {result['sample_rate_hz']/2:.6f} Hz")
        print(f"   Target frequency: {result['target_frequency']:.2f} Hz")
        print()
        print("   Status: Boundary in steady-state")
        print("   Note: 20.55 Hz detection requires sub-second sampling")
    
    # Add metadata
    result['scan_timestamp'] = datetime.utcnow().isoformat() + 'Z'
    result['data_points_analyzed'] = len(data)
    result['data_time_range'] = {
        'first': data[0].get('timestamp', 'unknown') if data else None,
        'last': data[-1].get('timestamp', 'unknown') if data else None
    }
    
    # Save results
    print()
    save_scan_result(result)
    
    # Phase derivative analysis
    print()
    print("=" * 80)
    print("PHASE DERIVATIVE ANALYSIS")
    print("=" * 80)
    
    timestamps = []
    bt_values = []
    
    for d in data:
        if 'timestamp' in d and 'bt_nT' in d:
            try:
                ts_str = d['timestamp'].replace(' ', 'T').replace('Z', '')
                # Parse as naive datetime (UTC assumed)
                ts = datetime.fromisoformat(ts_str)
                timestamps.append(ts)
                bt_values.append(d['bt_nT'])
            except (ValueError, AttributeError):
                continue
    
    if timestamps and bt_values:
        shifts = audit_phase_derivative(bt_values, timestamps)
        
        if shifts:
            print(f"✓ Detected {len(shifts)} significant coordinate shifts:")
            for shift in shifts[:5]:  # Show first 5
                print(f"  • {shift['time']}: v_shift={shift['v_shift']:.4f} nT/sec")
        else:
            print("  No significant phase shifts detected (v < 0.15 nT/sec)")
            print("  Vacuum pressure changing smoothly")
    
    print()
    print("=" * 80)
    print("NEXT SCAN: ~15 minutes")
    print("=" * 80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
