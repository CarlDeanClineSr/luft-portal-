---
id: "CAPSULE_HEARTBEAT_PLOT"
title: "Heartbeat Plot — χ vs Dynamic Pressure During CME (2025‑12)"
tags:
  - "heartbeat"
  - "cme"
  - "dynamic_pressure"
  - "boundary_recoil"
  - "plot"
status: "adopted"
date: "2025-12-05"
author: "Carl Dean Cline Sr."
ledger: "LUFT Portal"
---

# Capsule — Heartbeat Plot (χ vs P_dyn During CME, 2025‑12)

**Author:** Carl Dean Cline Sr.  
**Date:** 2025‑12‑05  
**Ledger:** LUFT Portal  

---

## 1. Purpose

This capsule enshrines the **first LUFT heartbeat plot** where:

- The **CME heartbeat log** for 2025‑12 is ingested,
- **Dynamic pressure** \(P_{\text{dyn}}\) is computed,
- **χ amplitude** from the heartbeat pipeline is overlaid,
- And the **boundary recoil law** is tested visually and numerically.

It bridges:

- Capsule math (Unified Fields, boundary recoil), and  
- Live audit data from orbital monitors (ACE/DSCOVR).

---

## 2. Data Source

The plot is generated from:

- **File:** `data/cme_heartbeat_log_2025_12.csv`  
- **Columns:**
  - `timestamp_utc`
  - `chi_amplitude`
  - `phase_radians`
  - `storm_phase` (`pre`, `peak`, `post-storm`)
  - `density_p_cm3`
  - `speed_km_s`
  - `bz_nT`
  - `bt_nT`
  - `source` (ACE/DSCOVR)

Dynamic pressure is computed from density and speed using the LUFT unified fields law:

\[
P_{\text{dyn}}[\text{nPa}] = 1.6726 \times 10^{-6} \, n \, v^2
\]

with:

- \(n\) in protons/cm³ (`density_p_cm3`),  
- \(v\) in km/s (`speed_km_s`).

---

## 3. Script

The canonical script for this plot is:

- **File:** `scripts/plot_cme_heartbeat_2025_12.py`

Core functions:

- Read `data/cme_heartbeat_log_2025_12.csv`  
- Compute `P_dyn_nPa` from density and speed  
- Compute predicted χ from boundary recoil law:
  \[
  \chi_{\text{pred}} = 0.0032 P_{\text{dyn}} + 0.054
  \]
- Map `storm_phase` to colors:
  - `peak` → red  
  - `post-storm` → green  
  - `pre` / other → grey  
- Produce a dual‑axis plot:
  - Left axis: \(P_{\text{dyn}}\) (black line),
  - Right axis: χ (colored scatter) + χ_pred (orange dashed line).

---

## 4. Plot Output

The script writes the figure to:

- **File:** `results/cme_heartbeat_2025_12_chi_pdyn.png`

Interpretation:

- **Black line (left axis):** Dynamic pressure \(P_{\text{dyn}}\) showing CME compression and relaxation.  
- **Colored points (right axis):** χ amplitude:
  - **Red:** `storm_phase == "peak"` — CME / ratchet moments.  
  - **Green:** `storm_phase == "post-storm"` — recovery / exhale.  
  - **Grey:** `storm_phase == "pre"` — pre‑event / background.  
- **Orange dashed line:** χ predicted by the **boundary recoil law**:
  \[
  \chi_{\text{pred}} = 0.0032 P_{\text{dyn}} + 0.054
  \]

The plot makes visible:

- The **heartbeat plateau** around χ ≈ 0.15 during the main CME,
- **Deviations** such as χ ≈ 0.1426 (and other dips),
- How well measured χ tracks the empirical recoil law across time.

---

## 5. Relation to Other Capsules

This capsule is part of the unified spine:

- **Unified Fields:** `CAPSULE_UNIFIED_FIELDS_E_TO_LUFT`  
- **Universal Modulation:** `CAPSULE_UNIVERSAL_MODULATION_055`  
- **Event Ratchet:** `CAPSULE_EVENT_RATCHET`  
- **Event Recovery:** `CAPSULE_EVENT_RECOVERY`  
- **Flare Foam Pipeline:** `CAPSULE_FLARE_FOAM_PIPELINE`  
- **Heartbeat Dashboard:** (dashboard markdown)  

Where the other capsules define:

- The **math** (boundary recoil law, χ and Ω),  
- The **events** (ratchet, recovery, flare),  
- The **pipelines** (solar wind ingest, heartbeat logger, flare foam),

this capsule defines the **canonical visualization** that ties them together.

---

## 6. Legacy Clause

- `data/cme_heartbeat_log_2025_12.csv`,  
- `scripts/plot_cme_heartbeat_2025_12.py`,  
- And `results/cme_heartbeat_2025_12_chi_pdyn.png`  

are to be preserved together as the **first LUFT heartbeat plot set**.

Future plots (other months, other CMEs) should:

- Use similar scripts and filenames,  
- Reference this capsule when updating the boundary recoil law or unified modulation parameters.

---

**Ledger proud — heartbeat made visible, χ and \(P_{\text{dyn}}\) dancing together on one plot, LUFT’s new physics rendered in color on a single page.**
