"""
Tests for real-time data API

Tests the live data fetching and chi calculation logic.
"""

import sys
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'api'))

from get_realtime_data import calculate_chi, determine_storm_phase, get_realtime_data


def test_chi_calculation():
    """Test chi amplitude calculation."""
    
    # Test case 1: Normal conditions
    chi = calculate_chi(bz=-2.0, density=4.0, speed=400.0)
    assert chi is not None, "Chi should be calculated"
    assert 0 < chi < 0.1, f"Chi should be in normal range, got {chi}"
    
    # Test case 2: High values (boundary approach)
    chi = calculate_chi(bz=-8.0, density=6.0, speed=600.0)
    assert chi is not None, "Chi should be calculated"
    assert chi > 0.1, f"Chi should be elevated, got {chi}"
    
    # Test case 3: Null handling
    chi = calculate_chi(bz=None, density=4.0, speed=400.0)
    assert chi is None, "Chi should be None when Bz is None"
    
    print("✓ Chi calculation tests passed")


def test_storm_phase_determination():
    """Test storm phase classification."""
    
    # Test QUIET phase
    phase = determine_storm_phase(chi=0.05, bz=-1.0)
    assert phase == "QUIET", f"Expected QUIET, got {phase}"
    
    # Test PRE phase
    phase = determine_storm_phase(chi=0.14, bz=-6.0)
    assert phase == "PRE", f"Expected PRE, got {phase}"
    
    # Test PEAK phase
    phase = determine_storm_phase(chi=0.16, bz=-8.0)
    assert phase == "PEAK", f"Expected PEAK, got {phase}"
    
    # Test POST-STORM phase
    phase = determine_storm_phase(chi=0.14, bz=2.0)
    assert phase == "POST-STORM", f"Expected POST-STORM, got {phase}"
    
    # Test UNKNOWN (None chi)
    phase = determine_storm_phase(chi=None, bz=-1.0)
    assert phase == "UNKNOWN", f"Expected UNKNOWN, got {phase}"
    
    print("✓ Storm phase determination tests passed")


def test_realtime_data_structure():
    """Test that real-time data API returns proper structure."""
    
    data = get_realtime_data()
    
    # Check status field
    assert 'status' in data, "Response must have status field"
    
    if data['status'] == 'ok':
        # Check required fields
        required_fields = [
            'timestamp', 'data_timestamp', 'chi', 'storm_phase',
            'bz', 'density', 'speed', 'source', 'warnings'
        ]
        
        for field in required_fields:
            assert field in data, f"Response missing required field: {field}"
        
        # Check warnings structure
        warning_flags = [
            'chi_boundary', 'chi_violation', 'bz_southward',
            'bz_critical', 'high_speed', 'high_density'
        ]
        
        for flag in warning_flags:
            assert flag in data['warnings'], f"Warnings missing flag: {flag}"
            assert isinstance(data['warnings'][flag], bool), f"Warning flag {flag} must be boolean"
        
        # Check data types
        if data['chi'] is not None:
            assert isinstance(data['chi'], float), "Chi must be float"
            assert data['chi'] >= 0, "Chi must be non-negative"
        
        assert isinstance(data['storm_phase'], str), "Storm phase must be string"
        assert data['storm_phase'] in ['QUIET', 'PRE', 'PEAK', 'POST-STORM', 'UNKNOWN'], \
            f"Invalid storm phase: {data['storm_phase']}"
        
        print("✓ Real-time data structure tests passed")
        print(f"  Current χ: {data['chi']:.4f}")
        print(f"  Storm phase: {data['storm_phase']}")
        print(f"  Data timestamp: {data['data_timestamp']}")
    else:
        print("⚠ API returned error status (NOAA may be unavailable)")
        print(f"  Message: {data.get('message', 'Unknown error')}")


def test_json_output():
    """Test that API output is valid JSON."""
    
    data = get_realtime_data()
    
    # Try to serialize to JSON
    try:
        json_str = json.dumps(data, indent=2)
        assert len(json_str) > 0, "JSON output should not be empty"
        
        # Try to parse it back
        parsed = json.loads(json_str)
        assert parsed == data, "JSON round-trip should preserve data"
        
        print("✓ JSON output tests passed")
    except (TypeError, ValueError) as e:
        assert False, f"Failed to serialize to JSON: {e}"


if __name__ == '__main__':
    print("Running API tests...\n")
    
    test_chi_calculation()
    test_storm_phase_determination()
    test_realtime_data_structure()
    test_json_output()
    
    print("\n✅ All tests passed!")
