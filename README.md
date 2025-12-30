# LUFT Portal — Universal Plasma Boundary Observatory

Live dashboard: https://carldeanclinesr.github.io/luft-portal-  
Repository: https://github.com/CarlDeanClineSr/luft-portal-

TL;DR
- Discovery: χ = |ΔB|/B ≤ 0.15 is a hard plasma coherence limit (the Cline Constant, χ_C).
- Evidence: 12,000+ solar wind observations, 0 violations; ~52% at exact 0.15 boundary.
- Status: Earth solar wind confirmed; magnetosphere testing; Mars (MAVEN) and CERN LHC collecting.
- Everything is public, automated, and reproducible.

---

## What the dashboard shows

- Live solar wind (DSCOVR/ACE), updates every 60 seconds
- χ boundary status (BELOW / AT_BOUNDARY), distribution, last 24h timeline
- Storm phase analysis (PRE / PEAK / POST)
- Multi-environment validation across Earth, magnetosphere, Mars, CERN
- Engine activity: workflows and last update times
- Data Explorer links to CSV/JSON artifacts and documentation

---

## The discovery

- χ (Chi) measures normalized magnetic oscillation amplitude: χ = |ΔB|/B
- Boundary: χ ≤ 0.15 observed in all tested solar wind conditions (0 violations)
- Interpretation: 0.15 is the elastic/damping threshold where growth stops and coherence is preserved

Applications
- Space weather: χ → 0.15 precedes storm peak (physics-based forecast)
- Fusion safety: χ approaching 0.15 = disruption warning (prevent rather than react)
- Plasma propulsion: performance peaks near χ ≈ 0.15 (MPD thruster data)
- Industrial plasma: better RF/microwave coupling and stability near the boundary

---

## Current validation status

- Earth Solar Wind (DSCOVR/ACE): Confirmed — 100% ≤ 0.15, ~52% at boundary
- Earth Magnetosphere (USGS 13 stations): Testing (7-day campaign)
- Mars Solar Wind (MAVEN): Collecting (daily)
- CERN LHC Plasma (Open Data): Collecting (daily)

FFT/AM-Graviton sideband search: in analysis, longer baseline required (<5% symmetry target)

---

## How it works (automation)

GitHub Actions run fully autonomous pipelines:
- Hourly: DSCOVR/ACE ingest, USGS magnetometers, NOAA feeds, Dst index
- Daily: MAVEN Mars plasma, CERN LHC luminosity
- 5-minute refresh: χ dashboard rebuild and deploy
- Engine health: status report, narrative, audit

All artifacts are written to `data/` and consumed by the dashboard.

---

## Data artifacts (key files)

- Solar wind timeseries:
  - `data/cme_heartbeat_log_YYYY_MM.csv`
- Storm phase outputs:
  - `data/storm_phase_summary.json` (counts, first/last PEAK)
  - `data/storm_phase_metrics.json` (per-phase avg/max/at-boundary)
  - `data/cme_heartbeat_log_YYYY_MM_with_phases.csv` (row labels)
- Domain datasets:
  - `data/usgs/...` (magnetosphere)
  - `data/maven_mars/...` (Mars)
  - `data/cern_lhc/...` (CERN)
- Paper harvests:
  - `data/papers/arxiv/*.json` (physics feed)

---

## Reproduce the observatory (fork-and-run)

1) Fork this repo and enable Actions in Settings  
2) Allow scheduled workflows (they run automatically)  
3) Enable GitHub Pages (deploy from main)  
4) Visit your live dashboard; you’ll get the same χ behavior

Data sources are public; analysis code and dashboards are open — full reproducibility.

---

## Storm phase analyzer (χ framing)

Phase logic (single-storm, robust):
- PEAK: χ ∈ [0.145, 0.155]
- PRE: valid points before first PEAK
- POST: valid points after last PEAK
- UNKNOWN: missing/invalid χ

Artifacts:
- `storm_phase_summary.json` — counts and first/last PEAK timestamps
- `storm_phase_metrics.json` — per-phase average/max/at-boundary
- `_with_phases.csv` — per-row labels for charts/tables

---

## Known notes

- “LIVE (−XXXXs ago)” display: timestamps are parsed as UTC and clamped; if you see a negative value, check CSV timestamp format (append `Z`).
- MAVEN/CERN panels depend on external endpoints; fallbacks/retries are in fetch tools and populate as data accumulates.
- FFT sideband search needs longer data windows; target symmetry error <5%.

---

## Roadmap

- Finish magnetosphere validation (USGS Day 7/7)
- Accumulate Mars/CERN datasets and compute χ per domain
- Multi-storm segmentation (gap-aware clustering)
- NOAA/UKAEA outreach for operational pilots
- Open preprint and journal submission

---

## Contributing

- Issues and PRs welcome (ingests, analysis, dashboard)
- Add new domain tests (tokamak probes, ALMA spectra)
- Cite this repo and the Cline Constant (χ_C = 0.15) when publishing

---

## Contact

- Author: Carl Dean Cline Sr. — carldcline@gmail.com
- GitHub: @CarlDeanClineSr
- Live dashboard: https://carldeanclinesr.github.io/luft-portal-

License: MIT (attribution requested)
