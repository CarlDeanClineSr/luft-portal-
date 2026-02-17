#!/usr/bin/env python3
"""
normalize_audit.py
Converts raw ACE audit JSON arrays to normalized JSON objects with named fields.
Preserves original raw data in 'original_row' field for provenance.

Usage:
    python3 scripts/normalize_audit.py

Inputs:
    data/ace_plasma_audit.json (raw array format)
    data/ace_mag_audit.json (raw array format)

Outputs:
    data/ace_plasma_audit_normalized.json (normalized object format)
    data/ace_mag_audit_normalized.json (normalized object format)
"""
import json
from pathlib import Path

DATA = Path('data')

# Input files (raw arrays)
PLASMA_IN = DATA / 'ace_plasma_audit.json'
MAG_IN = DATA / 'ace_mag_audit.json'

# Output files (normalized objects)
PLASMA_OUT = DATA / 'ace_plasma_audit_normalized.json'
MAG_OUT = DATA / 'ace_mag_audit_normalized.json'


def load_json(p):
    """Load JSON from file."""
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(p, obj):
    """Save JSON to file with pretty formatting."""
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def normalize_plasma(raw_array):
    """
    Convert raw plasma array to normalized object.
    Expected format: [timestamp, density, speed, temperature]
    """
    if len(raw_array) < 4:
        print(f"Warning: plasma array has {len(raw_array)} elements, expected 4")
        # Pad with None if needed
        while len(raw_array) < 4:
            raw_array.append(None)
    
    normalized = {
        'timestamp_utc': raw_array[0],
        'density_p_cm3': float(raw_array[1]) if raw_array[1] is not None else None,
        'speed_km_s': float(raw_array[2]) if raw_array[2] is not None else None,
        'temperature_k': float(raw_array[3]) if raw_array[3] is not None else None,
        'original_row': raw_array  # Preserve original data for provenance
    }
    return normalized


def normalize_mag(raw_array):
    """
    Convert raw magnetometer array to normalized object.
    Expected format: [timestamp, Bx_GSE, By_GSE, Bz_GSE, Bt, lat, lon]
    Note: Some mag fields may be anomalous but are preserved unchanged.
    """
    if len(raw_array) < 7:
        print(f"Warning: mag array has {len(raw_array)} elements, expected 7")
        # Pad with None if needed
        while len(raw_array) < 7:
            raw_array.append(None)
    
    normalized = {
        'timestamp_utc': raw_array[0],
        'Bx_GSE_nT': float(raw_array[1]) if raw_array[1] is not None else None,
        'By_GSE_nT': float(raw_array[2]) if raw_array[2] is not None else None,
        'Bz_GSE_nT': float(raw_array[3]) if raw_array[3] is not None else None,
        'Bt_nT': float(raw_array[4]) if raw_array[4] is not None else None,
        'lat_deg': float(raw_array[5]) if raw_array[5] is not None else None,
        'lon_deg': float(raw_array[6]) if raw_array[6] is not None else None,
        'original_row': raw_array,  # Preserve original data for provenance
        'anomaly_flag': 'preserved_unchanged'  # Flag for anomalous mag fields
    }
    return normalized


def main():
    """Main normalization pipeline."""
    print("Starting ACE audit normalization...")
    
    # Process plasma data
    if PLASMA_IN.exists():
        print(f"\nProcessing {PLASMA_IN}...")
        raw_plasma = load_json(PLASMA_IN)
        
        # Handle both single record and array of records
        if isinstance(raw_plasma[0], list):
            # Multiple records
            normalized_plasma = [normalize_plasma(rec) for rec in raw_plasma]
        else:
            # Single record
            normalized_plasma = [normalize_plasma(raw_plasma)]
        
        save_json(PLASMA_OUT, normalized_plasma)
        print(f"✓ Wrote {len(normalized_plasma)} normalized plasma record(s) to {PLASMA_OUT}")
    else:
        print(f"⚠ Warning: {PLASMA_IN} not found, skipping plasma normalization")
    
    # Process magnetometer data
    if MAG_IN.exists():
        print(f"\nProcessing {MAG_IN}...")
        raw_mag = load_json(MAG_IN)
        
        # Handle both single record and array of records
        if isinstance(raw_mag[0], list):
            # Multiple records
            normalized_mag = [normalize_mag(rec) for rec in raw_mag]
        else:
            # Single record
            normalized_mag = [normalize_mag(raw_mag)]
        
        save_json(MAG_OUT, normalized_mag)
        print(f"✓ Wrote {len(normalized_mag)} normalized mag record(s) to {MAG_OUT}")
        print(f"  Note: Anomalous mag fields preserved unchanged with 'anomaly_flag' marker")
    else:
        print(f"⚠ Warning: {MAG_IN} not found, skipping mag normalization")
    
    print("\n✓ Normalization complete!")
    print("\nNext steps:")
    print("  1. Run: python3 scripts/compute_pdyn_chi.py")
    print("  2. Run: python3 scripts/make_example_chart.py")
    print("  3. Run: python3 scripts/save_cycle_charts.py --cycle 1")
    print("  4. Run: python3 scripts/create_gif_luft.py")


if __name__ == '__main__':
    main()
