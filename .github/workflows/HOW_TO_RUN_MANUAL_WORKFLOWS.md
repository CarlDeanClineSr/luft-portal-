# How to Run Manual Workflows

**Date:** 2026-02-17  
**Status:** 21 workflows converted to manual dispatch only

## Overview

To reduce chaos and prevent workflows from "running into each other," we've converted 21 workflows from automatic scheduling to manual dispatch only. This means they will **ONLY** run when you manually trigger them from the GitHub Actions tab.

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

## 🎯 Manual Workflows (Run When You Want)

These **21 workflows** are now **manual dispatch only**. They will NOT run automatically.

### Analysis & Reporting Workflows
Run these when you want updated summaries or status reports:

- `hourly_summary.yml` - Generate hourly ACE/heartbeat summary
- `vault_narrator.yml` - Update vault status narration
- `vault_10row_forecast.yml` - Update 10-row forecast
- `hourly_dst_index.yml` - Calculate DST lattice index
- `heartbeat_plot.yml` - Generate CME heartbeat visualization
- `engine_status.yml` - Create space weather rapid report

### Daily Processing Workflows
Run these when you need daily aggregations or reports:

- `nightly_capsule.yml` - Generate daily capsule report
- `omni_ingest_daily.yml` - Process OMNIWeb daily data
- `daily_ml_rebound.yml` - Run ML rebound analysis
- `daily_noaa_forecast.yml` - Get NOAA 3-day forecast
- `daily_ligo_gw.yml` - Collect LIGO gravitational wave data
- `daily_cern_lhc.yml` - Collect CERN LHC luminosity data
- `nasa_daily_harvest.yml` - Harvest NASA magnetometer data

### Paper & Documentation Workflows
Run these when you want to collect new papers or update docs:

- `physics_paper_harvester.yml` - Harvest arXiv + CERN papers
- `inspire_harvest.yml` - Collect INSPIRE HEP papers
- `knowledge_index.yml` - Update repository knowledge index
- `index-job.yml` - Update capsule index & dashboard
- `build_papers.yml` - Build LaTeX papers to PDF
- `compile_paper.yml` - Compile discovery paper
- `physicist_note_pdf.yml` - Render physicist notes

### Code Quality Workflow
- `imperial_lexicon_guard.yml` - Scan for forbidden terminology

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

**Daily (Morning Check):**
- `engine_status.yml` - Get current space weather status
- `hourly_summary.yml` - Get latest summary
- `vault_narrator.yml` - Check vault status

**Weekly (Paper Updates):**
- `physics_paper_harvester.yml` - Get new papers
- `inspire_harvest.yml` - Get new INSPIRE papers

**Monthly (Major Updates):**
- `knowledge_index.yml` - Rebuild knowledge index
- `index-job.yml` - Update capsule index

**As Needed:**
- `nightly_capsule.yml` - After major data collection
- `daily_ligo_gw.yml` - When checking gravitational waves
- `daily_cern_lhc.yml` - When checking LHC data

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

## 🔄 Re-enabling Automatic Scheduling

If you want to restore automatic scheduling for any workflow:

1. Open the workflow file (e.g., `.github/workflows/hourly_summary.yml`)
2. Add back the schedule trigger:
   ```yaml
   on:
     schedule:
       - cron: '*/15 * * * *'  # Every 15 minutes
     workflow_dispatch:
   ```
3. Commit and push the change

The workflow will resume automatic execution.

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
A: No, they're optional. The core data collection continues automatically.

**Q: Can I run multiple workflows at the same time?**  
A: Yes, GitHub Actions can run multiple workflows concurrently.

**Q: What if I forget to run a manual workflow?**  
A: No problem! The satellite data is still being collected. Manual workflows just provide summaries and analysis.

**Q: Can I automate specific workflows again?**  
A: Yes, just add back the `schedule:` section to any workflow file.

## 🎯 Summary

- **19 automated workflows** = Live satellite data + utilities (keep running automatically)
- **21 manual workflows** = Summaries, analysis, papers (run when you want)
- **No more chaos** = Workflows won't run into each other
- **Full control** = You decide when to run summaries and reports

---

**Need help?** Check the Actions tab or run `gh workflow list` to see all available workflows.
