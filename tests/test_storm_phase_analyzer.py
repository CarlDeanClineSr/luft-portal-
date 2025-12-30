"""
Tests for storm phase analyzer

Tests the core storm-phase classification logic with various scenarios.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from storm_phase_analyzer import analyze_storm_phases


def test_basic_storm_classification():
    """Test basic storm phase classification with a clear peak."""
    
    # Create synthetic data with a clear storm peak
    timestamps = pd.date_range('2025-01-01', periods=100, freq='1H')
    chi_values = [0.08] * 30  # PRE phase
    chi_values += [0.15] * 10  # PEAK phase (at boundary)
    chi_values += [0.09] * 60  # POST phase
    
    df = pd.DataFrame({
        'timestamp': timestamps,
        'chi_amplitude': chi_values
    })
    
    summary, df_with_phases = analyze_storm_phases(df)
    
    # Verify storm was detected
    assert summary['has_storm'] == True, "Storm should be detected"
    assert summary['num_peak'] == 10, f"Expected 10 peak points, got {summary['num_peak']}"
    assert summary['num_pre'] == 30, f"Expected 30 pre points, got {summary['num_pre']}"
    assert summary['num_post'] == 60, f"Expected 60 post points, got {summary['num_post']}"
    assert summary['num_unknown'] == 0, "No unknown points expected"
    
    # Verify phase column exists
    assert 'phase' in df_with_phases.columns, "Phase column should exist"
    
    # Verify first and last peak times
    assert summary['first_peak_time'] is not None, "First peak time should be set"
    assert summary['last_peak_time'] is not None, "Last peak time should be set"
    
    print("✓ Basic storm classification test passed")


def test_no_storm_quiet_period():
    """Test classification when no storm is present (all PRE)."""
    
    # Create data with no values in peak range
    timestamps = pd.date_range('2025-01-01', periods=50, freq='1H')
    chi_values = [0.08] * 50  # All below boundary
    
    df = pd.DataFrame({
        'timestamp': timestamps,
        'chi_amplitude': chi_values
    })
    
    summary, df_with_phases = analyze_storm_phases(df)
    
    # Verify no storm detected
    assert summary['has_storm'] == False, "No storm should be detected"
    assert summary['num_peak'] == 0, "No peak points expected"
    assert summary['num_pre'] == 50, "All points should be PRE"
    assert summary['num_post'] == 0, "No POST points expected"
    assert summary['first_peak_time'] is None, "No first peak time"
    assert summary['last_peak_time'] is None, "No last peak time"
    
    print("✓ No storm (quiet period) test passed")


def test_insufficient_peak_points():
    """Test that storms require minimum peak points."""
    
    # Create data with only 2 peak points (below min_peak_points=3)
    timestamps = pd.date_range('2025-01-01', periods=20, freq='1H')
    chi_values = [0.08] * 10
    chi_values += [0.15] * 2  # Only 2 peak points
    chi_values += [0.09] * 8
    
    df = pd.DataFrame({
        'timestamp': timestamps,
        'chi_amplitude': chi_values
    })
    
    summary, df_with_phases = analyze_storm_phases(
        df,
        min_peak_points=3  # Require at least 3 peak points
    )
    
    # Should not classify as storm
    assert summary['has_storm'] == False, "Storm should not be detected with insufficient peak points"
    assert summary['num_pre'] == 20, "All valid points should be PRE"
    
    print("✓ Insufficient peak points test passed")


def test_missing_and_nan_values():
    """Test handling of missing and NaN chi values."""
    
    timestamps = pd.date_range('2025-01-01', periods=50, freq='1H')
    chi_values = [0.08] * 15
    chi_values += [np.nan] * 5  # Missing values
    chi_values += [0.15] * 10  # Peak
    chi_values += [np.nan] * 5  # More missing
    chi_values += [0.09] * 15
    
    df = pd.DataFrame({
        'timestamp': timestamps,
        'chi_amplitude': chi_values
    })
    
    summary, df_with_phases = analyze_storm_phases(df)
    
    # Verify NaN values are marked as UNKNOWN
    assert summary['num_unknown'] == 10, "Should have 10 unknown points"
    assert summary['has_storm'] == True, "Storm should still be detected"
    assert summary['num_peak'] == 10, "Peak points should be identified"
    
    print("✓ Missing/NaN values test passed")


def test_custom_boundary_parameters():
    """Test with custom chi boundary parameters."""
    
    timestamps = pd.date_range('2025-01-01', periods=50, freq='1H')
    chi_values = [0.10] * 20
    chi_values += [0.18] * 10  # Peak at different boundary
    chi_values += [0.12] * 20
    
    df = pd.DataFrame({
        'timestamp': timestamps,
        'chi_amplitude': chi_values
    })
    
    # Use custom boundaries
    summary, df_with_phases = analyze_storm_phases(
        df,
        chi_boundary_min=0.17,
        chi_boundary_max=0.19,
        min_peak_points=5
    )
    
    assert summary['has_storm'] == True, "Storm should be detected with custom boundaries"
    assert summary['num_peak'] == 10, "Should detect 10 peak points"
    assert summary['chi_boundary_min'] == 0.17, "Boundary min should be stored"
    assert summary['chi_boundary_max'] == 0.19, "Boundary max should be stored"
    
    print("✓ Custom boundary parameters test passed")


def test_alternate_timestamp_column():
    """Test with alternate timestamp column name (timestamp_utc)."""
    
    timestamps = pd.date_range('2025-01-01', periods=30, freq='1H')
    chi_values = [0.08] * 10
    chi_values += [0.15] * 10
    chi_values += [0.09] * 10
    
    df = pd.DataFrame({
        'timestamp_utc': timestamps,  # Alternate column name
        'chi_amplitude': chi_values
    })
    
    summary, df_with_phases = analyze_storm_phases(df)
    
    assert summary['has_storm'] == True, "Should work with timestamp_utc column"
    assert 'timestamp' in df_with_phases.columns, "Should create timestamp column"
    
    print("✓ Alternate timestamp column test passed")


def test_percentages_sum_to_100():
    """Test that phase percentages sum to approximately 100%."""
    
    timestamps = pd.date_range('2025-01-01', periods=100, freq='1H')
    chi_values = [0.08] * 40
    chi_values += [0.15] * 20
    chi_values += [0.09] * 40
    
    df = pd.DataFrame({
        'timestamp': timestamps,
        'chi_amplitude': chi_values
    })
    
    summary, _ = analyze_storm_phases(df)
    
    total_pct = (
        summary['pct_pre'] +
        summary['pct_peak'] +
        summary['pct_post'] +
        summary['pct_unknown']
    )
    
    assert abs(total_pct - 100.0) < 0.01, f"Percentages should sum to 100%, got {total_pct}"
    
    print("✓ Percentages sum to 100% test passed")


def test_real_data_structure():
    """Test with structure matching actual CME heartbeat log."""
    
    # Use fixed seed for reproducible tests
    np.random.seed(42)
    
    # Simulate real data structure
    data = {
        'timestamp_utc': pd.date_range('2025-12-01', periods=100, freq='1H'),
        'chi_amplitude': np.random.uniform(0.08, 0.12, 100),
        'phase_radians': np.random.uniform(0, 2*np.pi, 100),
        'storm_phase': ['pre'] * 100,  # Old phase column
        'density_p_cm3': np.random.uniform(1, 5, 100),
        'speed_km_s': np.random.uniform(300, 500, 100),
        'bz_nT': np.random.uniform(-5, 5, 100),
        'source': ['ACE/DSCOVR'] * 100
    }
    
    # Add some peak values
    for i in range(40, 50):
        data['chi_amplitude'][i] = 0.15
    
    df = pd.DataFrame(data)
    
    summary, df_with_phases = analyze_storm_phases(df)
    
    # Verify it works with real structure
    assert summary['has_storm'] == True, "Should detect storm in realistic data"
    assert len(df_with_phases) == 100, "Should preserve all rows"
    assert 'phase' in df_with_phases.columns, "Should add phase column"
    
    print("✓ Real data structure test passed")


if __name__ == '__main__':
    print("Running storm phase analyzer tests...")
    print()
    
    try:
        test_basic_storm_classification()
        test_no_storm_quiet_period()
        test_insufficient_peak_points()
        test_missing_and_nan_values()
        test_custom_boundary_parameters()
        test_alternate_timestamp_column()
        test_percentages_sum_to_100()
        test_real_data_structure()
        
        print()
        print("=" * 60)
        print("All storm phase analyzer tests passed! ✓")
        print("=" * 60)
        sys.exit(0)
    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"Test failed: {e}")
        print("=" * 60)
        sys.exit(1)
    except Exception as e:
        print()
        print("=" * 60)
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 60)
        sys.exit(1)
