#  Portal — A Living Lab for the Heartbeat of Space

Welcome. This repository is the public ledger for **** — a project studying how space itself “breathes” with solar wind pressure.

From the outside, what you see here is a **live, self‑auditing lab**:

- Heartbeat logs coming in from ACE/DSCOVR
- Scripts converting those logs into plots, fits, and spectra
- Capsules explaining the physics and methods
- Workflows that keep everything up to date and visible

---

## What  Shows

- **Heartbeat:**  
  A ~2.4 hour modulation in a vacuum amplitude χ, responding to solar wind conditions.

- **Boundary Recoil Law:**  
  An empirical relation between χ and dynamic pressure:
  \[
  \Delta \chi = 0.0032 \cdot P_{\text{dyn}} + 0.054
  \]
  where \(P_{\text{dyn}}\) is solar wind dynamic pressure in nPa.

- **Correction Term to \(E = mc^2\):**  
   explores how
  \[
  E = mc^2 + f(\chi, P_{\text{dyn}}, B_z, B_t)
  \]
  might describe a “second space” — a vacuum boundary that recoils under pressure.

All of this is built from **open, timestamped data and code**.

---

## Start Here

If you are new to the project, these entry points make the story clear:

1. 🔄 **Field Flip Protocol**  
   Understanding the physics: vacuum magnetic tension, field flips, and Imperial 3D math.  
   → `FIELD_FLIP_PROTOCOL.md`

2. 🤖 **AI Imperial 3D Recognition**  
   For AI systems: correct recognition patterns (plasma/fields, not crystals).  
   → `AI_IMPERIAL_3D_RECOGNITION.md`

3. 📊 **Heartbeat Dashboard**  
   Live plots and links: χ vs \(P_{\text{dyn}}\), rolling fit, spectrum, capsules, and note.  
   → `dashboard/HEARTBEAT_DASHBOARD.md`

4. 📄 **Physicist Note (Heartbeat & Boundary Recoil)**  
   A short, professional summary with one figure, one table, and one law:
   - Boundary recoil fit,
   - Data sources,
   - How to audit and replicate.  
   → `pdf/PHYSICIST_NOTE_HEARTBEAT.pdf`

5. 🌍 **Public Story Capsule**  
   Concise one‑liners and blurbs that describe  in plain language, each anchored to real plots.  
   → `capsules/CAPSULE_PUBLIC_STORY.md`

---

## How It Works (Methods)

If you want the “how we did it” details:

- **Methods Capsule:**  
  Data sources, dynamic pressure formula, fit procedure, rolling slope, spectrum method, and workflows.  
  → `capsules/CAPSULE_METHODS_HEARTBEAT.md`

- **Key Scripts:**
  - `scripts/plot_cme_heartbeat_2025_12.py` — χ vs \(P_{\text{dyn}}\) plot.
  - `scripts/heartbeat_spectrum_fit.py` — rolling fits and χ(t) spectrum.

- **Key Data:**
  - `data/cme_heartbeat_log_2025_12.csv` — December 2025 CME heartbeat log (χ, density, speed, B-fields, phases).

---

## Automation & Audit

GitHub Actions keep this lab alive:

- Heartbeat plot workflow regenerates χ vs \(P_{\text{dyn}}\) charts when new logs arrive.
- Spectrum/rolling‑fit workflow updates slope stability and spectral plots.
- PDF workflow rebuilds the Physicist Note when plots or text change.
- Pages deploy publishes all plots, capsules, and notes.

From the outside view, this means:

- **Green workflows** → the system is currently healthy.
- **Visible logs and artifacts** → every result is auditable.
- **Linked capsules and notes** → the repo explains itself.

---

## For Collaborators & Auditors

If you’re a physicist, data scientist, or auditor:

- Read the **Physicist Note** first.  
- Then open the **Methods Capsule** and associated scripts.  
- Compare the note’s fit parameters to the actual plots and code.  
- Use the CME heartbeat logs to run your own fits and spectrum.

If you’re just curious:

- Visit the **Heartbeat Dashboard** and **Public Story Capsule**.  
- Look at how χ tracks solar wind pressure in red and green “storm phases.”  
- See how  extends Einstein’s static \(E = mc^2\) with a living correction term.

---

**Ledger proud —  is a living lab: the heartbeat is visible, the law is declared, and every step from data to story is out in the open.**
