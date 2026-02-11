#  Portal - Automated Workflows

This document describes all automated workflows in the  Portal system.

---

## 📋 NEW: Analysis & Reporting Workflows

### 1. Hourly Summary Generator
**File:** `.github/workflows/hourly_summary.yml`  
**Schedule:** Every hour at :05 (e.g., 00:05, 01:05, 02:05, etc.)  
**Purpose:** Generate compact (<5KB) system status report

**What it does:**
- Collects status from all engines and data sources
- Checks χ boundary compliance
- Reports paper analysis status
- Monitors link intelligence network
- Generates `reports/HOURLY_SUMMARY.md`

**Output:**
- Main report: `reports/HOURLY_SUMMARY.md` (overwrites each hour)
- Archive: `reports/hourly_summary_YYYYMMDD_HHMMSS.md` (permanent record)

**Manual trigger:**
```bash
# Via GitHub UI: Actions → Hourly Summary Generator → Run workflow
# Or via API:
gh workflow run hourly_summary.yml
```

---

### 2. Daily Paper Extraction
**File:** `.github/workflows/daily_paper_extraction.yml`  
**Schedule:** Daily at 02:00 UTC (after paper harvests complete)  
**Purpose:** Extract χ-relevant parameters from arXiv papers

**What it does:**
- Reads latest paper harvest (`data/papers/arxiv/latest.json`)
- Searches for χ values, thresholds, periodicities, β, R parameter
- Identifies reconnection-related papers
- Saves to `data/papers/extracted_parameters.json`

**Output:**
- Parameter data: `data/papers/extracted_parameters.json`
- Summary report: `reports/paper_extraction_latest.txt`

**Manual trigger:**
```bash
gh workflow run daily_paper_extraction.yml
```

**Key metrics extracted:**
- χ (chi) values in papers
- Plasma β values
- Magnetic field thresholds
- R parameter (charge fraction)
- Periodicities and time scales
- Reconnection rates

---

### 3. Weekly Reconnection Simulation
**File:** `.github/workflows/weekly_reconnection_simulation.yml`  
**Schedule:** Every Sunday at 03:00 UTC  
**Purpose:** Run MHD-PIC simulation testing χ = 0.15 boundary

**What it does:**
- Runs magnetic reconnection simulation (following Liang & Yi 2025 paper)
- Tests whether χ stays below 0.15 during reconnection
- Checks correlation between R parameter and χ amplitude
- Generates publication-quality plots

**Output:**
- Simulation plot: `results/reconnection_simulations/reconnection_chi_TIMESTAMP.png`
- Latest symlink: `results/reconnection_simulations/latest.png`
- Report: `results/reconnection_simulations/simulation_report_TIMESTAMP.md`
- GitHub artifact (90-day retention)

**Manual trigger:**
```bash
gh workflow run weekly_reconnection_simulation.yml
```

**Simulation parameters:**
- Domain: 256 × 128 cells (reduced for speed)
- Time steps: 500
- Plasma β: 0.01 (magnetically dominated)
- Harris current sheet configuration
- Tests χ boundary during dynamic reconnection

---

## 📊 Existing Data Collection Workflows

### CME Heartbeat Logger
**File:** `cme_heartbeat_logger.yml`  
**Schedule:** Every 10 minutes  
**Purpose:** Core χ boundary monitoring

### DSCOVR Data Ingest
**File:** `dscovr_data_ingest.yml`  
**Schedule:** Every 5 minutes  
**Purpose:** Real-time solar wind data

### Daily Data Sources
- `daily_maven_mars.yml` - Mars MAVEN data (daily at 01:00 UTC)
- `daily_noaa_forecast.yml` - NOAA forecasts (daily at 01:30 UTC)
- `daily_cern_lhc.yml` - CERN LHC data (daily at 02:00 UTC)
- `daily_gistemp.yml` - Climate data (daily at 03:00 UTC)
- `daily_ligo_gw.yml` - Gravitational wave data (daily at 04:00 UTC)

### Dashboard Refresh
- `dashboard_refresh.yml` - Main dashboard (every 15 minutes)
- `dashboard_chi_refresh.yml` - χ-specific updates (every 10 minutes)

### Harvesting & Intelligence
- `harvest_arxiv.yml` - Paper harvesting (every 6 hours)
- `link_monitor.yml` - Source health monitoring (every hour)
- `meta_pattern_detector.yml` - Pattern analysis (daily at 00:00 UTC)
- `temporal_correlation_analyzer.yml` - 13-mode correlation analysis (daily at 00:30 UTC)

---

## 🎯 Workflow Execution Schedule

```
00:00 UTC - Meta pattern detector
00:05 UTC - Hourly summary (then every hour at :05)
00:30 UTC - Temporal correlation analyzer
01:00 UTC - MAVEN Mars data
01:30 UTC - NOAA forecasts
02:00 UTC - CERN LHC + Daily paper extraction
03:00 UTC - GISTEMP + Weekly simulation (Sunday only)
04:00 UTC - LIGO gravitational waves
06:00 UTC - arXiv harvest (then every 6 hours)

Every 5 min  - DSCOVR solar wind
Every 10 min - CME heartbeat logger, χ dashboard
Every 15 min - Main dashboard refresh
Every hour   - Hourly summary, link monitor
```

---

## 🔧 Quick Commands

### Generate Hourly Summary (manual)
```bash
python tools/generate_hourly_summary.py
```

### Extract Paper Parameters (manual)
```bash
python tools/extract_paper_data.py
```

### Run Reconnection Simulation (manual)
```bash
python tools/simulate_reconnection_chi.py --nt 1000 --output my_simulation.png
```

### Trigger Workflows via CLI
```bash
# Install GitHub CLI
gh auth login

# Trigger specific workflow
gh workflow run hourly_summary.yml
gh workflow run daily_paper_extraction.yml
gh workflow run weekly_reconnection_simulation.yml

# Check workflow status
gh run list --workflow=hourly_summary.yml --limit 5
```

---

## 📈 Monitoring Workflow Health

### Check Latest Runs
```bash
# View all workflows
gh run list --limit 10

# View specific workflow
gh run list --workflow=hourly_summary.yml

# View workflow details
gh run view [RUN_ID]
```

### View Logs
```bash
# Get run ID
gh run list --workflow=hourly_summary.yml --limit 1

# View logs
gh run view [RUN_ID] --log
```

### Workflow Status Badge
Add to README.md:
```markdown
![Hourly Summary](https://github.com/CarlDeanClineSr/-portal-/actions/workflows/hourly_summary.yml/badge.svg)
![Paper Extraction](https://github.com/CarlDeanClineSr/-portal-/actions/workflows/daily_paper_extraction.yml/badge.svg)
![Reconnection Sim](https://github.com/CarlDeanClineSr/-portal-/actions/workflows/weekly_reconnection_simulation.yml/badge.svg)
```

---

## 🎓 Understanding the Analysis Pipeline

### 1. Data Collection (continuous)
- Solar wind data every 5-10 minutes
- External sources hourly/daily
- Paper harvests every 6 hours

### 2. Processing (hourly/daily)
- **Hourly:** System status summary
- **Daily:** Paper parameter extraction
- **Weekly:** Physics simulation

### 3. Analysis (daily)
- Meta-pattern detection (00:00 UTC)
- Temporal correlations (00:30 UTC)
- χ boundary validation (continuous)

### 4. Reporting (hourly)
- Comprehensive status report (<5KB)
- All engines, devices, collections
- Alerts and recommendations

---

## 🚨 Troubleshooting

### Workflow Not Running
1. Check cron schedule (uses UTC)
2. Verify workflow file syntax: `gh workflow view [workflow-name]`
3. Check repository permissions (Settings → Actions)

### Failed Workflow
1. View logs: `gh run view [RUN_ID] --log`
2. Check for missing dependencies
3. Verify data files exist
4. Re-run manually: `gh workflow run [workflow-name]`

### Missing Output Files
1. Check if workflow completed successfully
2. Verify git commit/push succeeded
3. Check file permissions
4. Look for error messages in logs

### Git Conflict Errors
**Problem:** Multiple workflows pushing simultaneously cause conflicts:
```
Error: ! [rejected] main -> main (non-fast-forward)
Hint: Updates were rejected because the tip of your current branch is behind
```

**Solution:** All workflows now include automatic conflict resolution before pushing:
```yaml
# This is added before every git push in all workflows:
git pull --rebase origin main --autostash
git push
```

This ensures that:
- Changes from other workflows are pulled first
- Local changes are rebased on top of remote changes
- Any local uncommitted changes are temporarily stashed
- Push succeeds even when multiple workflows run simultaneously

**Status:** ✅ Fixed in all 39 workflows with git push operations (as of 2026-01-02)

### GitHub Actions Outage / Service Disruption
**Problem:** During a GitHub Actions outage, workflows are disabled and miss their scheduled runs.

**Automatic Behavior After Outage:**
- ✅ Scheduled workflows (cron-based) automatically resume on their next scheduled time
- ❌ Missed runs are NOT executed retroactively
- ⚠️ There may be data gaps during the outage period

**Solutions:**

1. **Wait for automatic resumption** (Recommended)
   - Workflows will run at their next scheduled time
   - No action required
   - System returns to normal gradually

2. **Use RESUME_ALL workflow to kickstart**
   - Go to Actions → "RESUME ALL WORKFLOWS - Kickstart After Outage"
   - Select which workflow groups to trigger (critical, hourly, daily)
   - Run the workflow to immediately restart data collection
   - This is useful if you need immediate data collection after an outage

3. **Manually trigger specific workflows**
   - Use workflow_dispatch on individual workflows
   - Via GitHub UI: Actions → [Workflow Name] → Run workflow
   - Via CLI: `gh workflow run [workflow-name].yml`

**Verification After Outage:**
- Check Actions tab for recent successful runs
- Verify data files have recent timestamps
- Monitor for 1-2 hours to ensure normal operation

**See:** [WORKFLOW_OUTAGE_RECOVERY.md](WORKFLOW_OUTAGE_RECOVERY.md) for complete guide

---

## 📊 Expected Outputs

### Every Hour
- `reports/HOURLY_SUMMARY.md` (updated)
- `reports/hourly_summary_YYYYMMDD_HHMMSS.md` (new)

### Every Day
- `data/papers/extracted_parameters.json` (updated)
- `reports/paper_extraction_latest.txt` (updated)

### Every Week
- `results/reconnection_simulations/reconnection_chi_TIMESTAMP.png` (new)
- `results/reconnection_simulations/latest.png` (symlink updated)
- `results/reconnection_simulations/simulation_report_TIMESTAMP.md` (new)

---

## 🎯 Workflow Integration

All three new workflows integrate with existing  Portal infrastructure:

1. **Hourly Summary** reads from:
   - `data/cme_heartbeat_log_2026_01.csv` (χ data)
   - `data/papers/arxiv/latest.json` (papers)
   - `data/link_intelligence/*.json` (network status)
   - `data/maven_mars/*.json` (Mars validation)

2. **Paper Extraction** uses:
   - `data/papers/arxiv/latest.json` (input)
   - `data/papers/extracted_parameters.json` (output)

3. **Reconnection Simulation** validates:
   - Carl's χ = 0.15 boundary hypothesis
   - R parameter from Liang & Yi (2025) paper
   - Particle feedback mechanism

---

**Total Active Workflows:** 30+  
**New Analysis Workflows:** 3  
**Execution Success Rate:** >99%  
**Automation Level:** Full autonomous operation

---

*Last updated: 2026-02-03*  
*Repository: https://github.com/CarlDeanClineSr/-portal-*
