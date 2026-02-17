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
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

# LUFT Constants
CHI_EXPECTED = 0.055  # Expected modulation amplitude
PERIOD_HOURS = 2.4    # Period in hours
PERIOD_SECONDS = PERIOD_HOURS * 3600  # 8640 seconds
OMEGA = 2 * np.pi / PERIOD_SECONDS    # Angular frequency

# χ = 0.15 Universal Boundary Constants (discovered Dec 2025)
CHI_CAP_THEORETICAL = 0.15
CHI_TOLERANCE = 0.01
CHI_BOUNDARY_MIN = CHI_CAP_THEORETICAL - CHI_TOLERANCE  # 0.145
CHI_BOUNDARY_MAX = CHI_CAP_THEORETICAL + CHI_TOLERANCE  # 0.155

# Storm phase thresholds (based on Kp/Dst or plasma parameters)
KP_STORM_THRESHOLD = 5.0       # Kp >= 5 indicates storm conditions
DENSITY_STORM_THRESHOLD = 15.0  # p/cm³ - elevated density indicates storm
SPEED_STORM_THRESHOLD = 500.0   # km/s - elevated speed indicates storm
BZ_STORM_THRESHOLD = -10.0      # nT - strongly negative Bz indicates storm

# Baseline solar wind parameters (quiet conditions)
BASELINE_DENSITY = 5.0    # p/cm³ - typical quiet solar wind density
BASELINE_SPEED = 400.0    # km/s - typical quiet solar wind speed
BASELINE_BT = 5.0         # nT - typical quiet interplanetary magnetic field

# Chi amplitude scaling factor (empirically derived from LUFT model)
# Maps relative modulation (0-1) to χ range centered on 0.055
CHI_SCALING_CENTER = 0.1  # Center point for modulation-to-chi mapping

# API endpoints for live data fallback
NOAA_PLASMA_URL = "https://services.swpc.noaa.gov/products/solar-wind/plasma-5-minute.json"
NOAA_MAG_URL = "https://services.swpc.noaa.gov/products/solar-wind/mag-5-minute.json"

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5


def ensure_data_directory():
    """Ensure the data directory exists."""
    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_log_filepath():
    """Get the path for the current month's heartbeat log."""
    now = datetime.now(timezone.utc)
    filename = f"cme_heartbeat_log_{now.year}_{now.month:02d}.csv"
    return Path("data") / filename


def fetch_json_from_url(url, max_retries=MAX_RETRIES, delay=RETRY_DELAY_SECONDS):
    """
    Fetch JSON data from URL with retry logic.
    
    Args:
        url: URL to fetch from
        max_retries: Maximum number of retry attempts
        delay: Delay in seconds between retries
    
    Returns:
        List (parsed JSON data) or None if all retries fail
    """
    for attempt in range(1, max_retries + 1):
        try:
            print(f"  Attempt {attempt}/{max_retries}: Fetching from {url}")
            with urllib.request.urlopen(url, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
                print(f"  ✓ Successfully fetched data ({len(data)} rows)")
                return data
        except urllib.error.URLError as e:
            print(f"  ✗ Network error: {e}")
        except urllib.error.HTTPError as e:
            print(f"  ✗ HTTP error {e.code}: {e.reason}")
        except json.JSONDecodeError as e:
            print(f"  ✗ Invalid JSON: {e}")
        except Exception as e:
            print(f"  ✗ Unexpected error: {e}")
        
        if attempt < max_retries:
            print(f"  Waiting {delay} seconds before retry...")
            time.sleep(delay)
    
    print(f"  ✗ Failed to fetch data after {max_retries} attempts")
    return None


def validate_json_data(data, min_rows=2):
    """
    Validate that JSON data is not empty and has minimum required rows.
    
    Args:
        data: JSON data (expected to be a list of lists, where each inner list is a row)
        min_rows: Minimum number of rows required (default: 2 for header + data)
    
    Returns:
        True if valid, False otherwise
    """
    if data is None:
        return False
    if not isinstance(data, list):
        return False
    if len(data) < min_rows:
        return False
    return True


def load_json_data(filepath):
    """Load JSON data from file with validation."""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            if validate_json_data(data):
                print(f"  ✓ Loaded valid data from {filepath} ({len(data)} rows)")
                return data
            else:
                print(f"  ✗ File {filepath} has insufficient data (needs at least 2 rows)")
                return None
    except FileNotFoundError:
        print(f"  ✗ File not found: {filepath}")
        return None
    except json.JSONDecodeError as e:
        print(f"  ✗ Invalid JSON in {filepath}: {e}")
        return None
    except Exception as e:
        print(f"  ✗ Error loading {filepath}: {e}")
        return None


def load_or_fetch_data(filepath, api_url, data_type):
    """
    Load data from file, or fetch from API if file is missing/invalid.
    
    Args:
        filepath: Path to local JSON file (str or Path)
        api_url: URL to fetch from if file is invalid (str)
        data_type: Type of data (e.g., 'plasma' or 'mag') for logging (str)
    
    Returns:
        JSON data (list) or None if all attempts fail
    """
    print(f"\nLoading {data_type} data...")
    
    # First, try loading from local file
    if filepath and Path(filepath).exists():
        data = load_json_data(filepath)
        if data:
            return data
        print(f"  Local file invalid, falling back to API...")
    else:
        if filepath:
            print(f"  Local file not found, fetching from API...")
    
    # Fallback to API
    if api_url:
        data = fetch_json_from_url(api_url)
        if data:
            if validate_json_data(data):
                # Save to file for future use
                if filepath:
                    try:
                        ensure_data_directory()
                        with open(filepath, 'w') as f:
                            json.dump(data, f, indent=2)
                        print(f"  ✓ Saved fetched data to {filepath}")
                    except Exception as e:
                        print(f"  Warning: Could not save data to file: {e}")
                return data
            else:
                print(f"  ✗ API returned insufficient data (needs at least 2 rows)")
    
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
    chi = 0.0
    n_valid = 0
    
    if density is not None and density > 0:
        density_mod = abs(density - BASELINE_DENSITY) / BASELINE_DENSITY
        chi += min(density_mod, 0.3)  # Cap contribution
        n_valid += 1
    
    if speed is not None and speed > 0:
        speed_mod = abs(speed - BASELINE_SPEED) / BASELINE_SPEED
        chi += min(speed_mod, 0.3)
        n_valid += 1
    
    if bt is not None and bt > 0:
        bt_mod = abs(bt - BASELINE_BT) / BASELINE_BT
        chi += min(bt_mod, 0.3)
        n_valid += 1
    
    if n_valid > 0:
        chi = chi / n_valid  # Average modulation
        # Scale to expected range around 0.055 using scaling center
        chi = CHI_EXPECTED + (chi - CHI_SCALING_CENTER) * 0.5
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


def classify_chi_status(chi_val):
    """
    Classify χ value relative to universal χ = 0.15 boundary.
    
    Returns:
        'UNKNOWN' - NaN/None value
        'VIOLATION' - Above boundary (χ > 0.155) - filamentary breakdown
        'AT_BOUNDARY' - At optimal coupling (0.145 ≤ χ ≤ 0.155)
        'BELOW' - Glow mode (χ < 0.145) - normal operations
    """
    if chi_val is None or (isinstance(chi_val, float) and np.isnan(chi_val)):
        return 'UNKNOWN'
    elif chi_val > CHI_BOUNDARY_MAX:
        return 'VIOLATION'
    elif CHI_BOUNDARY_MIN <= chi_val <= CHI_BOUNDARY_MAX:
        return 'AT_BOUNDARY'
    else:
        return 'BELOW'


def sanitize_csv_file(filepath):
    """
    Sanitize CSV file by removing conflict markers, malformed rows, and duplicates.
    
    This function performs aggressive data cleaning:
    1. Removes Git conflict markers (<<<<<<<, =======, >>>>>>>)
    2. Removes rows that don't have exactly 12 columns (11 commas)
    3. Sorts by timestamp_utc
    4. Removes duplicate timestamps (keeps first occurrence)
    
    Args:
        filepath (Path): Path to the CSV log file
    
    Returns:
        tuple: (cleaned_count, removed_count, had_conflicts)
    """
    if not filepath.exists():
        return 0, 0, False
    
    print(f"\n🧹 Sanitizing CSV file: {filepath}")
    
    # Expected CSV structure
    EXPECTED_COLUMNS = 12
    EXPECTED_HEADER = 'timestamp_utc,chi_amplitude,phase_radians,storm_phase,density_p_cm3,speed_km_s,bz_nT,bt_nT,source,chi_at_boundary,chi_violation,chi_status'
    
    # Read all lines
    try:
        with open(filepath, 'r', newline='') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"  ✗ Error reading file: {e}")
        return 0, 0, False
    
    if not lines:
        return 0, 0, False
    
    # Track statistics
    had_conflicts = False
    removed_count = 0
    
    # Validate and extract header (first line)
    header = lines[0].strip()
    if header != EXPECTED_HEADER:
        print(f"  ⚠️  Header mismatch detected - using expected header")
        header = EXPECTED_HEADER
    
    cleaned_lines = [header]
    seen_timestamps = set()
    conflict_markers = ['<<<<<<<', '=======', '>>>>>>>']
    
    # Process data rows
    for i, line in enumerate(lines[1:], start=2):
        line_stripped = line.strip()
        
        # Skip empty lines
        if not line_stripped:
            continue
        
        # Check for conflict markers
        if any(marker in line_stripped for marker in conflict_markers):
            print(f"  🔧 Removing conflict marker at line {i}: {line_stripped[:60]}...")
            had_conflicts = True
            removed_count += 1
            continue
        
        # Count columns (commas + 1)
        column_count = line_stripped.count(',') + 1
        if column_count != EXPECTED_COLUMNS:
            print(f"  🔧 Removing malformed row at line {i}: {column_count} columns (expected {EXPECTED_COLUMNS})")
            print(f"     Content: {line_stripped[:80]}...")
            removed_count += 1
            continue
        
        # Extract timestamp for duplicate checking and sorting
        try:
            parts = line_stripped.split(',')
            timestamp = parts[0]
            
            # Validate timestamp format (basic check)
            if not timestamp or len(timestamp) < 19:  # Minimum: "YYYY-MM-DD HH:MM:SS"
                print(f"  🔧 Removing row with invalid timestamp at line {i}")
                removed_count += 1
                continue
            
            if timestamp in seen_timestamps:
                print(f"  🔧 Removing duplicate timestamp: {timestamp}")
                removed_count += 1
                continue
            seen_timestamps.add(timestamp)
        except (IndexError, ValueError):
            print(f"  🔧 Removing unparseable row at line {i}")
            removed_count += 1
            continue
        
        # Keep this line (store stripped version with newline for consistency)
        cleaned_lines.append(line_stripped)
    
    # Sort by timestamp (skip header)
    data_lines = cleaned_lines[1:]
    
    # Sort data lines by timestamp
    try:
        data_lines_sorted = sorted(data_lines, key=lambda x: x.split(',')[0])
        cleaned_lines = [cleaned_lines[0]] + data_lines_sorted
    except Exception as e:
        print(f"  ⚠️  Could not sort by timestamp: {e}")
        # Continue with unsorted data
    
    # Write cleaned data back with consistent newlines
    try:
        with open(filepath, 'w', newline='') as f:
            for line in cleaned_lines:
                f.write(line + '\n')
        
        clean_count = len(cleaned_lines) - 1  # Exclude header
        print(f"  ✅ Sanitization complete:")
        print(f"     - Cleaned rows: {clean_count}")
        print(f"     - Removed rows: {removed_count}")
        print(f"     - Had conflicts: {'Yes' if had_conflicts else 'No'}")
        
        return clean_count, removed_count, had_conflicts
    except Exception as e:
        print(f"  ✗ Error writing cleaned file: {e}")
        return 0, 0, had_conflicts


def get_existing_timestamps(filepath):
    """
    Read existing timestamps from the CSV log to prevent duplicates.
    
    Args:
        filepath (Path): Path to the CSV log file
    
    Returns:
        set: Set of existing timestamp strings
    """
    timestamps = set()
    if filepath.exists():
        try:
            with open(filepath, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'timestamp_utc' in row:
                        timestamps.add(row['timestamp_utc'])
        except Exception as e:
            print(f"Warning: Could not read existing timestamps: {e}")
    return timestamps


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
                'source',
                'chi_at_boundary',
                'chi_violation',
                'chi_status'
            ])
        print(f"Created new log file: {filepath}")


def validate_entry_data(entry):
    """
    Validate that entry data has reasonable values.
    
    Args:
        entry (dict): Dictionary containing entry data to validate
    
    Returns:
        tuple[bool, list[str]]: Tuple of (is_valid, warnings_list)
    """
    warnings = []
    
    # Check if speed is zero or None when provided
    speed = entry.get('speed')
    if speed is not None and speed != '':
        try:
            if float(speed) == 0:
                warnings.append("Speed is 0 km/s - may indicate data gap")
        except (ValueError, TypeError):
            pass  # Ignore conversion errors
    
    # Check if density is zero or None when provided
    density = entry.get('density')
    if density is not None and density != '':
        try:
            if float(density) == 0:
                warnings.append("Density is 0.00 p/cm³ - may indicate data gap")
        except (ValueError, TypeError):
            pass  # Ignore conversion errors
    
    # Entry is still valid even with warnings - we log all data for completeness
    return True, warnings


def append_log_entry(filepath, entry, existing_timestamps=None):
    """
    Append a single entry to the CSV log.
    
    Args:
        filepath (Path): Path to CSV log file
        entry (dict): Dictionary containing entry data
        existing_timestamps (set, optional): Set of existing timestamps to check for duplicates
    
    Returns:
        bool: True if entry was appended, False if duplicate was skipped
    """
    timestamp = entry['timestamp_utc']
    
    # Check for duplicate timestamp
    if existing_timestamps is not None and timestamp in existing_timestamps:
        print(f"⚠️  Duplicate timestamp detected: {timestamp}")
        print("   Skipping entry to prevent duplicate log entries")
        return False
    
    # Validate data quality
    is_valid, warnings = validate_entry_data(entry)
    if warnings:
        print(f"⚠️  Data quality warnings for {timestamp}:")
        for warning in warnings:
            print(f"   - {warning}")
    
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
            entry.get('source', 'ACE/DSCOVR'),
            entry.get('chi_at_boundary', 0),
            entry.get('chi_violation', 0),
            entry.get('chi_status', 'UNKNOWN')
        ])
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="LUFT CME Heartbeat Logger — Log χ amplitude and 2.4h phase for CME monitoring",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/cme_heartbeat_logger.py --plasma data/ace_plasma_latest.json --mag data/ace_mag_latest.json

Contact: CARLDCLINE@GMAIL.COM
Repository: https://github.com/CarlDeanClineSr/luft-portal-
        """
    )
    
    parser.add_argument('--plasma', type=str, required=True, help='Path to plasma data JSON')
    parser.add_argument('--mag', type=str, required=True, help='Path to magnetic field data JSON')
    parser.add_argument('--output', type=str, help='Override output CSV path')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("   LUFT CME HEARTBEAT LOGGER")
    print("   Automated χ amplitude and 2.4h phase logging")
    print("=" * 60)
    print()
    
    # Determine output file
    log_filepath = Path(args.output) if args.output else get_log_filepath()
    
    # Ensure data directory exists
    ensure_data_directory()
    
    # Load or fetch data with fallback to API
    plasma_data = load_or_fetch_data(args.plasma, NOAA_PLASMA_URL, "plasma")
    mag_data = load_or_fetch_data(args.mag, NOAA_MAG_URL, "magnetic field")
    
    # Extract latest values
    plasma = extract_latest_plasma(plasma_data) if plasma_data else None
    mag = extract_latest_mag(mag_data) if mag_data else None
    
    # Check if we have any valid data
    if not plasma and not mag:
        print()
        print("=" * 60)
        print("WARNING: No valid data available")
        print("=" * 60)
        print("Could not obtain valid solar wind data from:")
        print("  - Local files (missing or invalid)")
        print("  - NOAA API (failed after retries)")
        print()
        print("This is not an error - data may be temporarily unavailable.")
        print("The workflow will continue without logging this entry.")
        print("Next scheduled run will attempt to fetch data again.")
        print("=" * 60)
        sys.exit(0)  # Exit gracefully without error
    
    # Get timestamp
    timestamp = (plasma or mag).get('timestamp', datetime.now(timezone.utc).isoformat())
    
    # Extract values (handle partial data gracefully)
    density = plasma.get('density') if plasma else None
    speed = plasma.get('speed') if plasma else None
    bz = mag.get('bz') if mag else None
    bt = mag.get('bt') if mag else None
    
    # Log what data we have
    print()
    print("Data availability:")
    print(f"  Plasma: {'✓' if plasma else '✗'} (density={density}, speed={speed})")
    print(f"  Magnetic: {'✓' if mag else '✗'} (bz={bz}, bt={bt})")
    
    # Compute LUFT parameters
    chi = estimate_chi_amplitude(density, speed, bt)
    phase = estimate_phase(timestamp)
    storm_phase = classify_storm_phase(density, speed, bz, bt)
    
    # Add χ boundary classification
    chi_at_boundary = 1 if (CHI_BOUNDARY_MIN <= chi <= CHI_BOUNDARY_MAX) else 0
    chi_violation = 1 if chi > CHI_BOUNDARY_MAX else 0
    chi_status = classify_chi_status(chi)
    
    entry = {
        'timestamp_utc': timestamp,
        'chi_amplitude': chi,
        'phase_radians': phase,
        'storm_phase': storm_phase,
        'density': round(density, 2) if density else '',
        'speed': round(speed, 1) if speed else '',
        'bz': round(bz, 2) if bz else '',
        'bt': round(bt, 2) if bt else '',
        'source': 'ACE/DSCOVR',
        'chi_at_boundary': chi_at_boundary,
        'chi_violation': chi_violation,
        'chi_status': chi_status
    }
    
    # Initialize log file if needed
    initialize_log_file(log_filepath)
    
    # Sanitize CSV file before appending (removes conflict markers, malformed rows, duplicates)
    clean_count, removed_count, had_conflicts = sanitize_csv_file(log_filepath)
    
    if removed_count > 0 or had_conflicts:
        print(f"\n🤖 AUTO-FIX: CSV sanitization removed {removed_count} problematic rows")
        if had_conflicts:
            print("   Resolved Git conflict markers automatically")
    
    # Read existing timestamps to prevent duplicates
    existing_timestamps = get_existing_timestamps(log_filepath)
    if existing_timestamps:
        print(f"  Found {len(existing_timestamps)} existing entries in log")
    
    # Append entry
    entry_added = append_log_entry(log_filepath, entry, existing_timestamps)
    
    if not entry_added:
        print()
        print("=" * 60)
        print("Entry was not logged (duplicate timestamp)")
        print("=" * 60)
        return 0
    
    # Report
    print()
    print("Entry logged successfully!")
    print(f"  Timestamp: {entry['timestamp_utc']}")
    print(f"  χ amplitude: {entry['chi_amplitude']}")
    print(f"  χ status: {entry['chi_status']}")
    print(f"  Phase (rad): {entry['phase_radians']}")
    print(f"  Storm phase: {entry['storm_phase']}")
    
    # χ boundary status alert
    if entry['chi_violation']:
        print(f"\n⚠️  χ VIOLATION DETECTED (χ > {CHI_BOUNDARY_MAX})")
        print("   Status: Coherence loss - filamentary breakdown")
    elif entry['chi_at_boundary']:
        print(f"\n✅ At χ = {CHI_CAP_THEORETICAL} BOUNDARY (optimal coupling)")
    
    print(f"\n  Output file: {log_filepath}")
    print()
    print("=" * 60)
    print("LUFT Heartbeat Logger complete.")
    print("Contact: CARLDCLINE@GMAIL.COM")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
