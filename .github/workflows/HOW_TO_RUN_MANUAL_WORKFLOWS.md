# How to Run Manual Workflows

**Date:** 2026-02-17  
**Status:** 21 workflows scheduled daily with manual dispatch available

## Overview

To reduce chaos and prevent workflows from "running into each other," we've scheduled 21 workflows to run **once per day** on staggered timers. These workflows still support manual dispatch if you need an extra run.

## 🛰️ Automated Workflows (Still Running)

These **15 workflows** remain automated because they collect **live/new satellite data**:

### High-Frequency (Every 2-10 minutes)
- `dscovr_data_ingest.yml` - Every 2 min
- `l1_ace_realtime_2min.yml` - Every 2 min  
- `magnetometer_realtime_3min.yml` - Every 3 min
- `goes_ingest.yml` - Every 5 min
- `cme_detection_5min.yml` - Every 5 min
- `hourly_noaa_solarwind.yml` - Every 5 min
- `cme_heartbeat_logger.yml` - Every 5 min
- `maven_realtime_10min.yml` - Every 10 min

### Medium-Frequency (Every 15-30 minutes)
- `luft-voyager-audit-superaction.yml` - Every 15 min
- `noaa_parse_feeds.yml` - Every 20 min
- `solar_wind_audit.yml` - Every 30 min

### Daily/Periodic
- `intermagnet_chi_analysis.yml` - Daily
- `psp_ingest.yml` - Daily
- `goes_data_audit.yml` - Every 6 hours
- `noaa_text_parser.yml` - Every 6 hours

### Utilities (Always Available)
- `PAUSE_ALL.yml` - Manual emergency pause
- `RESUME_ALL.yml` - Manual resume
- `manual_deploy.yml` - Manual deployment
- `pages-deployment.yml` - Auto-deploys website

## 🎯 Daily Scheduled Workflows (Automatic + Manual)

These **21 workflows** run **once per day** on staggered schedules. You can still run any of them manually.

### Analysis & Reporting Workflows
Run these when you want updated summaries or status reports:

- `hourly_summary.yml` - Daily 05:07 UTC - Generate hourly ACE/heartbeat summary
- `vault_narrator.yml` - Daily 09:07 UTC - Update vault status narration
- `vault_10row_forecast.yml` - Daily 10:07 UTC - Update 10-row forecast
- `hourly_dst_index.yml` - Daily 06:07 UTC - Calculate DST lattice index
- `heartbeat_plot.yml` - Daily 08:07 UTC - Generate CME heartbeat visualization
- `engine_status.yml` - Daily 07:07 UTC - Create space weather rapid report

### Daily Processing Workflows
Run these when you need daily aggregations or reports:

- `nightly_capsule.yml` - Daily 11:07 UTC - Generate daily capsule report
- `omni_ingest_daily.yml` - Daily 03:07 UTC - Process OMNIWeb daily data
- `daily_ml_rebound.yml` - Daily 04:07 UTC - Run ML rebound analysis
- `daily_noaa_forecast.yml` - Daily 00:07 UTC - Get NOAA 3-day forecast
- `daily_ligo_gw.yml` - Daily 02:07 UTC - Collect LIGO gravitational wave data
- `daily_cern_lhc.yml` - Daily 01:07 UTC - Collect CERN LHC luminosity data
- `nasa_daily_harvest.yml` - Daily 14:07 UTC - Harvest NASA magnetometer data

### Paper & Documentation Workflows
Run these when you want to collect new papers or update docs:

- `physics_paper_harvester.yml` - Daily 12:07 UTC - Harvest arXiv + CERN papers
- `inspire_harvest.yml` - Daily 13:07 UTC - Collect INSPIRE HEP papers
- `knowledge_index.yml` - Daily 17:07 UTC - Update repository knowledge index
- `index-job.yml` - Daily 18:07 UTC - Update capsule index & dashboard
- `build_papers.yml` - Daily 19:07 UTC - Build LaTeX papers to PDF
- `compile_paper.yml` - Daily 20:07 UTC - Compile discovery paper
- `physicist_note_pdf.yml` - Daily 21:07 UTC - Render physicist notes

### Code Quality Workflow
- `imperial_lexicon_guard.yml` - Daily 22:07 UTC - Scan for forbidden terminology

## 📖 How to Run a Manual Workflow

### Method 1: GitHub Web Interface (Easiest)

1. Go to your repository on GitHub
2. Click the **"Actions"** tab at the top
3. In the left sidebar, click on the workflow you want to run
4. Click the **"Run workflow"** button (top right)
5. Select the branch (usually `main`)
6. Click **"Run workflow"** to confirm

### Method 2: GitHub CLI (Command Line)

```bash
# Run a specific workflow
gh workflow run hourly_summary.yml

# Run with a specific branch
gh workflow run vault_narrator.yml --ref main

# List all workflows
gh workflow list

# View recent runs
gh run list --limit 10
```

### Method 3: GitHub API (Advanced)

```bash
# Using curl
curl -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.github.com/repos/CarlDeanClineSr/luft-portal-/actions/workflows/hourly_summary.yml/dispatches \
  -d '{"ref":"main"}'
```

## 💡 Recommended Workflow

### When to Run Manual Workflows

These workflows already run daily. Trigger manual runs only when you need an extra refresh.

### Batch Running Multiple Workflows

You can run multiple workflows at once:

```bash
# Morning routine
gh workflow run engine_status.yml
gh workflow run hourly_summary.yml
gh workflow run vault_narrator.yml

# Paper collection routine
gh workflow run physics_paper_harvester.yml
gh workflow run inspire_harvest.yml
```

## 🔄 Adjusting Automatic Scheduling

If you want to adjust the daily schedule for any workflow:

1. Open the workflow file (e.g., `.github/workflows/hourly_summary.yml`)
2. Add back the schedule trigger:
   ```yaml
   on:
     schedule:
       - cron: '*/15 * * * *'  # Every 15 minutes
     workflow_dispatch:
   ```
3. Commit and push the change

The workflow will keep running automatically on the updated schedule.

## 📊 Workflow Status Dashboard

You can view all workflow runs on the Actions tab:
- **Green check** ✅ = Success
- **Red X** ❌ = Failed
- **Yellow dot** 🟡 = Running
- **Gray circle** ⚫ = Queued

## ❓ FAQ

**Q: Will the satellite data still be collected automatically?**  
A: Yes! All 15 satellite data collectors remain automated.

**Q: Do I need to run the manual workflows?**  
A: No, they already run once per day. Manual runs are optional.

**Q: Can I run multiple workflows at the same time?**  
A: Yes, but the daily schedules are staggered to avoid conflicts.

**Q: What if I forget to run a manual workflow?**  
A: No problem! The daily schedule will still run automatically.

**Q: Can I change when a workflow runs?**  
A: Yes, edit the `schedule:` section in the workflow file.

## 🎯 Summary

- **19 automated workflows** = Live satellite data + utilities (keep running automatically)
- **21 daily workflows** = Summaries, analysis, papers (staggered)
- **No more chaos** = Workflows won't run into each other
- **Full control** = You can still run extra manual jobs

---

**Need help?** Check the Actions tab or run `gh workflow list` to see all available workflows.
