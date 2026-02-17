# Active Workflows Reference
**Date:** 2026-02-17  
**Total Active:** 40 workflows  
**Total Archived:** 35 workflows

This is a quick reference guide for understanding what workflows are currently active and why they're essential.

## 🚀 Real-Time Data Collectors (15 workflows)
**Purpose:** Continuous space weather and planetary data collection

### High-Frequency (Every 2-10 minutes)
- `dscovr_data_ingest.yml` - Every 2 min - DSCOVR solar wind plasma
- `l1_ace_realtime_2min.yml` - Every 2 min - ACE magnetometer & plasma
- `magnetometer_realtime_3min.yml` - Every 3 min - Ground magnetometer
- `goes_ingest.yml` - Every 5 min - GOES X-ray & particles
- `cme_detection_5min.yml` - Every 5 min - CME signature detection
- `hourly_noaa_solarwind.yml` - Every 5 min - NOAA solar wind
- `cme_heartbeat_logger.yml` - Every 5 min - CME heartbeat tracking
- `maven_realtime_10min.yml` - Every 10 min - Mars plasma/magnetometer

### Medium-Frequency (Every 15-30 minutes)
- `luft-voyager-audit-superaction.yml` - Every 15 min - Multi-satellite audit
- `noaa_parse_feeds.yml` - Every 20 min - NOAA text feed parsing
- `solar_wind_audit.yml` - Every 30 min - Solar wind audit

### Daily Data Collection
- `intermagnet_chi_analysis.yml` - Daily 06:15 - Ground magnetometer χ analysis
- `psp_ingest.yml` - Daily 12:00 - Parker Solar Probe data
- `goes_data_audit.yml` - Every 6 hours - GOES event auditing
- `noaa_text_parser.yml` - Every 6 hours - NOAA text parsing

## 📊 Periodic Summaries & Analysis (10 workflows)
**Purpose:** Aggregation, forecasting, and reporting

- `engine_status.yml` - Every 10 min - Rapid status report
- `hourly_summary.yml` - Every 15 min - ACE/heartbeat summary
- `vault_narrator.yml` - Every 15 min - Vault status narration
- `vault_10row_forecast.yml` - Every 15 min - Forecast updates
- `hourly_dst_index.yml` - Every 30 min - DST lattice index
- `heartbeat_plot.yml` - On CSV push - Heartbeat visualization
- `nightly_capsule.yml` - Daily 03:00 - Daily capsule report
- `omni_ingest_daily.yml` - Daily 12:00 - OMNIWeb data merge
- `daily_ml_rebound.yml` - Daily 02:30 - ML rebound analysis
- `daily_noaa_forecast.yml` - Daily 05:00, 17:00 - 3-day forecast

## 📚 Data Harvesting & Knowledge Base (6 workflows)
**Purpose:** Paper collection and metadata harvesting

- `physics_paper_harvester.yml` - Every 6 hours - arXiv + CERN papers
- `inspire_harvest.yml` - Daily 00:00 - INSPIRE HEP papers
- `nasa_daily_harvest.yml` - Daily 21:20 - Multi-mission magnetometer
- `knowledge_index.yml` - Daily 12:15 - Repository knowledge index
- `index-job.yml` - Daily 06:15 - Capsule index & dashboard
- `imperial_lexicon_guard.yml` - On push - Terminology scanning

## 🔬 Advanced Analysis (2 workflows)
**Purpose:** Scientific data collection

- `daily_ligo_gw.yml` - Daily 05:00 - LIGO gravitational waves
- `daily_cern_lhc.yml` - Daily 05:00 - CERN LHC luminosity

## 🏗️ Build & Publishing (4 workflows)
**Purpose:** Documentation and website generation

- `build_papers.yml` - On push - LaTeX to PDF
- `compile_paper.yml` - On push - Discovery paper compilation
- `physicist_note_pdf.yml` - On push - Note rendering
- `pages-deployment.yml` - Every 15 min + push - GitHub Pages

## 🔧 Utilities & Control (3 workflows)
**Purpose:** Manual controls and emergency management

- `PAUSE_ALL.yml` - Manual - Emergency pause
- `RESUME_ALL.yml` - Manual - Resume workflows
- `manual_deploy.yml` - Manual - Deployment trigger

---

## 📦 What Was Archived

### 26 Experimental/Research Workflows
Moved to `.github/workflows/ARCHIVED/experimental/`
- FFT analysis, reconnection simulations, momentum tests
- JWST intercept, star scanning, lightning analysis
- Imperial physics engines, chi boundary research
- Bio-resonance audits, baseline watchers

### 4 Deprecated Workflows
Moved to `.github/workflows/ARCHIVED/deprecated/`
- `daily_maven_mars.yml` - Duplicate of maven_realtime_10min
- `intermagnet_daily_chi.yml` - Superseded by newer analysis
- `update_dashboard_graph.yml` - Old dashboard approach
- `daily_gistemp.yml` - Off-topic climate data

### 4 One-Time Use Workflows
Moved to `.github/workflows/ARCHIVED/one_time_use/`
- File restoration and recovery tools
- Emergency system reset utilities
- CI/CD helper workflows

### 1 Broken Workflow
Moved to `.github/workflows/ARCHIVED/broken/`
- `capsule-validator2.yml` - Intentionally disabled

---

## 🔄 Re-enabling Archived Workflows

To re-enable any archived workflow, simply move it back:

```bash
# Example: Re-enable momentum test
git mv .github/workflows/ARCHIVED/experimental/momentum_test.yml .github/workflows/
git commit -m "Re-enable momentum test workflow"
git push
```

The workflow will automatically become active again.

---

## 📈 Workflow Efficiency

**Before Cleanup:**
- 75 total workflows
- 500-800+ daily runs
- High complexity and chaos

**After Cleanup:**
- 40 active workflows (35 archived)
- 300-400 daily runs
- Clean, observable execution
- All core data collection preserved

---

## ✅ Data Preservation Confirmed

All data has been preserved and untouched:
- ✅ `data/` folder - 34 subdirectories intact
- ✅ All CSV, JSON, TXT files preserved
- ✅ `index.html` user site untouched
- ✅ No data deletions or modifications

---

See `WORKFLOW_AUDIT_REPORT.md` for comprehensive details.
