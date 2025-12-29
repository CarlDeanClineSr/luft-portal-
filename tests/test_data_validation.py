"""
Tests for data ingestion validation functions
"""
import tempfile
from pathlib import Path
import sys

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'tools'))

from fetch_maven_mars import validate_csv_file as maven_validate
from fetch_cern_lhc import validate_csv_file as cern_validate


def test_detect_html_in_csv():
    """Test that HTML content in CSV is detected"""
    
    # Create a temporary HTML file (simulating 404 error page)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write('<html>\n')
        f.write('<head><title>Page Not Found</title></head>\n')
        f.write('<body>404 Error</body>\n')
        f.write('</html>\n')
        temp_file = Path(f.name)
    
    try:
        # Both validation functions should detect this as invalid
        assert not maven_validate(temp_file), "MAVEN validator should reject HTML file"
        assert not cern_validate(temp_file), "CERN validator should reject HTML file"
        print("✓ HTML detection test passed")
    finally:
        temp_file.unlink()


def test_detect_404_error():
    """Test that 404 error messages are detected"""
    
    # Create a temporary file with 404 error
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write('<!DOCTYPE html>\n')
        f.write('<html lang="en">\n')
        f.write('<title>Page not found</title>\n')
        temp_file = Path(f.name)
    
    try:
        assert not maven_validate(temp_file), "MAVEN validator should reject 404 page"
        assert not cern_validate(temp_file), "CERN validator should reject 404 page"
        print("✓ 404 error detection test passed")
    finally:
        temp_file.unlink()


def test_valid_csv_passes():
    """Test that valid CSV files pass validation"""
    
    # Create a temporary valid CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write('timestamp,value1,value2\n')
        f.write('2025-01-01T00:00:00,1.23,4.56\n')
        f.write('2025-01-01T00:01:00,1.24,4.57\n')
        temp_file = Path(f.name)
    
    try:
        assert maven_validate(temp_file), "MAVEN validator should accept valid CSV"
        assert cern_validate(temp_file), "CERN validator should accept valid CSV"
        print("✓ Valid CSV test passed")
    finally:
        temp_file.unlink()


if __name__ == '__main__':
    print("Running data validation tests...")
    print()
    
    try:
        test_detect_html_in_csv()
        test_detect_404_error()
        test_valid_csv_passes()
        
        print()
        print("=" * 50)
        print("All validation tests passed! ✓")
        print("=" * 50)
    except AssertionError as e:
        print()
        print("=" * 50)
        print(f"Test failed: {e}")
        print("=" * 50)
        sys.exit(1)
    except Exception as e:
        print()
        print("=" * 50)
        print(f"Unexpected error: {e}")
        print("=" * 50)
        sys.exit(1)
