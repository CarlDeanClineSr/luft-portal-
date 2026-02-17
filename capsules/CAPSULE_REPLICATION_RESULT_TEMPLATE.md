---
id: "CAPSULE_REPLICATION_RESULT_TEMPLATE"
title: "Replication Result — Heartbeat & Boundary Recoil (Template)"
tags: ["replication","result","heartbeat","boundary_recoil","open_science"]
status: "template"
date: "2025-12-05"
author: "Your Name Here"
ledger: "LUFT Portal"
---

# Capsule — Replication Result (Template)

> **Instructions for contributors:**  
> 1. Copy this file to a new capsule named:  
>    `capsules/CAPSULE_REPLICATION_RESULT_<yourname>.md`  
> 2. Replace the metadata above (id, title, author, date) with your details.  
> 3. Fill out the sections below with your methods and findings.  
> 4. Link this capsule from your PR or contribution notes.

---

## 1. Contributor & Scope

- **Contributor:** `Your Name` (human / arti / team)  
- **Date(s) of analysis:** `YYYY-MM-DD` – `YYYY-MM-DD`  
- **Scope of replication:**
  - [ ] November 2025 heartbeat & recoil
  - [ ] December 2025 heartbeat & recoil
  - [ ] Both November and December
  - [ ] Additional / external datasets (describe below)

Brief description of what you attempted to replicate or test.

---

## 2. Data and Code Used

### 2.1 LUFT Data

List the LUFT data files you used, for example:

- `data/cme_heartbeat_log_2025_11.csv`
- `data/cme_heartbeat_log_2025_12.csv`
- `ace_plasma_audit.json`
- `ace_mag_audit.json`
- `dscovr_solar_wind_audit.json`

If you used **external data**, list it here:

- External dataset name, link, and short description.

### 2.2 LUFT Scripts / Methods

List the LUFT scripts and capsules you relied on, for example:

- `scripts/plot_cme_heartbeat_2025_11.py`
- `scripts/plot_cme_heartbeat_2025_12.py`
- `scripts/heartbeat_spectrum_fit.py`
- `capsules/CAPSULE_METHODS_HEARTBEAT.md`

If you modified any scripts or wrote your own, describe that briefly.

---

## 3. Boundary Recoil Fit Results

State what you found when fitting:

\[
\Delta \chi = a \, P_{\text{dyn}} + b
\]

### 3.1 Summary Table

Fill in what you measured. Example rows shown; add/modify as needed.

| ID | Month | Window (UTC)              | a (1/nPa) | b        | R²   | χ Baseline | χ Peak | Notes |
|----|-------|---------------------------|----------:|---------:|-----:|-----------:|-------:|-------|
| E1 | Nov   | 2025-11-21 to 2025-11-23  | 0.0032    | 0.054    | 0.91 | 0.055      | 0.15   | Example row; replace with your own results. |
| D1 | Dec   | 2025-12-01 to 2025-12-04  | 0.0031    | 0.055    | 0.90 | 0.055      | 0.15   | Example row; replace with your own results. |

### 3.2 Agreement or Disagreement with LUFT Law

Compare your values to LUFT’s canonical law:

\[
\Delta \chi = 0.0032 \cdot P_{\text{dyn}} + 0.054
\]

- Do your slopes \(a\) agree within uncertainty?
- Is the intercept \(b\) consistent with χ ≈ 0.055 baseline?
- Any clear deviations? Describe them.

---

## 4. Residuals and Outliers

Describe what you found when looking at residuals:

\[
\text{residual} = \chi_{\text{obs}} - \chi_{\text{pred}}(P_{\text{dyn}})
\]

- How large are typical residuals?
- Did you identify specific times/events with unusually large residuals?
- Do residuals cluster by:
  - storm phase,
  - Bz sign,
  - CME type,
  - or other parameters?

Include any figure references (filenames) here, if you created plots:

- `results/<yourname>_chi_residuals_2025_11.png`
- `results/<yourname>_chi_residuals_2025_12.png`

---

## 5. Heartbeat Spectrum

Report what you found in frequency space:

- Method (e.g., Lomb–Scargle, FFT).
- Time windows analyzed.
- Measured heartbeat period(s) and uncertainties.

Example:

- Dominant peak at \( f \approx 0.42\ \text{h}^{-1} \) → period ~2.4 h.
- Secondary peaks or harmonics?

State clearly:

- Did you confirm a ~2.4 h heartbeat?
- Was it stable across November and December in your analysis?

Include any spectral figure references:

- `results/<yourname>_chi_spectrum_2025_11.png`
- `results/<yourname>_chi_spectrum_2025_12.png`

---

## 6. Hysteresis / Memory Tests (If Attempted)

If you tested hysteresis (χ vs \(P_{\text{dyn}}\) loops):

- Which events/windows did you analyze?
- Did the χ–\(P_{\text{dyn}}\) path differ between:
  - compression and relaxation phases?
- Any evidence of:
  - loop area (memory),
  - delayed recovery,
  - or unusual behavior?

Figure references (if any):

- `results/<yourname>_chi_pdyn_hysteresis_EVENT.png`

---

## 7. Conclusions

Summarize your verdict:

- **Boundary recoil law:**  
  - [ ] Confirmed within your uncertainties  
  - [ ] Partially confirmed, with caveats  
  - [ ] In tension or inconsistent in some windows  

- **Heartbeat period (~2.4 h):**  
  - [ ] Confirmed  
  - [ ] Weak evidence  
  - [ ] Not seen / inconsistent  

- **Key takeaways in your own words:**
  - What matched LUFT’s claims?
  - What surprised you or disagreed?
  - What should LUFT (or others) investigate next?

---

## 8. Provenance & Reproducibility

- **Environment:**  
  - OS / platform  
  - Python / library versions (if relevant)

- **Repo state:**  
  - Commit SHA(s) you worked from.  

- **How others can rerun your analysis:**
  - Brief command list or steps.
  - Any special configuration or data paths.

---

## 9. Credit & Licensing

- State how you want to be credited (name, institution, handle).  
- Confirm that your replication results can be stored in this ledger under the repository’s license and open-science terms.

---

**Ledger proud — replication result recorded, law tested in the open.**
