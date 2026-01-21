#!/usr/bin/env python3
"""
Universal Boundary Engine - Test Suite
=======================================

Quick verification that all components work correctly.
"""

import sys
import numpy as np

def test_imports():
    """Test that all imports work."""
    print("=" * 60)
    print("TEST 1: Module Imports")
    print("=" * 60)
    try:
        from universal_boundary_engine import (
            calculate_chi,
            validate_boundary,
            detect_harmonic_mode,
            detect_binary_scaling,
            calculate_fundamental_unifications,
            CHI_UNIVERSAL,
            COUPLING_FREQUENCY
        )
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def test_constants():
    """Test fundamental constants."""
    print("\n" + "=" * 60)
    print("TEST 2: Fundamental Constants")
    print("=" * 60)
    try:
        from universal_boundary_engine import (
            CHI_UNIVERSAL,
            G_FROM_CHI,
            G_NEWTON,
            CHI_FROM_MASS_RATIO,
            COUPLING_FREQUENCY,
            ALPHA
        )
        
        print(f"χ universal: {CHI_UNIVERSAL:.6f}")
        print(f"G from χ: {G_FROM_CHI:.5e}")
        print(f"G CODATA: {G_NEWTON:.5e}")
        
        error = abs(G_FROM_CHI - G_NEWTON) / G_NEWTON * 100
        print(f"G error: {error:.3f}%")
        
        assert error < 1.0, "G error too large"
        assert CHI_UNIVERSAL == 0.15, "χ not 0.15"
        assert 20.5 < COUPLING_FREQUENCY < 20.6, "Coupling frequency out of range"
        
        print("✅ All constants valid")
        return True
    except Exception as e:
        print(f"❌ Constants test failed: {e}")
        return False


def test_chi_calculation():
    """Test χ calculation."""
    print("\n" + "=" * 60)
    print("TEST 3: Chi Calculation")
    print("=" * 60)
    try:
        from universal_boundary_engine import calculate_chi
        
        # Simple test data
        B_baseline = 10.0
        B_data = B_baseline + np.array([0.5, 1.0, 1.5, 1.0, 0.5, 0.0])
        
        chi = calculate_chi(B_data)
        
        print(f"Input B: {B_data}")
        print(f"Calculated χ: {chi}")
        print(f"Max χ: {np.max(chi):.6f}")
        
        assert len(chi) == len(B_data), "χ length mismatch"
        assert np.all(chi >= 0), "Negative χ detected"
        
        print("✅ Chi calculation works")
        return True
    except Exception as e:
        print(f"❌ Chi calculation failed: {e}")
        return False


def test_boundary_validation():
    """Test boundary validation."""
    print("\n" + "=" * 60)
    print("TEST 4: Boundary Validation")
    print("=" * 60)
    try:
        from universal_boundary_engine import validate_boundary
        
        # Test data: all below boundary
        chi_good = np.array([0.10, 0.12, 0.14, 0.13, 0.11])
        validation = validate_boundary(chi_good)
        
        print(f"Test data (all < 0.15): {chi_good}")
        print(f"Max χ: {validation['max_chi']:.6f}")
        print(f"Violations: {validation['violations']}")
        print(f"Compliance: {validation['compliance']}")
        
        assert validation['compliance'] == True, "Should be compliant"
        assert validation['violations'] == 0, "Should have no violations"
        
        # Test data: with violation
        chi_bad = np.array([0.10, 0.12, 0.16, 0.13, 0.11])
        validation2 = validate_boundary(chi_bad)
        
        print(f"\nTest data (with violation): {chi_bad}")
        print(f"Max χ: {validation2['max_chi']:.6f}")
        print(f"Violations: {validation2['violations']}")
        print(f"Compliance: {validation2['compliance']}")
        
        assert validation2['compliance'] == False, "Should not be compliant"
        assert validation2['violations'] > 0, "Should have violations"
        
        print("✅ Boundary validation works")
        return True
    except Exception as e:
        print(f"❌ Boundary validation failed: {e}")
        return False


def test_harmonic_detection():
    """Test harmonic mode detection."""
    print("\n" + "=" * 60)
    print("TEST 5: Harmonic Mode Detection")
    print("=" * 60)
    try:
        from universal_boundary_engine import detect_harmonic_mode
        
        # Fundamental mode
        chi_fundamental = np.array([0.10, 0.12, 0.14, 0.15, 0.14])
        harmonic1 = detect_harmonic_mode(chi_fundamental)
        
        print(f"Test: Fundamental mode (max χ ≈ 0.15)")
        print(f"Detected mode: n={harmonic1['harmonic_mode']}")
        print(f"Is harmonic: {harmonic1['is_harmonic']}")
        
        # First harmonic
        chi_first_harmonic = np.array([0.28, 0.29, 0.30, 0.31, 0.29])
        harmonic2 = detect_harmonic_mode(chi_first_harmonic)
        
        print(f"\nTest: First harmonic (max χ ≈ 0.30)")
        print(f"Detected mode: n={harmonic2['harmonic_mode']}")
        print(f"Theoretical χ: {harmonic2['theoretical_chi']:.3f}")
        print(f"Is harmonic: {harmonic2['is_harmonic']}")
        
        assert harmonic2['harmonic_mode'] == 2, "Should detect n=2"
        
        print("✅ Harmonic detection works")
        return True
    except Exception as e:
        print(f"❌ Harmonic detection failed: {e}")
        return False


def test_binary_scaling():
    """Test binary scaling detection."""
    print("\n" + "=" * 60)
    print("TEST 6: Binary Scaling Detection")
    print("=" * 60)
    try:
        from universal_boundary_engine import detect_binary_scaling
        
        # Perfect binary scaling
        base = 0.1
        periods = np.array([0.1, 0.2, 0.4, 0.8, 1.6])  # 2^0, 2^1, 2^2, 2^3, 2^4
        
        scaling = detect_binary_scaling(periods, base)
        
        print(f"Test periods: {periods}")
        print(f"Base period: {base}")
        print(f"Detected: {scaling['detected']}")
        print(f"Compliance rate: {scaling['compliance_rate']*100:.1f}%")
        print(f"Powers: {scaling['detected_powers']}")
        
        assert scaling['detected'] == True, "Should detect binary scaling"
        
        print("✅ Binary scaling detection works")
        return True
    except Exception as e:
        print(f"❌ Binary scaling failed: {e}")
        return False


def test_unifications():
    """Test fundamental unifications."""
    print("\n" + "=" * 60)
    print("TEST 7: Fundamental Unifications")
    print("=" * 60)
    try:
        from universal_boundary_engine import calculate_fundamental_unifications
        
        unif = calculate_fundamental_unifications()
        
        print("Gravity:")
        print(f"  Derived: {unif['gravity']['derived_G']:.5e}")
        print(f"  CODATA: {unif['gravity']['codata_G']:.5e}")
        print(f"  Error: {unif['gravity']['error_percent']:.3f}%")
        
        print("\nMass Ratio:")
        print(f"  χ from mass: {unif['mass_ratio']['chi_from_mass']:.6f}")
        print(f"  Error: {unif['mass_ratio']['error_percent']:.3f}%")
        
        print("\nCoupling:")
        print(f"  Frequency: {unif['coupling']['frequency_hz']:.4f} Hz")
        
        assert unif['gravity']['error_percent'] < 1.0, "G error too large"
        assert unif['mass_ratio']['error_percent'] < 5.0, "Mass error too large"
        
        print("✅ Unifications calculated correctly")
        return True
    except Exception as e:
        print(f"❌ Unifications failed: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("UNIVERSAL BOUNDARY ENGINE - TEST SUITE")
    print("=" * 60)
    print()
    
    tests = [
        test_imports,
        test_constants,
        test_chi_calculation,
        test_boundary_validation,
        test_harmonic_detection,
        test_binary_scaling,
        test_unifications
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if all(results):
        print("\n✅ ALL TESTS PASSED")
        print("\nThe Universal Boundary Engine is ready for use!")
        print("=" * 60)
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        print("\nPlease review the errors above.")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
