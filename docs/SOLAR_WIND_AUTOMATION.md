# Solar Wind Data Automation Implementation Summary

## Overview

This implementation adds robust, production-ready GitHub Actions workflows to automatically fetch and validate ACE and DSCOVR L1 solar wind data from NOAA SWPC endpoints. The workflows are designed for reliability, auditability, and safe deployment through PR review.

## What Was Implemented

### 1. New Robust Workflows

#### `ace_solar_wind_ingest.yml`
- **Schedule:** Hourly at :15 minutes past the hour
- **Purpose:** Fetch ACE plasma and magnetometer data
- **Safety:** Creates feature branches for PR review
- **Validation:** Full JSON integrity checking with `jq`
- **Error Handling:** Detailed logging with specific exit codes

**Output Files:**
- `data/ace/ace_plasma_5min.json` - Full 5-minute plasma data
- `data/ace/ace_mag_5min.json` - Full 5-minute magnetometer data
- `data/ace/ace_plasma_latest.json` - Latest plasma entry for audit
- `data/ace/ace_mag_latest.json` - Latest mag entry for audit

#### `dscovr_solar_wind_ingest.yml`
- **Schedule:** Hourly at :30 minutes past the hour
- **Purpose:** Fetch DSCOVR real-time solar wind data
- **Safety:** Creates feature branches for PR review
- **Validation:** Full JSON integrity checking with `jq`
- **Special Features:** LUFT event detection (void/CME signatures)
- **Error Handling:** Detailed logging with specific exit codes

**Output Files:**
- `data/dscovr/dscovr_realtime.json` - Full DSCOVR data array
- `data/dscovr/dscovr_latest.json` - Latest entry for audit

### 2. Enhanced Legacy Workflow

#### `solar_wind_audit.yml` (Enhanced)
- Maintains backward compatibility with existing file paths
- Adds error handling and validation
- Commits directly to main (legacy behavior)
- Enhanced logging for troubleshooting

**Output Files (backward compatible):**
- `data/ace_plasma_audit.json` - Latest plasma entry
- `data/ace_mag_audit.json` - Latest mag entry

### 3. Infrastructure

- Created `data/ace/` directory with `.gitkeep`
- Created `data/dscovr/` directory with `.gitkeep`
- Comprehensive `README.md` in `.github/workflows/` with usage instructions

## Key Features

### Safety & Reliability
1. **Feature Branch Strategy:** New workflows push to timestamped feature branches, not main
2. **Manual Review:** All data updates require PR review before merging
3. **Error Isolation:** Each step validates and exits with specific codes on failure
4. **Network Validation:** Checks curl exit codes before processing data
5. **JSON Validation:** Uses `jq` to verify structure before extraction
6. **Directory Creation:** Automatically creates required directories if missing

### Observability
1. **Detailed Logging:** Every step logs success/failure with emoji indicators
2. **Error Codes:** Specific exit codes for different failure scenarios
3. **Data Statistics:** Displays record counts and key metrics
4. **Audit Trail:** Timestamped commits with detailed metadata
5. **Summary Reports:** Final summary of each workflow run

### LUFT-Specific Features
1. **Event Detection:** DSCOVR workflow flags potential void/CME events
   - Monitors: Bz < -2.0 nT AND density > 8 p/cm³ (protons per cubic centimeter)
   - Values validated as numeric before comparison
2. **Audit Extractions:** Latest entries preserved for quick reference
3. **Historical Data:** Full datasets maintained for analysis
4. **Field Validation:** Checks plasma and magnetic field parameters

## Error Handling

All workflows include comprehensive error handling:

| Exit Code | Meaning | Action |
|-----------|---------|--------|
| 1 | Network failure or endpoint unavailable | Check NOAA SWPC status, retry later |
| 2 | Invalid JSON from endpoint | Contact NOAA or wait for endpoint fix |
| 3 | Failed to extract latest entry | Check jq command and data format |
| 4 | Extracted entry is invalid JSON | Data corruption, needs investigation |
| 5 | Failed to push feature branch | Check permissions and network |

## Usage Instructions

### Manual Triggering
1. Go to GitHub Actions tab in repository
2. Select desired workflow
3. Click "Run workflow"
4. Select branch (usually `main`)
5. Click "Run workflow" button

### Reviewing Data Updates
1. Check "Branches" section after workflow runs
2. Find feature branch (e.g., `data-update/ace-solar-wind-20251124-120000`)
3. Create PR from feature branch to main
4. Review data changes
5. Merge when satisfied

### Monitoring
- Check Actions tab for workflow status
- Review logs for detailed execution information
- Look for emoji indicators:
  - ✅ Success
  - ❌ Error
  - ⚠️  Warning
  - 📡 Network operation
  - 🔍 Validation
  - 📊 Statistics

## Testing Performed

1. ✅ YAML syntax validation (Python yaml.safe_load)
2. ✅ Directory structure verification
3. ✅ `.gitkeep` files created
4. ✅ Workflow file structure validated
5. ✅ Enhanced legacy workflow maintains backward compatibility

## Schedule Summary

| Workflow | Schedule | Endpoint(s) |
|----------|----------|-------------|
| `solar_wind_audit.yml` (legacy) | :00 every hour | ACE plasma, ACE mag |
| `ace_solar_wind_ingest.yml` | :15 every hour | ACE plasma, ACE mag |
| `dscovr_solar_wind_ingest.yml` | :30 every hour | DSCOVR real-time |

This staggered schedule reduces load and provides regular updates throughout each hour.

## Future Improvements

Potential enhancements for consideration:
1. Automatic PR creation using GitHub CLI
2. Data quality metrics dashboard
3. Notification system for event detection
4. Historical data retention policy
5. Cross-validation between ACE and DSCOVR
6. Integration with LUFT analysis pipeline

## Maintenance

### Updating Schedules
Edit the `cron:` expression in workflow files:
```yaml
schedule:
  - cron: '15 * * * *'  # Minute Hour Day Month DayOfWeek
```

### Disabling Workflows
Comment out or remove the `schedule:` section. Keep `workflow_dispatch:` for manual runs.

### Troubleshooting
1. Check workflow logs in Actions tab
2. Verify NOAA SWPC endpoint availability
3. Test endpoints manually: `curl https://services.swpc.noaa.gov/products/solar-wind/plasma-5-minute.json`
4. Ensure repository permissions allow branch creation and pushing

## File Structure

```
.github/workflows/
├── README.md                       # Workflow documentation
├── ace_solar_wind_ingest.yml      # Robust ACE workflow (NEW)
├── dscovr_solar_wind_ingest.yml   # Robust DSCOVR workflow (NEW)
├── solar_wind_audit.yml           # Enhanced legacy workflow
├── goes_data_audit.yml            # Existing GOES workflow
├── goes_ingest.yml                # Existing GOES workflow
├── capsule-validator.yml          # Existing validator
├── capsule-validator2.yml         # Existing validator
└── static.yml                     # Existing static workflow

data/
├── ace/
│   └── .gitkeep                   # Directory placeholder
├── dscovr/
│   └── .gitkeep                   # Directory placeholder
├── ace_plasma_audit.json          # Legacy audit file
├── ace_mag_audit.json             # Legacy audit file
└── ace_solar_wind_audit.json      # Legacy audit file
```

## Compliance

This implementation meets all requirements from the problem statement:

1. ✅ Hourly scheduled data retrieval from official NOAA endpoints
2. ✅ Creates data/ace and data/dscovr folders as needed
3. ✅ Validates JSON files' integrity using 'jq'
4. ✅ Pushes data to safe feature branches for PR review before merging to main
5. ✅ Logs detailed errors (bad network, invalid data, missing folder) with clear notices
6. ✅ Well-structured YAML GitHub Action files
7. ✅ Robust curl/jq commands for reliability
8. ✅ Easy for Carl to review and restart (workflow_dispatch, detailed logs)

---

**Implementation Date:** 2025-11-24
**Last Updated:** 2025-11-24
**Status:** ✅ Complete and Ready for Deployment
