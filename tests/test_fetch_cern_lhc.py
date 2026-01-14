"""
Tests for CERN LHC luminosity data fetching
"""
import sys
from pathlib import Path
import tempfile
import json

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'tools'))

from fetch_cern_lhc import extract_csv_urls, validate_csv_file


def test_extract_csv_urls():
    """Test CSV URL extraction from API response"""
    
    # Mock API response with CSV files
    mock_response = {
        'hits': {
            'hits': [
                {
                    'id': '1053',
                    'metadata': {
                        'title': 'CMS detailed luminosity information, for 2011',
                        'files': [
                            {'key': '2011lumibyls_pxl.csv'},
                            {'key': '2011lumibyls_hfoc.csv'},
                            {'key': 'README.txt'}
                        ]
                    }
                },
                {
                    'id': '1054',
                    'metadata': {
                        'title': 'CMS detailed luminosity information, for 2012',
                        'files': [
                            {'key': 'data.root'}
                        ]
                    }
                }
            ]
        }
    }
    
    csv_urls = extract_csv_urls(mock_response)
    
    # Should find 2 CSV files from record 1053
    assert len(csv_urls) == 2, f"Expected 2 CSV files, found {len(csv_urls)}"
    
    # Check first CSV
    assert csv_urls[0]['record_id'] == '1053'
    assert csv_urls[0]['filename'] == '2011lumibyls_pxl.csv'
    assert 'opendata.cern.ch/record/1053/files/2011lumibyls_pxl.csv' in csv_urls[0]['url']
    
    # Check second CSV
    assert csv_urls[1]['filename'] == '2011lumibyls_hfoc.csv'
    
    print("✓ CSV URL extraction test passed")


def test_extract_csv_urls_empty():
    """Test CSV URL extraction with no CSV files"""
    
    mock_response = {
        'hits': {
            'hits': [
                {
                    'id': '12345',
                    'metadata': {
                        'title': 'Test dataset',
                        'files': [
                            {'key': 'data.root'},
                            {'key': 'config.json'}
                        ]
                    }
                }
            ]
        }
    }
    
    csv_urls = extract_csv_urls(mock_response)
    
    assert len(csv_urls) == 0, f"Expected 0 CSV files, found {len(csv_urls)}"
    print("✓ Empty CSV extraction test passed")


def test_validate_luminosity_csv():
    """Test that valid luminosity CSV files pass validation"""
    
    # Create a temporary CSV file that looks like real luminosity data
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write('#Data tag : 19v3 , Norm tag: None\n')
        f.write('#run:fill,ls,time,beamstatus,E(GeV),delivered(/fb),recorded(/fb),avgpu,source\n')
        f.write('254231:4201,1:1,08/13/15 05:14:40,STABLE BEAMS,6500,0.000001345,0.000001326,15.8,DT\n')
        f.write('254231:4201,2:2,08/13/15 05:15:03,STABLE BEAMS,6500,0.000001366,0.000001348,16.0,DT\n')
        temp_file = Path(f.name)
    
    try:
        assert validate_csv_file(temp_file), "Luminosity CSV should pass validation"
        print("✓ Luminosity CSV validation test passed")
    finally:
        temp_file.unlink()


def test_api_response_structure():
    """Test handling of malformed API responses"""
    
    # Test with empty response
    empty_response = {'hits': {'hits': []}}
    csv_urls = extract_csv_urls(empty_response)
    assert len(csv_urls) == 0
    
    # Test with missing metadata
    incomplete_response = {
        'hits': {
            'hits': [
                {'id': '123'}  # Missing metadata
            ]
        }
    }
    csv_urls = extract_csv_urls(incomplete_response)
    assert len(csv_urls) == 0
    
    print("✓ API response structure test passed")


if __name__ == '__main__':
    print("Running CERN LHC data fetching tests...")
    print()
    
    try:
        test_extract_csv_urls()
        test_extract_csv_urls_empty()
        test_validate_luminosity_csv()
        test_api_response_structure()
        
        print()
        print("=" * 50)
        print("All CERN LHC tests passed! ✓")
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
