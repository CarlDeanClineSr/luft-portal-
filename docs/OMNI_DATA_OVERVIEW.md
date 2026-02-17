# OMNIWeb Data Integration — LUFT χ Amplitude Validation

**Last Updated:** 2025-12-17  
**Data Source:** NASA OMNIWeb OMNI2 hourly-averaged solar wind dataset  
**Time Coverage:** November 1 – December 9, 2025 (extended to current via automated workflows)

---

## **1. What Is OMNIWeb OMNI2? **

The **Low Resolution OMNI (LRO)** dataset is a **1963-to-current compilation** of hourly-averaged, near-Earth solar wind magnetic field and plasma parameters from multiple spacecraft: 

- **Spacecraft:** IMP 1–8, ISEE 3, Wind, ACE, Geotail (see full list in §5 below)
- **Orbit Types:** Geocentric (IMP series) and L1 Lagrange point (Wind, ACE, ISEE 3)
- **Data Processing:** Cross-normalized across spacecraft, time-shifted to Earth bow shock arrival times
- **Resolution:** Hourly averages (from 1–5 min upstream data), with daily and 27-day averages also available

**Key Features:**

- **46+ parameters per timestamp** (see §3 below)
- **Activity indices** included:  Kp, Dst, AE, AL, AU, F10.7, sunspot number (Rz), PCN
- **Energetic particle fluxes:** Protons at 1, 2, 4, 10, 30, 60 MeV thresholds (IMP 7/8, GOES)
- **Quality-controlled:** Magnetosheath contamination removed, bow shock crossings flagged

**Why This Matters for LUFT:**

- **Gap-filling:** OMNIWeb provides complete density/speed/Bz when DSCOVR-only data has dropouts (as seen Dec 17, 07:19–15:20 UTC in our heartbeat log)
- **Multi-parameter validation:** Pressure, plasma beta, Mach numbers, electric field → test χ cap against **driving forces**, not just density/speed
- **Historical depth:** Extends back to 1963 → test χ = 0.15 saturation across solar cycles, CME regimes, different spacecraft instruments

---

## **2. Data Availability (Current)**

From OMNIWeb (https://omniweb.gsfc.nasa.gov/html/ow_data. html):

| Parameter                     | Date Range                   | Notes                                                  |
|-------------------------------|------------------------------|--------------------------------------------------------|
| **IMF (magnetic field)**      | 1963-11-27 → 2025-11-24      | Wind (S/C ID=51) primary source 1995–current          |
| **Plasma (density/speed/T)**  | 1963-11-27 → 2025-12-03      | Wind/SWE definitive (S/C ID=52) primary 1995–current  |
| **Energetic proton fluxes**   | 1967-05-30 → 2020-03-04      | IMP 7/8 (1973–2005), GOES 11/13/14 (2006–2020)        |
| **Kp, ap indices**            | 1963-01-01 → 2025-12-09      | GFZ Potsdam (3-hr resolution)                          |
| **Dst index**                 | 1963-01-01 → 2025-12-09      | Kyoto (1-hr resolution, quick-look after 2025-07-01)  |
| **AE, AL, AU indices**        | 1990-01-01 → 2025-11-30      | Kyoto (1-hr resolution, quick-look 2021–current)      |
| **F10.7 solar flux**          | 1963-01-01 → 2025-12-09      | Canada, adjusted to 1 AU                               |
| **Sunspot number (Rz v2)**    | 1963-01-01 → 2025-11-30      | SIDC Belgium                                           |
| **PCN polar cap index**       | 1975-01-01 → 2024-12-31      | DTU Denmark (definitive, 1-hr from 1-min data)        |
| **Solar Lyman-alpha**         | 1963-01-01 → 2025-12-08      | LASP Colorado                                          |

**LUFT Integration:**

- Our **CME Heartbeat Logger** currently uses **DSCOVR-only** plasma/mag data (via NOAA JSON APIs).
- We will **merge OMNIWeb hourly data** as a **secondary validation source** and **gap-filler** when DSCOVR has dropouts or instrument issues. 

---

## **3. Parameter List (56 Words per OMNI2 Record)**

Each hourly record contains **56 data words** (plus derived parameters). Below are the parameters **most relevant to LUFT χ amplitude validation**:

### **Magnetic Field (IMF) Parameters**

| Word | Parameter                  | Units        | Fill Value | Description                                                                 |
|------|----------------------------|--------------|------------|-----------------------------------------------------------------------------|
| 9    | `<F>` (scalar B avg)       | nT           | 999.9      | Average of field magnitude over fine-scale points in hour                   |
| 10   | `|<B>|` (vector B mag)     | nT           | 999.9      | Magnitude of vector-averaged field (GSE components)                         |
| 13   | Bx (GSE, GSM)              | nT           | 999.9      | X-component (radial, sunward-negative)                                      |
| 14   | By (GSE)                   | nT           | 999.9      | Y-component (ecliptic plane, dawn-dusk)                                     |
| 15   | Bz (GSE)                   | nT           | 999.9      | Z-component (ecliptic normal, north-south)                                  |
| 16   | By (GSM)                   | nT           | 999.9      | Y-component in Geocentric Solar Magnetospheric coords                       |
| 17   | Bz (GSM)                   | nT           | 999.9      | Z-component in GSM (key for geomagnetic coupling)                           |
| 18–22| σ(|B|), σ(B), σ(Bx/y/z)    | nT           | 999.9      | RMS standard deviations (measure of field turbulence)                       |

### **Plasma Parameters**

| Word | Parameter              | Units       | Fill Value | Description                                                                 |
|------|------------------------|-------------|------------|-----------------------------------------------------------------------------|
| 23   | Proton temperature (T) | K           | 9999999.   | Bulk proton temperature (from Faraday cup or ESA fits/moments)              |
| 24   | Proton density (Np)    | N/cm³       | 999. 9      | Number density of solar wind protons                                        |
| 25   | Bulk speed (V)         | km/s        | 9999.      | Scalar flow speed (radial component dominates)                              |
| 26   | Flow longitude (φ_V)   | degrees     | 999.9      | Azimuth angle of flow vector (GSE; 0° = -X axis, increases toward +Y)      |
| 27   | Flow latitude (θ_V)    | degrees     | 999.9      | Elevation angle (0° = ecliptic plane, + = north)                            |
| 28   | Na/Np (alpha/proton)   | ratio       | 9. 999      | Alpha particle to proton density ratio (He²⁺/H⁺)                            |

### **Derived Parameters (Key for LUFT Validation)**

| Word | Parameter                  | Units         | Fill Value | Formula / Description                                                       |
|------|----------------------------|---------------|------------|-----------------------------------------------------------------------------|
| 29   | **Flow pressure (P)**      | nPa           | 99. 99      | `P = (1. 67e-6) * Np * V² * (1 + 4*Na/Np)` if Na/Np valid, else `2e-6*Np*V²` |
| 36   | **Electric field (E)**     | mV/m          | 999.99     | `E = -V * Bz(GSM) * 1e-3` (convection electric field at magnetopause)      |
| 37   | **Plasma beta (β)**        | dimensionless | 999.99     | `β = [(T*4. 16e-5) + 5.34] * Np / B²` (thermal/magnetic pressure ratio)     |
| 38   | **Alfvén Mach (Ma)**       | dimensionless | 999.9      | `Ma = V * √Np / (20 * B)` (flow speed / Alfvén speed)                       |
| 55   | **Magnetosonic Mach (Mms)**| dimensionless | 99.9       | `Mms = V / √(c_s² + v_A²)` where c_s = sound speed, v_A = Alfvén speed     |
| 57   | **Quasi-Invariant (QI)**   | dimensionless | 9.9999     | `QI = (B²/8π) / (ρV²/2)` = magnetic/kinetic energy density ratio            |

### **Activity Indices**

| Word | Parameter          | Units       | Fill Value | Description                                                                 |
|------|--------------------|-------------|------------|-----------------------------------------------------------------------------|
| 39   | Kp * 10            | —           | 99         | Planetary K-index (3-hr resolution, scaled:  0 → 0, 1- → 7, 1 → 10, .. ., 9 → 90) |
| 40   | R (sunspot number) | count       | 999        | Daily sunspot number (version 2, SIDC Belgium)                              |
| 41   | Dst index          | nT          | 99999      | Disturbance storm time index (1-hr resolution, Kyoto)                       |
| 42   | AE index           | nT          | 9999       | Auroral electrojet index (1-hr resolution, Kyoto)                           |
| 50   | ap index           | nT          | 999        | 3-hr ap index (GFZ Potsdam)                                                 |
| 51   | F10.7 flux         | 10⁻²² W/m²/Hz | 999.9    | Daily solar radio flux at 10.7 cm (2800 MHz), adjusted to 1 AU             |
| 52   | PCN index          | —           | 999. 9      | Polar cap north index (DTU Denmark, 1-hr from 1-min data)                  |
| 53   | AL index           | nT          | 99999      | Lower auroral electrojet (Kyoto)                                            |
| 54   | AU index           | nT          | 99999      | Upper auroral electrojet (Kyoto)                                            |

### **Energetic Particle Fluxes** (Words 43–48)

Proton fluxes above energy thresholds:  1, 2, 4, 10, 30, 60 MeV (units: particles/cm²/sec/ster).  
**Note:** IMP 7/8 data end in 2005; GOES 11/13/14 data cover 2006–2020; **no energetic particle data after 2020-03-04** in current OMNI2.

---

## **4. Spacecraft Identifiers (S/C ID)**

OMNI2 assigns numeric IDs to each contributing spacecraft. For LUFT (1995–current), the key sources are:

| S/C ID | Spacecraft         | Role                                  | Data Type                       | Time Span          |
|--------|--------------------|---------------------------------------|---------------------------------|--------------------|
| **51** | **Wind**           | Primary IMF + plasma (KP parameters)  | Mag + plasma/SWE-KP             | 1995-01-01 → current |
| **52** | **Wind**           | Definitive plasma (NLF fits)          | Plasma/SWE-NLF (nonlinear fits) | 1995-01-01 → current |
| **71** | **ACE**            | Secondary IMF + plasma                | Mag + plasma/SWEPAM             | 1998-02-06 → current |
| **60** | **Geotail**        | Gap-filler (1995–2006)                | Mag + plasma/CPI                | 1995-05-08 → 2006-12-31 |
| **50** | **IMP 8**          | Historical (1973–2001)                | Mag + plasma/MIT                | 1973-10-30 → 2001-06-26 |
| **45** | **IMP 8**          | Historical plasma (LANL)              | Plasma/LANL                     | 1973-11-04 → 2000-07-16 |

**Prioritization (2004–current):**  
Wind (S/C 51/52) **primary**, ACE (S/C 71) **secondary** (used when Wind has magnetospheric incursions or data gaps).

**Cross-Normalization:**  
All plasma sources (IMP 8, ISEE 3, ACE, Geotail) are **cross-normalized to Wind/SWE definitive (NLF)** baseline (±2–3% density uncertainty, ±8% temperature uncertainty).

---

## **5. Time-Shifting of Upstream Data**

**Why:** Wind and ACE orbit at **L1 Lagrange point** (~1.5 million km upstream, ~200–260 Re in GSE X). Solar wind observed there takes **~30–80 minutes** to reach Earth's bow shock (depending on speed and spacecraft Y position).

**How OMNI2 Does It:**

1. **Shift equation** (simplified for planar phase fronts):
   \[
   \Delta t = \frac{X}{V} \cdot \frac{1 + (Y \cdot W)/X}{1 - V_e \cdot W / V}
   \]
   where: 
   - \( X, Y \) = spacecraft GSE position (km)
   - \( V \) = observed solar wind speed (km/s)
   - \( V_e = 30 \) km/s (Earth's orbital speed)
   - \( W = \tan[0.5 \cdot \arctan(V/428)] \) (phase front tilt parameter, halfway between corotation and pure convection)

2. **Procedure:**
   - Take 1–5 min upstream data (e.g., Wind/MFI 1-min mag, Wind/SWE 92-sec plasma)
   - Apply time shift to each fine-scale point → new "arrival time at Earth"
   - Compute hourly averages over all shifted points falling within each Earth-hour (00:00–01:00, 01:00–02:00, etc.)

**Impact Parameter (IP):**  
\[
IP_{ij} = \sqrt{\left[(Y_i - Y_j) + (X_i - X_j) \cdot V_e/V\right]^2 + (Z_i - Z_j)^2}
\]
Measures transverse separation between spacecraft pair.  OMNI2 data intercomparisons use **IP < 60 Re** filter to minimize spatial gradient effects.

**LUFT Note:**  
Our **current CME Heartbeat Logger** does **not** time-shift DSCOVR data (assumed negligible at L1 with ~1-hour transit). When merging OMNIWeb, we use **their pre-shifted hourly averages** directly.

---

## **6. Cross-Normalization Equations**

OMNI2 cross-normalizes all plasma sources to **Wind/SWE definitive (NLF)** baseline. Below are the key equations for sources we may encounter:

### **Wind/SWE KP → Wind/SWE NLF** (1995–current)

**Density (all V, all time):**
\[
\log N_{\text{norm}} = -0.055 + 1.037 \cdot \log N_{\text{obsvd}}
\]

**Temperature:**
- **1995–1997 (all V):**  
  \[
  \log T_{\text{norm}} = -0.30 + 1.055 \cdot \log T_{\text{obsvd}}
  \]
- **≥1998 (all V):**  
  \[
  \log T_{\text{norm}} = \log T_{\text{obsvd}} \quad \text{(no correction)}
  \]

### **ACE/SWEPAM → Wind/SWE NLF** (1998–current)

**Density (time + speed dependent):**

Let \( t \) = fractional years since 1998.0 (e.g., \( t = 1. 5 \) on 1999-07-01).

- **V < 395 km/s:**  
  \[
  N_{\text{norm}} = [0.925 + 0.0039 \cdot t] \cdot N_{\text{obsvd}}
  \]
- **V > 405 km/s:**  
  \[
  N_{\text{norm}} = [0.761 + 0.0210 \cdot t] \cdot N_{\text{obsvd}}
  \]
- **395 ≤ V ≤ 405 km/s:**  
  \[
  N_{\text{norm}} = \frac{74. 02 - 0.164 \cdot V - 6.72 \cdot t + 0.0171 \cdot t \cdot V}{10} \cdot N_{\text{obsvd}}
  \]

**Temperature (all V, updated 2019–2020):**
- **2019–2020:**  
  \[
  \log T_{\text{norm}} = 0.266 + 0.947 \cdot \log T_{\text{obsvd}}
  \]

**Alpha/Proton Ratio:**  
**Removed from OMNI2 for all ACE data** (poor correlation with Wind/SWE NLF). Use **Wind/SWE NLF Na/Np** when available.

### **Geotail/CPI → Wind/SWE NLF** (1995–2006)

**Density (all time, all V):**
\[
\log N_{\text{norm}} = -0.072 + 0.980 \cdot \log N_{\text{obsvd}}
\]

**Temperature:**
- **1995–1998 (all V):**  
  \[
  \log T_{\text{norm}} = 0.166 + 0.925 \cdot \log T_{\text{obsvd}}
  \]
- **1999–2005 (all V):**  
  \[
  \log T_{\text{norm}} = -0.362 + 1.052 \cdot \log T_{\text{obsvd}}
  \]

**No Na/Np ratio** for Geotail. 

---

## **7. LUFT χ Amplitude — Testable Hypotheses with OMNIWeb Data**

### **Hypothesis 1: χ = 0.15 ceiling holds across pressure/beta/Mach regimes**

**Prediction:**  
Even when **flow pressure P**, **plasma beta β**, or **Mach numbers (Ma, Mms)** vary by orders of magnitude, χ amplitude **saturates at 0.15** (no overshoot).

**Test:**  
- Compute χ from OMNI2 density/speed/Bz
- Bin by pressure (low/med/high), beta (< 1, 1–10, > 10), Mach (sub-Alfvénic vs. super-Alfvénic)
- Plot χ vs.  time for each bin → ceiling at 0.15 in all regimes? 

### **Hypothesis 2: Recoil floor (~0.04–0.06) corresponds to rarefaction + Bz flip**

**Prediction:**  
Deep χ dips below 0.08 (toward floor ~0.04) occur when: 
1. **Density drops** (< 1 p/cm³, rarefaction)
2. **Bz flips** (south → north or vice versa, rapid field rotation)
3. **Pressure drops** (< 1 nPa, low dynamic pressure)

**Test:**  
- Identify all χ < 0.08 events in Nov–Dec 2025 data
- Check concurrent density, Bz, pressure → do they all show rarefaction + flip? 

### **Hypothesis 3: Electric field E correlates with recoil rate (snap-back speed)**

**Prediction:**  
When χ dips deeply (elastic compression release), the **rebound rate** (Δχ/Δt after nadir) correlates with convection electric field \( E = -V \cdot B_z \) (magnetopause driving force).

**Test:**  
- Find recoil events (χ drops then climbs back)
- Measure rise slope (Δχ/Δt over next 2–4 hours)
- Correlate with peak |E| during rebound → positive correlation = lattice "spring constant" tied to field stress

### **Hypothesis 4: Quasi-Invariant (QI) bounds χ range**

**Prediction:**  
\( QI = \frac{B^2/(8\pi)}{\rho V^2/2} \) (magnetic/kinetic energy density ratio) **inversely correlates** with χ amplitude: 
- High QI (field-dominated) → χ low (lattice relaxed)
- Low QI (flow-dominated) → χ high (lattice compressed, approaching 0.15 cap)

**Test:**  
- Scatter plot:  χ vs. QI for all Nov–Dec 2025 hours → negative trend?
- If yes → χ measures **lattice compression under kinetic stress**

---

## **8. Next Steps — OMNI Integration into LUFT Workflows**

### **Priority 1: Parse OMNI2 Fixed-Width Format**

**Script:** `tools/parse_omni2.py` (commit-ready, see FILE SET 2 below)

- Reads OMNIWeb annual ASCII files (format: 2I4,I3,I5,2I3,2I4,14F6.1,F9.0,...  per line)
- Maps word positions to parameter names (Bx, By, Bz, density, speed, T, pressure, beta, Mach, etc.)
- Replaces fill values (999.9, 9999., etc.) with NaN
- Builds datetime index from YEAR/DOY/HR → creates pandas DataFrame
- Outputs:  `data/omni2_parsed_YYYY. csv` (one per year, or merged multi-year)

### **Priority 2: Merge with CME Heartbeat Log**

**Script:** `tools/merge_omni_heartbeat.py` (commit-ready, see FILE SET 2 below)

- Loads `data/cme_heartbeat_log_2025_12. csv` (our DSCOVR-derived χ, density, speed, Bz)
- Loads `data/omni2_parsed_2025.csv` (OMNIWeb hourly data)
- Outer join on timestamp (UTC hour)
- **Fill gaps:** Where DSCOVR has blanks (e.g., Dec 17, 07:19–15:20), use OMNIWeb density/speed/Bz → recompute χ
- **Add extra drivers:** Append pressure, beta, Mach, E-field, QI columns from OMNIWeb
- Outputs: `data/extended_heartbeat_log_2025.csv` (complete dataset with all drivers)

### **Priority 3: Validate χ Across Parameter Space**

**Script:** `tools/validate_chi_omni. py` (commit-ready, see FILE SET 2 below)

- Reads extended heartbeat log
- Bins data by pressure/beta/Mach
- Computes statistics: max(χ), mean(χ), % time at χ ≥ 0.15, deepest dips
- Generates summary report:  `reports/chi_validation_omni_2025.md`

### **Priority 4: Automated OMNIWeb Ingest Workflow**

**Workflow:** `.github/workflows/omni_ingest_daily.yml` (commit-ready, see FILE SET 3 below)

- Runs daily at 12:00 UTC
- Downloads latest OMNIWeb data for current year (via FTP or web scraping)
- Parses, merges with heartbeat log
- Commits updated `data/extended_heartbeat_log_2025.csv`
- Triggers Vault Narrator update with new χ values (gap-filled)

---

## **9. References**

- **OMNIWeb Documentation:** https://omniweb.gsfc.nasa.gov/html/ow_data.html
- **OMNI2 Format Specification:** https://omniweb.gsfc.nasa.gov/html/omni2_doc_old.html
- **Data FTP Access:** https://spdf.gsfc.nasa.gov/pub/data/omni/
- **Spacecraft Prioritization (§8):** https://omniweb.gsfc.nasa.gov/html/omni2_doc_old.html#8
- **Wind/SWE Plasma Data:** https://spdf.gsfc.nasa.gov/pub/data/wind/swe/
- **ACE/SWEPAM:** https://izw1.caltech.edu/ACE/ASC/level2/
- **Kyoto Dst/AE Indices:** https://wdc.kugi.kyoto-u.ac.jp/wdc/Sec3. html
- **GFZ Kp/ap Indices:** https://kp.gfz-potsdam.de/en/data

---

## **10. Acknowledgments**

We thank: 

- **NASA SPDF** for maintaining and serving OMNIWeb data since 1963
- **Wind/SWE team** (MIT, J. Kasper et al.) for definitive NLF plasma parameters
- **ACE/SWEPAM team** (SWRI/LANL, D. McComas, R. Skoug) for moments-based plasma data
- **Kyoto University WDC** for geomagnetic indices (Dst, AE, AL, AU)
- **GFZ Potsdam** for Kp/ap indices
- **All spacecraft PI teams** (IMP 8, ISEE 3, Geotail, etc.) whose multi-decade efforts make OMNI2 possible

---

**Maintained by:** Carl Dean Cline Sr & Copilot  
**Contact:** CARLDCLINE@GMAIL.COM  
**License:** Data usage per NASA SPDF open data policy; LUFT analysis code under MIT/Unlicense
