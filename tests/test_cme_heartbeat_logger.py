#!/usr/bin/env python3
"""
Tests for cme_heartbeat_logger.py
Validates duplicate detection and data validation functionality.
"""

import csv
import sys
from pathlib import Path
from datetime import datetime, timezone

import pytest

# Add scripts directory to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from cme_heartbeat_logger import (
    get_existing_timestamps,
    initialize_log_file,
    append_log_entry,
    validate_entry_data,
    sanitize_csv_file,
)


def test_get_existing_timestamps_empty_file(tmp_path):
    """Test reading timestamps from a non-existent file."""
    log_file = tmp_path / "test_log.csv"
    timestamps = get_existing_timestamps(log_file)
    assert timestamps == set()


def test_get_existing_timestamps_with_data(tmp_path):
    """Test reading timestamps from an existing CSV file."""
    log_file = tmp_path / "test_log.csv"
    
    # Create a CSV file with some timestamps
    with open(log_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp_utc', 'chi_amplitude', 'phase_radians', 'storm_phase'])
        writer.writerow(['2026-01-13 12:00:00.000', '0.15', '1.234', 'pre'])
        writer.writerow(['2026-01-13 13:00:00.000', '0.14', '2.345', 'pre'])
        writer.writerow(['2026-01-13 14:00:00.000', '0.13', '3.456', 'peak'])
    
    timestamps = get_existing_timestamps(log_file)
    assert len(timestamps) == 3
    assert '2026-01-13 12:00:00.000' in timestamps
    assert '2026-01-13 13:00:00.000' in timestamps
    assert '2026-01-13 14:00:00.000' in timestamps


def test_initialize_log_file_creates_headers(tmp_path):
    """Test that initialize_log_file creates file with proper headers."""
    log_file = tmp_path / "test_log.csv"
    initialize_log_file(log_file)
    
    assert log_file.exists()
    
    with open(log_file, 'r', newline='') as f:
        reader = csv.reader(f)
        headers = next(reader)
        assert 'timestamp_utc' in headers
        assert 'chi_amplitude' in headers
        assert 'phase_radians' in headers
        assert 'storm_phase' in headers
        assert 'density_p_cm3' in headers
        assert 'speed_km_s' in headers


def test_append_log_entry_adds_new_entry(tmp_path):
    """Test that append_log_entry successfully adds a new entry."""
    log_file = tmp_path / "test_log.csv"
    initialize_log_file(log_file)
    
    entry = {
        'timestamp_utc': '2026-01-13 12:00:00.000',
        'chi_amplitude': 0.15,
        'phase_radians': 1.234,
        'storm_phase': 'pre',
        'density': 5.0,
        'speed': 400.0,
        'bz': -2.0,
        'bt': 5.0,
        'source': 'ACE/DSCOVR',
        'chi_at_boundary': 1,
        'chi_violation': 0,
        'chi_status': 'AT_BOUNDARY'
    }
    
    result = append_log_entry(log_file, entry)
    assert result is True
    
    # Verify entry was written
    with open(log_file, 'r', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]['timestamp_utc'] == '2026-01-13 12:00:00.000'
        assert rows[0]['chi_amplitude'] == '0.15'


def test_append_log_entry_skips_duplicate(tmp_path):
    """Test that append_log_entry skips duplicate timestamps."""
    log_file = tmp_path / "test_log.csv"
    initialize_log_file(log_file)
    
    entry = {
        'timestamp_utc': '2026-01-13 12:00:00.000',
        'chi_amplitude': 0.15,
        'phase_radians': 1.234,
        'storm_phase': 'pre',
        'density': 5.0,
        'speed': 400.0,
        'bz': -2.0,
        'bt': 5.0,
        'source': 'ACE/DSCOVR',
        'chi_at_boundary': 1,
        'chi_violation': 0,
        'chi_status': 'AT_BOUNDARY'
    }
    
    # Add entry first time
    existing_timestamps = get_existing_timestamps(log_file)
    result1 = append_log_entry(log_file, entry, existing_timestamps)
    assert result1 is True
    
    # Try to add same entry again
    existing_timestamps = get_existing_timestamps(log_file)
    result2 = append_log_entry(log_file, entry, existing_timestamps)
    assert result2 is False
    
    # Verify only one entry exists
    with open(log_file, 'r', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1


def test_validate_entry_data_with_zero_speed():
    """Test that validate_entry_data detects zero speed."""
    entry = {
        'speed': 0.0,
        'density': 5.0
    }
    
    is_valid, warnings = validate_entry_data(entry)
    assert is_valid is True  # Still valid, just with warnings
    assert len(warnings) > 0
    assert any('Speed' in w for w in warnings)


def test_validate_entry_data_with_zero_density():
    """Test that validate_entry_data detects zero density."""
    entry = {
        'speed': 400.0,
        'density': 0.0
    }
    
    is_valid, warnings = validate_entry_data(entry)
    assert is_valid is True  # Still valid, just with warnings
    assert len(warnings) > 0
    assert any('Density' in w for w in warnings)


def test_validate_entry_data_with_both_zero():
    """Test that validate_entry_data detects both zero values."""
    entry = {
        'speed': 0.0,
        'density': 0.0
    }
    
    is_valid, warnings = validate_entry_data(entry)
    assert is_valid is True  # Still valid, just with warnings
    assert len(warnings) == 2
    assert any('Speed' in w for w in warnings)
    assert any('Density' in w for w in warnings)


def test_validate_entry_data_with_valid_values():
    """Test that validate_entry_data passes valid values without warnings."""
    entry = {
        'speed': 400.0,
        'density': 5.0
    }
    
    is_valid, warnings = validate_entry_data(entry)
    assert is_valid is True
    assert len(warnings) == 0


def test_validate_entry_data_with_empty_values():
    """Test that validate_entry_data handles empty values correctly."""
    entry = {
        'speed': '',
        'density': ''
    }
    
    is_valid, warnings = validate_entry_data(entry)
    assert is_valid is True
    assert len(warnings) == 0


def test_validate_entry_data_with_invalid_types():
    """Test that validate_entry_data handles invalid types gracefully."""
    entry = {
        'speed': 'invalid',
        'density': 'not_a_number'
    }
    
    is_valid, warnings = validate_entry_data(entry)
    assert is_valid is True
    assert len(warnings) == 0  # Should not crash, just skip validation


def test_sanitize_csv_file_removes_conflict_markers(tmp_path):
    """Test that sanitize_csv_file removes Git conflict markers."""
    log_file = tmp_path / "test_log.csv"
    
    # Create a CSV with conflict markers
    with open(log_file, 'w', newline='') as f:
        f.write('timestamp_utc,chi_amplitude,phase_radians,storm_phase,density_p_cm3,speed_km_s,bz_nT,bt_nT,source,chi_at_boundary,chi_violation,chi_status\n')
        f.write('2026-01-13 12:00:00.000,0.15,1.0,pre,2.0,500.0,1.0,5.0,ACE/DSCOVR,1,0,AT_BOUNDARY\n')
        f.write('<<<<<<< Updated upstream\n')
        f.write('2026-01-13 13:00:00.000,0.14,1.1,pre,2.1,501.0,1.1,5.1,ACE/DSCOVR,1,0,BELOW\n')
        f.write('=======\n')
        f.write('2026-01-13 13:00:00.000,0.15,1.2,pre,2.2,502.0,1.2,5.2,ACE/DSCOVR,1,0,AT_BOUNDARY\n')
        f.write('>>>>>>> Stashed changes\n')
        f.write('2026-01-13 14:00:00.000,0.15,1.3,pre,2.3,503.0,1.3,5.3,ACE/DSCOVR,1,0,AT_BOUNDARY\n')
    
    clean_count, removed_count, had_conflicts = sanitize_csv_file(log_file)
    
    assert had_conflicts is True
    assert removed_count >= 3  # At least 3 conflict markers
    assert clean_count >= 2  # At least 2 valid data rows
    
    # Verify no conflict markers remain
    with open(log_file, 'r') as f:
        content = f.read()
        assert '<<<<<<' not in content
        assert '=======' not in content
        assert '>>>>>>>' not in content


def test_sanitize_csv_file_removes_malformed_rows(tmp_path):
    """Test that sanitize_csv_file removes rows with incorrect column count."""
    log_file = tmp_path / "test_log.csv"
    
    # Create a CSV with malformed rows
    with open(log_file, 'w', newline='') as f:
        f.write('timestamp_utc,chi_amplitude,phase_radians,storm_phase,density_p_cm3,speed_km_s,bz_nT,bt_nT,source,chi_at_boundary,chi_violation,chi_status\n')
        f.write('2026-01-13 12:00:00.000,0.15,1.0,pre,2.0,500.0,1.0,5.0,ACE/DSCOVR,1,0,AT_BOUNDARY\n')
        f.write('2026-01-13 13:00:00.000,0.14,1.1,pre,2.1,501.0,1.1\n')  # Only 7 columns
        f.write('2026-01-13 14:00:00.000,0.15,1.3,pre,2.3,503.0,1.3,5.3,ACE/DSCOVR,1,0,AT_BOUNDARY\n')
    
    clean_count, removed_count, had_conflicts = sanitize_csv_file(log_file)
    
    assert removed_count == 1  # One malformed row removed
    assert clean_count == 2  # Two valid rows remain
    
    # Verify all rows have 12 columns
    with open(log_file, 'r') as f:
        for i, line in enumerate(f):
            column_count = line.count(',') + 1
            assert column_count == 12, f"Line {i} has {column_count} columns"


def test_sanitize_csv_file_removes_duplicates(tmp_path):
    """Test that sanitize_csv_file removes duplicate timestamps."""
    log_file = tmp_path / "test_log.csv"
    
    # Create a CSV with duplicate timestamps
    with open(log_file, 'w', newline='') as f:
        f.write('timestamp_utc,chi_amplitude,phase_radians,storm_phase,density_p_cm3,speed_km_s,bz_nT,bt_nT,source,chi_at_boundary,chi_violation,chi_status\n')
        f.write('2026-01-13 12:00:00.000,0.15,1.0,pre,2.0,500.0,1.0,5.0,ACE/DSCOVR,1,0,AT_BOUNDARY\n')
        f.write('2026-01-13 13:00:00.000,0.14,1.1,pre,2.1,501.0,1.1,5.1,ACE/DSCOVR,1,0,BELOW\n')
        f.write('2026-01-13 13:00:00.000,0.15,1.2,pre,2.2,502.0,1.2,5.2,ACE/DSCOVR,1,0,AT_BOUNDARY\n')  # Duplicate
        f.write('2026-01-13 14:00:00.000,0.15,1.3,pre,2.3,503.0,1.3,5.3,ACE/DSCOVR,1,0,AT_BOUNDARY\n')
    
    clean_count, removed_count, had_conflicts = sanitize_csv_file(log_file)
    
    assert removed_count == 1  # One duplicate removed
    assert clean_count == 3  # Three unique rows remain
    
    # Verify no duplicate timestamps
    timestamps = set()
    with open(log_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ts = row['timestamp_utc']
            assert ts not in timestamps, f"Duplicate timestamp: {ts}"
            timestamps.add(ts)


def test_sanitize_csv_file_sorts_by_timestamp(tmp_path):
    """Test that sanitize_csv_file sorts rows by timestamp."""
    log_file = tmp_path / "test_log.csv"
    
    # Create a CSV with unsorted timestamps
    with open(log_file, 'w', newline='') as f:
        f.write('timestamp_utc,chi_amplitude,phase_radians,storm_phase,density_p_cm3,speed_km_s,bz_nT,bt_nT,source,chi_at_boundary,chi_violation,chi_status\n')
        f.write('2026-01-13 14:00:00.000,0.15,1.3,pre,2.3,503.0,1.3,5.3,ACE/DSCOVR,1,0,AT_BOUNDARY\n')
        f.write('2026-01-13 12:00:00.000,0.15,1.0,pre,2.0,500.0,1.0,5.0,ACE/DSCOVR,1,0,AT_BOUNDARY\n')
        f.write('2026-01-13 13:00:00.000,0.14,1.1,pre,2.1,501.0,1.1,5.1,ACE/DSCOVR,1,0,BELOW\n')
    
    clean_count, removed_count, had_conflicts = sanitize_csv_file(log_file)
    
    assert clean_count == 3
    
    # Verify rows are sorted by timestamp
    with open(log_file, 'r') as f:
        reader = csv.DictReader(f)
        timestamps = [row['timestamp_utc'] for row in reader]
        assert timestamps == sorted(timestamps), "Rows should be sorted by timestamp"


def test_sanitize_csv_file_with_empty_file(tmp_path):
    """Test that sanitize_csv_file handles empty files gracefully."""
    log_file = tmp_path / "test_log.csv"
    log_file.touch()  # Create empty file
    
    clean_count, removed_count, had_conflicts = sanitize_csv_file(log_file)
    
    assert clean_count == 0
    assert removed_count == 0
    assert had_conflicts is False


def test_sanitize_csv_file_with_nonexistent_file(tmp_path):
    """Test that sanitize_csv_file handles non-existent files gracefully."""
    log_file = tmp_path / "nonexistent.csv"
    
    clean_count, removed_count, had_conflicts = sanitize_csv_file(log_file)
    
    assert clean_count == 0
    assert removed_count == 0
    assert had_conflicts is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
