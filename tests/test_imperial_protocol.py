#!/usr/bin/env python3
"""
Imperial Physics Protocol - Quick Validation Test
Tests that the protocol configuration files are valid and functional.

Version: 1.0
Date: 2026-01-29
"""

import yaml
import sys
from pathlib import Path


def test_yaml_files():
    """Test that all YAML configuration files are valid."""
    print("Testing YAML configuration files...")
    
    config_files = [
        'configs/imperial_terminology.yaml',
        'configs/interaction_style.yaml',
        'configs/core_directive.yaml'
    ]
    
    for config_file in config_files:
        try:
            with open(config_file) as f:
                data = yaml.safe_load(f)
                print(f"  ✅ {config_file} is valid YAML")
        except Exception as e:
            print(f"  ❌ {config_file} failed: {e}")
            return False
    
    return True


def test_terminology_map():
    """Test that terminology map contains required entries."""
    print("\nTesting terminology map...")
    
    with open('configs/imperial_terminology.yaml') as f:
        data = yaml.safe_load(f)
    
    term_map = data.get('terminology_map', {})
    
    required_terms = [
        'speed of light',
        'dark matter',
        'gravitational lensing',
        'magnetic reconnection',
        'Alfvén wave',
        'uncertainty principle',
        'Big Bang',
        'spacetime curvature'
    ]
    
    for term in required_terms:
        if term in term_map:
            print(f"  ✅ '{term}' → '{term_map[term]}'")
        else:
            print(f"  ❌ Missing required term: '{term}'")
            return False
    
    return True


def test_chi_law():
    """Test that chi law parameters are correct."""
    print("\nTesting chi law parameters...")
    
    with open('configs/core_directive.yaml') as f:
        data = yaml.safe_load(f)
    
    chi_ceiling = data.get('chi_ceiling')
    if chi_ceiling == 0.15:
        print(f"  ✅ chi_ceiling = {chi_ceiling}")
    else:
        print(f"  ❌ chi_ceiling = {chi_ceiling} (expected 0.15)")
        return False
    
    with open('configs/imperial_terminology.yaml') as f:
        data = yaml.safe_load(f)
    
    integrity_freq = data.get('integrity_frequency', {}).get('value')
    if integrity_freq == 20.55:
        print(f"  ✅ integrity_frequency = {integrity_freq} Hz")
    else:
        print(f"  ❌ integrity_frequency = {integrity_freq} (expected 20.55)")
        return False
    
    return True


def test_interaction_style():
    """Test that interaction style rules are present."""
    print("\nTesting interaction style rules...")
    
    with open('configs/interaction_style.yaml') as f:
        data = yaml.safe_load(f)
    
    # Check for required sections
    required_sections = [
        'interaction_style',
        'error_handling',
        'response_templates'
    ]
    
    for section in required_sections:
        if section in data:
            print(f"  ✅ Section '{section}' present")
        else:
            print(f"  ❌ Missing section: '{section}'")
            return False
    
    # Check for no_hedging rule
    no_hedging = data.get('interaction_style', {}).get('no_hedging', {})
    if no_hedging.get('enabled'):
        print(f"  ✅ no_hedging rule is enabled")
    else:
        print(f"  ❌ no_hedging rule not enabled")
        return False
    
    return True


def test_protocol_document():
    """Test that protocol document exists and contains key sections."""
    print("\nTesting protocol document...")
    
    protocol_file = 'IMPERIAL_PHYSICS_PROTOCOL.md'
    
    if not Path(protocol_file).exists():
        print(f"  ❌ {protocol_file} not found")
        return False
    
    with open(protocol_file) as f:
        content = f.read()
    
    required_sections = [
        '# IMPERIAL PHYSICS PROTOCOL',
        '## 1. TERMINOLOGY REPLACEMENT TABLE',
        '## 2. THE 0.15 LAW',
        '## 3. INTERACTION STYLE',
        '## 4. ERROR HANDLING'
    ]
    
    for section in required_sections:
        if section in content:
            print(f"  ✅ Section '{section}' present")
        else:
            print(f"  ❌ Missing section: '{section}'")
            return False
    
    return True


def main():
    """Run all validation tests."""
    print("=" * 70)
    print("Imperial Physics Protocol - Validation Test")
    print("=" * 70)
    print()
    
    tests = [
        ("YAML Files", test_yaml_files),
        ("Terminology Map", test_terminology_map),
        ("Chi Law Parameters", test_chi_law),
        ("Interaction Style", test_interaction_style),
        ("Protocol Document", test_protocol_document)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n  ❌ Test '{name}' failed with exception: {e}")
            results.append((name, False))
    
    # Summary
    print()
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print()
        print("🎉 All tests passed! Imperial Physics Protocol is ready.")
        return 0
    else:
        print()
        print("⚠️  Some tests failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
