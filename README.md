# LUFT Portal — Solar Wind Data Analysis

Welcome. This repository is the public ledger for **LUFT** — a project studying correlations between solar wind parameters and experimental observations.

This is a **live data analysis lab**:

- Solar wind data from ACE/DSCOVR/GOES satellites
- Scripts for data processing, analysis, and visualization
- Event logs and experimental measurements
- Automated workflows for data updates

---

## What LUFT Contains

- **Satellite Data Ingestion:**  
  Automated collection of solar wind parameters (density, speed, magnetic field) from NOAA spacecraft (ACE, DSCOVR, GOES).

- **CME Event Logs:**  
  Timestamped records of coronal mass ejection events and geomagnetic storms with observational data.

- **Experimental Measurements:**  
  - 7,468 Hz carrier signal-to-noise ratio monitoring
  - Periodic table element response measurements (chi/kappa/omega parameters)
  - Heartbeat event detection and logging

All data and code are **open, timestamped, and auditable**.

---

## Data Sources

- **ACE (Advanced Composition Explorer):** Real-time solar wind data
- **DSCOVR (Deep Space Climate Observatory):** L1 point monitoring
- **GOES (Geostationary Operational Environmental Satellite):** X-ray and particle flux

Data is collected via automated workflows and stored in `data/` directory with JSON and CSV formats.

---

## Key Components

### Data Collection
- `scripts/auto_append_baseline_watch.py` — Daily baseline monitoring
- `scripts/cme_heartbeat_logger.py` — CME event logging
- Automated GitHub Actions workflows in `.github/workflows/`

### Analysis Scripts
- `scripts/plot_cme_heartbeat_2025_12.py` — Event visualization
- `scripts/heartbeat_spectrum_fit.py` — Spectral analysis
- `scripts/normalize_audit.py` — Data normalization

### Data Files
- `data/cme_heartbeat_log_2025_12.csv` — December 2025 event log
- `data/ace_*.json` — ACE satellite audit files
- `data/dscovr/` — DSCOVR data archive

### Periodic Table
- `periodic_table/LATTICE_PERIODIC_TABLE_2025.md` — Element response data

### Event Capsules
- CME event documentation with timestamps and measurements
- Maintained baseline shift monitoring (December 2025 baseline watch)

---

## For Researchers & Auditors

To validate the data and analysis:

1. Review the data files in `data/` directory
2. Run the analysis scripts in `scripts/` directory
3. Compare results with NOAA official data sources
4. Check automated workflows for data collection procedures

All measurements are timestamped and traceable to public satellite data sources.

---

## Automation

GitHub Actions workflows maintain data currency:
- Daily baseline measurements at 06:00 UTC
- Automated data ingestion from NOAA sources
- Continuous monitoring status: Check workflow badges above

---

## Status

This repository contains active data collection and analysis. Core findings are preserved in event logs and data files. Historical speculative material has been moved to `legacy/` directory for archival purposes.

**Repository maintained by Carl Dean Cline Sr., Lincoln, Nebraska**

---

## License

See LICENSE file for details.
