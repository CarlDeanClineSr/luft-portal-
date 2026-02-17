# Capsule—Review Guidelines for  Figures Update PRs

**Author:** Carl Dean Cline Sr.  
**Date:** 2025‑12‑04  
**Ledger:**  Portal  
**Purpose:** This capsule sets out the peer review criteria and checklist for all automated figure updates to  capsules, ensuring transparency, reproducibility, and scientific rigor.

---

## Review Checklist for Figures PR

**1. Data Source:**  
- Confirm `cme_heartbeat_log_2025_12.csv` is the source log.
- Timestamp and event lineage are properly documented.

**2. Code & Script Version:**  
- Plotting scripts (e.g., `plot_capsule_figures.py`) are up-to-date.
- Script changes are clearly described in commit/PR body.

**3. Figure Audit:**  
- All updated figures (`figure1_saturation.png`, `figure2_hysteresis.png`, `figure3_magnetic.png`, `figure4_phase.png`) are present.
- PNGs show correct overlays for capsule equations.

**4. Math Reproducibility:**  
- Capsule equations in markdown match the underlying script output.
- Parameters are fit directly from CSV—no missing code/data links.

**5. Visual Proof:**  
- Labels, axes, and captions match capsule text.
- Saturation, hysteresis, gain, and phase plots replicate capsule logic.

**6. Peer Approval:**  
- PRs are labeled with `auto-update`, `figures`.
- At least one contributor confirms visual + code integrity before merge to main.

**7. Ledger Provenance:**  
- Capsule, commit, and PR all cross-link to event timestamp, source data, and result figures.
- Provenance is clear; audit can be replicated by any peer.

---

## Audit Note

This capsule is living. Reviewers may update checklist and add context as  dashboards, capsule equations, or data sources evolve.

Relay proud—every  figure update is scientifically accountable, transparent, and ready for challenge or replication.

---
