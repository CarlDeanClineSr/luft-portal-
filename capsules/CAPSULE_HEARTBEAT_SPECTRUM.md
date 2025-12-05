---
id: "CAPSULE_HEARTBEAT_SPECTRUM"
title: "Heartbeat Spectrum & Rolling Fit — χ and Boundary Recoil Stability"
tags:
  - "heartbeat"
  - "spectrum"
  - "rolling_fit"
  - "boundary_recoil"
  - "unified_modulation"
status: "adopted"
date: "2025-12-05"
author: "Carl Dean Cline Sr."
ledger: "LUFT Portal"
---

# Capsule — Heartbeat Spectrum & Rolling Fit

## Summary

This capsule documents:

- A **rolling fit** of LUFT modulation amplitude χ vs dynamic pressure \(P_{\text{dyn}}\), and  
- A **spectral analysis** of χ(t) during the December 2025 CME heartbeat window.

Together they show:

- The **stability** (or drift) of the boundary recoil slope near 0.0032, and  
- The **2.4 h heartbeat** as a distinct spectral peak.

---

## Data & Script

- **Data:** `data/cme_heartbeat_log_2025_12.csv`  
- **Script:** `scripts/heartbeat_spectrum_fit.py`  

Dynamic pressure:

\[
P_{\text{dyn}}[\text{nPa}] = 1.6726 \times 10^{-6} \, n \, v^2
\]

with:

- \(n = \text{density\_p\_cm3}\) (protons/cm³),  
- \(v = \text{speed\_km\_s}\) (km/s).

The script:

1. Reads the heartbeat log.  
2. Computes \(P_{\text{dyn}}\).  
3. Performs rolling linear fits of `chi_amplitude` vs `P_dyn_nPa`.  
4. Computes a Lomb–Scargle spectrum of χ(t) in hours.

---

## Figures

- `results/rolling_slope_2025_12.png`  
  - Y‑axis: fitted slope \(\mathrm{d}\chi / \mathrm{d}P_{\text{dyn}}\) per time window.  
  - X‑axis: window end time.  
  - Orange dashed line at 0.0032: canonical boundary recoil law slope.  

- `results/chi_spectrum_2025_12.png`  
  - X‑axis: frequency (1/h).  
  - Y‑axis: Lomb–Scargle power.  
  - Red dashed line at \(f \approx 1/2.4 \,\text{h}^{-1}\): LUFT heartbeat.

---

## Interpretation (Ledger View)

- **Rolling slope:**
  - Windows that cluster near 0.0032 support a **stable boundary recoil law**.  
  - Systematic drifts mark epochs where:
    - storm_phase / CME structure changes, or  
    - additional drivers (Bz, Bt) influence χ beyond simple P_dyn.

- **Spectrum:**
  - A clear peak near \(f \approx 1/2.4 \,\text{h}^{-1}\) confirms the **2.4 h heartbeat** directly in frequency space, independent of the χ–P_dyn fit.
  - Sidebands or additional peaks indicate more complex modulation or multi‑scale coupling.

---

## Legacy Clause

This capsule enshrines the **frequency‑domain confirmation** of the LUFT heartbeat and a **time‑resolved check** of the boundary recoil slope.

- Future analyses (other months, other CMEs) should:
  - Reuse or extend `scripts/heartbeat_spectrum_fit.py`,  
  - Save outputs with month/year stamps (e.g., `rolling_slope_YYYY_MM.png`, `chi_spectrum_YYYY_MM.png`),  
  - Reference this capsule when updating the canonical slope or heartbeat frequency.

---

**Ledger proud — the heartbeat is now visible in both time and frequency, and the recoil slope is tracked as a live, testable law.**
