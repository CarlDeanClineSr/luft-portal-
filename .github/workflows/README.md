# GitHub Actions Workflows for Solar Wind Data Automation

This directory contains robust GitHub Actions workflows that automatically fetch and validate solar wind data from NOAA SWPC (Space Weather Prediction Center).

## Available Workflows

### 1. ACE Solar Wind Data Ingest (`ace_solar_wind_ingest.yml`)

**Schedule:** Every hour at :15 minutes past the hour  
**Endpoints:**
- ACE Plasma: `https://services.swpc.noaa.gov/products/solar-wind/plasma-5-minute.json`
- ACE Magnetometer: `https://services.swpc.noaa.gov/products/solar-wind/mag-5-minute.json`

**What it does:**
1. Creates `data/ace/` directory if needed
2. Downloads 5-minute cadence plasma and magnetometer data
3. Validates JSON integrity using `jq`
4. Extracts latest entries for audit
5. Commits to timestamped feature branch (e.g., `data-update/ace-solar-wind-20251124-120000`)
6. Ready for PR review before merging to main

**Output Files:**
- `data/ace/ace_plasma_5min.json` - Full plasma data array
- `data/ace/ace_mag_5min.json` - Full magnetometer data array
- `data/ace/ace_plasma_latest.json` - Latest plasma entry
- `data/ace/ace_mag_latest.json` - Latest magnetometer entry

### 2. DSCOVR Solar Wind Data Ingest (`dscovr_solar_wind_ingest.yml`)

**Schedule:** Every hour at :30 minutes past the hour  
**Endpoint:** `https://services.swpc.noaa.gov/products/solar-wind/dscovr.json`

**What it does:**
1. Creates `data/dscovr/` directory if needed
2. Downloads real-time DSCOVR L1 solar wind data
3. Validates JSON integrity using `jq`
4. Parses and displays key plasma and magnetic field parameters
5. Flags potential void/CME events (Bz < -2.0 nT AND density > 8 p/cm³)
6. Commits to timestamped feature branch (e.g., `data-update/dscovr-solar-wind-20251124-123000`)
7. Ready for PR review before merging to main

**Output Files:**
- `data/dscovr/dscovr_realtime.json` - Full DSCOVR data array
- `data/dscovr/dscovr_latest.json` - Latest DSCOVR entry

## How to Use

### Manual Triggering

You can manually trigger any workflow from the GitHub Actions tab:

1. Go to your repository on GitHub
2. Click on "Actions" tab
3. Select the workflow you want to run (e.g., "ACE Solar Wind Data Ingest (Robust)")
4. Click "Run workflow" button
5. Select the branch (usually `main`)
6. Click "Run workflow"

### Reviewing Data Updates

After a workflow runs successfully:

1. Go to "Branches" in your repository
2. Find the new feature branch (e.g., `data-update/ace-solar-wind-...`)
3. Click "New pull request" for that branch
4. Review the data changes in the PR
5. Merge to main when satisfied

### Monitoring and Troubleshooting

All workflows include detailed logging with emoji indicators:
- ✅ Success steps
- ❌ Error conditions with detailed messages
- ⚠️  Warnings (e.g., empty data, potential issues)
- 📡 Network operations
- 🔍 Validation steps
- 📊 Data statistics
- 🌿 Branch operations

**Common Error Codes:**
- Exit 1: Network failure or endpoint unavailable
- Exit 2: Invalid JSON from NOAA endpoint
- Exit 3: Failed to extract latest entry
- Exit 4: Extracted entry is invalid JSON
- Exit 5: Failed to push feature branch (permissions or network issue)

### Restarting Failed Workflows

If a workflow fails:

1. Check the workflow logs in the Actions tab
2. Identify the error from the detailed log messages
3. Address the issue (if it's in your control)
4. Manually trigger the workflow again using "Run workflow" button

## Data Format Examples

### ACE Plasma Data Format
```json
[
  "2025-11-24 12:05:00.000",  // Timestamp
  "3.30",                      // Density (p/cm³)
  "686.6",                     // Speed (km/s)
  "821411"                     // Temperature (K)
]
```

### ACE Magnetometer Data Format
```json
[
  "2025-11-24 12:05:00.000",  // Timestamp
  "-12.24",                    // Bx (nT)
  "7.37",                      // By (nT)
  "-4.50",                     // Bz (nT)
  "148.96",                    // Bt (nT)
  "-17.49",                    // Latitude (degrees)
  "14.98"                      // Longitude (degrees)
]
```

### DSCOVR Data Format
```json
[
  "2025-11-24 12:30:00.000",  // Timestamp
  "5.20",                      // Density (p/cm³)
  "420.2",                     // Speed (km/s)
  "78000",                     // Temperature (K)
  "3.11",                      // Bx (nT)
  "-7.43",                     // By (nT)
  "-1.85",                     // Bz (nT)
  "10.36"                      // Bt (nT)
]
```

## Safety Features

Both workflows implement multiple safety layers:

1. **Directory Creation:** Automatically creates required directories
2. **Network Validation:** Checks curl exit codes for download success
3. **JSON Validation:** Uses `jq` to validate structure before processing
4. **Data Verification:** Checks for non-empty arrays and required fields
5. **Feature Branch Strategy:** All commits go to timestamped feature branches
6. **PR Review Process:** Changes must be manually reviewed and merged
7. **Detailed Logging:** Every step logs success/failure with context
8. **Error Isolation:** Failures exit with specific codes for troubleshooting

## LUFT-Specific Features

### DSCOVR Event Detection
The DSCOVR workflow includes LUFT-specific event detection:
- Monitors for Bz < -2.0 nT AND density > 8 p/cm³
- Flags potential void events or CME signatures
- Useful for foam fraction analysis and quantum tunnel research

### Audit Trail
Both workflows maintain audit trails:
- Latest entries extracted for quick reference
- Full datasets preserved for historical analysis
- Timestamped commits with detailed metadata

## Maintenance

### Updating Schedule
To change the schedule, edit the `cron` expression in the workflow file:
```yaml
schedule:
  - cron: '15 * * * *'  # Currently: hourly at :15
```

Common cron patterns:
- `'0 * * * *'` - Every hour at :00
- `'*/30 * * * *'` - Every 30 minutes
- `'0 */2 * * *'` - Every 2 hours
- `'0 0 * * *'` - Daily at midnight

### Disabling a Workflow
To temporarily disable a workflow:
1. Edit the workflow file
2. Comment out or remove the `schedule:` section
3. Keep `workflow_dispatch:` for manual triggering

## Support

For issues with:
- **Workflows not running:** Check GitHub Actions permissions in repository settings
- **Network errors:** NOAA endpoints may be temporarily down; retry later
- **Invalid JSON:** Contact NOAA SWPC or check endpoint status
- **Branch permissions:** Ensure LUFT-bot has write access to repository

---

*Workflows maintained for the LUFT Portal project*  
*Last updated: 2025-11-24*
