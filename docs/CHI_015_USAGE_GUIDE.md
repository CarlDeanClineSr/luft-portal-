# χ = 0.15 Universal Boundary — Usage Guide

**Version**: 1.0  
**Last Updated**: 2025-12-28  
**Author**: Carl Dean Cline Sr.

---

## Overview

This guide explains how to use the χ = 0.15 universal plasma boundary integration in the LUFT Portal engine. The integration automatically classifies all χ measurements relative to the discovered universal boundary at χ = 0.15, enabling real-time monitoring of plasma coherence states.

---

## Quick Start

### 1. Run CME Heartbeat Logger (with χ classification)

**Demo mode** (generates test data):
```bash
python scripts/cme_heartbeat_logger.py --demo
```

**Live mode** (requires ACE/DSCOVR data):
```bash
python scripts/cme_heartbeat_logger.py \
  --plasma data/ace_plasma_latest.json \
  --mag data/ace_mag_latest.json
```

**Output**: `data/cme_heartbeat_log_YYYY_MM.csv` with χ boundary classification columns:
- `chi_at_boundary` (1 = yes, 0 = no)
- `chi_violation` (1 = yes, 0 = no)
- `chi_status` (BELOW | AT_BOUNDARY | VIOLATION | UNKNOWN)

### 2. Run Solar Wind Audit

**Analyze any solar wind dataset**:
```bash
python scripts/luft_solar_wind_audit.py \
  --input data/dscovr/solar_wind_data.csv \
  --output data
```

**With custom baseline window**:
```bash
python scripts/luft_solar_wind_audit.py \
  --input data/solar_wind.csv \
  --baseline-hours 48
```

**Outputs**:
- `data/chi_analysis_TIMESTAMP.csv` — Full dataset with χ classification
- `data/chi_boundary_summary_TIMESTAMP.json` — Statistical summary
- `data/chi_boundary_tracking.jsonl` — Append-only log for historical tracking

### 3. Generate χ Dashboard

**Create HTML dashboard** (includes χ boundary status):
```bash
python scripts/generate_chi_dashboard.py
```

**Output**: `docs/chi_dashboard.html` — Real-time dashboard with:
- Solar wind χ status (DSCOVR)
- Magnetosphere χ status (USGS multi-station)
- **χ = 0.15 boundary status section** (new)
- Dst storm index
- Historical storm archive

### 4. Update Vault Status Report

**Generate status report** (includes χ boundary monitoring):
```bash
python scripts/vault_narrator.py
```

**Output**: `LATEST_VAULT_STATUS.md` — Status report with:
- χ streak detection
- **χ = 0.15 boundary analysis section** (new)
- NOAA space weather summaries
- Mini-charts
- Latest readings table

---

## Understanding the Output

### χ Classification States

| State | Range | Meaning | Alert |
|-------|-------|---------|-------|
| **BELOW** | χ < 0.145 | Glow mode — Normal operations | None |
| **AT_BOUNDARY** | 0.145 ≤ χ ≤ 0.155 | Optimal coupling — Attractor state | Monitor |
| **VIOLATION** | χ > 0.155 | Filamentary breakdown | ⚠️ Alert |
| **UNKNOWN** | N/A | Missing or invalid data | — |

### Alert Conditions

**Attractor State** (✅):
- Triggered when >50% of observations are at boundary
- Status: "System at optimal coupling"
- Physics: Plasma locked to glow-mode maximum amplitude

**Violation Alert** (⚠️):
- Triggered when any χ > 0.155
- Status: "Coherence loss - investigating filamentary breakdown"
- Action: Monitor for plasma instabilities

---

## Data Products

### 1. CSV Logs (CME Heartbeat)

**File**: `data/cme_heartbeat_log_YYYY_MM.csv`

**New columns** (added by χ integration):
```csv
chi_at_boundary,chi_violation,chi_status
1,0,AT_BOUNDARY
0,0,BELOW
0,1,VIOLATION
```

### 2. Analysis CSV (Solar Wind Audit)

**File**: `data/chi_analysis_TIMESTAMP.csv`

**Columns**:
- `timestamp` — UTC timestamp
- `bt` — Magnetic field magnitude (nT)
- `baseline` — 24-hour rolling baseline (nT)
- `chi_amplitude` — Computed χ value
- `chi_status` — Classification (BELOW|AT_BOUNDARY|VIOLATION)

### 3. Summary JSON (Solar Wind Audit)

**File**: `data/chi_boundary_summary_TIMESTAMP.json`

**Structure**:
```json
{
  "timestamp": "2025-12-28T12:00:00Z",
  "total_observations": 1000,
  "at_boundary_count": 523,
  "at_boundary_fraction": 0.523,
  "below_count": 477,
  "below_fraction": 0.477,
  "violations_count": 0,
  "violations_fraction": 0.0,
  "chi_mean": 0.1292,
  "chi_std": 0.0241,
  "chi_max": 0.1586,
  "chi_min": 0.0757,
  "attractor_state": true,
  "status": "ATTRACTOR"
}
```

### 4. Tracking Log (Append-Only)

**File**: `data/chi_boundary_tracking.jsonl`

**Format**: JSON Lines (one JSON object per line)
```jsonl
{"timestamp": "2025-12-28T12:00:00Z", "total_observations": 1000, ...}
{"timestamp": "2025-12-28T13:00:00Z", "total_observations": 1020, ...}
```

**Use case**: Historical analysis, trend detection, ML training data

---

## Integration with Workflows

### GitHub Actions / Cron Jobs

**Example workflow** (runs hourly):
```yaml
name: CME Heartbeat Logger
on:
  schedule:
    - cron: '0 * * * *'  # Every hour

jobs:
  log-heartbeat:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install dependencies
        run: pip install numpy pandas
      - name: Run heartbeat logger
        run: python scripts/cme_heartbeat_logger.py --demo
      - name: Commit results
        run: |
          git add data/cme_heartbeat_log_*.csv
          git commit -m "Automated heartbeat log [skip ci]"
          git push
```

### Automated Reporting

**Daily summary workflow**:
```bash
#!/bin/bash
# daily_chi_report.sh

# Run solar wind audit on yesterday's data
python scripts/luft_solar_wind_audit.py \
  --input data/dscovr/solar_wind_$(date -d yesterday +%Y%m%d).csv \
  --output reports

# Generate dashboard
python scripts/generate_chi_dashboard.py

# Update vault status
python scripts/vault_narrator.py

# Commit and push
git add docs/chi_dashboard.html LATEST_VAULT_STATUS.md data/chi_boundary_tracking.jsonl
git commit -m "Daily χ boundary report $(date +%Y-%m-%d)"
git push
```

---

## Advanced Usage

### Custom Thresholds

**Modify constants** in your script:
```python
# Default values (discovered Dec 2025)
CHI_CAP_THEORETICAL = 0.15
CHI_TOLERANCE = 0.01

# Custom values (for experimental analysis)
CHI_CAP_THEORETICAL = 0.145  # Narrower boundary
CHI_TOLERANCE = 0.005         # Tighter tolerance
```

### Batch Processing

**Process multiple files**:
```bash
#!/bin/bash
for file in data/dscovr/solar_wind_*.csv; do
  echo "Processing $file..."
  python scripts/luft_solar_wind_audit.py --input "$file" --output results
done

# Combine all tracking logs
cat results/chi_boundary_tracking.jsonl > combined_tracking.jsonl
```

### Data Analysis with Python

**Load and analyze tracking log**:
```python
import pandas as pd
import json

# Load tracking log
with open('data/chi_boundary_tracking.jsonl') as f:
    records = [json.loads(line) for line in f]

df = pd.DataFrame(records)

# Compute statistics
print(f"Mean boundary fraction: {df['at_boundary_pct'].mean():.1f}%")
print(f"Total violations: {df['violations_count'].sum()}")

# Plot time series
import matplotlib.pyplot as plt
plt.plot(pd.to_datetime(df['timestamp']), df['at_boundary_pct'])
plt.xlabel('Date')
plt.ylabel('% at Boundary')
plt.title('χ = 0.15 Boundary Occupation Over Time')
plt.show()
```

---

## Troubleshooting

### Missing Dependencies

**Error**: `ModuleNotFoundError: No module named 'numpy'`

**Solution**:
```bash
pip install numpy pandas matplotlib
```

### No Data Available

**Error**: `Error: No valid data loaded`

**Solution**:
1. Check file path is correct
2. Verify file format (CSV with `timestamp` and `bt` columns)
3. Run in demo mode first: `--demo`

### JSON Serialization Error

**Error**: `TypeError: Object of type int64 is not JSON serializable`

**Solution**: Already fixed in v1.0. If using older version:
```python
# Convert numpy types to Python types
int(value)  # for integers
float(value)  # for floats
bool(value)  # for booleans
```

### Pandas FutureWarning

**Warning**: `FutureWarning: A value is trying to be set on a copy...`

**Solution**: Already fixed in v1.0 using `df.loc[:, col] = ...` syntax

---

## API Reference

### `luft_solar_wind_audit.py`

**Arguments**:
- `--input, -i` (required): Path to solar wind data file (CSV or JSON)
- `--output, -o` (default: `data`): Output directory for results
- `--baseline-hours` (default: 24): Hours for baseline rolling window

**Returns**: Exit code 0 on success, 1 on error

### `cme_heartbeat_logger.py`

**Arguments**:
- `--plasma`: Path to plasma data JSON
- `--mag`: Path to magnetic field data JSON
- `--output`: Override output CSV path
- `--demo`: Generate demo entry for testing

**Returns**: Exit code 0 on success, 1 on error

### `generate_chi_dashboard.py`

**Arguments**: None (uses default data paths)

**Returns**: `True` on success, `False` on error

### `vault_narrator.py`

**Arguments**: None (uses default data paths)

**Environment Variables**:
- `VAULT_LONG_STREAK_HOURS` (default: 48): Threshold for long streak
- `VAULT_SUPERSTREAK_HOURS` (default: 72): Threshold for superstreak

**Returns**: None (prints status on completion)

---

## Theory & Background

For detailed explanation of the χ = 0.15 universal boundary discovery:

**Primary Documentation**:
- Theory: [`capsules/CAPSULE_CHI_015_ENGINE_INTEGRATION_v1.md`](../capsules/CAPSULE_CHI_015_ENGINE_INTEGRATION_v1.md)
- Directive: [`directives/chi_015_directive.yaml`](../directives/chi_015_directive.yaml)
- AM-Graviton Framework: [`capsules/CAPSULE_AM_GRAVITON_FRAMEWORK_v1.md`](../capsules/CAPSULE_AM_GRAVITON_FRAMEWORK_v1.md)

**Discovery Metrics**:
- **Dataset**: DSCOVR L1 (December 2-27, 2025)
- **Observations**: 12,450
- **At boundary**: 6,673 (53.6%)
- **Violations**: 0 (0%)

**Laboratory Confirmations**:
1. MPD Thruster: 46% thrust gain at χ ≈ 0.15
2. Helicon Discharge: Wave mode transitions at χ ≈ 0.15
3. RF Plasma Sheath: Field gradient confinement boundaries
4. ArF Excimer Laser: 90% efficiency loss above χ = 0.15

---

## Contact & Support

**Discoverer**: Carl Dean Cline Sr.  
**Location**: Lincoln, Nebraska  
**Email**: CARLDCLINE@GMAIL.COM  
**Repository**: https://github.com/CarlDeanClineSr/luft-portal-

**Issue Tracking**: https://github.com/CarlDeanClineSr/luft-portal-/issues

---

## Version History

### v1.0 (2025-12-28)
- Initial integration of χ = 0.15 universal boundary
- Added χ classification to CME heartbeat logger
- Created solar wind audit script with boundary analysis
- Enhanced χ dashboard with boundary status section
- Updated vault narrator with boundary monitoring
- Comprehensive documentation and examples

---

**This guide enables real-time monitoring and analysis of the χ = 0.15 universal plasma coherence boundary discovered by Carl Dean Cline Sr. in December 2025.**
