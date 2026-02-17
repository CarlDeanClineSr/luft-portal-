#!/usr/bin/env python3
"""
Chi Boundary Monitor Script
===========================

This script is called by the GitHub Actions workflow to process
real-time space weather data and validate the χ ≤ 0.15 boundary.

It reads DSCOVR/ACE magnetometer data and generates validation reports.
"""

import json
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys

# Import our boundary engine
sys.path.insert(0, '.')
from universal_boundary_engine import (
    calculate_chi, 
    validate_boundary, 
    detect_harmonic_mode,
    CHI_UNIVERSAL
)

def main():
    """Main monitoring function."""
    print("=" * 80)
    print("CHI BOUNDARY MONITOR - Real-time Validation")
    print("=" * 80)
    
    # Load DSCOVR magnetic field data
    mag_file = Path('data/chi_monitor/dscovr_mag_latest.json')
    if not mag_file.exists():
        print(f"⚠️  Mag file not found: {mag_file}")
        return 1
    
    print(f"\n📂 Loading: {mag_file}")
    try:
        with open(mag_file, 'r') as f:
            mag_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ ERROR: Failed to parse JSON from {mag_file}")
        print(f"   JSON error: {e}")
        print(f"   The file may be corrupted or contain invalid data.")
        print(f"   This usually happens when the NOAA API returns an error page instead of JSON.")
        print(f"   Please try running the workflow again, or check the NOAA API status.")
        return 1
    except Exception as e:
        print(f"❌ ERROR: Unexpected error reading {mag_file}: {e}")
        return 1
    
    # Skip header row and convert to DataFrame
    if len(mag_data) <= 1:
        print("⚠️  No data rows in mag file")
        return 1
    
    df = pd.DataFrame(mag_data[1:], columns=mag_data[0])
    
    # Convert to numeric
    df['bx_gsm'] = pd.to_numeric(df['bx_gsm'], errors='coerce')
    df['by_gsm'] = pd.to_numeric(df['by_gsm'], errors='coerce')
    df['bz_gsm'] = pd.to_numeric(df['bz_gsm'], errors='coerce')
    
    # Remove null values
    df = df.dropna(subset=['bx_gsm', 'by_gsm', 'bz_gsm'])
    
    if len(df) <= 10:
        print(f"⚠️  Insufficient valid data points: {len(df)}")
        return 1
    
    print(f"✅ Loaded {len(df)} valid data points")
    
    # Calculate magnetic field magnitude
    B = np.sqrt(df['bx_gsm']**2 + df['by_gsm']**2 + df['bz_gsm']**2)
    
    # Calculate χ
    print("\n🔬 Computing χ = |B - B_baseline| / B_baseline...")
    chi = calculate_chi(B.values)
    
    # Validate boundary
    print("\n📊 Validating Universal Boundary (χ ≤ 0.15)...")
    validation = validate_boundary(chi)
    
    # Detect harmonic mode
    harmonic = detect_harmonic_mode(chi)
    
    # Print results
    print("\n" + "=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)
    print(f"Data Points: {validation['total_points']:,}")
    print(f"Maximum χ: {validation['max_chi']:.6f}")
    print(f"Mean χ: {validation['mean_chi']:.6f}")
    print(f"Median χ: {validation['median_chi']:.6f}")
    print("-" * 80)
    
    # Boundary compliance
    if validation['compliance']:
        print(f"✅ BOUNDARY CONFIRMED: χ ≤ {CHI_UNIVERSAL}")
        print(f"   Violations: {validation['violations']}")
    else:
        print(f"❌ BOUNDARY VIOLATION DETECTED!")
        print(f"   Violations: {validation['violations']}")
        print(f"   Max χ: {validation['max_chi']:.6f}")
    
    # Attractor state
    print(f"\n🎯 Attractor State:")
    print(f"   Points at boundary: {validation['attractor_count']:,}")
    print(f"   Percentage: {validation['attractor_percentage']:.1f}%")
    if validation['attractor_percentage'] > 40:
        print(f"   ✅ Attractor confirmed (>40%)")
    
    # Harmonic mode
    print(f"\n🔊 Harmonic Mode:")
    if harmonic['is_harmonic'] and harmonic['harmonic_mode'] > 1:
        print(f"   ⚠️  HARMONIC TRANSITION DETECTED")
        print(f"   Mode: n = {harmonic['harmonic_mode']}")
        print(f"   χ_theoretical: {harmonic['theoretical_chi']:.3f}")
    else:
        print(f"   Operating at fundamental (n=1)")
    
    print("=" * 80)
    
    # Save validation log
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'source': 'DSCOVR',
        'data_points': int(validation['total_points']),
        'max_chi': float(validation['max_chi']),
        'mean_chi': float(validation['mean_chi']),
        'violations': int(validation['violations']),
        'attractor_percentage': float(validation['attractor_percentage']),
        'compliance': bool(validation['compliance']),
        'harmonic_mode': int(harmonic['harmonic_mode']),
        'is_harmonic_transition': bool(harmonic['is_harmonic'] and harmonic['harmonic_mode'] > 1)
    }
    
    # Append to log file
    log_file = Path('data/chi_monitor/chi_validation_log.jsonl')
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
    
    print(f"\n💾 Log saved to: {log_file}")
    
    # Save latest validation
    latest_file = Path('data/chi_monitor/chi_latest_validation.json')
    with open(latest_file, 'w') as f:
        json.dump(log_entry, f, indent=2)
    
    print(f"💾 Latest validation saved to: {latest_file}")
    print("\n✅ Chi calculation complete")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
