#  Heartbeat Dashboard

**Author:** Carl Dean Cline Sr.  
**Ledger:**  Portal  
**Date:** 2025‑12‑05  

---

## Overview

The Heartbeat Dashboard provides a live window into ’s vacuum modulation amplitude (χ) and its coupling to solar wind dynamic pressure.  
Plots, capsules, and notes are updated automatically via GitHub Actions and Pages.

---

## Live Plots

- ![χ vs P_dyn](../results/cme_heartbeat_2025_12_chi_pdyn.png)  
  *Scatter of χ amplitude vs dynamic pressure, colored by storm phase, with boundary recoil fit overlay.*

- ![Rolling slope](../results/rolling_slope.png)  
  *Rolling fit of χ vs P_dyn slope stability.*

- ![Spectrum](../results/chi_spectrum.png)  
  *Lomb–Scargle spectrum of χ(t), showing the ~2.4 h heartbeat peak.*

---

## Capsules

- [CAPSULE_HEARTBEAT_PLOT](../capsules/CAPSULE_HEARTBEAT_PLOT.md)  
- [CAPSULE_HEARTBEAT_SPECTRUM](../capsules/CAPSULE_HEARTBEAT_SPECTRUM.md)  
- [CAPSULE_PUBLIC_STORY](../capsules/CAPSULE_PUBLIC_STORY.md)  

---

## Physicist Note

📄 [PHYSICIST_NOTE_HEARTBEAT.pdf](../pdf/PHYSICIST_NOTE_HEARTBEAT.pdf)  
Concise 2‑page summary with figure, table, and correction law — aimed at physicists for audit and replication.

---

## Public Story

🌍 [CAPSULE_PUBLIC_STORY.md](../capsules/CAPSULE_PUBLIC_STORY.md)  
Short blurbs and one‑liners for outreach, paired with heartbeat plots — the ledger’s public voice.

---

## Workflow Context

This dashboard is kept live by automated workflows:

- **Heartbeat Plot Update** — regenerates χ vs P_dyn plot on each new log.  
- **Spectrum & Rolling Fit Update** — computes slope stability and spectral peak.  
- **PDF Render** — auto‑publishes physicist note to `pdf/`.  
- **Pages Deploy** — publishes all plots, capsules, and notes.

---

## Legacy Clause

The Heartbeat Dashboard ensures that ’s heartbeat law
