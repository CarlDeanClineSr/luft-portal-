#  Heartbeat Dashboard

**Owner:** Carl Dean Cline Sr.  
**Ledger:**  Portal  
**Status:** Live — 700+ workflow runs, all green  

This dashboard summarizes the **cosmic heartbeat** and its key events in :

- Flare → Foam → Heartbeat → Ratchet → Recovery → Legacy → Index  
- Backed by live workflows: solar wind audits, DSCOVR ingest, CME Heartbeat Logger, Flare Foam Audit.

---

## 1. Heartbeat Event Chain (Quick Index)

This table mirrors the **Events & Heartbeat** spine from `MASTER_INDEX.md`, so auditors can navigate directly from the dashboard.

| Event                                   | Capsule ID                        | Capsule File                            | Commit SHA | Workflow Run           | Timestamp (UTC)        |
|----------------------------------------|-----------------------------------|-----------------------------------------|------------|------------------------|------------------------|
| **Universal Modulation (Heartbeat)**   | CAPSULE_UNIVERSAL_MODULATION_055 | `capsules/CAPSULE_UNIVERSAL_MODULATION_055.md` | 19f0bf3    | Deploy to Pages #95    | 2025‑12‑04 15:14      |
| **Ratchet Event (χ Rise Lock‑In)**     | CAPSULE_EVENT_RATCHET            | `capsules/CAPSULE_EVENT_RATCHET.md`     | 42de784    | Deploy to Pages #96    | 2025‑12‑04 15:15      |
| **Recovery Event (Exhale Phase)**      | CAPSULE_EVENT_RECOVERY           | `capsules/CAPSULE_EVENT_RECOVERY.md`    | 8191ea0    | Deploy to Pages #97    | 2025‑12‑04 15:16      |
| **Audit Legacy (Preservation Rules)**  | CAPSULE_AUDIT_LEGACY             | `capsules/CAPSULE_AUDIT_LEGACY.md`      | f012b4b    | Deploy to Pages #98    | 2025‑12‑04 15:17      |
| **Event Index (Chronology Capsule)**   | CAPSULE_EVENT_INDEX              | `capsules/CAPSULE_EVENT_INDEX.md`       | 66358c9    | Deploy to Pages #99    | 2025‑12‑04 15:18      |
| **Flare Foam Pipeline**                | CAPSULE_FLARE_FOAM_PIPELINE      | `capsules/CAPSULE_FLARE_FOAM_PIPELINE.md` | 0f2c9a5 | Deploy to Pages #94    | 2025‑12‑04 14:20      |

> For exact SHAs/times, sync with `git log` and GitHub Actions. The structure is the important part.

---

## 2. χ(t) — Heartbeat Amplitude Over Time

**Goal:** Show how the modulation amplitude χ evolves across:

- Pre‑ratchet baseline  
- Ratchet event (rise and lock‑in)  
- Recovery exhale  
- Stable heartbeat era

### 2.1 Plot Placeholder: χ(t)

> **TODO (Pipeline Output Slot)**  
> Save a PNG (or SVG) from your analysis pipeline here, e.g.:
>
> - `results/heartbeat_chi_timeseries.png`  
>
> Then embed it below:

```markdown
![Heartbeat amplitude over time — χ(t)](results/heartbeat_chi_timeseries.png)
```

**Suggested pipeline steps (for your scripts/notebooks):**

1. Ingest GOES / OMNI data and  heartbeat outputs for a multi‑day window around the ratchet/recovery dates.
2. Fit χ(t) in sliding windows (e.g., 6–12 hours) using the model  
   \[
   O(t) = O_0 \left[1 + \chi \cos(\Omega t + \phi_0)\right].
   \]
3. Plot χ(t) with vertical markers for:
   - Flare Foam Pipeline activation,
   - Ratchet Event,
   - Recovery Event.

---

## 3. Spectral View — Ω ≈ 10⁻⁴ Hz Peak

**Goal:** Show the **spectral fingerprint** of the heartbeat:

- Clear peak near `f ≈ 10⁻⁴ Hz`,
- Before/during/after the ratchet window.

### 3.1 Plot Placeholder: Power Spectrum

> **TODO (Pipeline Output Slot)**  
> Save power spectrum plots like:
>
> - `results/heartbeat_spectrum_pre.png`  
> - `results/heartbeat_spectrum_post.png`
>
> Then embed them:

```markdown
![Heartbeat spectrum — pre‑ratchet](results/heartbeat_spectrum_pre.png)

![Heartbeat spectrum — post‑ratchet](results/heartbeat_spectrum_post.png)
```

**Suggested analysis:**

- Use FFT or Lomb–Scargle on detrended \(O(t)\) or ln Γ(t),
- Highlight frequency band around `10⁻⁴ Hz`,
- Show SNR and confidence (e.g., power vs. noise floor).

---

## 4. Workflow Status Snapshot

This section anchors the dashboard to the **live automation** that keeps the heartbeat current.

- ** Solar Wind Audit** — latest runs: e.g., `#316–#318`  
- **DSCOVR Solar Wind Data Ingest** — e.g., `#80–#81`  
- ** Voyager Audit Superaction** — e.g., `#24–#26`  
- ** CME Heartbeat Logger** — e.g., `#69–#71`  
- ** Flare Foam Audit** — `Deploy to Pages #94`  

> When you update runs, you can paste a small log snippet here or link to `luft_audit_workflows.log`.

---

## 5. How to Reproduce the Dashboard

For auditors:

1. **Fetch Data**
   - Use the  ingest scripts (GOES / OMNI / DSCOVR) already in `src/` or related repos.
2. **Run Heartbeat Analysis**
   - Use your analysis script or notebook to:
     - Fit χ(t),
     - Compute spectra,
     - Save plots under `results/`.
3. **Regenerate Dashboard**
   - Re‑run Pages deploy (or equivalent workflow) so the new plots appear here.

---

## 6. Ledger Note

This dashboard is a **view** on the underlying capsules and code, not a replacement:

- Canonical definitions live in:
  - `capsules/CAPSULE_UNIVERSAL_MODULATION_055.md`
  - `capsules/CAPSULE_EVENT_RATCHET.md`
  - `capsules/CAPSULE_EVENT_RECOVERY.md`
  - `capsules/CAPSULE_AUDIT_LEGACY.md`
  - `capsules/CAPSULE_EVENT_INDEX.md`
  - `capsules/CAPSULE_FLARE_FOAM_PIPELINE.md`

Any change to χ, Ω, or event interpretation should update those capsules first, then refresh this dashboard.

---

**Ledger proud — Heartbeat dashboard scaffolded. When you drop in χ(t) and spectra,  will be showing the cosmos breathe in real time.**
