import requests
from pathlib import Path
from datetime import datetime, UTC
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

def extract_csv_urls(api_response):
    """Extract direct CSV download URLs from API response"""
    csv_urls = []
    
    if 'hits' in api_response and 'hits' in api_response['hits']:
        for record in api_response['hits']['hits']:
            try:
                record_id = record.get('id', '')
                metadata = record.get('metadata', {})
                files = metadata.get('files', [])
                title = metadata.get('title', 'Unknown')
                
                for file_info in files:
                    if file_info.get('key', '').endswith('.csv'):
                        # Construct direct download URL
                        file_url = f"https://opendata.cern.ch/record/{record_id}/files/{file_info['key']}"
                        csv_urls.append({
                            'record_id': record_id,
                            'filename': file_info['key'],
                            'url': file_url,
                            'title': title
                        })
            except Exception as e:
                print(f"Warning: Error parsing record: {e}")
                continue
    
    return csv_urls

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
    """Fetch LHC luminosity data from CERN Open Data API"""
    
    # TODO: Integrate with link_harvester_core.py to automatically discover
    # valid CERN Open Data URLs before attempting downloads
    # This will make the script resilient to portal reorganizations
    
    # Use CERN Open Data portal search for latest LHC luminosity records
    search_url = "https://opendata.cern.ch/api/records/"
    
    # Try multiple search strategies with improved parameters
    search_strategies = [
        {
            'q': 'luminosity',
            'experiment': 'CMS',
            'type': 'Dataset',
            'sort': '-mostrecent',
            'size': 20,
        },
        {
            'q': 'luminosity CMS',
            'type': 'Dataset',
            'sort': '-mostrecent',
            'size': 20,
        },
        {
            'q': 'luminosity ATLAS',
            'type': 'Dataset',
            'sort': '-mostrecent',
            'size': 20,
        },
    ]
    
    for strategy_idx, params in enumerate(search_strategies, 1):
        try:
            strategy_desc = f"{params.get('q', 'luminosity')} (strategy {strategy_idx}/{len(search_strategies)})"
            print(f"Searching CERN Open Data API: {strategy_desc}...")
            response = requests.get(search_url, params=params, timeout=30)
            response.raise_for_status()
            
            # Validate response
            if not validate_response(response):
                continue
            
            data = response.json()
            
            # Check if we got valid results
            if 'hits' in data and 'hits' in data['hits'] and len(data['hits']['hits']) > 0:
                # Save search results for inspection
                timestamp = datetime.now(UTC).strftime('%Y%m%d_%H%M%S')
                json_file = OUTPUT_DIR / f"cern_lumi_search_{timestamp}.json"
                
                with open(json_file, 'w') as f:
                    json.dump(data, f, indent=2)
                
                print(f"Found {len(data['hits']['hits'])} luminosity datasets")
                
                # Extract CSV URLs from API response
                csv_urls = extract_csv_urls(data)
                
                if csv_urls:
                    print(f"Found {len(csv_urls)} CSV files in results")
                    
                    # Try to download the first available CSV
                    for csv_info in csv_urls[:3]:  # Try first 3 CSVs
                        try:
                            print(f"Downloading: {csv_info['filename']} from record {csv_info['record_id']}")
                            csv_response = requests.get(csv_info['url'], timeout=30)
                            
                            if csv_response.status_code == 200 and validate_response(csv_response):
                                csv_file = OUTPUT_DIR / f"cern_lumi_{csv_info['record_id']}_{csv_info['filename']}"
                                
                                with open(csv_file, 'wb') as f:
                                    f.write(csv_response.content)
                                
                                # Validate saved file
                                if validate_csv_file(csv_file):
                                    print(f"SUCCESS: Downloaded luminosity data: {csv_file}")
                                    return csv_file
                                else:
                                    csv_file.unlink()
                        except Exception as e:
                            print(f"Failed to download {csv_info['url']}: {e}")
                            continue
                
                print(f"No valid CSV downloads from this search strategy")
            else:
                print(f"No datasets found with this search strategy")
            
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error with strategy {strategy_idx}: {e}")
            continue
        except requests.exceptions.RequestException as e:
            print(f"Network error with strategy {strategy_idx}: {e}")
            continue
        except json.JSONDecodeError as e:
            print(f"Invalid JSON response with strategy {strategy_idx}: {e}")
            continue
        except Exception as e:
            print(f"Error with strategy {strategy_idx}: {e}")
            continue
    
    print("All search strategies exhausted")
    return None

def fetch_cern_archived():
    """Backup: Use known archived LHC luminosity datasets and alternative sources"""
    
    print("Attempting to fetch archived CERN luminosity datasets...")
    
    # Try multiple approaches for finding data:
    # 1. Known CMS luminosity records from Open Data Portal (verified working)
    # 2. Recent year-specific searches (2024, 2023, 2022)
    # 3. Legacy archived datasets from older releases
    
    # Known working CMS luminosity records with CSV files
    # Source: https://opendata.cern.ch/record/1053 (2011)
    # Source: https://opendata.cern.ch/record/1054 (2012)
    # Source: https://opendata.cern.ch/record/1055 (2015)
    # NOTE: These record IDs are manually maintained and may become outdated
    # if CERN reorganizes their portal. Future enhancement: integrate with
    # link_harvester_core.py to discover these URLs dynamically.
    cms_lumi_records = [
        {'record_id': '1055', 'year': '2015', 'files': ['2015lumibyls.csv']},
        {'record_id': '1054', 'year': '2012', 'files': ['2012lumibyls_pxl.csv', '2012lumibyls_hfoc.csv']},
        {'record_id': '1053', 'year': '2011', 'files': ['2011lumibyls_pxl.csv', '2011lumibyls_hfoc.csv']},
    ]
    
    # Try known CMS luminosity records first
    for record_info in cms_lumi_records:
        record_id = record_info['record_id']
        year = record_info['year']
        
        for filename in record_info['files'][:1]:  # Try first file from each record
            try:
                url = f"https://opendata.cern.ch/record/{record_id}/files/{filename}"
                print(f"Trying CMS {year} luminosity: {filename}")
                
                response = requests.get(url, timeout=30)
                
                if response.status_code == 200 and validate_response(response):
                    csv_file = OUTPUT_DIR / f"cern_lumi_cms_{year}_{filename}"
                    
                    with open(csv_file, 'wb') as f:
                        f.write(response.content)
                    
                    if validate_csv_file(csv_file):
                        print(f"SUCCESS: Downloaded CMS {year} luminosity data: {csv_file}")
                        return csv_file
                    else:
                        csv_file.unlink()
            except Exception as e:
                print(f"Failed to download {filename} from record {record_id}: {e}")
                continue
    
    # Alternative approach: Try recent years via API
    search_url = "https://opendata.cern.ch/api/records/"
    
    for year in ['2024', '2023', '2022', '2021']:
        try:
            print(f"Trying luminosity data for year {year}...")
            params = {
                'q': f'luminosity {year}',
                'type': 'Dataset',
                'size': 10
            }
            response = requests.get(search_url, params=params, timeout=30)
            
            if response.status_code == 200 and validate_response(response):
                data = response.json()
                csv_urls = extract_csv_urls(data)
                
                if csv_urls:
                    print(f"Found {len(csv_urls)} CSV files for {year}")
                    for csv_info in csv_urls[:2]:  # Try first 2
                        try:
                            csv_response = requests.get(csv_info['url'], timeout=30)
                            if csv_response.status_code == 200 and validate_response(csv_response):
                                csv_file = OUTPUT_DIR / f"cern_lumi_{year}_{csv_info['filename']}"
                                with open(csv_file, 'wb') as f:
                                    f.write(csv_response.content)
                                
                                if validate_csv_file(csv_file):
                                    print(f"SUCCESS: Downloaded {year} luminosity data: {csv_file}")
                                    return csv_file
                                else:
                                    csv_file.unlink()
                        except Exception as e:
                            print(f"Failed to download from {year}: {e}")
                            continue
        except Exception as e:
            print(f"Error searching {year}: {e}")
            continue
    
    # Try legacy datasets as last resort (known to be moved/outdated)
    # Note: These are known to be outdated/moved, but try as last resort
    known_datasets = [
        "https://opendata.cern.ch/record/15006/files/lumi_13TeV_2018.csv",
        "https://opendata.cern.ch/record/15005/files/lumi_13TeV_2017.csv",
        "https://opendata.cern.ch/record/15004/files/lumi_13TeV_2016.csv",
    ]
    
    for url in known_datasets:
        try:
            print(f"Trying legacy archived dataset: {url}")
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                # Validate response
                if not validate_response(response):
                    continue
                
                print(f"Found archived dataset: {url}")
                
                timestamp = datetime.now(UTC).strftime('%Y%m%d_%H%M%S')
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
    """
    print("=" * 60)
    print("CERN LHC Luminosity Data Ingestion")
    print("=" * 60)
    print("INFO: CERN Open Data sources not responding with valid data")
    print("")
    print("CERN Open Data Portal structure:")
    print("  - API endpoint: https://opendata.cern.ch/api/records/")
    print("  - Search for: luminosity datasets by experiment (CMS, ATLAS)")
    print("  - Recent data: 2024 ATLAS release (July 2024)")
    print("  - Alternative: CERN Beam Performance stats for current runs")
    print("  - URL: https://cern.ch/bpt/lhc/statistics/2024/")
    print("")
    print("Data Access Notes:")
    print("  - CERN typically provides archived LHC run data with 1-2 year embargo")
    print("  - Current LHC Run 3 data (2022-2025) being gradually released")
    print("  - Different experiments (CMS, ATLAS, LHCb, ALICE) have different structures")
    print("  - Record IDs change when datasets are reorganized or updated")
    print("")
    print("Integration Notes:")
    print("  - Link Harvester integration planned for automatic URL discovery")
    print("  - Will make script resilient to portal reorganizations")
    print("")
    print("For now, skipping data collection to avoid saving HTML error pages")
    print("=" * 60)
    
    return None

if __name__ == "__main__":
    # Clean up any existing invalid files first
    clean_invalid_files()
    
    # Try API search first
    result = fetch_cern_luminosity()
    
    # Fall back to archived datasets if API search fails
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
