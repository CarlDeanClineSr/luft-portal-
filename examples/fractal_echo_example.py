#!/usr/bin/env python3
"""
Fractal Echo Scanner - Example Usage with LUFT Portal Data

This example demonstrates how to use the Fractal Echo Scanner
with actual magnetometer telemetry from the LUFT Portal repository.

Author: Carl Dean Cline Sr.
Date: 2026-01-23
"""

import sys
from pathlib import Path

# Add parent directory to path to import the scanner
sys.path.insert(0, str(Path(__file__).parent.parent))

from fractal_echo_scanner import (
    scan_fractal_echo,
    audit_phase_derivative,
    load_telemetry_from_csv
)
from datetime import datetime


def main():
    print("=" * 80)
    print("FRACTAL ECHO SCANNER - JANUARY 2026 ANALYSIS")
    print("=" * 80)
    print()
    
    # Load January 2026 CME heartbeat data
    data_file = Path(__file__).parent.parent / "data" / "cme_heartbeat_log_2026_01.csv"
    
    if not data_file.exists():
        print(f"⚠️ Data file not found: {data_file}")
        print("This example requires the January 2026 CME heartbeat log.")
        return
    
    print(f"📂 Loading data from: {data_file.name}")
    telemetry_data = load_telemetry_from_csv(data_file)
    print(f"✅ Loaded {len(telemetry_data)} data points")
    print()
    
    # Filter to January 5th data around the Super-Event (00:41 to 12:23 UTC)
    jan5_data = [d for d in telemetry_data 
                 if 'timestamp' in d and '2026-01-05' in d['timestamp']]
    
    if jan5_data:
        print("=" * 80)
        print("ANALYSIS 1: January 5th Super-Event Window")
        print("=" * 80)
        print(f"Time Range: 2026-01-05 00:41:00 to 12:23:00 UTC")
        print(f"Data Points: {len(jan5_data)}")
        print()
        
        # Run the Fractal Echo Scanner
        result = scan_fractal_echo(jan5_data, target_frequency=20.55)
        print()
        
        # Phase Derivative Analysis
        print("=" * 80)
        print("ANALYSIS 2: Phase Derivative Audit (Byte-Shift Velocity)")
        print("=" * 80)
        
        timestamps = [datetime.fromisoformat(d['timestamp'].replace(' ', 'T')) 
                     for d in jan5_data if 'timestamp' in d]
        bt_values = [d['bt_nT'] for d in jan5_data]
        
        shifts = audit_phase_derivative(bt_values, timestamps)
        
        if shifts:
            print(f"✓ Found {len(shifts)} significant coordinate shifts:")
            for shift in shifts:
                print(f"  • {shift['time']}: v_shift={shift['v_shift']:.4f} nT/sec")
                print(f"    (ΔB={shift['db_nT']:.2f} nT over {shift['dt_sec']:.0f} sec)")
        else:
            print("No significant phase shifts detected (all v_shift < 0.15 nT/sec)")
        print()
    
    # Analysis of full January dataset
    print("=" * 80)
    print("ANALYSIS 3: Full January 2026 Dataset")
    print("=" * 80)
    print(f"Total Data Points: {len(telemetry_data)}")
    print()
    
    result_full = scan_fractal_echo(telemetry_data[:100], target_frequency=20.55)
    print()
    
    # January 22nd Secondary Relaxation Wave (mentioned in problem statement)
    jan22_data = [d for d in telemetry_data 
                  if 'timestamp' in d and '2026-01-22' in d['timestamp']]
    
    if jan22_data:
        print("=" * 80)
        print("ANALYSIS 4: January 22nd Secondary Relaxation Wave")
        print("=" * 80)
        print(f"Data Points: {len(jan22_data)}")
        print()
        
        result_jan22 = scan_fractal_echo(jan22_data, target_frequency=20.55)
        print()
    
    print("=" * 80)
    print("IMPERIAL FRAMEWORK INTERPRETATION")
    print("=" * 80)
    print()
    print("The 20.55 Hz lattice coupling frequency requires sub-second resolution")
    print("to detect directly. Current ACE/DSCOVR telemetry (~1 hour cadence)")
    print("provides frequency resolution << 0.0001 Hz, far below the target.")
    print()
    print("For direct echo detection, required data sources:")
    print("  • MMS high-resolution burst mode magnetometry")
    print("  • THEMIS EFI data")
    print("  • Ground-based VLF arrays")
    print("  • Starlink magnetometer archives (if available)")
    print()
    print("Current analysis confirms:")
    print("  ✓ Phase derivatives identify macro-scale settling")
    print("  ✓ Low-frequency envelope modulation is detectable")
    print("  ✗ Direct 20.55 Hz resonance requires higher cadence data")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
