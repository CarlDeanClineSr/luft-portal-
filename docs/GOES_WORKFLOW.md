# GOES Workflow Documentation

## Overview

The GOES (Geostationary Operational Environmental Satellite) data ingestion workflow automatically downloads, validates, and stores solar monitoring data from NOAA's Space Weather Prediction Center.

## Workflows

### goes_data_audit.yml (Active)

**Purpose:** Download and validate GOES X-ray and proton flux data hourly.

**Schedule:** Runs every hour at HH:07 (e.g., 00:07, 01:07, 02:07, etc.)

**Manual Trigger:** Can be triggered manually via workflow_dispatch

#### What It Does

1. **Creates data/goes directory** if it doesn't exist
2. **Downloads GOES X-ray flux data** from `https://services.swpc.noaa.gov/products/goes-xray-flux.json`
   - Includes 3 retry attempts with 5-second delays
   - 30-second timeout per attempt
   - Validates JSON structure with jq
3. **Downloads GOES proton flux data** from `https://services.swpc.noaa.gov/products/goes-proton-flux.json`
   - Same retry logic and validation
4. **Creates audit files** by extracting the latest event from each dataset
5. **Commits to feature branch** named `data/goes-audit-YYYYMMDD`
6. **Displays summary** of downloaded data in workflow logs

#### Output Files

- `data/goes/goes_xray_flux.json` - Full X-ray flux time series
- `data/goes/goes_xray_audit.json` - Latest X-ray flux measurement
- `data/goes/goes_proton_flux.json` - Full proton flux time series
- `data/goes/goes_proton_audit.json` - Latest proton flux measurement

#### Branch Strategy

Data is committed to daily feature branches (e.g., `data/goes-audit-20251124`) rather than directly to main. This allows for:
- Review of data before merging to main
- Detection of anomalous data patterns
- Ability to reject bad data runs

#### Error Handling

The workflow fails gracefully with clear error messages if:
- Network is unavailable
- NOAA endpoint returns invalid data
- JSON validation fails
- File operations fail

All errors are logged with descriptive messages and exit codes.

### goes_ingest.yml (Deprecated)

**Status:** Deprecated - Displays notice when triggered

This workflow has been superseded by goes_data_audit.yml. It remains in the repository for backward compatibility reference but will show a deprecation notice if manually triggered.

## Usage

### Monitoring Workflow Runs

1. Go to GitHub Actions tab in the repository
2. Select "GOES Data Audit — Robust" workflow
3. View recent runs and their status
4. Click on a run to see detailed logs

### Reviewing Data Updates

When the workflow runs successfully:

1. Check for a new branch named `data/goes-audit-YYYYMMDD`
2. Review the commit and changed files
3. If data looks good, create a Pull Request to main
4. Merge the PR to update main branch

### Manual Triggering

To trigger the workflow manually:

1. Go to GitHub Actions tab
2. Select "GOES Data Audit — Robust"
3. Click "Run workflow"
4. Select branch and click "Run workflow"

### Troubleshooting

#### Workflow fails immediately
- Check GitHub Actions logs for error messages
- Look for network connectivity issues
- Verify NOAA endpoints are accessible

#### JSON validation fails
- Check if NOAA is returning error messages instead of JSON
- Look for API format changes
- Review the raw content displayed in error logs

#### No changes committed
- This is normal if data hasn't changed since last run
- Workflow will show "No changes to commit" message

#### Branch already exists
- Workflow will update existing daily branch
- Multiple runs on same day append to same branch

## Data Format

### X-ray Flux JSON Structure

```json
[
  {
    "time_tag": "2025-11-24T12:10:00Z",
    "satellite": 16,
    "flux": 1.67e-6,
    "observed_flux": 1.67e-6,
    "electron_correction": 0.0,
    "electron_contamination": false,
    "energy": "0.05-0.4nm"
  }
]
```

### Proton Flux JSON Structure

```json
[
  {
    "time_tag": "2025-11-24T12:10:00Z",
    "satellite": 16,
    "flux": 0.67,
    "energy": ">=10 MeV"
  }
]
```

## Testing

A test script validates the workflow logic:

```bash
./tests/test_goes_workflow.sh
```

This test:
- Creates mock GOES data
- Validates JSON parsing with jq
- Extracts latest events
- Confirms audit file generation

The test runs without network dependencies.

## Maintenance

### Updating Retry Logic

Edit the `MAX_RETRIES` variable in the download steps (currently set to 3).

### Changing Schedule

Modify the cron expression in the `on.schedule` section:
```yaml
schedule:
  - cron: "7 * * * *"  # Current: every hour at HH:07
```

### Adding New Data Sources

Follow the existing pattern:
1. Add download step with retry logic
2. Add jq validation
3. Create audit file extraction
4. Update git add command to include new files

### Data Retention

The workflow accumulates data in feature branches. Periodically:
1. Merge feature branches to main
2. Delete old merged feature branches
3. Consider archiving historical data

## Security

- No credentials needed (NOAA data is public)
- Git commits use GitHub Actions bot identity
- No direct pushes to main branch
- All data validated before commit

## References

- [NOAA SWPC Products](https://www.swpc.noaa.gov/products)
- [GOES Data Documentation](https://www.swpc.noaa.gov/products/goes-xray-flux)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
