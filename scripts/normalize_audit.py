#!/usr/bin/env python3
"""
normalize_audit.py
==================
Normalize ACE audit data from raw array format to structured JSON with provenance.

Converts:
- data/ace_plasma_audit.json (array format) -> data/ace_plasma_audit_normalized.json
- data/ace_mag_audit.json (array format) -> data/ace_mag_audit_normalized.json

The normalized files preserve original data in 'original_row' fields for provenance.
Anomalous or missing values are flagged but left unchanged.

Usage:
    python3 scripts/normalize_audit.py

Author: Carl Dean Cline Sr.
Repository: https://github.com/CarlDeanClineSr/luft-portal-
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_json(filepath: Path) -> Any:
    """Load JSON from file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(filepath: Path, data: Any) -> None:
    """Save data to JSON file with pretty formatting."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Wrote {filepath}")


def normalize_plasma_row(row: List[str]) -> Dict[str, Any]:
    """
    Normalize a plasma audit row from array format to structured object.
    
    Expected format: [timestamp, density, speed, temperature]
    
    Args:
        row: List of string values [timestamp, density, speed, temperature]
    
    Returns:
        Dictionary with normalized fields and original_row for provenance
    """
    if len(row) < 4:
        return {
            'error': 'Invalid row length',
            'original_row': row
        }
    
    timestamp_str = row[0]
    density_str = row[1]
    speed_str = row[2]
    temp_str = row[3]
    
    # Parse values, marking anomalies
    normalized = {
        'timestamp_utc': timestamp_str,
        'original_row': row  # Preserve provenance
    }
    
    # Parse density
    try:
        density = float(density_str)
        normalized['density_p_cm3'] = density
        # Flag anomalous values (negative or extremely high)
        if density < 0 or density > 1000:
            normalized['density_anomaly'] = True
    except (ValueError, TypeError):
        normalized['density_p_cm3'] = None
        normalized['density_anomaly'] = True
    
    # Parse speed
    try:
        speed = float(speed_str)
        normalized['speed_km_s'] = speed
        # Flag anomalous values
        if speed < 0 or speed > 3000:
            normalized['speed_anomaly'] = True
    except (ValueError, TypeError):
        normalized['speed_km_s'] = None
        normalized['speed_anomaly'] = True
    
    # Parse temperature
    try:
        temp = float(temp_str)
        normalized['temperature_K'] = temp
        # Flag anomalous values
        if temp < 0 or temp > 1e7:
            normalized['temperature_anomaly'] = True
    except (ValueError, TypeError):
        normalized['temperature_K'] = None
        normalized['temperature_anomaly'] = True
    
    return normalized


def normalize_mag_row(row: List[str]) -> Dict[str, Any]:
    """
    Normalize a magnetometer audit row from array format to structured object.
    
    Expected format: [timestamp, bx, by, bz, bt, lat, lon]
    
    Args:
        row: List of string values [timestamp, bx, by, bz, bt, lat, lon]
    
    Returns:
        Dictionary with normalized fields and original_row for provenance
    """
    if len(row) < 7:
        return {
            'error': 'Invalid row length',
            'original_row': row
        }
    
    timestamp_str = row[0]
    bx_str = row[1]
    by_str = row[2]
    bz_str = row[3]
    bt_str = row[4]
    lat_str = row[5]
    lon_str = row[6]
    
    normalized = {
        'timestamp_utc': timestamp_str,
        'original_row': row  # Preserve provenance
    }
    
    # Parse magnetic field components
    for field_name, field_str, key in [
        ('Bx', bx_str, 'bx_nT'),
        ('By', by_str, 'by_nT'),
        ('Bz', bz_str, 'bz_nT'),
        ('Bt', bt_str, 'bt_nT')
    ]:
        try:
            value = float(field_str)
            normalized[key] = value
            # Flag anomalous values (extremely high magnetic field)
            if abs(value) > 1000:
                normalized[f'{key.split("_")[0]}_anomaly'] = True
        except (ValueError, TypeError):
            normalized[key] = None
            normalized[f'{key.split("_")[0]}_anomaly'] = True
    
    # Parse lat/lon
    try:
        lat = float(lat_str)
        normalized['latitude_deg'] = lat
        if abs(lat) > 90:
            normalized['latitude_anomaly'] = True
    except (ValueError, TypeError):
        normalized['latitude_deg'] = None
        normalized['latitude_anomaly'] = True
    
    try:
        lon = float(lon_str)
        normalized['longitude_deg'] = lon
        if abs(lon) > 360:
            normalized['longitude_anomaly'] = True
    except (ValueError, TypeError):
        normalized['longitude_deg'] = None
        normalized['longitude_anomaly'] = True
    
    return normalized


def normalize_plasma_audit(input_path: Path, output_path: Path) -> None:
    """
    Normalize plasma audit file.
    
    Args:
        input_path: Path to raw plasma audit JSON (array format)
        output_path: Path to write normalized JSON
    """
    print(f"Normalizing plasma audit: {input_path}")
    
    raw_data = load_json(input_path)
    
    # Handle both single row and list of rows
    if isinstance(raw_data, list) and len(raw_data) > 0 and isinstance(raw_data[0], str):
        # Single row case
        normalized = [normalize_plasma_row(raw_data)]
    elif isinstance(raw_data, list):
        # Multiple rows case
        normalized = [normalize_plasma_row(row) for row in raw_data]
    else:
        print(f"ERROR: Unexpected data format in {input_path}")
        sys.exit(1)
    
    save_json(output_path, normalized)
    print(f"Normalized {len(normalized)} plasma record(s)")


def normalize_mag_audit(input_path: Path, output_path: Path) -> None:
    """
    Normalize magnetometer audit file.
    
    Args:
        input_path: Path to raw mag audit JSON (array format)
        output_path: Path to write normalized JSON
    """
    print(f"Normalizing magnetometer audit: {input_path}")
    
    raw_data = load_json(input_path)
    
    # Handle both single row and list of rows
    if isinstance(raw_data, list) and len(raw_data) > 0 and isinstance(raw_data[0], str):
        # Single row case
        normalized = [normalize_mag_row(raw_data)]
    elif isinstance(raw_data, list):
        # Multiple rows case
        normalized = [normalize_mag_row(row) for row in raw_data]
    else:
        print(f"ERROR: Unexpected data format in {input_path}")
        sys.exit(1)
    
    save_json(output_path, normalized)
    print(f"Normalized {len(normalized)} magnetometer record(s)")


def main():
    """Main entry point for normalization script."""
    data_dir = Path('data')
    
    # Define input and output paths
    plasma_in = data_dir / 'ace_plasma_audit.json'
    plasma_out = data_dir / 'ace_plasma_audit_normalized.json'
    
    mag_in = data_dir / 'ace_mag_audit.json'
    mag_out = data_dir / 'ace_mag_audit_normalized.json'
    
    # Check inputs exist
    if not plasma_in.exists():
        print(f"ERROR: Input file not found: {plasma_in}")
        sys.exit(1)
    
    if not mag_in.exists():
        print(f"ERROR: Input file not found: {mag_in}")
        sys.exit(1)
    
    # Normalize plasma data
    normalize_plasma_audit(plasma_in, plasma_out)
    
    # Normalize magnetometer data
    normalize_mag_audit(mag_in, mag_out)
    
    print("\nNormalization complete!")
    print(f"Next steps:")
    print(f"  1. Run: python3 scripts/compute_pdyn_chi.py")
    print(f"  2. Run: python3 scripts/make_example_chart.py")
    print(f"  3. Run: python3 scripts/save_cycle_charts.py --cycle 1")
    print(f"  4. Run: python3 scripts/create_gif_luft.py")


if __name__ == '__main__':
    main()
