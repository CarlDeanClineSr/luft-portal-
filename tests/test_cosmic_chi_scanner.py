"""
Tests for cosmic_chi_scanner.py

Tests the COSMIC CHI SCANNER functions including load_light_curve,
compute_stellar_chi, and scan_for_lattice_lock.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import tempfile
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from scripts.cosmic_chi_scanner import load_light_curve, compute_stellar_chi, scan_for_lattice_lock


def test_load_light_curve_with_flux():
    """Test load_light_curve with flux column."""
    
    # Create a temporary CSV file with flux data
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write('time,flux\n')
        f.write('1.0,100.0\n')
        f.write('2.0,95.0\n')
        f.write('3.0,100.0\n')
        temp_file = f.name
    
    try:
        df = load_light_curve(temp_file)
        assert df is not None, "DataFrame should not be None"
        assert 'time' in df.columns, "time column should exist"
        assert 'flux' in df.columns, "flux column should exist"
        assert len(df) == 3, "Should have 3 rows"
        print("✓ load_light_curve with flux test passed")
    finally:
        os.unlink(temp_file)


def test_load_light_curve_with_magnitude():
    """Test load_light_curve with magnitude column (converts to flux)."""
    
    # Create a temporary CSV file with magnitude data
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write('Time,Mag\n')
        f.write('1.0,15.0\n')
        f.write('2.0,15.5\n')
        f.write('3.0,15.0\n')
        temp_file = f.name
    
    try:
        df = load_light_curve(temp_file)
        assert df is not None, "DataFrame should not be None"
        assert 'time' in df.columns, "time column should exist (normalized)"
        assert 'mag' in df.columns, "mag column should exist (normalized)"
        assert 'flux' in df.columns, "flux column should be created"
        assert len(df) == 3, "Should have 3 rows"
        # Verify flux conversion (Flux = 10^(-0.4 * Mag))
        expected_flux = 10**(-0.4 * 15.0)
        assert abs(df['flux'].iloc[0] - expected_flux) < 1e-6, "Flux conversion should be correct"
        print("✓ load_light_curve with magnitude test passed")
    finally:
        os.unlink(temp_file)


def test_compute_stellar_chi():
    """Test compute_stellar_chi function."""
    
    # Create synthetic stellar data
    time = np.arange(0, 200, 1)
    # Create a baseline flux with a dip
    flux = np.full(200, 100.0)
    flux[90:110] = 85.0  # 15% dip
    
    df = pd.DataFrame({
        'time': time,
        'flux': flux
    })
    
    # Compute chi
    df = compute_stellar_chi(df)
    
    # Verify required columns exist
    assert 'flux_baseline' in df.columns, "flux_baseline column should exist"
    assert 'delta_flux' in df.columns, "delta_flux column should exist"
    assert 'chi' in df.columns, "chi column should exist"
    
    # Verify chi calculation in the dip region
    dip_region = df[(df['time'] >= 95) & (df['time'] <= 105)]
    # Chi should be around 0.15 (15% dip)
    mean_chi_dip = dip_region['chi'].mean()
    assert mean_chi_dip > 0.1, "Chi in dip region should be > 0.1"
    assert mean_chi_dip < 0.2, "Chi in dip region should be < 0.2"
    
    print(f"✓ compute_stellar_chi test passed (mean chi in dip: {mean_chi_dip:.4f})")


def test_scan_for_lattice_lock_detected():
    """Test scan_for_lattice_lock when lock is present."""
    
    # Create synthetic data with chi values at 0.15
    time = np.arange(0, 100, 1)
    chi = np.full(100, 0.02)  # Baseline chi
    chi[40:50] = 0.15  # Lock at 0.15
    
    df = pd.DataFrame({
        'time': time,
        'chi': chi
    })
    
    # Should detect the lock
    result = scan_for_lattice_lock(df, tolerance=0.01)
    assert result is True, "Should detect lattice lock"
    print("✓ scan_for_lattice_lock detection test passed")


def test_scan_for_lattice_lock_not_detected():
    """Test scan_for_lattice_lock when no lock is present."""
    
    # Create synthetic data without chi values at 0.15
    time = np.arange(0, 100, 1)
    chi = np.full(100, 0.02)  # All below threshold
    chi[40:50] = 0.08  # Some variation but not at 0.15
    
    df = pd.DataFrame({
        'time': time,
        'chi': chi
    })
    
    # Should not detect the lock
    result = scan_for_lattice_lock(df, tolerance=0.01)
    assert result is False, "Should not detect lattice lock"
    print("✓ scan_for_lattice_lock no detection test passed")


def test_deprecated_method_not_used():
    """Test that deprecated fillna(method='bfill') is not used."""
    
    # Read the script file and check it doesn't use the deprecated method
    script_path = Path(__file__).parent.parent / "scripts" / "cosmic_chi_scanner.py"
    with open(script_path, 'r') as f:
        content = f.read()
    
    # Check that fillna(method= is not used
    assert "fillna(method=" not in content, "Deprecated fillna(method=) should not be used"
    # Check that .bfill() is used instead
    assert ".bfill()" in content, "Should use .bfill() instead of fillna(method='bfill')"
    print("✓ Deprecated method check passed")


if __name__ == '__main__':
    test_load_light_curve_with_flux()
    test_load_light_curve_with_magnitude()
    test_compute_stellar_chi()
    test_scan_for_lattice_lock_detected()
    test_scan_for_lattice_lock_not_detected()
    test_deprecated_method_not_used()
    print("\n✅ All cosmic_chi_scanner tests passed!")
