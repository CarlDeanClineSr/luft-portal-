# Workflow Pause and Resume

This directory contains two utility workflows for managing GitHub Actions during maintenance or outages:

## PAUSE_ALL.yml
**Purpose:** Notice-only workflow to document when workflows are manually disabled.

**What it does:**
- Echoes a message indicating workflows are paused
- Does NOT actually pause, disable, or control other workflows
- Serves as a marker/notification in the Actions history

**When to use:**
- During planned maintenance
- During GitHub Actions outages
- When you manually disable workflows in Settings

**How to use:**
1. Go to Settings → Actions → General
2. Select "Disable Actions" or disable individual workflows
3. Run PAUSE_ALL workflow to document the pause in Actions history

## RESUME_ALL.yml
**Purpose:** Kickstart critical workflows after an outage or maintenance period.

**What it does:**
- Provides options to trigger groups of workflows immediately
- Automatically triggers critical, hourly, or daily workflows
- Helps resume data collection without waiting for next scheduled run

**When to use:**
- After re-enabling workflows following a GitHub Actions outage
- After planned maintenance when you want immediate data collection
- When you need to "catch up" missed workflow runs

**How to use:**
1. Go to Actions → "RESUME ALL WORKFLOWS - Kickstart After Outage"
2. Click "Run workflow"
3. Select which groups to kickstart:
   - ✅ **Critical workflows** (every 5 min) - DSCOVR, CME heartbeat, NOAA solar wind
   - ✅ **Hourly workflows** - Summary, monitoring, data collection
   - ⬜ **Daily workflows** - Only if needed (will run at scheduled time anyway)
4. Click "Run workflow"

## Understanding Workflow Resumption

### Automatic Behavior
When you re-enable workflows after disabling them:
- ✅ Scheduled workflows (cron-based) **automatically resume** on their next scheduled run
- ❌ Missed runs are **NOT executed retroactively**
- ⏰ Workflows simply wait for their next cron schedule and continue from there

### Example Timeline
If workflows were disabled from 10:00 to 12:00:
- A workflow scheduled every 5 minutes will NOT run 24 times to catch up
- It will simply run at the next 5-minute mark after 12:00 (e.g., 12:05)
- Data from the 10:00-12:00 period will be missing unless manually backfilled

### Manual Kickstart vs Automatic Resumption

| Method | Speed | Data Gaps | Use Case |
|--------|-------|-----------|----------|
| **Automatic** | Slower (wait for schedule) | May have gaps | Normal resumption, gradual return |
| **Manual Kickstart** | Immediate | May still have gaps | Urgent data collection needed |
| **Manual Backfill** | Custom | Can fill gaps | Need complete historical data |

## Workflow Status

### How to Check If Workflows Are Running

**Via GitHub UI:**
1. Go to **Actions** tab
2. Look for recent workflow runs (green ✓ = success)
3. Check timestamps to verify workflows are running on schedule

**Via GitHub CLI:**
```bash
# List recent workflow runs
gh run list --limit 20

# Check specific workflow
gh run list --workflow=cme_heartbeat_logger.yml --limit 5

# View detailed status
gh run view [RUN_ID]
```

**Via Data Files:**
- Check `data/cme_heartbeat_log_*.csv` for recent timestamps
- Look at git commit history: `git log --oneline -20`
- Verify `reports/HOURLY_SUMMARY.md` is updating

## Complete Documentation

For comprehensive information about handling outages and workflow management:
- 📖 [WORKFLOW_OUTAGE_RECOVERY.md](../../WORKFLOW_OUTAGE_RECOVERY.md) - Complete outage recovery guide
- 📚 [WORKFLOW_DOCUMENTATION.md](../../WORKFLOW_DOCUMENTATION.md) - All workflow documentation
- 📊 [WORKFLOWS. md](../../WORKFLOWS.%20md) - Workflow overview and statistics

## Quick Reference

| Scenario | Action | File to Use |
|----------|--------|-------------|
| **Planned maintenance starting** | Run PAUSE_ALL, then disable workflows in Settings | PAUSE_ALL.yml |
| **Maintenance ended** | Re-enable workflows, optionally run RESUME_ALL | RESUME_ALL.yml |
| **After GitHub Actions outage** | Re-enable workflows (if needed), run RESUME_ALL | RESUME_ALL.yml |
| **Need immediate data collection** | Run RESUME_ALL with appropriate options | RESUME_ALL.yml |
| **Just checking status** | No workflow needed, check Actions tab | N/A |

---

**Note:** Both workflows are triggered via `workflow_dispatch`, meaning they only run when manually triggered. They do not run on a schedule and do not affect other workflows automatically.
