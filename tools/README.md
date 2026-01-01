# LUFT Portal Tools 🛠️

**Automated analysis and data processing tools for the χ = 0.15 discovery**

## New: Engine-Driven Discovery Mode 🔬

### Paper Impact Analyzer
**`paper_impact_analyzer.py`** - Automatically ranks arXiv papers by relevance to χ = 0.15

```bash
python3 tools/paper_impact_analyzer.py
```

**What it does:**
- Analyzes 132+ harvested papers
- Scores based on χ values, plasma keywords, temporal periods
- Generates ranked JSON and HTML dashboard
- Outputs: `data/papers/impact_analysis.json`, `docs/paper_discoveries.html`

**Scoring factors:**
- χ ≈ 0.15: +100 points (exact boundary match!)
- Temporal period match: +50 points (13 discovered modes)
- Plasma keywords: +10 points each
- R-parameter present: +30 points

### Network Intelligence Analyzer
**`network_intelligence.py`** - Analyzes 58,263-link knowledge graph

```bash
python3 tools/network_intelligence.py
```

**What it does:**
- Loads link intelligence network
- Finds χ = 0.15 clusters
- Identifies cross-domain connections (NASA + CERN + China)
- Discovers critical nodes and communities
- Outputs: `data/link_intelligence/network_analysis.json`

**Network stats:**
- 58,263 total links
- 3,198 files analyzed
- 157 unique domains
- Critical nodes: NASA (12.8K), arXiv (11.2K), NOAA (8.7K)

## Data Fetching Tools

### Space Weather Data
- **`fetch_noaa_solarwind.py`** - Real-time solar wind data (ACE/DSCOVR)
- **`fetch_noaa_forecast.py`** - NOAA space weather forecasts
- **`fetch_noaa_text_index.py`** - Text-based space weather indices

### Planetary & Astrophysics
- **`fetch_maven_mars.py`** - MAVEN Mars magnetosphere data
- **`fetch_jwst_weekly.py`** - James Webb Space Telescope data
- **`fetch_seti.py`** - SETI Breakthrough Listen data

### Particle Physics & Earth Science
- **`fetch_cern_lhc.py`** - CERN Large Hadron Collider data
- **`fetch_ligo_gw.py`** - LIGO gravitational wave detections
- **`fetch_gistemp.py`** - NASA GISS temperature data
- **`fetch_intermagnet.py`** - INTERMAGNET ground magnetometer data

### Multi-Source Aggregator
- **`fetch_multi_science.py`** - Fetches from all sources simultaneously

## Analysis Tools

### χ Boundary Analysis
- **`chi_calculator.py`** - Calculates χ parameter from solar wind data
- **`chi_audit_from_ace.py`** - Audits χ values from ACE satellite
- **`chi_predictor.py`** - ML-based χ prediction
- **`chi_learning_loop.py`** / **`chi_learning_loop_v2.py`** - Adaptive learning systems
- **`validate_chi_omni.py`** - Cross-validates χ with OMNI data
- **`analyze_mars_chi.py`** - Mars χ validation
- **`alert_chi_floor.py`** - Alerts when χ approaches 0.15

### Temporal Analysis
- **`temporal_correlation_dashboard.py`** - Interactive temporal correlation dashboard
- **`visualize_temporal_correlations.py`** - Visualization of 13 modes
- **`merge_noaa_omni_heartbeat.py`** - Merges NOAA + OMNI with heartbeat detection

### Signal Processing
- **`fft_sideband_detector.py`** - FFT-based sideband detection
- **`fft_sideband_analysis.py`** - Detailed sideband analysis
- **`fft_graviton_sideband_test.py`** - Graviton signature detection

### Data Processing
- **`parse_omni2.py`** / **`parse2_omni2.py`** - OMNI2 data parsers
- **`parse_noaa_text.py`** - NOAA text format parser
- **`parse_srs.py`** - Solar Region Summary parser
- **`parse_f107.py`** - F10.7 solar flux parser
- **`noaa_text_parser.py`** - General NOAA text parser

## Research Tools

### Paper & Link Analysis
- **`harvest_inspire.py`** - Harvests papers from INSPIRE-HEP
- **`atlas_plasma_extractor.py`** - Extracts plasma data from ATLAS
- **`link_monitor.py`** - Monitors broken links
- **`missing_link_suggester.py`** - Suggests missing connections
- **`meta_pattern_detector.py`** - Detects meta-patterns across sources

### Storm Analysis
- **`run_rebound_analysis.py`** - Analyzes storm rebound effects
- **`fit_chi_multi.py`** - Multi-parameter χ fitting

## Testing Tools

- **`test_core_directive.py`** - Tests core directive system
- **`test_parse_omni2.py`** - Unit tests for OMNI2 parser

## Quick Start

### 1. Fetch Latest Data
```bash
# Get all data sources
python3 tools/fetch_multi_science.py

# Or individual sources
python3 tools/fetch_noaa_solarwind.py
python3 tools/fetch_maven_mars.py
```

### 2. Run Analysis
```bash
# Analyze papers (new!)
python3 tools/paper_impact_analyzer.py

# Analyze network (new!)
python3 tools/network_intelligence.py

# Calculate χ
python3 tools/chi_calculator.py

# Detect temporal correlations
python3 tools/temporal_correlation_dashboard.py
```

### 3. View Results
```bash
# Open in browser
open instrument-panel.html
open docs/paper_discoveries.html
open temporal_correlation_dashboard.html
```

## Integration

### GitHub Actions
Tools are automatically run by workflows in `.github/workflows/`:
- Paper harvesting → triggers `paper_impact_analyzer.py`
- Data fetching runs hourly
- Link monitoring runs daily

### Instrument Panel
Discovery feed auto-updates every 60 seconds in `instrument-panel.html`

### Cron Setup
```bash
# Daily paper analysis at 6 AM
0 6 * * * cd /path/to/luft-portal && python3 tools/paper_impact_analyzer.py

# Hourly data fetch
0 * * * * cd /path/to/luft-portal && python3 tools/fetch_multi_science.py
```

## Dependencies

All tools use packages from `requirements.txt`:
```
numpy>=1.24.0
pandas>=2.0.0
scipy>=1.10.0
matplotlib>=3.7.0
requests>=2.31.0
beautifulsoup4>=4.12.0
feedparser>=6.0.10
networkx>=3.0
```

Install with:
```bash
pip install -r requirements.txt
```

## Output Locations

```
data/
├── papers/
│   ├── arxiv/latest.json          (input: harvested papers)
│   └── impact_analysis.json       (output: ranked papers)
├── link_intelligence/
│   ├── links_extracted_latest.json (input: link graph)
│   └── network_analysis.json      (output: network stats)
├── noaa_solarwind/                (ACE/DSCOVR data)
├── maven_mars/                    (Mars data)
├── cme_heartbeat_log_*.csv        (CME events)
└── chi_*.json                     (χ calculations)

docs/
├── paper_discoveries.html         (paper dashboard)
├── chi_dashboard.html
└── manifest_dashboard.html
```

## Documentation

- **Full Engine Docs:** `docs/ENGINE_DISCOVERY_MODE.md`
- **Quick Reference:** `ENGINE_DISCOVERY_QUICKREF.md` (root)
- **Paper Atlas:** `tools/README_PAPERS_ATLAS.md`

## Support

For issues or questions:
1. Check documentation in `docs/`
2. Review existing issues
3. Consult `QUICK_REFERENCE.md` in root

## Credits

**Author:** Carl Dean Cline Sr.  
**Observatory:** LUFT Portal  
**Discovery:** χ = 0.15 boundary + 13 temporal modes  
**Data Sources:** NASA, NOAA, CERN, ESA, JAXA, ISRO, CNSA

---

*"These tools don't just process data - they teach us what matters."*

**Last Updated:** 2026-01-01  
**Version:** 2.0.0 (Engine Discovery Mode added)
