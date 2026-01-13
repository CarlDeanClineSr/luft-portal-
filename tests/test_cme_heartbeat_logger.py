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


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
