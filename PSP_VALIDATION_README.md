# PSP Multi-Encounter χ ≤ 0.15 Validation Pipeline

## Overview

This pipeline validates Carl Dean Cline Sr.'s χ ≤ 0.15 universal boundary discovery using Parker Solar Probe (PSP) data at extreme solar proximity (~0.08 AU, ~12 solar radii).

## Background

Carl Dean Cline Sr. discovered through empirical analysis that normalized magnetic field perturbations in space plasmas never exceed χ = 0.15, where:

```
χ = |B - B_baseline| / B_baseline ≤ 0.15
```

This boundary has been validated across:
- Earth's solar wind (DSCOVR, ACE): 12,000+ observations
- Mars orbit (MAVEN): 86,400+ observations
- Various other space environments

## Purpose

Testing at PSP distances validates whether this boundary is truly scale-invariant under extreme conditions:
- **Magnetic field**: 50-100x stronger than at Earth (~150-250 nT vs ~5 nT)
- **Plasma β**: Much lower (magnetic pressure dominated)
- **Temperature**: Electron temperature >> Proton temperature (inverted from 1 AU)
- **Turbulence**: "Pristine" cascades, less evolved than at Earth
- **Distance**: 0.08 AU (~12 solar radii) vs 1 AU

## Files

### Core Scripts

1. **`fetch_psp_encounter17.py`**
   - Downloads PSP FIELDS MAG L2 RTN data for specific encounters
   - Supports encounters 17-20 (Sep 2023 - Jun 2024)
   - Uses pyspedas (preferred) or cdasws (fallback)
   - Outputs CSV with timestamp, B_R, B_T, B_N columns

2. **`batch_psp_encounters.sh`**
   - Main orchestration script
   - Performs dependency checking
   - Downloads data for each encounter
   - Runs χ analysis on each dataset
   - Generates comprehensive summary report

3. **`chi_calculator.py`** (existing, enhanced)
   - Calculates χ parameter from magnetometer data
   - Now supports CSV format with RTN coordinates
   - Compatible with PSP data output

## Installation

### Requirements

- Python 3.7+
- Required packages:
  ```bash
  pip install pandas numpy pyspedas
  # OR (fallback)
  pip install pandas numpy cdasws
  ```

### Quick Install

```bash
# Install from requirements.txt
pip install -r requirements.txt
```

## Usage

### Process All Encounters (17-20)

```bash
bash batch_psp_encounters.sh
```

This will:
1. Check dependencies
2. Download PSP data for each encounter (~2-5 min per encounter)
3. Calculate χ for each dataset (~30 sec per encounter)
4. Generate summary report

**Total runtime**: ~15-20 minutes (with good internet connection)

### Process Specific Encounters

```bash
# Process Encounters 17 and 18 only
bash batch_psp_encounters.sh 17 18

# Process just Encounter 20
bash batch_psp_encounters.sh 20
```

### Fetch Individual Encounter Data

```bash
# Fetch Encounter 17 data
python fetch_psp_encounter17.py --encounter 17

# Fetch with custom output directory
python fetch_psp_encounter17.py --encounter 18 --output-dir my_data/psp
```

### Run χ Analysis Manually

```bash
python chi_calculator.py \
  --file data/psp/psp_encounter17_mag.csv \
  --time-col timestamp \
  --bx B_R \
  --by B_T \
  --bz B_N \
  --output results/encounter17_chi.csv
```

## Output Structure

```
-portal-/
├── data/psp/
│   ├── psp_encounter17_mag.csv      # Raw magnetic field data (RTN)
│   ├── psp_encounter18_mag.csv
│   ├── psp_encounter19_mag.csv
│   └── psp_encounter20_mag.csv
│
└── results/psp_validation/
    ├── encounter17_chi_analysis.txt       # Detailed χ analysis
    ├── encounter17_chi_processed.csv      # Processed data with χ values
    ├── encounter18_chi_analysis.txt
    ├── encounter18_chi_processed.csv
    ├── encounter19_chi_analysis.txt
    ├── encounter19_chi_processed.csv
    ├── encounter20_chi_analysis.txt
    ├── encounter20_chi_processed.csv
    └── multi_encounter_summary.txt        # MASTER SUMMARY
```

## Encounter Information

| Encounter | Perihelion Date | Distance | Date Range |
|-----------|----------------|----------|------------|
| 17 | 2023-09-27 | ~0.08 AU | 2023-09-22 to 2023-10-02 |
| 18 | 2023-12-29 | ~0.08 AU | 2023-12-24 to 2024-01-03 |
| 19 | 2024-03-30 | ~0.08 AU | 2024-03-25 to 2024-04-04 |
| 20 | 2024-06-30 | ~0.08 AU | 2024-06-25 to 2024-07-05 |

Each encounter window spans perihelion ± 5 days for comprehensive coverage.

## Expected Results

If χ ≤ 0.15 is truly universal, we expect:
- **Zero violations** (χ > 0.15) across all ~1.2M observations
- **Boundary clustering**: ~50-53% of observations at χ = 0.145-0.155
- **Maximum χ**: ~0.143-0.149 (near but not exceeding 0.15)

### Success Criteria

✅ **Boundary Confirmed**: Zero violations across all encounters
- Validates scale-invariance across 12 orders of magnitude
- Supports fundamental constraint on plasma dynamics

⚠️ **Violations Detected**: χ > 0.15 observed
- Indicates temperature/mass-ratio dependence
- Still valuable scientific finding about boundary conditions

## Data Provenance

- **Mission**: Parker Solar Probe (PSP)
- **Instrument**: FIELDS/MAG (Fluxgate Magnetometer)
- **Data Level**: Level 2 (calibrated, science-ready)
- **Coordinates**: RTN (Radial-Tangential-Normal)
- **Source**: NASA CDAWeb / SPDF
- **Cadence**: Resampled to 1-minute for consistency

## Troubleshooting

### "Neither pyspedas nor cdasws installed"

```bash
pip install pyspedas
# OR
pip install cdasws
```

### "No data available for the requested time range"

This may occur if:
- Data hasn't been publicly released yet
- CDAWeb is temporarily unavailable
- Network connectivity issues

Try:
- An earlier encounter (17-18 are older and fully public)
- Checking [NASA CDAWeb](https://cdaweb.gsfc.nasa.gov/) for data availability
- Running again later

### Download takes too long

- Each encounter downloads ~300,000 data points (~5-10 MB)
- Typical download time: 2-5 minutes per encounter
- If consistently slow, check your internet connection

## References

- Discovery: Carl Dean Cline Sr., November 2025
- Location: Lincoln, Nebraska, USA
- Email: CARLDCLINE@GMAIL.COM
- Repository: https://github.com/CarlDeanClineSr/-portal-

## Citation

If you use this pipeline or validate the χ ≤ 0.15 boundary:

```
Cline Sr., C. D. (2025). Universal χ ≤ 0.15 boundary in space plasma 
perturbations: Validation at extreme solar proximity using Parker Solar Probe. 
https://github.com/CarlDeanClineSr/-portal-
```

## License

See LICENSE file in repository root.

## Help

```bash
# Get help for batch script
bash batch_psp_encounters.sh --help

# Get help for fetch script
python fetch_psp_encounter17.py --help

# Get help for chi calculator
python chi_calculator.py --help
```

## Contact

For questions about the χ ≤ 0.15 discovery or this validation pipeline:
- Email: CARLDCLINE@GMAIL.COM
- Repository Issues: https://github.com/CarlDeanClineSr/-portal-/issues
