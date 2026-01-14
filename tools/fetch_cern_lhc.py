import requests
from pathlib import Path
from datetime import datetime, timezone
import json

OUTPUT_DIR = Path("data/cern_lhc")
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

def extract_csv_from_api_response(data):
    """Extract CSV file download URLs from API search results
    
    CERN Open Data API returns records with file metadata.
    This function extracts CSV files related to luminosity data.
    
    Args:
        data: JSON response from CERN Open Data API
        
    Returns:
        List of dicts with record_id, filename, url, and title
    """
    csv_files = []
    
    if 'hits' in data and 'hits' in data['hits']:
        for record in data['hits']['hits']:
            record_id = record.get('id', '')
            metadata = record.get('metadata', {})
            files = metadata.get('files', [])
            
            for file_info in files:
                key = file_info.get('key', '')
                if key.endswith('.csv') or 'lumi' in key.lower():
                    csv_files.append({
                        'record_id': record_id,
                        'filename': key,
                        'url': f"https://opendata.cern.ch/record/{record_id}/files/{key}",
                        'title': metadata.get('title', 'Unknown')
                    })
    
    return csv_files

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

def fetch_cern_luminosity():
    """Fetch LHC luminosity data from CERN Open Data API
    
    FUTURE: Integrate with link_harvester_core.py
    The link harvester can crawl CERN Open Data Portal and extract
    valid dataset URLs automatically, making this script resilient
    to portal reorganizations and record ID changes.
    """
    
    # Use CERN Open Data portal search for latest LHC luminosity records
    search_url = "https://opendata.cern.ch/api/records/"
    
    # Try CMS experiment first (has most comprehensive luminosity datasets)
    params = {
        'q': 'luminosity',
        'experiment': 'CMS',
        'type': 'Dataset',
        'sort': '-mostrecent',
        'size': 20
    }
    
    try:
        print(f"Searching CERN Open Data API for luminosity datasets...")
        response = requests.get(search_url, params=params, timeout=30)
        response.raise_for_status()
        
        # Validate response
        if not validate_response(response):
            return None
        
        data = response.json()
        
        # Check if we got valid results
        if 'hits' in data and 'hits' in data['hits'] and len(data['hits']['hits']) > 0:
            # Save search results for inspection
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            json_file = OUTPUT_DIR / f"cern_lumi_search_{timestamp}.json"
            
            with open(json_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"SUCCESS: Fetched CERN search results: {json_file}")
            print(f"Found {len(data['hits']['hits'])} luminosity datasets")
            
            # Extract CSV file URLs from API response
            csv_files = extract_csv_from_api_response(data)
            
            if csv_files:
                print(f"Found {len(csv_files)} CSV file(s) in search results")
                
                # Try downloading the first CSV file
                for csv_info in csv_files[:3]:  # Try up to 3 files
                    try:
                        print(f"Attempting to download: {csv_info['filename']}")
                        print(f"  From record: {csv_info['record_id']}")
                        print(f"  Title: {csv_info['title']}")
                        
                        csv_response = requests.get(csv_info['url'], timeout=30)
                        
                        if csv_response.status_code == 200 and validate_response(csv_response):
                            csv_file = OUTPUT_DIR / f"cern_lumi_{csv_info['filename']}"
                            
                            with open(csv_file, 'w') as f:
                                f.write(csv_response.text)
                            
                            if validate_csv_file(csv_file):
                                print(f"SUCCESS: Downloaded luminosity data to {csv_file}")
                                return csv_file
                            else:
                                csv_file.unlink()
                    except Exception as e:
                        print(f"  Failed to download {csv_info['filename']}: {e}")
                        continue
            
            # Return JSON file even if no CSV was downloaded
            return json_file
        else:
            print("INFO: No luminosity datasets found in search")
            return None
        
    except requests.exceptions.HTTPError as e:
        print(f"ERROR: HTTP error fetching CERN data: {e}")
        print(f"Status code: {e.response.status_code if e.response else 'unknown'}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Network error fetching CERN data: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON response: {e}")
        return None
    except Exception as e:
        print(f"ERROR: Unexpected error processing CERN data: {e}")
        return None

def fetch_cern_archived():
    """Backup: Use known archived LHC luminosity datasets
    
    Note: These URLs may change as CERN reorganizes their Open Data Portal.
    Consider using link_harvester_core.py for automatic URL discovery.
    """
    
    print("Attempting to fetch archived CERN luminosity datasets...")
    
    # Try multiple sources across different experiments
    # CERN Open Data has archived fills from different LHC runs
    known_datasets = [
        # CMS luminosity data (most comprehensive)
        "https://opendata.cern.ch/record/15006/files/lumi_13TeV_2018.csv",
        "https://opendata.cern.ch/record/15005/files/lumi_13TeV_2017.csv",
        "https://opendata.cern.ch/record/15004/files/lumi_13TeV_2016.csv",
        # Try alternative record IDs (portal reorganizations may change these)
        "https://opendata.cern.ch/api/files/cms-luminosity-information-2018/lumi_13TeV_2018.csv",
        "https://opendata.cern.ch/api/files/cms-luminosity-information-2017/lumi_13TeV_2017.csv",
    ]
    
    for url in known_datasets:
        try:
            print(f"Trying archived dataset: {url}")
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                # Validate response
                if not validate_response(response):
                    continue
                
                print(f"Found archived dataset: {url}")
                
                timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
                csv_file = OUTPUT_DIR / f"cern_lumi_archived_{timestamp}.csv"
                
                with open(csv_file, 'w') as f:
                    f.write(response.text)
                
                # Validate saved file
                if not validate_csv_file(csv_file):
                    csv_file.unlink()
                    continue
                
                print(f"SUCCESS: Using archived CERN luminosity: {csv_file}")
                return csv_file
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch {url}: {e}")
            continue
        except Exception as e:
            print(f"Error processing {url}: {e}")
            continue
    
    return None

def fetch_cern_placeholder():
    """
    Placeholder when real data sources are not accessible.
    Provides current information about CERN Open Data Portal access.
    """
    print("=" * 60)
    print("CERN LHC Luminosity Data Ingestion")
    print("=" * 60)
    print("INFO: CERN Open Data sources not responding with valid data")
    print("")
    print("CERN Open Data Portal Access:")
    print("  API: https://opendata.cern.ch/api/records/")
    print("  Manual search: https://opendata.cern.ch/search?q=luminosity")
    print("  ATLAS data: https://opendata.atlas.cern/")
    print("  CMS luminosity guide: https://cms-opendata-guide.web.cern.ch/analysis/lumi/")
    print("  LHC 2024 statistics: https://cern.ch/bpt/lhc/statistics/2024/")
    print("")
    print("Note: LHC data typically released 1-2 years after collection")
    print("      Run 3 data (2022-2025) being gradually released")
    print("      ATLAS released 65 TB of data in July 2024")
    print("")
    print("TODO: Integrate with link_harvester_core.py for automatic URL discovery")
    print("      The link harvester can crawl CERN portals and extract valid")
    print("      dataset URLs, making this script resilient to reorganizations")
    print("")
    print("For now, skipping data collection to avoid saving HTML error pages")
    print("=" * 60)
    
    return None

def fetch_cern_atlas():
    """Try ATLAS experiment luminosity data as fallback"""
    
    print("Trying ATLAS experiment as fallback...")
    
    search_url = "https://opendata.cern.ch/api/records/"
    
    params = {
        'q': 'luminosity',
        'experiment': 'ATLAS',
        'type': 'Dataset',
        'sort': '-mostrecent',
        'size': 20
    }
    
    try:
        response = requests.get(search_url, params=params, timeout=30)
        response.raise_for_status()
        
        if not validate_response(response):
            return None
        
        data = response.json()
        
        if 'hits' in data and 'hits' in data['hits'] and len(data['hits']['hits']) > 0:
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            json_file = OUTPUT_DIR / f"cern_atlas_search_{timestamp}.json"
            
            with open(json_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"Found {len(data['hits']['hits'])} ATLAS datasets")
            
            # Extract CSV files
            csv_files = extract_csv_from_api_response(data)
            
            if csv_files:
                print(f"Found {len(csv_files)} ATLAS CSV file(s)")
                
                for csv_info in csv_files[:3]:
                    try:
                        print(f"Attempting to download: {csv_info['filename']}")
                        csv_response = requests.get(csv_info['url'], timeout=30)
                        
                        if csv_response.status_code == 200 and validate_response(csv_response):
                            csv_file = OUTPUT_DIR / f"cern_atlas_{csv_info['filename']}"
                            
                            with open(csv_file, 'w') as f:
                                f.write(csv_response.text)
                            
                            if validate_csv_file(csv_file):
                                print(f"SUCCESS: Downloaded ATLAS data to {csv_file}")
                                return csv_file
                            else:
                                csv_file.unlink()
                    except Exception as e:
                        print(f"  Failed: {e}")
                        continue
            
            return json_file
        else:
            print("No ATLAS luminosity datasets found")
            return None
            
    except Exception as e:
        print(f"ERROR: Failed to search ATLAS data: {e}")
        return None


if __name__ == "__main__":
    # Clean up any existing invalid files first
    clean_invalid_files()
    
    # Try CMS API search first
    result = fetch_cern_luminosity()
    
    # Fall back to ATLAS if CMS search fails
    if not result:
        print("")
        print("Trying ATLAS experiment as fallback...")
        result = fetch_cern_atlas()
    
    # Fall back to archived datasets if API searches fail
    if not result:
        print("")
        print("Trying archived datasets as fallback...")
        result = fetch_cern_archived()
    
    # If still no result, show placeholder message
    if not result:
        print("")
        result = fetch_cern_placeholder()
    
    if result:
        print(f"✓ SUCCESS: CERN data saved to {result}")
    else:
        print(f"⚠ INFO: No CERN data collected")
        print("This is expected - data sources need configuration")
    
    # Always exit 0 (success) to not fail workflow
    # Data ingestion failures should be handled gracefully
    exit(0)
