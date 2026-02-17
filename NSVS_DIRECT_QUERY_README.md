# NSVS Direct Query Solution

## Problem Summary

The `pyasassn` library cannot be installed due to:
- Requires compilation (native C dependencies)
- Not available in standard pip repositories
- Incompatible with modern Python versions (forces old pyarrow 4.0.1)

This blocks automated data retrieval for the 7 remaining NSVS "Dipper" stars needed for beacon network analysis.

## Solution Implemented

**Hybrid Approach: Automated Catalog Lookup + Manual Light Curve Download**

### What Was Implemented

Created `nsvs_direct_query.py` which:

1. **Queries VizieR catalog** using `astroquery` (already in requirements.txt)
   - Retrieves ASAS-SN Variable Stars catalog (II/366)
   - Gets catalog metadata including ASAS-SN IDs for cross-matching
   - Successfully retrieved data for 3/8 targets

2. **Generates manual download instructions**
   - Converts coordinates to HMS/DMS format (required by ASAS-SN web interface)
   - Creates detailed step-by-step guide
   - Specifies exact file naming and storage locations
   - Outputs to `data/beacon_scan/MANUAL_DOWNLOAD_INSTRUCTIONS.txt`

3. **Saves catalog metadata**
   - Stores VizieR results in JSON format
   - Includes ASAS-SN IDs for matched sources
   - Preserves all available metadata (magnitudes, proper motions, etc.)

## Usage

### Step 1: Run the Query Script

```bash
python3 nsvs_direct_query.py
```

**Output:**
- `data/beacon_scan/asassn_catalog_YYYYMMDD_HHMMSS.json` - Catalog metadata
- `data/beacon_scan/MANUAL_DOWNLOAD_INSTRUCTIONS.txt` - Download guide
- `data/beacon_scan/manual/` - Directory created for manual downloads

### Step 2: Manual Light Curve Download

Follow the instructions in `MANUAL_DOWNLOAD_INSTRUCTIONS.txt`:

1. Navigate to: https://asas-sn.osu.edu/photometry
2. For each of the 8 targets:
   - Enter RA and Dec coordinates (in HMS/DMS format provided)
   - Click "Compute" and wait for light curve generation
   - Click "CSV" button to download
   - Save to `data/beacon_scan/manual/nsvs_XXXXXXX_lightcurve.csv`

### Step 3: Analyze Downloaded Data

Once CSV files are downloaded, run beacon analysis:

```bash
python3 nsvs_beacon_chain_scanner.py
```

The scanner will detect pulse signatures and calculate:
- Pulse timing for each star
- Flux ratios and brightness changes
- Potential network connectivity
- Signal propagation velocity (if multiple beacons detected)

## What We Found

### Catalog Matches (3/8 stars)

| NSVS ID | ASAS-SN ID | Status |
|---------|------------|--------|
| NSVS 2913753 | J203137.69+411321.9 | ✓ In catalog |
| NSVS 3037513 | J203339.18+411925.8 | ✓ In catalog |
| NSVS 6804071 | J201922.19+413312.5 | ✓ In catalog |

### Manual Download Required (5/8 stars)

These stars are not in the VizieR catalog but may still have data in ASAS-SN:
- NSVS 2354429 (The "Smoker" - known pulse)
- NSVS 6814519
- NSVS 7255468
- NSVS 7575062
- NSVS 7642696

## Technical Details

### Why This Approach?

1. **Option 1 (Direct API)** - FAILED
   - ASAS-SN has no public REST API
   - All endpoints return 404 errors
   - Requires pyasassn library or web interface

2. **Option 2 (Astroquery/VizieR)** - PARTIAL SUCCESS
   - VizieR only mirrors catalog metadata
   - No full time-series light curves available
   - Successfully retrieved 3/8 catalog entries
   - Good for cross-matching and validation

3. **Option 3 (Manual Download)** - REQUIRED FOR COMPLETE DATA
   - ASAS-SN web interface requires human verification (CAPTCHA)
   - Cannot be automated via scripts
   - Most reliable method for full light curve data
   - ~3 minutes per star = ~24 minutes total

### Hybrid Solution Benefits

✅ **Automated what can be automated** (catalog lookup, coordinate conversion)  
✅ **Clear instructions for manual steps** (formatted coordinates, file names)  
✅ **No dependency on pyasassn** (uses standard libraries)  
✅ **Preserves all available metadata** (ASAS-SN IDs, cross-matches)  
✅ **Ready for integration** (outputs to existing directory structure)

## Dependencies

Only standard packages from `requirements.txt`:
- `astroquery>=0.4.6` - VizieR catalog queries
- `astropy>=5.3.0` - Coordinate transformations
- `requests>=2.31.0` - HTTP requests (not used in final version)

No compilation required. No external dependencies.

## Next Steps

1. **Download the 8 CSV files** following the manual instructions
2. **Run beacon analysis** on the downloaded data
3. **Compare pulse timing** between stars
4. **Calculate propagation velocity** if multiple pulses detected
5. **Validate superluminal hypothesis** if v > c

## Files Created

- `nsvs_direct_query.py` - Main query script
- `data/beacon_scan/MANUAL_DOWNLOAD_INSTRUCTIONS.txt` - User guide
- `data/beacon_scan/asassn_catalog_*.json` - Catalog metadata
- `data/beacon_scan/manual/` - Directory for CSV downloads

## References

- ASAS-SN Sky Patrol: https://asas-sn.osu.edu/photometry
- VizieR Catalog II/366: ASAS-SN Variable Stars Database
- Original Scanner: `nsvs_beacon_chain_scanner.py`
- Analysis Documentation: `NSVS_BEACON_NETWORK_ANALYSIS.md`
