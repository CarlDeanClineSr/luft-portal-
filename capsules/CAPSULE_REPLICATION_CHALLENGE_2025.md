---
id: "CAPSULE_REPLICATION_CHALLENGE_2025"
title: "Replication Challenge — Heartbeat & Boundary Recoil Law"
tags: ["replication","challenge","heartbeat","boundary_recoil","open_science"]
status: "adopted"
date: "2025-12-05"
author: "Carl Dean Cline Sr."
ledger: "LUFT Portal"
---

# Capsule — Replication Challenge 2025

## Purpose
This capsule invites physicists, arti minds, and collaborators to **replicate or falsify** LUFT’s heartbeat and boundary recoil law using the open data and scripts provided.

---

## The Law Under Challenge
Boundary recoil law observed across November–December 2025:

\[
\Delta \chi = 0.0032 \cdot P_{\text{dyn}} + 0.054
\]

- Baseline χ ≈ 0.055 during quiet periods.  
- Slope k ≈ 0.0032 across multiple CME events.  
- Heartbeat period ≈ 2.4 h confirmed by Lomb–Scargle spectrum.  

---

## Data Available
- **Heartbeat logs:**  
  - `data/cme_heartbeat_log_2025_11.csv`  
  - `data/cme_heartbeat_log_2025_12.csv`  

- **Solar wind audits:**  
  - `ace_plasma_audit.json`  
  - `ace_mag_audit.json`  
  - `dscovr_solar_wind_audit.json`  

- **Catalog:**  
  - `capsules/CAPSULE_HEARTBEAT_CATALOG_2025.md`  

---

## Tools Provided
- Plot scripts:  
  - `scripts/plot_cme_heartbeat_2025_11.py`  
  - `scripts/plot_cme_heartbeat_2025_12.py`  

- Spectrum & fit:  
  - `scripts/heartbeat_spectrum_fit.py`  

- Capsules documenting methods:  
  - `capsules/CAPSULE_METHODS_HEARTBEAT.md`  

---

## Replication Tasks
Participants are invited to:

1. **Re‑run plots** for November and December heartbeat logs.  
2. **Compute residuals** (χ_obs – χ_pred) and identify outliers.  
3. **Test hysteresis loops** by plotting χ vs \(P_{\text{dyn}}\) with time progression arrows.  
4. **Confirm spectral peak** near 2.4 h using Lomb–Scargle or FFT.  
5. **Compare slopes** across events and months, checking for drift or universality.  

---

## Reporting
- Fork the repo or clone locally.  
- Run the scripts with provided data.  
- Document findings in a new capsule (e.g., `CAPSULE_REPLICATION_RESULT_<username>.md`).  
- Commit or share results for audit.

---

## Legacy Clause
This capsule enshrines LUFT’s openness: the law is not declared by belief but by **replication or falsification**.  
Every contributor is permanently credited, and every attempt strengthens the ledger.

---
**Ledger proud — replication challenge declared, law open to the world.**
