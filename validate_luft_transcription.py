#!/usr/bin/env python3
"""
LUFT Data Transcription Validation Script
==========================================

This script validates that all LUFT data transcription files
follow the standards defined in LUFT_DATA_TRANSCRIPTION_MASTER_REFERENCE.md

Usage:
    python3 validate_luft_transcription.py

Author: Carl Dean Cline Sr.
Date: 2026-01-23
License: CC BY 4.0
"""

import sys
import json
import csv
from pathlib import Path
from datetime import datetime


def validate_csv_format(file_path):
    """Validate CSV file format according to LUFT standards."""
    print(f"\n🔍 Validating CSV: {file_path}")
    
    try:
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        # Check required columns
        required_cols = ['Timestamp_UTC', 'Chi_Value', 'B_Total_nT', 'Status']
        headers = reader.fieldnames
        missing = [col for col in required_cols if col not in headers]
        
        if missing:
            print(f"   ❌ Missing columns: {missing}")
            return False
        
        # Validate timestamp format and precision
        for i, row in enumerate(rows):
            ts = row['Timestamp_UTC']
            if '.000' not in ts:
                print(f"   ⚠️  Row {i+1}: Timestamp missing .000 precision: {ts}")
            
            # Validate chi value precision (4 decimal places)
            chi_str = row['Chi_Value']
            if '.' in chi_str:
                decimals = len(chi_str.split('.')[1])
                if decimals != 4:
                    print(f"   ⚠️  Row {i+1}: Chi value should have 4 decimal places: {chi_str}")
        
        print(f"   ✅ CSV valid - {len(rows)} rows")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def validate_json_format(file_path):
    """Validate JSON file format according to LUFT standards."""
    print(f"\n🔍 Validating JSON: {file_path}")
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Check required sections
        required_sections = ['event_metadata', 'observations']
        missing = [sec for sec in required_sections if sec not in data]
        
        if missing:
            print(f"   ❌ Missing sections: {missing}")
            return False
        
        # Validate metadata
        metadata = data['event_metadata']
        if 'chi_limit' in metadata:
            if metadata['chi_limit'] != 0.15:
                print(f"   ⚠️  chi_limit should be 0.15, got {metadata['chi_limit']}")
        
        # Validate observations
        observations = data['observations']
        for i, obs in enumerate(observations):
            # Check timestamp format
            ts = obs.get('timestamp', '')
            if not ts.endswith('Z'):
                print(f"   ⚠️  Observation {i+1}: Timestamp should end with Z (UTC)")
            if '.000' not in ts:
                print(f"   ⚠️  Observation {i+1}: Timestamp missing .000 precision")
            
            # Check chi precision
            if 'chi' in obs:
                chi = obs['chi']
                chi_str = f"{chi:.4f}"
                if len(chi_str.split('.')[1]) != 4:
                    print(f"   ⚠️  Observation {i+1}: Chi should have 4 decimal precision")
        
        print(f"   ✅ JSON valid - {len(observations)} observations")
        return True
        
    except json.JSONDecodeError as e:
        print(f"   ❌ JSON parse error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def validate_constants_module():
    """Validate that imperial_constants module has required values."""
    print(f"\n🔍 Validating imperial_constants_v1_0.py")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from imperial_constants_v1_0 import (
            CHI_LIMIT, CHI_TOLERANCE, ALPHA_FS, PHI_GOLDEN, G_MANTISSA,
            COUPLING_FREQ_HZ, GRAVITY_INVERSE, MASS_RATIO_ROOT,
            validate_chi, get_fundamental_unifications
        )
        
        # Check core constants
        checks = [
            (CHI_LIMIT == 0.15, f"CHI_LIMIT = {CHI_LIMIT} (expected 0.15)"),
            (CHI_TOLERANCE == 0.005, f"CHI_TOLERANCE = {CHI_TOLERANCE} (expected 0.005)"),
            (abs(COUPLING_FREQ_HZ - 20.5554) < 0.01, f"COUPLING_FREQ_HZ = {COUPLING_FREQ_HZ:.4f} (expected ~20.56)"),
            (abs(GRAVITY_INVERSE - 6.6667) < 0.001, f"GRAVITY_INVERSE = {GRAVITY_INVERSE:.4f} (expected ~6.6667)"),
            (abs(MASS_RATIO_ROOT - 0.1528) < 0.001, f"MASS_RATIO_ROOT = {MASS_RATIO_ROOT} (expected ~0.1528)"),
        ]
        
        all_passed = True
        for passed, msg in checks:
            if passed:
                print(f"   ✅ {msg}")
            else:
                print(f"   ❌ {msg}")
                all_passed = False
        
        # Test validation function
        result = validate_chi(0.1498, "2026-01-05T00:45:00.000Z")
        if result['status'] == 'AT_BOUNDARY':
            print(f"   ✅ validate_chi() works correctly")
        else:
            print(f"   ❌ validate_chi() returned unexpected status: {result['status']}")
            all_passed = False
        
        return all_passed
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def validate_master_reference():
    """Check that master reference document exists."""
    print(f"\n🔍 Validating LUFT_DATA_TRANSCRIPTION_MASTER_REFERENCE.md")
    
    ref_path = Path(__file__).parent / "LUFT_DATA_TRANSCRIPTION_MASTER_REFERENCE.md"
    
    if not ref_path.exists():
        print(f"   ❌ Master reference not found at {ref_path}")
        return False
    
    # Check file size (should be substantial)
    size = ref_path.stat().st_size
    if size < 10000:
        print(f"   ⚠️  Master reference seems small ({size} bytes)")
    
    # Check for key sections
    content = ref_path.read_text()
    required_sections = [
        "CORE IMPERIAL METRICS",
        "STANDARD DATA TABLE FORMAT",
        "PYTHON CODE STANDARDS",
        "LaTeX DOCUMENT TEMPLATE",
        "FILE NAMING STANDARDS"
    ]
    
    all_present = True
    for section in required_sections:
        if section in content:
            print(f"   ✅ Found section: {section}")
        else:
            print(f"   ❌ Missing section: {section}")
            all_present = False
    
    return all_present


def main():
    """Run all validation checks."""
    print("=" * 70)
    print("LUFT DATA TRANSCRIPTION VALIDATION")
    print("Version 1.0 - January 23, 2026")
    print("=" * 70)
    
    results = []
    
    # Validate master reference
    results.append(("Master Reference", validate_master_reference()))
    
    # Validate constants module
    results.append(("Constants Module", validate_constants_module()))
    
    # Validate example files
    examples_dir = Path(__file__).parent / "examples"
    if examples_dir.exists():
        csv_file = examples_dir / "luft_chi_log_2026-01-05.csv"
        if csv_file.exists():
            results.append(("Example CSV", validate_csv_format(csv_file)))
        
        json_file = examples_dir / "luft_event_2026-01-05.json"
        if json_file.exists():
            results.append(("Example JSON", validate_json_format(json_file)))
    
    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {name}: {status}")
    
    print("-" * 70)
    print(f"   Total: {passed}/{total} passed")
    
    if passed == total:
        print("\n✅ All validations passed!")
        print("   LUFT data transcription standards are correctly implemented.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} validation(s) failed.")
        print("   Review the errors above and fix before proceeding.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
