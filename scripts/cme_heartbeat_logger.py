#!/usr/bin/env python3
"""
cme_heartbeat_logger.py
=======================
LUFT Automated CME Heartbeat Logger — Logs χ amplitude and 2.4h phase for CME monitoring.

Discovered by Carl Dean Cline Sr., Lincoln, Nebraska
December 2025

This script processes hourly ACE/GOES/SWPC data and logs:
- χ (chi) amplitude estimate
- 2.4-hour phase estimate
- Storm phase tagging ('pre', 'peak', 'post-storm')

Output: cme_heartbeat_log_2025_12.csv

Usage:
    python scripts/cme_heartbeat_logger.py --plasma data/ace_plasma_latest.json --mag data/ace_mag_latest.json
    python scripts/cme_heartbeat_logger.py --demo  # Run with demo data for testing

Contact: CARLDCLINE@GMAIL.COM
Repository: https://github.com/CarlDeanClineSr/luft-portal-
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

# LUFT Constants
CHI_EXPECTED = 0.055  # Expected modulation amplitude
PERIOD_HOURS = 2.4    # Period in hours
PERIOD_SECONDS = PERIOD_HOURS * 3600  # 8640 seconds
OMEGA = 2 * np.pi / PERIOD_SECONDS    # Angular frequency

# Storm phase thresholds (based on Kp/Dst or plasma parameters)
KP_STORM_THRESHOLD = 5.0       # Kp >= 5 indicates storm conditions
DENSITY_STORM_THRESHOLD = 15.0  # p/cm³ - elevated density indicates storm
SPEED_STORM_THRESHOLD = 500.0   # km/s - elevated speed indicates storm
BZ_STORM_THRESHOLD = -10.0      # nT - strongly negative Bz indicates storm


def get_log_filepath():
    """Get the path for the current month's heartbeat log."""
    now = datetime.now(timezone.utc)
    filename = f"cme_heartbeat_log_{now.year}_{now.month:02d}.csv"
    return Path("data") / filename


def load_json_data(filepath):
    """Load JSON data from file."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: File not found: {filepath}")
        return None
    except json.JSONDecodeError as e:
        print(f"Warning: Invalid JSON in {filepath}: {e}")
        return None


def extract_latest_plasma(data):
    """Extract latest plasma measurements from NOAA JSON format."""
    if not data or len(data) < 2:
        return None
    
    # NOAA format: first row is headers, data rows follow
    # Format: [time_tag, density, speed, temperature]
    try:
        latest = data[-1]
        if len(latest) >= 4:
            return {
                'timestamp': latest[0],
                'density': float(latest[1]) if latest[1] else None,
                'speed': float(latest[2]) if latest[2] else None,
                'temperature': float(latest[3]) if latest[3] else None
            }
    except (ValueError, TypeError, IndexError) as e:
        print(f"Warning: Could not parse plasma data: {e}")
    return None


def extract_latest_mag(data):
    """Extract latest magnetic field measurements from NOAA JSON format."""
    if not data or len(data) < 2:
        return None
    
    # NOAA format: [time_tag, bx_gsm, by_gsm, bz_gsm, bt, lat_gsm, lon_gsm]
    try:
        latest = data[-1]
        if len(latest) >= 5:
            return {
                'timestamp': latest[0],
                'bx': float(latest[1]) if latest[1] else None,
                'by': float(latest[2]) if latest[2] else None,
                'bz': float(latest[3]) if latest[3] else None,
                'bt': float(latest[4]) if latest[4] else None
            }
    except (ValueError, TypeError, IndexError) as e:
        print(f"Warning: Could not parse mag data: {e}")
    return None


def estimate_chi_amplitude(density, speed, bt):
    """
    Estimate χ amplitude from solar wind parameters.
    
    Uses a simplified model based on density and speed fluctuations
    relative to baseline values.
    """
    # Baseline values (quiet solar wind)
    baseline_density = 5.0   # p/cm³
    baseline_speed = 400.0   # km/s
    baseline_bt = 5.0        # nT
    
    chi = 0.0
    n_valid = 0
    
    if density is not None and density > 0:
        density_mod = abs(density - baseline_density) / baseline_density
        chi += min(density_mod, 0.3)  # Cap contribution
        n_valid += 1
    
    if speed is not None and speed > 0:
        speed_mod = abs(speed - baseline_speed) / baseline_speed
        chi += min(speed_mod, 0.3)
        n_valid += 1
    
    if bt is not None and bt > 0:
        bt_mod = abs(bt - baseline_bt) / baseline_bt
        chi += min(bt_mod, 0.3)
        n_valid += 1
    
    if n_valid > 0:
        chi = chi / n_valid  # Average modulation
        # Scale to expected range around 0.055
        chi = 0.055 + (chi - 0.1) * 0.5
        chi = max(0.01, min(chi, 0.15))  # Clamp to reasonable range
    else:
        chi = CHI_EXPECTED  # Default if no valid data
    
    return round(chi, 4)


def estimate_phase(timestamp_str):
    """
    Estimate 2.4-hour phase from timestamp.
    
    Phase is computed as the position within the 2.4-hour cycle,
    normalized to [0, 2π].
    """
    try:
        # Parse timestamp
        if 'T' in timestamp_str:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
            dt = dt.replace(tzinfo=timezone.utc)
        
        # Compute seconds since epoch reference
        epoch = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        seconds_since_epoch = (dt - epoch).total_seconds()
        
        # Phase within 2.4-hour cycle
        phase = (seconds_since_epoch % PERIOD_SECONDS) / PERIOD_SECONDS * 2 * np.pi
        return round(phase, 4)
    except Exception as e:
        print(f"Warning: Could not compute phase from timestamp: {e}")
        return 0.0


def classify_storm_phase(density, speed, bz, bt):
    """
    Classify the current storm phase based on solar wind parameters.
    
    Returns: 'pre', 'peak', or 'post-storm'
    """
    storm_indicators = 0
    
    # Check storm indicators
    if density is not None and density > DENSITY_STORM_THRESHOLD:
        storm_indicators += 1
    if speed is not None and speed > SPEED_STORM_THRESHOLD:
        storm_indicators += 1
    if bz is not None and bz < BZ_STORM_THRESHOLD:
        storm_indicators += 2  # Strong Bz is a key indicator
    if bt is not None and bt > 15.0:
        storm_indicators += 1
    
    # Classify based on indicators
    if storm_indicators >= 3:
        return 'peak'
    elif storm_indicators >= 1:
        return 'pre'
    else:
        return 'post-storm'


def initialize_log_file(filepath):
    """Initialize CSV log file with headers if it doesn't exist."""
    if not filepath.exists():
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp_utc',
                'chi_amplitude',
                'phase_radians',
                'storm_phase',
                'density_p_cm3',
                'speed_km_s',
                'bz_nT',
                'bt_nT',
                'source'
            ])
        print(f"Created new log file: {filepath}")


def append_log_entry(filepath, entry):
    """Append a single entry to the CSV log."""
    with open(filepath, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            entry['timestamp_utc'],
            entry['chi_amplitude'],
            entry['phase_radians'],
            entry['storm_phase'],
            entry.get('density', ''),
            entry.get('speed', ''),
            entry.get('bz', ''),
            entry.get('bt', ''),
            entry.get('source', 'ACE/DSCOVR')
        ])


def generate_demo_entry():
    """Generate a demo log entry for testing."""
    now = datetime.now(timezone.utc)
    
    # Simulate solar wind data with some variation
    density = 5.0 + np.random.normal(0, 2)
    speed = 400.0 + np.random.normal(0, 50)
    bz = -2.0 + np.random.normal(0, 3)
    bt = 5.0 + np.random.normal(0, 2)
    
    chi = estimate_chi_amplitude(density, speed, bt)
    phase = estimate_phase(now.isoformat())
    storm_phase = classify_storm_phase(density, speed, bz, bt)
    
    return {
        'timestamp_utc': now.isoformat(),
        'chi_amplitude': chi,
        'phase_radians': phase,
        'storm_phase': storm_phase,
        'density': round(max(0, density), 2),
        'speed': round(max(0, speed), 1),
        'bz': round(bz, 2),
        'bt': round(max(0, bt), 2),
        'source': 'DEMO'
    }


def main():
    parser = argparse.ArgumentParser(
        description="LUFT CME Heartbeat Logger — Log χ amplitude and 2.4h phase for CME monitoring",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/cme_heartbeat_logger.py --plasma data/ace_plasma_latest.json --mag data/ace_mag_latest.json
  python scripts/cme_heartbeat_logger.py --demo

Contact: CARLDCLINE@GMAIL.COM
Repository: https://github.com/CarlDeanClineSr/luft-portal-
        """
    )
    
    parser.add_argument('--plasma', type=str, help='Path to plasma data JSON')
    parser.add_argument('--mag', type=str, help='Path to magnetic field data JSON')
    parser.add_argument('--output', type=str, help='Override output CSV path')
    parser.add_argument('--demo', action='store_true', help='Generate demo entry for testing')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("   LUFT CME HEARTBEAT LOGGER")
    print("   Automated χ amplitude and 2.4h phase logging")
    print("=" * 60)
    print()
    
    # Determine output file
    log_filepath = Path(args.output) if args.output else get_log_filepath()
    
    if args.demo:
        print("Running in DEMO mode...")
        entry = generate_demo_entry()
    else:
        if not args.plasma or not args.mag:
            print("Error: Please provide --plasma and --mag data files, or use --demo")
            sys.exit(1)
        
        # Load data
        print(f"Loading plasma data from: {args.plasma}")
        plasma_data = load_json_data(args.plasma)
        
        print(f"Loading magnetic data from: {args.mag}")
        mag_data = load_json_data(args.mag)
        
        # Extract latest values
        plasma = extract_latest_plasma(plasma_data)
        mag = extract_latest_mag(mag_data)
        
        if not plasma and not mag:
            print("Error: Could not extract any valid data from input files")
            sys.exit(1)
        
        # Get timestamp
        timestamp = (plasma or mag).get('timestamp', datetime.now(timezone.utc).isoformat())
        
        # Extract values
        density = plasma.get('density') if plasma else None
        speed = plasma.get('speed') if plasma else None
        bz = mag.get('bz') if mag else None
        bt = mag.get('bt') if mag else None
        
        # Compute LUFT parameters
        chi = estimate_chi_amplitude(density, speed, bt)
        phase = estimate_phase(timestamp)
        storm_phase = classify_storm_phase(density, speed, bz, bt)
        
        entry = {
            'timestamp_utc': timestamp,
            'chi_amplitude': chi,
            'phase_radians': phase,
            'storm_phase': storm_phase,
            'density': round(density, 2) if density else '',
            'speed': round(speed, 1) if speed else '',
            'bz': round(bz, 2) if bz else '',
            'bt': round(bt, 2) if bt else '',
            'source': 'ACE/DSCOVR'
        }
    
    # Initialize log file if needed
    initialize_log_file(log_filepath)
    
    # Append entry
    append_log_entry(log_filepath, entry)
    
    # Report
    print()
    print("Entry logged successfully!")
    print(f"  Timestamp: {entry['timestamp_utc']}")
    print(f"  χ amplitude: {entry['chi_amplitude']}")
    print(f"  Phase (rad): {entry['phase_radians']}")
    print(f"  Storm phase: {entry['storm_phase']}")
    print(f"  Output file: {log_filepath}")
    print()
    print("=" * 60)
    print("LUFT Heartbeat Logger complete.")
    print("Contact: CARLDCLINE@GMAIL.COM")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
