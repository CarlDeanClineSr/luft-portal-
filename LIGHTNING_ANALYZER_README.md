# Lightning Storm Phase Analyzer

This directory contains tools for analyzing terrestrial atmospheric plasma phenomena (lightning) using the same χ boundary enforcement framework applied to CME storms, solar wind, QCD, black holes, and other plasma systems.

## Overview

The lightning analysis extends the  portal's universality principle to natural spark-gap physics. Lightning channels represent atmospheric plasma discharges that follow the same χ ≤ 0.15 boundary constraint observed across all plasma phenomena.

### Physics Connection

- **Lightning channels**: ~10^18 cm⁻³ density, ~30,000 K temperature
- **χ_proxy**: Normalized VLF amplitude perturbation (analogous to CME χ)
- **Expected behavior**: χ_proxy ≤ 0.15 at peak stroke events
- **Violations**: 0 expected (boundary enforced by physics)
- **Discrete events**: Lightning strokes show quantized energy transfer

## Scripts

### 1. Lightning Phase Analyzer (`lightning_phase_analyzer.py`)

Analyzes VLF/sferic recordings and classifies observations into storm phases:
- **PRE**: Buildup phase before lightning strokes
- **PEAK**: Discrete spark events hitting the χ boundary
- **POST**: Decay/recovery after stroke events

**Usage:**

```bash
# Process all files in data/lightning/
python scripts/lightning_phase_analyzer.py

# Process specific file
python scripts/lightning_phase_analyzer.py data/lightning/may_storm1.csv

# Custom output directory
python scripts/lightning_phase_analyzer.py data/lightning/ --output results/lightning
```

**Input Format:**

CSV files with columns:
- `timestamp`: ISO datetime or parseable string
- `peak_amplitude` or `vlf_amplitude` or `sferic_power`: raw measurement
- `baseline`: baseline level for normalization

Or pre-computed:
- `timestamp`
- `chi_proxy`: normalized perturbation

**Output:**

- `results/lightning_phases_{name}.csv`: Timestamped data with phase labels
- `results/lightning_summary_{name}.json`: Analysis summary with statistics

### 2. Whistler/Sferic Spectral Analyzer (`lightning_whistler_detector.py`)

Performs FFT analysis to detect spectral bands and gaps at χ multiples (0.3, 0.5, 0.6), similar to MMS nonlinear coupling observations.

**Usage:**

```bash
# Analyze spectrum
python scripts/lightning_whistler_detector.py data/lightning/may_storm1.csv

# With sampling rate
python scripts/lightning_whistler_detector.py data/lightning/may_storm1.csv --sampling-rate 44100
```

**Output:**

- `results/lightning_whistler_{name}.json`: Spectral features and χ matches

## Data Format

### HDSDR CSV Export

If using HDSDR for VLF recording:

1. Export peak detections or spectrogram data as CSV
2. Ensure columns include:
   - Timestamp
   - Amplitude or power measurement
   - Baseline reference

3. Place in `data/lightning/` directory

### Example Data

```csv
timestamp,peak_amplitude,baseline
2025-05-15T14:00:00,100.0,100.0
2025-05-15T14:00:01,102.0,100.0
2025-05-15T14:00:02,105.0,100.0
2025-05-15T14:00:03,110.0,100.0
2025-05-15T14:00:04,114.5,100.0
...
```

## GitHub Actions Workflow

The lightning analyzer runs automatically:

- **Schedule**: Daily at noon UTC (`0 12 * * *`)
- **Manual**: Via workflow_dispatch in GitHub Actions
- **Auto-commit**: Results pushed to `results/lightning_*`

See: `.github/workflows/lightning_analyzer.yml`

## Results Interpretation

### Phase Analysis

- **has_storm**: True if PEAK events detected
- **num_strokes**: Count of discrete lightning strokes
- **violations**: Should be 0 (χ_proxy ≤ 0.15 enforced)
- **pct_peak**: Typically small (brief discrete events)

### Spectral Analysis

- **bands**: Frequency bands with significant power
- **gaps**: Spectral gaps between bands
- **chi_matches**: Alignments with χ = 0.3, 0.5, 0.6
- Links to MMS nonlinear coupling observations

## Physics Validation

Expected results:
1. ✅ χ_proxy ≤ 0.15 during PEAK strokes
2. ✅ Zero boundary violations
3. ✅ Discrete stroke events (not continuous)
4. ✅ Spectral gaps at χ multiples (similar to MMS)

This proves universality: QCD → CME → Solar Wind → BH → vacuum QCD → Turbulence → **Lightning**

## Integration with  Portal

Lightning data becomes proof #7 for universality:
- Add to synthesis paper table
- Update unified dashboard
- Cross-reference with other plasma phenomena

## References

-  CME Boundary Ceiling: `capsules/CAPSULE_CME_BOUNDARY_CEILING_2025-12.md`
- Storm Phase Analyzer: `storm_phase_analyzer.py`
- MMS Nonlinear Coupling: See synthesis documents
