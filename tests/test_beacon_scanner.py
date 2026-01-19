"""
Tests for NSVS Beacon Chain Scanner

Tests the beacon detection logic and coordinate resolution.
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nsvs_beacon_chain_scanner import BeaconScanner, NSVS_TARGETS


class TestBeaconScanner:
    """Test beacon scanner functionality"""
    
    def test_scanner_initialization(self):
        """Test that scanner initializes properly"""
        scanner = BeaconScanner()
        assert scanner is not None
        assert hasattr(scanner, 'PULSE_MAGNITUDE_THRESHOLD')
        assert hasattr(scanner, 'QUIET_MAGNITUDE_THRESHOLD')
        assert hasattr(scanner, 'BEACON_FLUX_RATIO_THRESHOLD')
    
    def test_detection_thresholds(self):
        """Test that detection thresholds are set correctly"""
        scanner = BeaconScanner()
        assert scanner.PULSE_MAGNITUDE_THRESHOLD == 11.0
        assert scanner.QUIET_MAGNITUDE_THRESHOLD == 13.0
        assert scanner.BEACON_FLUX_RATIO_THRESHOLD == 5.0
        assert scanner.CONE_SEARCH_RADIUS == 5
    
    def test_nsvs_targets_loaded(self):
        """Test that all NSVS targets are defined"""
        assert len(NSVS_TARGETS) == 8
        assert "2354429" in NSVS_TARGETS
        assert "7642696" in NSVS_TARGETS
    
    def test_nsvs_2354429_coordinates(self):
        """Test NSVS 2354429 has correct coordinates"""
        target = NSVS_TARGETS["2354429"]
        assert target['ra'] == pytest.approx(240.25563, abs=0.001)
        assert target['dec'] == pytest.approx(27.61100, abs=0.001)
        assert target['name'] == "NSVS 2354429"
    
    def test_all_targets_have_coordinates(self):
        """Test that all targets have coordinates defined"""
        for nsvs_id, target in NSVS_TARGETS.items():
            assert 'ra' in target
            assert 'dec' in target
            assert target['ra'] is not None
            assert target['dec'] is not None
            assert isinstance(target['ra'], (int, float))
            assert isinstance(target['dec'], (int, float))
    
    def test_analyze_known_beacon(self):
        """Test analysis of NSVS 2354429 known beacon data"""
        scanner = BeaconScanner()
        data = scanner._get_nsvs_2354429_data()
        
        target_info = NSVS_TARGETS["2354429"]
        analysis = scanner.analyze_light_curve(data, target_info)
        
        # Should be detected as beacon
        assert analysis['is_beacon'] is True
        assert analysis['has_pulse_state'] is True
        assert analysis['min_magnitude'] == pytest.approx(10.317, abs=0.001)
        assert analysis['flux_ratio'] > scanner.BEACON_FLUX_RATIO_THRESHOLD
        
        # Should have event_time field with HJD of pulse
        assert 'event_time' in analysis
        assert 'HJD' in analysis['event_time']
        assert '2456999.929' in analysis['event_time']  # Known pulse time
    
    def test_analyze_empty_data(self):
        """Test analysis with no data"""
        scanner = BeaconScanner()
        analysis = scanner.analyze_light_curve([], {})
        
        assert analysis['is_beacon'] is False
        assert 'reason' in analysis
        assert 'No data' in analysis['reason']
    
    def test_flux_ratio_calculation(self):
        """Test flux ratio calculation for known magnitude difference"""
        scanner = BeaconScanner()
        
        # Create test data with known magnitude difference
        # Δmag = 2.5 should give flux ratio of 10
        data = [
            {'hjd': 1, 'mag': 12.5},  # median
            {'hjd': 2, 'mag': 10.0},   # pulse (2.5 mag brighter)
            {'hjd': 3, 'mag': 12.5},
        ]
        
        analysis = scanner.analyze_light_curve(data, {})
        
        # Flux ratio should be approximately 10
        assert analysis['flux_ratio'] == pytest.approx(10.0, rel=0.01)
    
    def test_cygnus_lyra_cluster(self):
        """Test that most targets are in Cygnus/Lyra region"""
        cygnus_lyra_count = 0
        
        for nsvs_id, target in NSVS_TARGETS.items():
            # Cygnus/Lyra region is approximately RA ~300-310°, Dec ~+40-42°
            if 300 <= target['ra'] <= 310 and 40 <= target['dec'] <= 43:
                cygnus_lyra_count += 1
        
        # 7 out of 8 targets should be in Cygnus/Lyra
        assert cygnus_lyra_count == 7


class TestBeaconDetection:
    """Test beacon detection criteria"""
    
    def test_pulse_detection(self):
        """Test that bright events are detected as pulses"""
        scanner = BeaconScanner()
        
        # Magnitude 10 should be detected as pulse (< 11)
        data = [
            {'hjd': 1, 'mag': 12.5},
            {'hjd': 2, 'mag': 10.0},  # PULSE
            {'hjd': 3, 'mag': 12.5},
        ]
        
        analysis = scanner.analyze_light_curve(data, {})
        assert analysis['has_pulse_state'] is True
        assert analysis['min_magnitude'] < scanner.PULSE_MAGNITUDE_THRESHOLD
    
    def test_quiet_state_detection(self):
        """Test that dim baseline is detected as quiet state"""
        scanner = BeaconScanner()
        
        # Magnitude 14 should be detected as quiet (> 13)
        data = [
            {'hjd': 1, 'mag': 14.0},  # QUIET
            {'hjd': 2, 'mag': 10.0},
            {'hjd': 3, 'mag': 14.0},  # QUIET
        ]
        
        analysis = scanner.analyze_light_curve(data, {})
        assert analysis['has_quiet_state'] is True
        assert analysis['max_magnitude'] > scanner.QUIET_MAGNITUDE_THRESHOLD
    
    def test_non_beacon_variability(self):
        """Test that normal variable stars are not classified as beacons"""
        scanner = BeaconScanner()
        
        # Small variation (< 5× flux change)
        data = [
            {'hjd': 1, 'mag': 12.5},
            {'hjd': 2, 'mag': 12.0},  # Only 0.5 mag change
            {'hjd': 3, 'mag': 12.5},
        ]
        
        analysis = scanner.analyze_light_curve(data, {})
        assert analysis['flux_ratio'] < scanner.BEACON_FLUX_RATIO_THRESHOLD


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
