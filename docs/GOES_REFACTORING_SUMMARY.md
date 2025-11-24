# GOES Workflow Refactoring - Summary for Carl

## What Was Fixed

Both GOES workflows (goes_ingest.yml and goes_data_audit.yml) were failing every run due to multiple issues:

1. **Missing Directory Creation**: Workflows tried to write to data/goes/ before creating it
2. **No Retry Logic**: Network failures caused immediate failure
3. **No JSON Validation**: Invalid or error responses weren't caught
4. **Direct Main Commits**: No review process for data quality
5. **Poor Error Messages**: Hard to diagnose what went wrong
6. **Overlapping Functionality**: Two workflows doing similar things

## Solution

### One Robust Workflow: goes_data_audit.yml

I've rebuilt the GOES data audit workflow with enterprise-grade reliability:

**Reliability Features:**
- ✅ Creates data/goes directory automatically
- ✅ Downloads BOTH X-ray and proton flux data
- ✅ 3 retry attempts with 5-second delays for network issues
- ✅ 30-second timeout protection per attempt
- ✅ jq validation after every JSON operation
- ✅ Clear ✓/✗ status indicators in logs

**Safety Features:**
- ✅ Pushes to daily feature branches (data/goes-audit-20251124)
- ✅ Never touches main directly - you review via PR
- ✅ Shows data summary in workflow logs
- ✅ Handles both new and existing branches gracefully

**Files Created:**
- `data/goes/goes_xray_flux.json` - Full X-ray time series
- `data/goes/goes_xray_audit.json` - Latest X-ray reading
- `data/goes/goes_proton_flux.json` - Full proton time series
- `data/goes/goes_proton_audit.json` - Latest proton reading

### Deprecated: goes_ingest.yml

The goes_ingest.yml workflow has been deprecated because:
- It overlapped with goes_data_audit.yml
- Referenced scripts that don't exist (goes_capsule_builder.py)
- Had the same issues as goes_data_audit.yml

I kept the file with a clear deprecation notice. If you want capsule generation in the future, it can be rebuilt to consume the validated data from goes_data_audit.yml.

## How to Use It

### Monitoring (After Hourly Runs)

1. Go to **GitHub Actions** tab
2. Look for **"GOES Data Audit — Robust"**
3. Check if latest run succeeded (green ✓)
4. Click on run to see details and data summary

### Reviewing Data (Daily or Weekly)

1. Look for new branch: **data/goes-audit-YYYYMMDD**
2. Review the files changed in that branch
3. If data looks good, create a **Pull Request to main**
4. Merge the PR to update main branch

### Manual Testing

1. Go to **Actions** → **"GOES Data Audit — Robust"**
2. Click **"Run workflow"**
3. Select your branch
4. Click **"Run workflow"** button
5. Watch it run and check the logs

## What to Expect

### Success Scenario
```
✓ Directory ready at data/goes
✓ Download successful
✓ JSON validation passed
✓ X-ray audit file created
✓ Proton audit file created
✓ Changes committed and pushed to data/goes-audit-20251124
```

You'll see a new branch and can review the data.

### Failure Scenario
```
✗ Download failed (curl exit code: 6)
Attempt 2 of 3...
Retrying in 5 seconds...
```

Workflow will retry up to 3 times. If all fail, you'll see clear error messages about what went wrong (network down, invalid JSON, etc.).

## Files in This PR

- `.github/workflows/goes_data_audit.yml` - The robust workflow
- `.github/workflows/goes_ingest.yml` - Deprecated (shows notice)
- `tests/test_goes_workflow.sh` - Test script (validates logic)
- `tests/README.md` - Test documentation
- `docs/GOES_WORKFLOW.md` - Complete user guide

## Testing Done

✅ Test script validates all workflow logic
✅ YAML syntax validated
✅ CodeQL security scan: 0 vulnerabilities
✅ Backward compatible with existing data structures

## Next Steps for You

1. **Review this PR** - Check the workflow changes make sense
2. **Merge the PR** - Deploy the new robust workflow
3. **Wait for next hourly run** (HH:07) - See it work automatically
4. **Review a data branch** - See the new feature branch workflow
5. **Merge data to main** - Complete the cycle

## Questions?

Check `docs/GOES_WORKFLOW.md` for:
- Detailed usage instructions
- Troubleshooting guide
- Data format reference
- Maintenance procedures

## Bottom Line

Instead of two broken workflows that fail every run, you now have:
- ✅ One robust workflow that handles failures gracefully
- ✅ Clear error messages when things go wrong
- ✅ Safe review process before data hits main
- ✅ Complete documentation for maintenance
- ✅ Test coverage for future changes

The workflow runs hourly at HH:07 and creates daily branches for you to review. When you're satisfied with the data quality, merge the branch to main via PR.
