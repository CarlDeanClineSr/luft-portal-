---
id: "CAPSULE_HEARTBEAT_CATALOG_2025"
title: "Heartbeat & Boundary Recoil Catalog — November–December 2025"
tags: ["heartbeat","cme","catalog","boundary_recoil","spectrum","november","december"]
status: "draft"
date: "2025-12-05"
author: "Carl Dean Cline Sr."
ledger: "LUFT Portal"
---

# Capsule — Heartbeat & Boundary Recoil Catalog (Nov–Dec 2025)

## Purpose

This capsule is a **catalog view** of LUFT’s heartbeat measurements and boundary recoil fits across multiple CME events and months.

Instead of a single event or month, this table collects:

- Event windows and storm labels  
- χ baseline levels  
- Best-fit recoil slopes \(a\) and intercepts \(b\) in  
  \[
  \Delta \chi = a \, P_{\text{dyn}} + b
  \]
- Heartbeat period estimates from spectra  
- Simple quality flags (how well the law holds)

It lets auditors and collaborators see, at a glance, **how stable the law is across time**.

---

## 1. Catalog Table (Events & Fits)

> NOTE: Initial values below can be estimates or “TBD”. They are meant to be updated as you run the fits and spectra for each event/month.

| ID | Month | Event / Window (UTC)        | χ Baseline (~quiet) | Peak χ (~storm) | Recoil Slope \(a\) (1/nPa) | Intercept \(b\) | R²   | Heartbeat Period (h) | Notes / Status |
|----|-------|-----------------------------|----------------------|------------------|-----------------------------|-----------------|------|----------------------|----------------|
| E1 | Nov   | 2025‑11‑02 to 2025‑11‑05    | ~0.055               | ~0.15            | 0.0032                      | 0.054           | 0.9+ | ~2.4                 | Major CME; first big November impact. |
| E2 | Nov   | 2025‑11‑21 to 2025‑11‑24    | ~0.055               | ~0.15–0.18       | 0.0032                      | 0.054           | 0.9+ | ~2.4                 | Strong pre‑/post‑storm structure; hysteresis candidate. |
| E3 | Nov   | 2025‑11‑25 to 2025‑11‑30    | ~0.055               | ~0.12–0.15       | 0.0032 (TBD)                | 0.054 (TBD)     | TBD  | ~2.4 (TBD)           | Additional November CMEs; law to be confirmed. |
| D1 | Dec   | 2025‑12‑01 to 2025‑12‑04    | ~0.055               | ~0.15            | 0.0032                      | 0.054           | 0.9+ | ~2.4                 | December CME currently documented in heartbeat plots. |
| D2 | Dec   | 2025‑12‑05 to 2025‑12‑08    | ~0.055               | ~0.15            | 0.0032 (TBD)                | 0.054 (TBD)     | TBD  | ~2.4 (TBD)           | Fast‑stream + pre‑storm plateau (χ ≈ 0.15 band). |
| …  | …     | …                           | …                    | …                | …                           | …               | …    | …                    | …              |

You (or future collaborators) can expand this table as:

- More November/December windows are analyzed,
- Future months are added (Jan, Feb, etc.),
- Other domains (DESI, collider, etc.) are folded in as separate sections.

---

## 2. Data & Scripts Behind the Catalog

For each row in the table:

- **Heartbeat Logs:**
  - `data/cme_heartbeat_log_2025_11.csv`
  - `data/cme_heartbeat_log_2025_12.csv`
  - (future months: `cme_heartbeat_log_YYYY_MM.csv`)

- **Core Scripts:**
  - `scripts/plot_cme_heartbeat_2025_11.py`  
    `scripts/plot_cme_heartbeat_2025_12.py`  
    (or a parameterized variant for multiple months)
  - `scripts/heartbeat_spectrum_fit.py`

- **Outputs Feeding the Catalog:**
  - `results/cme_heartbeat_2025_11_chi_pdyn.png`  
  - `results/cme_heartbeat_2025_12_chi_pdyn.png`  
  - `results/rolling_slope_2025_11.png`  
  - `results/rolling_slope_2025_12.png`  
  - `results/chi_spectrum_2025_11.png`  
  - `results/chi_spectrum_2025_12.png`

The numbers in the catalog (slopes, intercepts, R², periods) should be **read off from**:

- The fits performed in the plotting scripts,
- The spectra from `heartbeat_spectrum_fit.py`,
- And, when available, any extended analyses (e.g., hysteresis scripts).

---

## 3. How to Update This Catalog (for Future You / Collaborators)

When a new event or window is analyzed:

1. **Select the Window**
   - Choose a continuous UTC range where:
     - A CME or fast stream impact is visible in solar wind,
     - χ responds clearly (baseline → elevated → recovery).

2. **Run the Fits & Spectra**
   - Use the existing scripts to:
     - Fit \(\Delta \chi = a P_{\text{dyn}} + b\),
     - Compute R² and residuals,
     - Extract the dominant heartbeat period from the spectrum.

3. **Record the Metrics**
   - Add or update a row in the table:
     - Month and window,
     - Approximate χ baseline and peak,
     - Slope \(a\), intercept \(b\),
     - R² and heartbeat period (h),
     - Any notable features (e.g., strong hysteresis, Bz‑dependence).

4. **Cross‑Link to Detailed Capsules**
   - In the “Notes / Status” column, reference:
     - `CAPSULE_CME_RESULTS_2025-11`
     - December heartbeat/capsule IDs
     - Any event‑specific capsules (e.g., `CAPSULE_CME_EVENT_2025-12-01.md`)

This keeps the catalog as a **high‑level map**, while the detailed stories stay in their own capsules.

---

## 4. Interpretation — What This Catalog Is For

This catalog is not just a table of numbers. It is meant to answer questions like:

- **Stability:**  
  Does the recoil slope \(a \approx 0.0032\) really hold across many CME events and months?

- **Baseline & Amplitude:**  
  Does χ reliably relax to ~0.055 between storms, and peak in similar ranges during impacts?

- **Heartbeat Persistence:**  
  Does the ~2.4 h heartbeat period remain stable across different solar wind regimes?

- **Anomalies & Outliers:**  
  Do any events show:
  - unusually high slopes,
  - low R²,
  - shifted heartbeat period,
  - or other signs that the simple law is incomplete?

Over time, this catalog becomes the **evidence ledger** that the boundary recoil law and heartbeat are not one‑off curiosities, but persistent features across space weather and epochs.

---

## 5. Legacy Clause

This capsule is designed to grow.

- As new months are analyzed, add new rows.  
- As other domains are included (DESI, collider, lab data), they can be:
  - Added as new sections, or  
  - Referenced via parallel catalogs.

No change to the canonical law or heartbeat period should be claimed without updating this catalog (or a successor to it) to show where the new values come from.

**Ledger proud — November and December heartbeat results, side by side, forming the first catalog of LUFT’s boundary recoil across time.**
