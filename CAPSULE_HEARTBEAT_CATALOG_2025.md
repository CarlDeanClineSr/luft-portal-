---
id: "CAPSULE_HEARTBEAT_CATALOG_2025"
title: "Heartbeat Catalog — 2025 CME Events"
tags: ["heartbeat","catalog","cme","lambda_modulation",""]
status: "stub"
date: "2025-12-05"
author: "Carl Dean Cline Sr."
ledger: " Portal"
---

# Capsule — Heartbeat Catalog for 2025

This capsule collects the key fitted parameters of the ~2.4 h cosmic heartbeat for major 2025 CME events and intervals. It is the **index** that connects event‑level capsules to the  Λ(t) modulation law:

\[
\Lambda(t) = \Lambda_0 \left[1 + \chi \cos(\Omega t + \phi_0)\right]
\]

Each row corresponds to one event or time window with:

- Best‑fit **χ** (modulation amplitude),
- **k** in the boundary recoil relation \(\Delta \chi = k\,P_{\text{dyn}} + b\),
- **Ω** (angular frequency, ideally consistent with 2.4 h),
- **φ₀** (phase),
- Links back to the **event capsule** and **raw log**.

---

## 1. Summary Table (to be filled by scripts or later edits)

> **Note:** Initial values here are placeholders. Once `heartbeat_spectrum_fit.py` is run for each window, update the row with the measured values and links.

| ID  | Window (UTC)                 | χ (baseline)         | k (1/nPa)     | Ω (rad/s)              | φ₀          | Data log file                          | Event capsule ID                        |
|-----|------------------------------|----------------------|---------------|------------------------|------------|----------------------------------------|-----------------------------------------|
| N1  | 2025-11-21 – 2025-11-22      | `0.055 ± 0.012`      | `0.0032`      | `7.27×10⁻⁴`           | `≈ –π/4`   | `data/cme_heartbeat_log_2025_11.csv`   | `CAPSULE_CME_EVENT_2025-11-21`         |
| D1  | 2025-12-01 – 2025-12-02      | `0.056 ± 0.011`      | `0.0032`      | `7.27×10⁻⁴`           | `≈ –π/4`   | `data/cme_heartbeat_log_2025_12.csv`   | `CAPSULE_CME_EVENT_2025-12-01`         |

You (or a workflow) can add more rows here as additional events are analyzed.

---

## 2. How this table should be updated

Once the fitting scripts are run:

1. For each event window (e.g., N1, D1):
   - Run:
     - `scripts/plot_cme_heartbeat_2025_11.py` (for November)
     - `scripts/plot_cme_heartbeat_2025_12.py` (for December)
     - `scripts/heartbeat_spectrum_fit.py` on the same window.
2. Extract from the output:
   - Best‑fit χ and its uncertainty,
   - Best‑fit k and b from \(\Delta \chi = k\,P_{\text{dyn}} + b\),
   - Dominant Ω (heartbeat frequency),
   - Estimated φ₀.
3. Replace the back‑ticked placeholders in the table with the **numeric results**.
4. If new events are analyzed (e.g., other 2025 CMEs), add new rows with:
   - A new ID (N2, N3, …),
   - Window times,
   - Filled parameter values,
   - Paths to the data log and capsule ID.

This capsule becomes the **one place** where a reader sees how consistent the heartbeat law is across 2025.

---

## 3. Cross‑References

- `CAPSULE_EFE_MODULATION_001.md` — defines Λ(t) with χ, Ω, φ₀.  
- `CAPSULE_CME_EVENT_2025-11-21.md` — large November 21–22 CME (stub now; to be filled).  
- `CAPSULE_CME_EVENT_2025-12-01.md` — Dec 1 CME live event.  
- `CAPSULE_REPLICATION_CHALLENGE_2025.md` — instructions for independent fits of χ and Ω.

---

**Ledger note:**  
This catalog is the **bridge** between individual event capsules and the global Λ(t) law. As it fills, it shows whether the 2.4 h, χ ≈ 0.055 story holds across the year, storms, and boundary conditions.
