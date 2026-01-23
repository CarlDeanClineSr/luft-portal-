#!/usr/bin/env python3
"""
LUFT Data Transcription Example
================================

This script demonstrates the proper usage of LUFT Imperial Constants
and data transcription standards as defined in:
    LUFT_DATA_TRANSCRIPTION_MASTER_REFERENCE.md

Author: Carl Dean Cline Sr.
Date: 2026-01-23
License: CC BY 4.0
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import imperial_constants
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import LUFT Imperial Constants
try:
    from imperial_constants_v1_0 import (
        CHI_LIMIT, COUPLING_FREQ_HZ, GRAVITY_INVERSE, MASS_RATIO_ROOT,
        STATUS_BOUNDARY, STATUS_COMPLIANT, STATUS_RECOVERY,
        validate_chi, get_fundamental_unifications, format_timestamp_iso8601
    )
except ImportError as e:
    print(f"Error: Cannot import imperial_constants_v1_0.py: {e}")
    print("Make sure the file is in the parent directory")
    sys.exit(1)


def example_1_validate_event():
    """
    Example 1: Validate χ measurements from January 5, 2026 event
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Event Validation")
    print("=" * 70)
    
    # Event data from January 5, 2026 (solar wind compression)
    events = [
        {"time": "2026-01-05T00:41:00.000Z", "chi": 0.1284, "b": 7.28},
        {"time": "2026-01-05T00:45:00.000Z", "chi": 0.1498, "b": 8.12},
        {"time": "2026-01-05T01:00:00.000Z", "chi": 0.1389, "b": 7.54},
        {"time": "2026-01-05T01:13:00.000Z", "chi": 0.0917, "b": 6.47},
    ]
    
    print("\nLUFT Boundary Validation Report")
    print("-" * 70)
    
    violations = 0
    for event in events:
        result = validate_chi(event["chi"], event["time"])
        status_symbol = "✅" if result['compliant'] else "❌"
        
        print(f"{status_symbol} {result['timestamp']}: χ={result['chi_observed']:.4f}, "
              f"B={event['b']:.2f} nT → {result['status']}")
        
        if not result['compliant']:
            violations += 1
    
    print("-" * 70)
    print(f"Total Events: {len(events)}")
    print(f"Violations: {violations}")
    print(f"Compliance: {'✅ PASSED' if violations == 0 else '❌ FAILED'}")


def example_2_fundamental_constants():
    """
    Example 2: Display fundamental constants and unifications
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Fundamental Constants")
    print("=" * 70)
    
    print("\n🔬 CORE IMPERIAL METRICS:")
    print(f"   Universal Boundary (χ)      = {CHI_LIMIT}")
    print(f"   Coupling Frequency (Λ)      = {COUPLING_FREQ_HZ:.4f} Hz")
    print(f"   Gravity Relation (1/χ)      = {GRAVITY_INVERSE:.4f}")
    print(f"   Mass Ratio Root             = {MASS_RATIO_ROOT}")
    
    print("\n🌌 FUNDAMENTAL UNIFICATIONS:")
    unif = get_fundamental_unifications()
    
    print(f"   Gravity Synthesis:")
    print(f"      Formula: {unif['gravity']['formula']}")
    print(f"      Derived G: {unif['gravity']['derived_G']:.5e} m³/(kg·s²)")
    print(f"      Error: {unif['gravity']['error_percent']:.3f}%")
    
    print(f"   Mass Ratio Unification:")
    print(f"      Formula: {unif['mass_ratio']['formula']}")
    print(f"      χ from mass: {unif['mass_ratio']['chi_from_mass']:.6f}")
    print(f"      Error: {unif['mass_ratio']['error_percent']:.3f}%")
    
    print(f"   Coupling Frequency:")
    print(f"      Formula: {unif['coupling']['formula']}")
    print(f"      Frequency: {unif['coupling']['frequency_hz']:.4f} Hz")
    print(f"      Application: {unif['coupling']['application']}")


def example_3_csv_export():
    """
    Example 3: Export data in CSV format
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 3: CSV Export")
    print("=" * 70)
    
    # Sample data
    data = [
        ["2026-01-05T00:41:00.000", 0.1284, 7.28, 531.4, 1.63, "BELOW_LIMIT", "GOOD", "Peak pre-event"],
        ["2026-01-05T00:45:00.000", 0.1498, 8.12, 567.9, 1.89, "AT_BOUNDARY", "GOOD", "System engaged limit"],
        ["2026-01-05T01:00:00.000", 0.1389, 7.54, 542.1, 1.71, "RECOVERY", "GOOD", "Elastic rebound initiated"],
        ["2026-01-05T01:13:00.000", 0.0917, 6.47, 498.6, 1.29, "BELOW_LIMIT", "GOOD", "Full recovery"],
    ]
    
    # Create CSV content
    csv_content = "Timestamp_UTC,Chi_Value,B_Total_nT,Speed_km_s,Density_p_cm3,Status,Quality_Flag,Notes\n"
    for row in data:
        csv_content += ",".join(str(x) for x in row) + "\n"
    
    # Write to file
    output_file = Path("/tmp/luft_chi_log_example.csv")
    output_file.write_text(csv_content)
    
    print(f"\n✅ CSV file created: {output_file}")
    print(f"   Rows: {len(data)}")
    print(f"   Format: Standard LUFT CSV (timestamps with .000 precision)")


def example_4_json_export():
    """
    Example 4: Export data in JSON format
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 4: JSON Export")
    print("=" * 70)
    
    # Create JSON structure following LUFT standard
    event_data = {
        "event_metadata": {
            "date": "2026-01-05",
            "observer": "Carl Dean Cline Sr.",
            "location": "Lincoln, Nebraska",
            "data_sources": ["DSCOVR", "ACE"],
            "chi_limit": CHI_LIMIT,
            "violations": 0
        },
        "observations": [
            {
                "timestamp": "2026-01-05T00:41:00.000Z",
                "chi": 0.1284,
                "b_total_nt": 7.28,
                "speed_km_s": 531.4,
                "density_p_cm3": 1.63,
                "status": "BELOW_LIMIT"
            },
            {
                "timestamp": "2026-01-05T00:45:00.000Z",
                "chi": 0.1498,
                "b_total_nt": 8.12,
                "speed_km_s": 567.9,
                "density_p_cm3": 1.89,
                "status": "AT_BOUNDARY"
            },
            {
                "timestamp": "2026-01-05T01:00:00.000Z",
                "chi": 0.1389,
                "b_total_nt": 7.54,
                "speed_km_s": 542.1,
                "density_p_cm3": 1.71,
                "status": "RECOVERY"
            },
            {
                "timestamp": "2026-01-05T01:13:00.000Z",
                "chi": 0.0917,
                "b_total_nt": 6.47,
                "speed_km_s": 498.6,
                "density_p_cm3": 1.29,
                "status": "BELOW_LIMIT"
            }
        ],
        "summary": {
            "duration_minutes": 32,
            "peak_chi": 0.1498,
            "max_field_nt": 8.12,
            "recovery_time_minutes": 28
        }
    }
    
    # Write to file
    output_file = Path("/tmp/luft_event_example.json")
    with open(output_file, 'w') as f:
        json.dump(event_data, f, indent=2)
    
    print(f"\n✅ JSON file created: {output_file}")
    print(f"   Observations: {len(event_data['observations'])}")
    print(f"   Format: Standard LUFT JSON (API/machine readable)")


def example_5_timestamp_formatting():
    """
    Example 5: Proper timestamp formatting
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Timestamp Formatting")
    print("=" * 70)
    
    # Current time
    now = datetime.now()
    
    # Format according to LUFT standard
    iso_timestamp = format_timestamp_iso8601(now)
    
    print(f"\n📅 Current UTC Time:")
    print(f"   Python datetime: {now}")
    print(f"   ISO 8601 format: {iso_timestamp}")
    print(f"\n✅ Note: Timestamps include .000 for millisecond precision")
    print(f"   This ensures zero precision loss across all platforms")


def main():
    """
    Main function - runs all examples
    """
    print("\n" + "=" * 70)
    print("LUFT DATA TRANSCRIPTION EXAMPLES")
    print("Version 1.0 - January 23, 2026")
    print("Author: Carl Dean Cline Sr.")
    print("=" * 70)
    print("\nThis script demonstrates proper usage of LUFT Imperial Constants")
    print("and data transcription standards.")
    
    # Run all examples
    example_1_validate_event()
    example_2_fundamental_constants()
    example_3_csv_export()
    example_4_json_export()
    example_5_timestamp_formatting()
    
    print("\n" + "=" * 70)
    print("ALL EXAMPLES COMPLETED")
    print("=" * 70)
    print("\nReference Documents:")
    print("   - LUFT_DATA_TRANSCRIPTION_MASTER_REFERENCE.md")
    print("   - imperial_constants_v1_0.py")
    print("\nOutput Files Created:")
    print("   - /tmp/luft_chi_log_example.csv")
    print("   - /tmp/luft_event_example.json")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
