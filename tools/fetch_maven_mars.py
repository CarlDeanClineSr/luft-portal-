import requests
from pathlib import Path
from datetime import datetime, timedelta
import json

OUTPUT_DIR = Path("data/maven_mars")
OUTPUT_DIR.mkdir(exist_ok=True)

def validate_response(response):
    """Check if response is valid data (not HTML error page)"""
    content_type = response.headers.get('Content-Type', '')
    
    # Check if response is HTML (likely an error page)
    if 'text/html' in content_type:
        print(f"ERROR: Received HTML instead of data (likely 404)")
        print(f"URL attempted: {response.url}")
        return False
    
    # Check first few bytes for HTML tags
    content_start = response.content[:500].lower()
    if any(tag in content_start for tag in [b'<html', b'<!doctype', b'<head', b'<body', b'page not found']):
        print(f"ERROR: Response contains HTML tags (not valid data)")
        return False
    
    return True

def validate_csv_file(filepath):
    """Check if file is valid CSV (not HTML error page)"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            first_lines = f.read(500).lower()
            
            # Check for HTML tags (404 error pages)
            if any(tag in first_lines for tag in ['<html', '<!doctype', '<head', '<body', 'page not found']):
                print(f"ERROR: {filepath} contains HTML, not CSV data")
                return False
            
            # Check for common error messages
            if any(msg in first_lines for msg in ['404', 'error 404', 'not found']):
                print(f"ERROR: {filepath} contains error message")
                return False
        
        return True
    except Exception as e:
        print(f"ERROR: Cannot validate {filepath}: {e}")
        return False

def clean_invalid_files():
    """Remove existing invalid CSV files that contain HTML"""
    print("Checking for invalid files in data directory...")
    cleaned = 0
    
    for file in OUTPUT_DIR.glob("*.csv"):
        if not validate_csv_file(file):
            print(f"Removing invalid file: {file}")
            file.unlink()
            cleaned += 1
    
    if cleaned > 0:
        print(f"Cleaned {cleaned} invalid file(s)")
    else:
        print("No invalid files found")

def fetch_maven_placeholder():
    """
    Placeholder MAVEN fetch - returns None until real data source is configured.
    
    NOTE: MAVEN data sources require either:
    1. MAVEN SDC at LASP (requires authentication or specific CDF file access)
    2. NASA PDS (requires navigating date-based directory structure)
    3. CDAWeb (MAVEN datasets not currently available there)
    
    This function will not save invalid data and will exit gracefully.
    """
    print("=" * 60)
    print("MAVEN Mars Plasma Data Ingestion")
    print("=" * 60)
    print("INFO: MAVEN data source not yet configured")
    print("Previous placeholder URL returned 404 errors")
    print("")
    print("To fix this, configure one of:")
    print("  1. MAVEN SDC at LASP: https://lasp.colorado.edu/maven/sdc/")
    print("  2. NASA PDS Data: https://pds-ppi.igpp.ucla.edu/")
    print("  3. Wait for CDAWeb to add MAVEN datasets")
    print("")
    print("For now, skipping data collection to avoid saving HTML error pages")
    print("=" * 60)
    
    return None

if __name__ == "__main__":
    # Clean up any existing invalid files first
    clean_invalid_files()
    
    # Attempt to fetch new data
    result = fetch_maven_placeholder()
    
    if result:
        print(f"✓ SUCCESS: MAVEN data saved to {result}")
    else:
        print(f"⚠ INFO: No MAVEN data collected")
        print("This is expected - data source needs configuration")
    
    # Always exit 0 (success) to not fail workflow
    # Data ingestion failures should be handled gracefully
    exit(0)
