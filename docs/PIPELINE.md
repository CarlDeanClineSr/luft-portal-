# LUFT ML Pipeline & Provenance

**Purpose:**  
This file documents the pipeline scripts and workflows that produce the core scientific tables, ML fits, and summary capsules in LUFT. All runs are linked to source commits and auditable by reviewers.

## Files

| File | Path | Purpose | Commit message |
|---|---:|---|---|
| merge_noaa_omni_heartbeat.py | tools/merge_noaa_omni_heartbeat.py | Merge NOAA CSVs, OMNI2 parsed CSV, and DSCOVR heartbeat into hourly table | data: merge NOAA/OMNI/DSCOVR into extended heartbeat log |
| rebound_runner.py | ml/rebound_runner.py | Extract rebound events, compute driver metrics, fit model, save results and summary | ml: add rebound runner and summary report |
| daily_ml_rebound.yml | .github/workflows/daily_ml_rebound.yml | Schedule daily run: merge, fit, alert, commit | ci: daily ML rebound run |
| alert_chi_floor.py | tools/alert_chi_floor.py | Alert script for chi < 0.08 or recovery issues | ops: add chi floor alerting |
| rebound_dashboard.html | pages/plots/rebound_dashboard.html | Static dashboard fragment with daily plots and summary | docs: add rebound dashboard fragment |

## Outputs

- `data/extended_heartbeat_log_YYYYMMDD.csv`: merged/derived main table
- `results/rebound_fit_YYYYMMDD_events.csv`: rebound event table
- `results/rebound_fit_YYYYMMDD_fit.json`: fit coefficients/result
- `reports/rebound_fit_YYYYMMDD_summary.md`: daily ML capsule
- `reports/plots/`: daily diagnostic plots (png)
- `alerts/`: per-event alerts for fast review

## Governance

- Commit SHA listed in fit/result JSON for traceability.
- All input files and times logged.
- Exclude events with >20% source disagreement.
- Reports must be human-signed before Pages promotion.

---

_This document is living, updated as the pipeline evolves._
