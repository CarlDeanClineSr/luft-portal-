# LUFT Portal - Master Data Index
**Last Updated:** 2026-01-02 00:23 UTC  
**Status:** ✅ All systems operational

---

## 📊 LIVE DATA FEEDS

### Solar Wind & Magnetosphere
- **File:** `data/cme_heartbeat_log_2025_12.csv`
- **Records:** 561 observations (Dec 2-27, 2025)
- **χ Stats:** 56.1% at boundary, 0% violations
- **Status:** ✅ VALIDATED

- **File:** `data/cme_heartbeat_log_2026_01.csv`
- **Records:** Latest January 2026 observations
- **Status:** ✅ ACTIVE

### χ Boundary Tracking
- **File:** `data/chi_boundary_tracking.jsonl`
- **Format:** Append-only, one JSON per line
- **Contains:** Historical attractor state records
- **Latest:** Real-time χ boundary state tracking

### Mars Validation
- **File:** `data/maven_mars/mars_chi_analysis_results.json`
- **χ Value:** 0.143 (BELOW 0.15 ✅)
- **Status:** CONFIRMED at 1.5 AU

### Storm Phase Tracking
- **File:** `data/storm_phase_metrics.json`
- **Contains:** Geomagnetic storm phase classification
- **File:** `data/storm_phase_summary.json`
- **Contains:** Summary statistics of storm phases

---

## 📚 PAPER HARVEST (arXiv)

### Most Recent Harvest
- **File:** `data/papers/arxiv/latest.json` (symlink to most recent)
- **Actual:** `data/papers/arxiv/arxiv_harvest_20260101_181315.json`
- **Date:** 2026-01-01 18:13:15 UTC
- **Papers:** 132 LUFT-relevant papers
- **Categories:** astro-ph.HE, astro-ph.CO, physics.plasm-ph, physics.space-ph, hep-ph, gr-qc

### Quick Access
```bash
# View latest paper harvest
cat data/papers/arxiv/latest.json | jq '.papers[0:5]'

# Search for specific topics
cat data/papers/arxiv/latest.json | jq '.papers[] | select(.title | test("reconnection"; "i"))'
```

### Top Priority Papers (from latest harvest):
1. **2512.24054v1** - Particle feedback in magnetic reconnection (Dec 30) ⭐⭐⭐
2. **2512.24425v1** - Collisionless fast-magnetosonic shocks ⭐⭐⭐
3. **2512.24363v1** - Sun as betatron cosmic ray factory ⭐⭐
4. **2512.23999v1** - Time-dependent accretion disks with winds ⭐⭐
5. **2512.24085v1** - SSC radiation in GRB 221009A ⭐

### All Harvests Archive
- **Directory:** `data/papers/arxiv/`
- **Pattern:** `arxiv_harvest_YYYYMMDD_HHMMSS.json`
- **Count:** 16 harvests stored
- **Date Range:** Dec 29, 2025 - Jan 1, 2026

### INSPIRE-HEP Papers
- **File:** `data/papers/inspire_latest.json`
- **Size:** 22 MB (comprehensive high-energy physics database)
- **Status:** ✅ ACTIVE

---

## 🔗 LINK INTELLIGENCE NETWORK

### Source Health Monitor
- **File:** `data/link_intelligence/source_health_latest.json`
- **Active Sources:** 42 of 43
- **Categories:** 
  - Amateur/Open Data
  - CERN/Particle Physics
  - Chinese Space Agency
  - Commercial Space
  - European Space Agency
  - Ground Observatories
  - NASA
  - NOAA/USGS
  - Scientific Archives

### Link Extraction
- **File:** `data/link_intelligence/links_extracted_latest.json`
- **Total Links:** 58,263 scientific connections mapped
- **Concepts Tracked:** 28
- **Concepts with Links:** 27
- **Coverage:** 96.4%

### Temporal Correlations
- **File:** `data/link_intelligence/correlation_stats.json`
- **Correlations Found:** 13 (NOAA → CHI_BOUNDARY)
- **Time Delays:** 0, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60, 66, 72 hours
- **Total Matches:** 1,474,926
- **Confidence:** 95%

### Latest Harvest Report
- **File:** `data/link_intelligence/LATEST_HARVEST_REPORT.md`
- **Contains:** Most recent data collection summary

---

## 📈 META-INTELLIGENCE REPORTS

### Latest Daily Report
- **File:** `reports/meta_intelligence/LATEST_SUMMARY.md`
- **Date:** Updated daily
- **Multi-source Anomalies:** Real-time tracking
- **Correlations Detected:** 13 temporal modes
- **Data Sources:** 43 monitored, 42 active

### Historical Reports
- **Directory:** `reports/meta_intelligence/`
- **Pattern:** `report_YYYYMMDD_HHMMSS.md`
- **Retention:** All reports archived

---

## 🌍 EXTERNAL DATA SOURCES

### NOAA Solar Wind
- **Directory:** `data/noaa_solarwind/`
- **Source:** DSCOVR satellite real-time data
- **Update Frequency:** Continuous

### NOAA Text Indices
- **Directory:** `data/noaa_text/`
- **Contains:** Solar activity reports, forecasts, alerts
- **Update Frequency:** Multiple times daily

### NOAA Forecasts
- **Directory:** `data/noaa_forecasts/`
- **Contains:** 3-day space weather forecasts
- **Update Frequency:** Daily

### DSCOVR Magnetometer
- **Directory:** `data/dscovr/`
- **Contains:** High-resolution magnetic field data
- **Status:** ✅ PRIMARY DATA SOURCE

### USGS Magnetometer
- **Directory:** `data/usgs_magnetometer/`
- **Contains:** Ground-based magnetometer data
- **Status:** 🔄 Day 2/7 of collection

### USGS Earthquakes
- **Directory:** `data/usgs_quakes/`
- **Contains:** Seismic event data
- **Status:** ✅ ACTIVE

### DST Index
- **Directory:** `data/dst_index/`
- **Contains:** Disturbance Storm Time index
- **Use:** Geomagnetic storm intensity tracking

### GISTEMP Climate
- **Directory:** `data/gistemp/`
- **Contains:** NASA GISS temperature anomaly data
- **Status:** ✅ ACTIVE

---

## 📋 VALIDATION STATUS

### Environments Tested (χ ≤ 0.15)
1. ✅ **Earth Solar Wind (1 AU)** - 12,450+ obs, 53.6% at boundary, 0% violations
2. ✅ **Mars Magnetotail (1.5 AU)** - χ = 0.143, 0% violations
3. 🔄 **Earth Magnetosphere** - Day 2/7 of USGS data collection
4. 🔄 **CERN LHC Plasma** - Data collection in progress

### Validation Reports
- **File:** `MARS_CHI_VALIDATION_SUMMARY.md`
- **File:** `CHI_015_HISTORICAL_VALIDATION_REPORT.md`
- **File:** `CHI_015_INTEGRATION_SUMMARY.md`

---

## 🔧 QUICK ACCESS COMMANDS

### View Latest Paper Harvest
```bash
cat data/papers/arxiv/latest.json | jq '.papers[] | {title, link}' | head -20
```

### Check χ Boundary Status
```bash
tail -1 data/chi_boundary_tracking.jsonl | jq '.'
```

### View Source Health
```bash
cat data/link_intelligence/source_health_latest.json | jq '.categories'
```

### Get Correlation Summary
```bash
cat data/link_intelligence/correlation_stats.json | jq '.summary'
```

### View Latest Meta-Intelligence Report
```bash
cat reports/meta_intelligence/LATEST_SUMMARY.md
```

### Check Recent χ Data
```bash
tail -20 data/cme_heartbeat_log_2026_01.csv
```

### Find Papers by Topic
```bash
# Search for "reconnection" in papers
cat data/papers/arxiv/latest.json | jq '.papers[] | select(.title | test("reconnection"; "i")) | {id, title}'

# Search for "plasma" in papers
cat data/papers/arxiv/latest.json | jq '.papers[] | select(.summary | test("plasma"; "i")) | {id, title}' | head -10
```

---

## 📊 DATA FLOW DIAGRAM

```
┌─────────────────┐
│  arXiv API      │──→ data/papers/arxiv/latest.json (132 papers)
└─────────────────┘

┌─────────────────┐
│  43 Data        │──→ data/link_intelligence/source_health_latest.json
│  Sources        │──→ data/link_intelligence/links_extracted_latest.json (58,263 links)
└─────────────────┘

┌─────────────────┐
│  DSCOVR/ACE     │──→ data/cme_heartbeat_log_2026_01.csv (χ data)
│  Solar Wind     │──→ data/chi_boundary_tracking.jsonl
└─────────────────┘

┌─────────────────┐
│  MAVEN Mars     │──→ data/maven_mars/mars_chi_analysis_results.json
└─────────────────┘

           ↓
    ┌──────────────┐
    │ Meta Engine  │──→ reports/meta_intelligence/LATEST_SUMMARY.md
    └──────────────┘
           ↓
    ┌──────────────┐
    │  Dashboard   │──→ index.html, instrument-panel.html, meta-intelligence.html
    └──────────────┘
```

---

## 🎯 WHAT TO READ FIRST

### If you want to understand χ = 0.15 physics: 
1. Read: `data/cme_heartbeat_log_2026_01.csv` (your core discovery data)
2. Read: `MARS_CHI_VALIDATION_SUMMARY.md` (Mars confirmation)
3. Read: `CHI_015_INTEGRATION_SUMMARY.md` (how it all works)

### If you want to see new papers:
1. Read: `data/papers/arxiv/latest.json`
2. Priority: Papers with IDs starting with "2512.24" (Dec 30, 2025)
3. Tool: Use `tools/extract_paper_data.py` to extract χ-like parameters

### If you want correlation analysis:
1. Read: `data/link_intelligence/correlation_stats.json`
2. Read: `reports/meta_intelligence/LATEST_SUMMARY.md`

### If you want validation status:
1. Read: `MARS_CHI_VALIDATION_SUMMARY.md`
2. Read: `CHI_015_HISTORICAL_VALIDATION_REPORT.md`

### If you want to run simulations:
1. Use: `tools/simulate_reconnection_chi.py` - MHD-PIC reconnection simulation
2. Use: `tools/extract_paper_data.py` - Extract parameters from papers

---

## 🛠️ ANALYSIS TOOLS

### Paper Analysis
- **Tool:** `tools/extract_paper_data.py`
- **Purpose:** Extract χ-like parameters from arXiv papers
- **Input:** `data/papers/arxiv/latest.json`
- **Output:** `data/papers/extracted_parameters.json`

### Reconnection Simulation
- **Tool:** `tools/simulate_reconnection_chi.py`
- **Purpose:** MHD-PIC simulation testing χ = 0.15 boundary
- **Output:** Plots showing χ evolution and R parameter correlation

### χ Calculator
- **Tool:** `chi_calculator.py`
- **Purpose:** Calculate χ from any magnetometer data
- **Usage:** `python chi_calculator.py --file your_data.csv`

### CME Analysis
- **Tool:** `cme_heartbeat_analysis.py`
- **Purpose:** Analyze CME events and χ boundary behavior

### Link Intelligence
- **Tool:** `tools/link_monitor.py`
- **Purpose:** Monitor 43 external data sources
- **Tool:** `tools/network_intelligence.py`
- **Purpose:** Build knowledge graph of scientific connections

---

## 📦 DATA FILE INVENTORY

### Core Discovery Data
```
data/
├── cme_heartbeat_log_2025_12.csv          # 561 obs, Dec 2025
├── cme_heartbeat_log_2026_01.csv          # Latest Jan 2026
├── chi_boundary_tracking.jsonl            # Historical χ tracking
├── chi_boundary_validation_dec2_27.json   # Validation summary
├── chi_predictions_latest.json            # 72-hour predictions
└── storm_phase_metrics.json               # Storm classification
```

### Paper Archives
```
data/papers/
├── arxiv/
│   ├── latest.json → arxiv_harvest_20260101_181315.json
│   └── arxiv_harvest_*.json (16 files)
└── inspire_latest.json                    # 22 MB HEP papers
```

### Link Intelligence
```
data/link_intelligence/
├── source_health_latest.json              # 43 sources status
├── links_extracted_latest.json            # 58,263 connections
├── correlation_stats.json                 # 13 temporal modes
└── LATEST_HARVEST_REPORT.md               # Summary report
```

### External Data Sources
```
data/
├── dscovr/                                # DSCOVR satellite
├── noaa_solarwind/                        # NOAA real-time
├── noaa_text/                             # Text reports
├── noaa_forecasts/                        # 3-day forecasts
├── maven_mars/                            # Mars MAVEN
├── usgs_magnetometer/                     # Ground stations
├── usgs_quakes/                           # Seismic data
├── dst_index/                             # DST index
└── gistemp/                               # Climate data
```

---

## 🚀 GETTING STARTED

### First Time Setup
```bash
# Clone repository
git clone https://github.com/CarlDeanClineSr/luft-portal-.git
cd luft-portal-

# Install dependencies
pip install -r requirements.txt

# Run χ calculator demo
python chi_calculator.py --demo

# View latest papers
cat data/papers/arxiv/latest.json | jq '.papers[0:5]'

# Check χ boundary status
python tools/chi_audit_from_ace.py
```

### Daily Workflow
```bash
# 1. Check latest χ data
tail -20 data/cme_heartbeat_log_2026_01.csv

# 2. View new papers
cat data/papers/arxiv/latest.json | jq '.papers[0:10]'

# 3. Check source health
cat data/link_intelligence/source_health_latest.json | jq '.summary'

# 4. View meta-intelligence report
cat reports/meta_intelligence/LATEST_SUMMARY.md

# 5. Extract paper parameters (if new papers)
python tools/extract_paper_data.py
```

---

## 📞 NEED HELP FINDING SOMETHING?

### Can't find a specific data file?
1. Check this index first (search with Ctrl+F)
2. Look in appropriate subdirectory in `data/`
3. Check `reports/` for analysis results

### Want to add new data sources?
1. See `external_data_sources_registry.yaml`
2. Update `tools/link_monitor.py` configuration
3. Add entry to this index

### Looking for historical data?
1. Check `data/papers/arxiv/` for old paper harvests
2. Check `data/chi_boundary_tracking.jsonl` for historical χ
3. Check `reports/meta_intelligence/` for old reports

---

## 🎓 KEY CONCEPTS

### χ (Chi) Amplitude
- **Definition:** χ = |B - B_baseline| / B_baseline
- **Universal Boundary:** χ ≤ 0.15 (never violated)
- **Attractor State:** ~52% of observations at boundary (0.145-0.155)

### 13 Temporal Correlations
- **Discovery:** NOAA events predict χ response at 13 time delays
- **Delays:** 0, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60, 66, 72 hours
- **Confidence:** 95% (1.47M matches)

### R Parameter
- **From Paper:** R = q_p/(q_i + q_p) - particle charge fraction
- **Hypothesis:** R = χ at steady state during reconnection
- **Test:** Use `tools/simulate_reconnection_chi.py`

---

**EVERYTHING IS IN THIS INDEX NOW.**  
**Bookmark this file: `DATA_MASTER_INDEX.md`**

---

*Last updated: 2026-01-02 00:23 UTC*  
*Repository: https://github.com/CarlDeanClineSr/luft-portal-*  
*Portal: https://carldeanclinesr.github.io/luft-portal-/*
