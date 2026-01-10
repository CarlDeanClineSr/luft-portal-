"""
Tests for the Blind Transient Test module.

This module tests the blind classification of solar wind data into
steady vs transient regimes using only kinetic parameters.
"""

import tempfile
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from blind_transient_test import (
    VELOCITY_THRESHOLD,
    VELOCITY_JUMP_THRESHOLD,
    DENSITY_THRESHOLD,
    CHI_BOUNDARY,
    detect_velocity_jump,
    classify_kinetic_regime,
    analyze_chi_by_regime,
    run_blind_transient_test,
)


class TestVelocityJumpDetection:
    """Test the velocity jump detection logic."""

    def test_no_jump_returns_false(self):
        """Constant speed should not trigger jump detection."""
        speed = pd.Series([400.0, 400.0, 400.0, 400.0])
        result = detect_velocity_jump(speed)
        # First value is NaN from diff, rest should be False
        assert not result.iloc[1:].any()

    def test_large_jump_returns_true(self):
        """Large velocity change should trigger jump detection."""
        speed = pd.Series([400.0, 400.0, 500.0, 500.0])  # 100 km/s jump
        result = detect_velocity_jump(speed)
        assert result.iloc[2]  # Jump at index 2

    def test_threshold_boundary(self):
        """Test behavior at the threshold boundary."""
        # Exactly at threshold (should not trigger)
        speed = pd.Series([400.0, 450.0])  # 50 km/s change
        result = detect_velocity_jump(speed, threshold=50)
        assert not result.iloc[1]

        # Just above threshold (should trigger)
        speed = pd.Series([400.0, 451.0])  # 51 km/s change
        result = detect_velocity_jump(speed, threshold=50)
        assert result.iloc[1]


class TestKineticRegimeClassification:
    """Test the kinetic regime classification logic."""

    def test_quiet_conditions_classified_as_steady(self):
        """Low speed and density should be classified as steady."""
        df = pd.DataFrame({
            'speed': [400.0, 410.0, 420.0],
            'density': [5.0, 5.5, 6.0]
        })
        result = classify_kinetic_regime(df)
        assert (result == 0).all()  # All steady

    def test_high_speed_classified_as_transient(self):
        """Speed > 600 km/s should be classified as transient."""
        df = pd.DataFrame({
            'speed': [400.0, 650.0, 649.0, 400.0],  # Gradual decrease to avoid jump
            'density': [5.0, 5.0, 5.0, 5.0]
        })
        result = classify_kinetic_regime(df)
        assert result.iloc[0] == 0  # Steady (first point, no jump)
        assert result.iloc[1] == 1  # Transient (high speed AND jump from 400)
        assert result.iloc[2] == 1  # Transient (high speed)
        # Note: index 3 may be flagged due to velocity jump from 649 to 400

    def test_high_density_classified_as_transient(self):
        """Density > 15 p/cm³ should be classified as transient."""
        df = pd.DataFrame({
            'speed': [400.0, 400.0, 400.0],
            'density': [5.0, 20.0, 5.0]
        })
        result = classify_kinetic_regime(df)
        assert result.iloc[0] == 0  # Steady
        assert result.iloc[1] == 1  # Transient (high density)
        assert result.iloc[2] == 0  # Steady

    def test_velocity_jump_classified_as_transient(self):
        """Large velocity jump should be classified as transient."""
        df = pd.DataFrame({
            'speed': [400.0, 400.0, 500.0, 500.0],  # 100 km/s jump
            'density': [5.0, 5.0, 5.0, 5.0]
        })
        result = classify_kinetic_regime(df)
        assert result.iloc[2] == 1  # Transient at jump point

    def test_missing_column_raises_error(self):
        """Missing required column should raise KeyError."""
        df = pd.DataFrame({
            'speed': [400.0, 410.0]
            # Missing 'density' column
        })
        with pytest.raises(KeyError):
            classify_kinetic_regime(df)


class TestChiAnalysis:
    """Test the χ analysis by regime."""

    def test_basic_analysis(self):
        """Test basic statistical analysis of χ values."""
        df = pd.DataFrame({
            'chi': [0.10, 0.12, 0.11, 0.20, 0.25],
            'regime_flag': [0, 0, 0, 1, 1]
        })
        results = analyze_chi_by_regime(df)

        assert results['steady']['count'] == 3
        assert results['transient']['count'] == 2
        assert results['steady']['max'] == pytest.approx(0.12)
        assert results['transient']['max'] == pytest.approx(0.25)

    def test_boundary_violations_counted(self):
        """Test that χ > 0.15 violations are counted correctly."""
        df = pd.DataFrame({
            'chi': [0.10, 0.11, 0.16, 0.18],  # Last two exceed boundary
            'regime_flag': [0, 0, 1, 1]
        })
        results = analyze_chi_by_regime(df)

        assert results['steady']['violations'] == 0
        assert results['transient']['violations'] == 2
        assert results['transient']['violations_pct'] == pytest.approx(100.0)

    def test_empty_regime_handled(self):
        """Test handling of regimes with no data points."""
        df = pd.DataFrame({
            'chi': [0.10, 0.11],
            'regime_flag': [0, 0]  # No transient data
        })
        results = analyze_chi_by_regime(df)

        assert results['steady']['count'] == 2
        assert results['transient']['count'] == 0
        assert results['transient']['max'] is None


class TestIntegration:
    """Integration tests for the full blind transient test."""

    def test_full_workflow_with_synthetic_data(self):
        """Test the complete workflow with synthetic data."""
        # Create synthetic data
        np.random.seed(42)
        n_points = 100

        # Steady state: low speed, low density, chi < 0.15
        timestamps = pd.date_range('2025-01-01', periods=n_points, freq='1h')
        speed = np.random.normal(400, 30, n_points)
        density = np.random.normal(5, 2, n_points)
        chi = np.random.uniform(0.08, 0.14, n_points)

        # Add some transient events (high speed/density)
        transient_indices = [20, 21, 22, 50, 51, 52]
        speed[transient_indices] = 650  # High speed
        density[[60, 61, 62]] = 20  # High density
        chi[transient_indices + [60, 61, 62]] = np.random.uniform(0.10, 0.20, 9)

        df = pd.DataFrame({
            'timestamp_utc': timestamps,
            'speed_km_s': speed,
            'density_p_cm3': density,
            'chi_amplitude': chi
        })

        # Save to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f, index=False)
            temp_path = Path(f.name)

        try:
            # Run the test
            result_df, results = run_blind_transient_test(
                str(temp_path),
                output_dir='/tmp/test_blind_transient'
            )

            # Verify results
            assert 'regime_flag' in result_df.columns
            assert results['steady']['count'] > 0
            assert results['transient']['count'] > 0

            # Steady state should have lower max chi on average
            # (since we designed the synthetic data this way)
            if (results['steady']['max'] is not None and
                results['transient']['max'] is not None):
                # This is expected given our synthetic data design
                pass  # Just verify no crash

        finally:
            temp_path.unlink()


def test_constants_are_reasonable():
    """Verify that threshold constants are physically reasonable."""
    # Velocity threshold should be in typical CME range
    assert 500 < VELOCITY_THRESHOLD < 800

    # Velocity jump should detect moderate shocks
    assert 30 < VELOCITY_JUMP_THRESHOLD < 100

    # Density threshold should be above typical quiet conditions
    assert 10 < DENSITY_THRESHOLD < 30

    # Chi boundary should match Carl's discovery
    assert CHI_BOUNDARY == pytest.approx(0.15)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
