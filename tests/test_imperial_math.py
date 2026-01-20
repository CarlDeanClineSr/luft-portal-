"""
Tests for imperial_math.py

Tests the LUFT Imperial Math Core functions including compute_luft_metrics
and generate_storm_report.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from io import StringIO

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from scripts.imperial_math import compute_luft_metrics, generate_storm_report, compute_chi, rolling_median


def test_compute_luft_metrics_basic():
    """Test compute_luft_metrics with basic synthetic data."""
    
    # Create synthetic magnetic field data
    timestamps = pd.date_range('2025-01-01', periods=100, freq='h')
    b_values = [50.0] * 50 + [57.5] * 50  # Baseline 50, then 15% increase
    
    df = pd.DataFrame({
        'B': b_values
    }, index=timestamps)
    
    # Apply the Cline Transform
    df = compute_luft_metrics(df)
    
    # Verify required columns exist
    assert 'B_baseline' in df.columns, "B_baseline column should exist"
    assert 'delta_B' in df.columns, "delta_B column should exist"
    assert 'chi' in df.columns, "chi column should exist"
    assert 'status' in df.columns, "status column should exist"
    
    # Verify chi calculation (after baseline stabilizes)
    # After 24h (24 rows), baseline should be well-established
    stable_row = df.iloc[30]
    assert stable_row['B_baseline'] == 50.0, "Baseline should be 50.0 in stable period"
    assert stable_row['delta_B'] == 0.0, "Delta should be 0 when at baseline"
    assert stable_row['chi'] == 0.0, "Chi should be 0 when at baseline"
    assert stable_row['status'] == 'BELOW', "Status should be BELOW when chi < 0.14"
    
    print("✓ Basic compute_luft_metrics test passed")


def test_compute_luft_metrics_boundary_detection():
    """Test that the 0.15 boundary detection works correctly."""
    
    # Create data that crosses the 0.15 boundary
    timestamps = pd.date_range('2025-01-01', periods=100, freq='h')
    
    # Create a stable baseline of 100, then add 15% perturbation
    b_values = [100.0] * 50  # Establish baseline
    b_values += [115.0] * 50  # 15% increase (chi = 0.15)
    
    df = pd.DataFrame({
        'B': b_values
    }, index=timestamps)
    
    df = compute_luft_metrics(df)
    
    # Check shortly after the transition (row 52 = 2 hours after transition)
    # At this point, baseline is still 100.0, but B is now 115.0
    boundary_row = df.iloc[52]
    
    # B is 115, baseline is 100, so delta_B should be 15, chi should be 0.15
    assert abs(boundary_row['chi'] - 0.15) < 0.01, f"Chi should be near 0.15, got {boundary_row['chi']}"
    assert boundary_row['status'] in ['AT_BOUNDARY', 'PRECURSOR_MODE'], \
        f"Status should indicate boundary or precursor, got {boundary_row['status']}"
    
    print("✓ Boundary detection test passed")


def test_compute_luft_metrics_precursor_mode():
    """Test that PRECURSOR_MODE is detected for chi > 0.16."""
    
    timestamps = pd.date_range('2025-01-01', periods=100, freq='h')
    
    # Create a stable baseline of 100, then add 20% perturbation (well above boundary)
    b_values = [100.0] * 50
    b_values += [120.0] * 50  # 20% increase (chi = 0.20)
    
    df = pd.DataFrame({
        'B': b_values
    }, index=timestamps)
    
    df = compute_luft_metrics(df)
    
    # Check shortly after the transition (row 52 = 2 hours after transition)
    # At this point, baseline is still 100.0, but B is now 120.0
    precursor_row = df.iloc[52]
    assert precursor_row['chi'] > 0.16, f"Chi should be > 0.16 for precursor mode, got {precursor_row['chi']}"
    assert precursor_row['status'] == 'PRECURSOR_MODE', \
        f"Status should be PRECURSOR_MODE, got {precursor_row['status']}"
    
    print("✓ Precursor mode detection test passed")


def test_generate_storm_report_locked(capsys):
    """Test generate_storm_report when system is locked at boundary."""
    
    # Create synthetic data with 20 AT_BOUNDARY entries and 1 BELOW (95% locked)
    timestamps = pd.date_range('2025-01-01', periods=21, freq='h')
    
    df = pd.DataFrame({
        'status': ['AT_BOUNDARY'] * 20 + ['BELOW']
    }, index=timestamps)
    
    # Generate report
    generate_storm_report(df)
    
    # Capture printed output
    captured = capsys.readouterr()
    
    # Verify report contents
    assert "--- LUFT SYSTEM STATE REPORT ---" in captured.out
    assert "95.24%" in captured.out, "Should show 95.24% lock percentage"
    assert "FRACTAL REGULATION ACTIVE" in captured.out, "Should indicate active regulation"
    assert "dumping entropy" in captured.out
    
    print("✓ Storm report (locked) test passed")


def test_generate_storm_report_unstable(capsys):
    """Test generate_storm_report when system is unstable."""
    
    # Create synthetic data with only 10 AT_BOUNDARY entries out of 21 (47.6% locked)
    timestamps = pd.date_range('2025-01-01', periods=21, freq='h')
    
    df = pd.DataFrame({
        'status': ['AT_BOUNDARY'] * 10 + ['BELOW'] * 6 + ['PRECURSOR_MODE'] * 5
    }, index=timestamps)
    
    # Generate report
    generate_storm_report(df)
    
    # Capture printed output
    captured = capsys.readouterr()
    
    # Verify report contents
    assert "--- LUFT SYSTEM STATE REPORT ---" in captured.out
    assert "47.62%" in captured.out, "Should show 47.62% lock percentage"
    assert "UNSTABLE" in captured.out, "Should indicate unstable state"
    assert "PRECURSOR BUILDUP" in captured.out
    
    print("✓ Storm report (unstable) test passed")


def test_compute_chi_existing_function():
    """Test that the existing compute_chi function still works."""
    
    b_series = pd.Series([100, 110, 105, 115, 120])
    baseline = pd.Series([100, 100, 100, 100, 100])
    
    chi = compute_chi(b_series, baseline)
    
    expected = pd.Series([0.0, 0.1, 0.05, 0.15, 0.2])
    
    # Check that chi values are correct
    assert np.allclose(chi, expected, atol=1e-10), "Chi calculation should match expected values"
    
    print("✓ Existing compute_chi function test passed")


def test_rolling_median_existing_function():
    """Test that the existing rolling_median function still works."""
    
    series = pd.Series([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
    
    result = rolling_median(series, window_hours=3)
    
    # First window should use min_periods, so starts computing immediately
    assert not result.isna().all(), "Rolling median should compute values"
    
    # The 3rd value (index 2) should be the median of [10, 20, 30] = 20
    assert result.iloc[2] == 20.0, f"Third value should be 20.0, got {result.iloc[2]}"
    
    print("✓ Existing rolling_median function test passed")


def test_compute_luft_metrics_with_nans():
    """Test compute_luft_metrics handles NaN values gracefully."""
    
    timestamps = pd.date_range('2025-01-01', periods=50, freq='h')
    b_values = [100.0] * 50
    b_values[10] = np.nan  # Introduce a NaN
    
    df = pd.DataFrame({
        'B': b_values
    }, index=timestamps)
    
    # Should not raise an exception
    df = compute_luft_metrics(df)
    
    # Verify columns exist
    assert 'chi' in df.columns
    assert 'status' in df.columns
    
    print("✓ NaN handling test passed")


if __name__ == '__main__':
    # Run all tests
    print("Running imperial_math tests...\n")
    
    test_compute_luft_metrics_basic()
    test_compute_luft_metrics_boundary_detection()
    test_compute_luft_metrics_precursor_mode()
    # Skip capsys-dependent tests when running standalone
    # test_generate_storm_report_locked(None)
    # test_generate_storm_report_unstable(None)
    test_compute_chi_existing_function()
    test_rolling_median_existing_function()
    test_compute_luft_metrics_with_nans()
    
    print("\n✅ Non-capsys tests passed! Run with pytest for full test suite.")
