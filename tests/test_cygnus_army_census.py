"""
Tests for Cygnus Army Census Scanner

Tests the phase calculation, resonance detection, and report generation logic.
"""

import pytest
import sys
import os
import math
import pandas as pd
from unittest.mock import patch, mock_open

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import after path setup
from src.cygnus_army_census import (
    get_phase, 
    get_mock_data, 
    RA_CENTER, 
    DEC_CENTER, 
    TARGETS, 
    TOLERANCE
)


class TestPhaseCalculation:
    """Test Cline Phase Calculation"""
    
    def test_phase_calculation_basic(self):
        """Test basic phase calculation"""
        # HJD with fractional part 0.2152 should give phase ~1.3526 rad
        hjd = 2459000.7152
        phase = get_phase(hjd)
        expected_phase = ((0.7152 + 0.5) % 1.0) * 2 * math.pi
        assert phase == pytest.approx(expected_phase, abs=0.0001)
    
    def test_phase_calculation_range(self):
        """Test that phase is always in [0, 2π)"""
        test_hjds = [2459000.0, 2459000.5, 2459000.9999, 2458999.5]
        for hjd in test_hjds:
            phase = get_phase(hjd)
            assert 0 <= phase < 2 * math.pi
    
    def test_phase_calculation_periodicity(self):
        """Test that phase calculation is periodic with period 1 day"""
        base_hjd = 2459000.5
        phase1 = get_phase(base_hjd)
        phase2 = get_phase(base_hjd + 1.0)
        phase3 = get_phase(base_hjd + 10.0)
        
        assert phase1 == pytest.approx(phase2, abs=0.0001)
        assert phase1 == pytest.approx(phase3, abs=0.0001)
    
    def test_phase_target_1_calculation(self):
        """Test phase calculation for target 1 (1.3526 rad)"""
        # To get phase 1.3526 rad, we need day_frac = 1.3526/(2*pi) ≈ 0.2152
        # So HJD = X.2152 gives (0.2152 + 0.5) % 1.0 = 0.7152
        # And 0.7152 * 2π ≈ 4.493 rad, not 1.3526
        # Actually, we need (X + 0.5) % 1.0 = 0.2152
        # So X % 1.0 = 0.7152 - 0.5 = 0.2152 (if >= 0) or 0.7152 + 0.5 = 1.2152 -> 0.2152
        # Actually X.7152 gives us the right answer
        hjd = 2459000.7152
        phase = get_phase(hjd)
        # (0.7152 + 0.5) % 1.0 = 0.2152
        # 0.2152 * 2π = 1.3526
        day_frac = (0.7152 + 0.5) % 1.0
        expected = day_frac * 2 * math.pi
        assert phase == pytest.approx(expected, abs=0.0001)
        assert phase == pytest.approx(1.3526, abs=0.01)
    
    def test_phase_target_2_calculation(self):
        """Test phase calculation for target 2 (4.0143 rad)"""
        # For phase 4.0143 rad, day_frac = 4.0143/(2*pi) ≈ 0.6388
        # (X + 0.5) % 1.0 = 0.6388
        # X % 1.0 = 0.1388
        hjd = 2459000.1388
        phase = get_phase(hjd)
        day_frac = (0.1388 + 0.5) % 1.0
        expected = day_frac * 2 * math.pi
        assert phase == pytest.approx(expected, abs=0.0001)
        assert phase == pytest.approx(4.0143, abs=0.01)


class TestMockData:
    """Test mock data generation"""
    
    def test_mock_data_structure(self):
        """Test that mock data has correct structure"""
        df = get_mock_data()
        
        assert not df.empty
        assert 'id' in df.columns
        assert 'mag_v' in df.columns
        assert 'HJD' in df.columns
    
    def test_mock_data_count(self):
        """Test that mock data has expected number of stars"""
        df = get_mock_data()
        assert len(df) == 5
    
    def test_mock_data_star_ids(self):
        """Test that mock data has ASAS-SN format star IDs"""
        df = get_mock_data()
        for star_id in df['id']:
            assert star_id.startswith('ASAS-SN-V')
    
    def test_mock_data_has_locked_stars(self):
        """Test that mock data includes stars at resonance phases"""
        df = get_mock_data()
        
        locked_count = 0
        for _, star in df.iterrows():
            phase = get_phase(star['HJD'])
            for target in TARGETS:
                if abs(phase - target) < TOLERANCE:
                    locked_count += 1
                    break
        
        # Should have at least 2 locked stars in mock data
        assert locked_count >= 2


class TestResonanceDetection:
    """Test resonance detection logic"""
    
    def test_resonance_detection_target_1(self):
        """Test detection of resonance at target 1"""
        # Create a phase very close to target 1 (1.3526 rad)
        phase = 1.3526
        
        is_locked = False
        for target in TARGETS:
            if abs(phase - target) < TOLERANCE:
                is_locked = True
                break
        
        assert is_locked is True
    
    def test_resonance_detection_target_2(self):
        """Test detection of resonance at target 2"""
        # Create a phase very close to target 2 (4.0143 rad)
        phase = 4.0143
        
        is_locked = False
        for target in TARGETS:
            if abs(phase - target) < TOLERANCE:
                is_locked = True
                break
        
        assert is_locked is True
    
    def test_resonance_detection_drift(self):
        """Test that non-resonant phases are marked as drift"""
        # Create a phase far from any target
        phase = 3.0  # Between the two targets but not close to either
        
        is_locked = False
        for target in TARGETS:
            if abs(phase - target) < TOLERANCE:
                is_locked = True
                break
        
        assert is_locked is False
    
    def test_resonance_tolerance_boundary(self):
        """Test resonance detection at tolerance boundary"""
        # Test slightly outside TOLERANCE distance from target
        phase_outside = TARGETS[0] + TOLERANCE + 0.001
        
        is_locked = False
        for target in TARGETS:
            if abs(phase_outside - target) < TOLERANCE:
                is_locked = True
                break
        
        # Outside the boundary, should not be locked
        assert is_locked is False
        
        # Just inside the boundary should be locked
        phase_inside = TARGETS[0] + TOLERANCE * 0.9
        is_locked = False
        for target in TARGETS:
            if abs(phase_inside - target) < TOLERANCE:
                is_locked = True
                break
        
        assert is_locked is True


class TestConfiguration:
    """Test configuration constants"""
    
    def test_ra_center_valid(self):
        """Test that RA_CENTER is valid coordinate"""
        ra = float(RA_CENTER)
        assert 0 <= ra < 360
    
    def test_dec_center_valid(self):
        """Test that DEC_CENTER is valid coordinate"""
        dec = float(DEC_CENTER)
        assert -90 <= dec <= 90
    
    def test_targets_in_valid_range(self):
        """Test that all targets are in valid phase range [0, 2π)"""
        for target in TARGETS:
            assert 0 <= target < 2 * math.pi
    
    def test_tolerance_positive(self):
        """Test that tolerance is positive"""
        assert TOLERANCE > 0
    
    def test_tabbys_star_coordinates(self):
        """Test that coordinates match Tabby's Star (KIC8462852)"""
        # Tabby's Star is at approximately RA 301.56°, Dec 44.46°
        ra = float(RA_CENTER)
        dec = float(DEC_CENTER)
        
        assert ra == pytest.approx(301.5644, abs=0.01)
        assert dec == pytest.approx(44.4568, abs=0.01)


class TestPhaseCalculationEdgeCases:
    """Test edge cases in phase calculation"""
    
    def test_phase_with_zero_hjd(self):
        """Test phase calculation with HJD = 0"""
        phase = get_phase(0)
        expected = (0.5 % 1.0) * 2 * math.pi
        assert phase == pytest.approx(expected, abs=0.0001)
    
    def test_phase_with_negative_hjd(self):
        """Test phase calculation with negative HJD"""
        phase = get_phase(-100.5)
        # Should still return valid phase in [0, 2π)
        assert 0 <= phase < 2 * math.pi
    
    def test_phase_with_large_hjd(self):
        """Test phase calculation with very large HJD"""
        phase = get_phase(2500000.123)
        # Should still return valid phase in [0, 2π)
        assert 0 <= phase < 2 * math.pi
    
    def test_phase_calculation_consistency(self):
        """Test that same HJD always gives same phase"""
        hjd = 2459000.7152
        phase1 = get_phase(hjd)
        phase2 = get_phase(hjd)
        assert phase1 == phase2


class TestResonanceLocking:
    """Test resonance lock counting logic"""
    
    def test_lock_only_counted_once_per_star(self):
        """Test that each star is only counted once even if near multiple targets"""
        # This is a logic test - if a star somehow matched multiple targets,
        # it should only be counted once due to the 'break' statement
        
        # Create a scenario where we're checking if break prevents double-counting
        test_phase = TARGETS[0] + 0.01  # Very close to first target
        
        lock_count = 0
        for target in TARGETS:
            if abs(test_phase - target) < TOLERANCE:
                lock_count += 1
                break  # Should stop after first match
        
        assert lock_count == 1
    
    def test_different_stars_counted_separately(self):
        """Test that different locked stars are counted separately"""
        # Create multiple locked stars
        locked_phases = [1.3526, 1.36, 4.0143]  # 3 stars near targets
        
        total_locked = 0
        for phase in locked_phases:
            for target in TARGETS:
                if abs(phase - target) < TOLERANCE:
                    total_locked += 1
                    break
        
        assert total_locked == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
