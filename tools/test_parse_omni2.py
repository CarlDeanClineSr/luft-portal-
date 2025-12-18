#!/usr/bin/env python3
"""
Test script for parse_omni2.py error handling.
Tests validation of missing files, empty files, HTML content, and corrupted data.
"""

import sys
import tempfile
from pathlib import Path

# Add tools directory to path for importing
sys.path.insert(0, str(Path(__file__).parent))

from parse_omni2 import parse_omni2


def test_missing_file():
    """Test handling of missing file."""
    print("Test 1: Missing file...")
    # Use tempfile.gettempdir() for cross-platform compatibility
    non_existent = Path(tempfile.gettempdir()) / "non_existent_omni2_test_file.txt"
    try:
        parse_omni2(non_existent)
        print("  ❌ FAILED: Should have raised FileNotFoundError")
        return False
    except FileNotFoundError as e:
        print(f"  ✓ PASSED: Caught FileNotFoundError: {e}")
        return True
    except Exception as e:
        print(f"  ❌ FAILED: Wrong exception type: {type(e).__name__}: {e}")
        return False


def test_empty_file():
    """Test handling of empty file."""
    print("Test 2: Empty file...")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        parse_omni2(temp_path)
        print("  ❌ FAILED: Should have raised ValueError")
        return False
    except ValueError as e:
        if "empty" in str(e).lower():
            print(f"  ✓ PASSED: Caught ValueError for empty file: {e}")
            return True
        else:
            print(f"  ❌ FAILED: Wrong error message: {e}")
            return False
    except Exception as e:
        print(f"  ❌ FAILED: Wrong exception type: {type(e).__name__}: {e}")
        return False
    finally:
        temp_path.unlink()


def test_html_content():
    """Test handling of HTML content (failed download)."""
    print("Test 3: HTML content...")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("<!DOCTYPE html>\n")
        f.write("<html><body><h1>404 Not Found</h1></body></html>\n")
        temp_path = Path(f.name)
    
    try:
        parse_omni2(temp_path)
        print("  ❌ FAILED: Should have raised ValueError")
        return False
    except ValueError as e:
        if "html" in str(e).lower():
            print(f"  ✓ PASSED: Caught ValueError for HTML content: {e}")
            return True
        else:
            print(f"  ❌ FAILED: Wrong error message: {e}")
            return False
    except Exception as e:
        print(f"  ❌ FAILED: Wrong exception type: {type(e).__name__}: {e}")
        return False
    finally:
        temp_path.unlink()


def test_corrupted_data():
    """Test handling of corrupted data that can't be parsed as integers."""
    print("Test 4: Corrupted data...")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        # Write data that looks like OMNI2 format but has invalid values
        f.write("ABCD  XY 999   invalid data here\n")
        f.write("corrupted line with random text\n")
        temp_path = Path(f.name)
    
    try:
        parse_omni2(temp_path)
        print("  ❌ FAILED: Should have raised ValueError")
        return False
    except ValueError as e:
        if "datetime" in str(e).lower() or "parse" in str(e).lower():
            print(f"  ✓ PASSED: Caught ValueError for corrupted data: {e}")
            return True
        else:
            print(f"  ❌ FAILED: Wrong error message: {e}")
            return False
    except Exception as e:
        print(f"  ❌ FAILED: Wrong exception type: {type(e).__name__}: {e}")
        return False
    finally:
        temp_path.unlink()


def test_valid_data():
    """Test handling of valid OMNI2 data (minimal sample)."""
    print("Test 5: Valid data (minimal sample)...")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        # Write a valid OMNI2 line (simplified format matching WIDTHS)
        # YEAR DOY HR Bartels... (needs to be exactly in fixed width format)
        # Sample valid line for 2025-01-01 00:00
        line = "2025   1  0 2866  0  0   0   0   5.2   5.3   1.2  45.6   3.2  -1.5  -2.3  -1.5  -2.3   0.5   0.3   0.2   0.2   0.3  300000   8.5  450  12.3  -3.4 0.150  2.34  150000   1.2  25  1.5  2.1 0.050   2.45  0.75  10.5 45 123-12345 1234 123456.12  12345.67  12345.67  12345.67  12345.67  12345.67  0  12 150.5 999.9-99999-99999 99.9 0.123456 1.2345\n"
        f.write(line)
        temp_path = Path(f.name)
    
    try:
        df = parse_omni2(temp_path)
        if len(df) > 0:
            print(f"  ✓ PASSED: Successfully parsed {len(df)} records")
            return True
        else:
            print("  ❌ FAILED: Parsed but no records found")
            return False
    except Exception as e:
        print(f"  ❌ FAILED: Exception on valid data: {type(e).__name__}: {e}")
        return False
    finally:
        temp_path.unlink()


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing parse_omni2.py error handling")
    print("=" * 60)
    
    tests = [
        test_missing_file,
        test_empty_file,
        test_html_content,
        test_corrupted_data,
        test_valid_data,
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
        print()
    
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
