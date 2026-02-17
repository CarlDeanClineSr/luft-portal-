# Workflow Outage Recovery Guide

## What Happened During the GitHub Actions Outage

On 2026-02-02, GitHub Actions experienced a worldwide outage. During this time:

1. **All scheduled workflows were paused** - GitHub temporarily disabled workflow execution
2. **The PAUSE_ALL.yml workflow was created** - This was a notice-only workflow to document the pause
3. **Workflows were re-enabled** - After the outage ended, workflows were turned back on

## Understanding Workflow Behavior After Re-enabling

### ✅ What Happens Automatically

When you re-enable workflows after they've been disabled, **scheduled workflows (cron-based) will automatically resume** on their next scheduled run time. No action is required for them to start running again.

For example:
- A workflow scheduled to run every 5 minutes (`cron: '*/5 * * * *'`) will run at the next 5-minute mark after being enabled
- A daily workflow at 5:00 UTC (`cron: '0 5 * * *'`) will run the next day at 5:00 UTC

### ⚠️ What Does NOT Happen Automatically

**Missed runs are NOT executed retroactively.** If workflows were disabled from 10:00 to 12:00:
- A 5-minute workflow will NOT run 24 times to catch up
- A hourly workflow will NOT run twice to make up for the missed hours
- Workflows simply wait for their next scheduled time and continue from there

### 🎯 Do You Need to "Counter" the PAUSE_ALL Workflow?

**No.** The `PAUSE_ALL.yml` workflow does not actually pause or control other workflows. It's just a notice workflow that echoes a message. It has no effect on the operation of other workflows.

## How to Resume Operations After an Outage

### Option 1: Wait for Automatic Resumption (Recommended)

Simply wait for workflows to run on their next scheduled time. This is the safest approach as it:
- Avoids overwhelming GitHub Actions with simultaneous workflow runs
- Allows the system to return to normal gradually
- Ensures proper timing and coordination between workflows

**Timeline for automatic resumption:**
- **Every 5 minutes:** DSCOVR solar wind, CME heartbeat, NOAA solar wind
- **Every 10-15 minutes:** Dashboard updates, heartbeat plots
- **Every hour:** Summary generator, monitoring workflows
- **Daily:** Data ingestion from CERN, LIGO, MAVEN, etc.

### Option 2: Manually Kickstart Workflows (If Needed)

If you need to immediately resume data collection, use the **RESUME_ALL workflow**:

1. **Go to Actions tab** in GitHub
2. **Click on "RESUME ALL WORKFLOWS - Kickstart After Outage"**
3. **Click "Run workflow"**
4. **Select which groups to kickstart:**
   - ✅ Critical workflows (DSCOVR, CME heartbeat, NOAA) - **Recommended**
   - ✅ Hourly workflows (Summary, DST, USGS, GOES) - **Recommended**
   - ⬜ Daily workflows - Only if needed (they'll run at their scheduled time anyway)

5. **Click "Run workflow"** to execute

This will manually trigger the selected workflows immediately, without waiting for their next scheduled run.

### Option 3: Manually Trigger Specific Workflows

If you only need to kickstart specific workflows:

**Via GitHub UI:**
1. Go to **Actions** tab
2. Click on the specific workflow (e.g., "CME Heartbeat Logger")
3. Click **"Run workflow"** button
4. Select branch (usually `main`)
5. Click **"Run workflow"**

**Via GitHub CLI:**
```bash
# Install GitHub CLI if needed
gh auth login

# Trigger a specific workflow
gh workflow run cme_heartbeat_logger.yml
gh workflow run hourly_noaa_solarwind.yml
gh workflow run hourly_summary.yml

# Check status
gh run list --limit 10
```

## Checking Workflow Status

### Via GitHub UI

1. Go to **Actions** tab
2. View recent workflow runs
3. Look for:
   - ✅ Green checkmarks = successful runs
   - ❌ Red X = failed runs
   - 🟡 Yellow dot = currently running

### Via GitHub CLI

```bash
# List recent runs
gh run list --limit 20

# List runs for a specific workflow
gh run list --workflow=cme_heartbeat_logger.yml --limit 5

# View details of a specific run
gh run view [RUN_ID]

# View logs
gh run view [RUN_ID] --log
```

### Via Monitoring Files

Check these files to verify data collection has resumed:
- `data/cme_heartbeat_log_*.csv` - Should show recent timestamps
- `data/noaa_solarwind/*.csv` - Recent solar wind data
- `reports/HOURLY_SUMMARY.md` - Should update every hour
- Check git commit history: `git log --oneline -20`

## Verifying Everything is Working

After resumption, verify these key indicators within 1-2 hours:

- [ ] CME heartbeat logger has run (check `data/cme_heartbeat_log_*.csv`)
- [ ] DSCOVR solar wind data is being collected
- [ ] NOAA solar wind data is being collected
- [ ] Hourly summary has been generated
- [ ] Recent commits show "data:" or workflow updates
- [ ] No failed workflows in Actions tab

## Troubleshooting

### Problem: Workflows aren't running after re-enabling

**Check:**
1. Are workflows actually enabled? (Settings → Actions → General → Actions permissions)
2. Check the schedule time - it may not be the scheduled time yet
3. Look for errors in Actions tab
4. Verify workflow files exist in `.github/workflows/`

**Solution:**
- Manually trigger critical workflows using RESUME_ALL or workflow_dispatch
- Wait for the next scheduled run time
- Check repository permissions

### Problem: Workflows failing after resumption

**Common causes:**
1. Git conflicts (multiple workflows pushing simultaneously)
2. Data source APIs may have changed during outage
3. Dependency issues
4. Rate limiting

**Solution:**
1. Check workflow logs for specific errors
2. Re-run failed workflows manually
3. All workflows have automatic conflict resolution (`git pull --rebase`)
4. Wait a few minutes and retry if rate-limited

### Problem: Need to backfill missed data

**Manual backfill:**
1. Identify which time periods are missing
2. Manually trigger workflows with workflow_dispatch
3. Or run the Python scripts directly:
   ```bash
   python tools/fetch_noaa_solarwind.py
   python scripts/cme_heartbeat_logger.py
   python tools/generate_hourly_summary.py
   ```

## Summary

### Key Points

✅ **Scheduled workflows resume automatically** - No action required
❌ **Missed runs are NOT executed retroactively** - Data gaps may exist
🔄 **Use RESUME_ALL to kickstart** - If you want immediate resumption
📊 **Monitor for 1-2 hours** - Verify data collection resumes
🔍 **Check Actions tab** - Confirm no failures

### Quick Reference

| Scenario | Action Required | Method |
|----------|----------------|--------|
| Just re-enabled workflows | None - wait for next scheduled run | Automatic |
| Need immediate resumption | Run RESUME_ALL workflow | Manual kickstart |
| Need specific workflow now | Trigger via workflow_dispatch | Manual single trigger |
| Need to backfill data | Run workflows or scripts manually | Manual execution |
| Checking status | View Actions tab or use `gh run list` | Monitoring |

## Additional Resources

- [GitHub Actions Status](https://www.githubstatus.com/)
- [Workflow Documentation](WORKFLOW_DOCUMENTATION.md)
- [ Portal Workflows Overview](WORKFLOWS.%20md)

---

**Last Updated:** 2026-02-03  
**Status:** ✅ All workflows operational  
**Imperial Physics Observatory:** Online and monitoring χ ≤ 0.15
