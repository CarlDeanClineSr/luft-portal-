# LUFT Portal - Paper Harvesting & ATLAS Integration

This directory contains tools for harvesting physics papers and integrating ATLAS collision data for χ boundary testing across all energy scales.

## Tools Overview

### 1. INSPIRE-HEP Paper Harvester (`harvest_inspire.py`)

Fetches plasma physics papers from INSPIRE-HEP (no 403 errors).

**Features:**
- Uses INSPIRE-HEP open API (no authentication required)
- Searches multiple plasma physics topics:
  - Plasma physics
  - Magnetohydrodynamics (MHD)
  - Quark-gluon plasma
  - Heavy ion collisions
  - Particle detector plasma
  - Tokamak plasma
- Removes duplicate papers
- Saves results to `data/papers/`

**Usage:**
```bash
python tools/harvest_inspire.py
```

**Output:**
- `data/papers/inspire_papers_YYYYMMDD_HHMMSS.json` - Timestamped harvest
- `data/papers/inspire_latest.json` - Latest harvest (for easy access)

**Automated Collection:**
- Runs weekly via GitHub Actions (`.github/workflows/inspire_harvest.yml`)
- Scheduled for Sunday midnight UTC

### 2. ATLAS Plasma Extractor (`atlas_plasma_extractor.py`)

Framework for extracting plasma-relevant data from ATLAS collision events to test χ = 0.15 boundary at GeV-TeV energy scales.

**Concept:**
Tests whether the χ = 0.15 boundary (confirmed in solar wind at keV scales) also appears in:
- ATLAS detector solenoid field stability (2 Tesla baseline)
- Quark-gluon plasma energy density (heavy ion collisions)
- Cosmic ray muon flux correlations

**Current Status:**
- Framework ready for data integration
- Placeholder functions for field and energy density extraction
- Requires ATLAS Open Data download

**Usage:**
```bash
python tools/atlas_plasma_extractor.py
```

**Next Steps:**
1. Download ATLAS Open Data: https://opendata.atlas.cern/docs/documentation/overview_data
2. Install dependencies:
   ```bash
   pip install uproot awkward numpy
   ```
3. Identify relevant datasets:
   - Heavy ion collision data (Pb-Pb)
   - Detector calibration data
   - Luminosity block data
4. Integrate ROOT file reading
5. Extract magnetic field and energy density values
6. Calculate χ values and test boundary hypothesis

### 3. Existing Harvester (`harvest_cern.py`)

Legacy CERN Document Server harvester (may experience 403 errors).

**Note:** Use `harvest_inspire.py` instead for reliable paper collection.

## Integration with LUFT Portal

### Energy Scale Testing

The INSPIRE harvester and ATLAS framework support testing χ = 0.15 universality across all energy scales:

- ✅ **Solar wind (keV)**: χ = 0.15 confirmed (574 observations, 0% violations)
- ⏳ **Magnetosphere**: USGS data, test pending Jan 3
- ⏳ **Fusion plasma (MeV)**: Future ITER data integration
- ⏳ **Particle collisions (GeV-TeV)**: ATLAS framework ready

### Workflow Integration

Papers harvested by INSPIRE are automatically:
1. Collected weekly
2. Filtered for LUFT-relevant topics
3. Committed to repository
4. Available for analysis and review

## File Locations

```
luft-portal-/
├── tools/
│   ├── harvest_inspire.py         # INSPIRE-HEP harvester
│   ├── atlas_plasma_extractor.py  # ATLAS integration framework
│   ├── harvest_cern.py            # Legacy CERN harvester
│   └── harvest_arxiv.py           # arXiv harvester
├── .github/workflows/
│   ├── inspire_harvest.yml        # Weekly INSPIRE collection
│   └── physics_paper_harvester.yml # Legacy arXiv/CERN collection
└── data/papers/
    ├── inspire_latest.json        # Latest INSPIRE harvest
    ├── arxiv/                     # arXiv papers
    └── cern/                      # CERN papers
```

## References

- **INSPIRE-HEP API**: https://inspirehep.net/api
- **ATLAS Open Data**: https://opendata.atlas.cern
- **LUFT χ Boundary Research**: See `CHI_015_*.md` files in repository root

## Contributing

When adding new paper sources or ATLAS data integrations:
1. Follow existing patterns in harvester scripts
2. Add error handling for API failures
3. Document data sources and formats
4. Update this README with new features
