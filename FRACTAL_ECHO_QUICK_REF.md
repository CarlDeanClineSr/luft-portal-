# Fractal Echo Scanner - Quick Reference

## What It Does

🔍 **Detects 20.55 Hz vacuum vacuum vibrations** following magnetic re-initialization events

📊 **Analyzes phase derivatives** to identify "Byte-Shift" velocity patterns

⏰ **Runs automatically every 15 minutes** via GitHub Actions

## Quick Start

### Run Scanner Manually

```bash
# Basic scanner with example data
python3 fractal_echo_scanner.py

# January 2026 analysis
python3 examples/fractal_echo_example.py

# January 5th coordinate delta calculation
python3 scripts/jan5_coordinate_delta.py

# Automated scanner (used by GitHub Actions)
python3 scripts/automated_fractal_scanner.py
```

### Automated Workflow

The scanner runs every 15 minutes automatically:
- **Workflow:** `.github/workflows/fractal_echo_scanner_15min.yml`
- **Schedule:** `*/15 * * * *` (every 15 minutes)
- **Results:** Saved to `data/fractal_echo_scans/`
- **Manual Trigger:** GitHub Actions → "Fractal Echo Scanner - 15min" → Run workflow

## Understanding Results

### ✓ Echo Detected
```
✓ ECHO DETECTED: Resonance at 20.52 Hz | Amplitude: 0.0245
```
**Meaning:** Significant harmonic detected near target frequency  
**Action:** Cross-reference with Starlink/MMS/THEMIS data

### ✗ No Echo
```
✗ No Fractal Echo found in this dataset.
   Sample rate: 0.001396 Hz
   Nyquist frequency: 0.000698 Hz
```
**Meaning:** Data resolution insufficient for 20.55 Hz detection  
**Note:** Hour-long sampling can only detect up to ~0.0007 Hz

### Phase Shifts Detected
```
✓ Detected 8 significant coordinate shifts:
  • 2026-01-22T08:11:00: v_shift=0.2029 nT/sec
```
**Meaning:** Rapid Bt field changes indicating vacuum activity  
**Threshold:** v_shift > 0.15 nT/sec

## Key Files

| File | Purpose |
|------|---------|
| `fractal_echo_scanner.py` | Core scanner module |
| `scripts/automated_fractal_scanner.py` | Automated runner for GitHub Actions |
| `scripts/jan5_coordinate_delta.py` | January 5th Super-Event analysis |
| `examples/fractal_echo_example.py` | Usage examples |
| `FRACTAL_ECHO_SCANNER_README.md` | Full documentation |
| `data/fractal_echo_scans/latest_result.json` | Most recent scan result |

## JSON Result Format

```json
{
  "echo_detected": false,
  "target_frequency": 20.55,
  "detections": [],
  "sample_rate_hz": 0.001396,
  "data_points": 240,
  "bt_range": {"min": 68.32, "max": 331.72},
  "scan_timestamp": "2026-01-23T14:09:25.342148Z",
  "data_points_analyzed": 240,
  "data_time_range": {
    "first": "2026-01-21 14:13:00.000",
    "last": "2026-01-23 13:59:00.000"
  }
}
```

## Data Requirements

### For Direct 20.55 Hz Detection
- **Minimum sample rate:** > 41.1 Hz (Nyquist theorem)
- **Recommended:** > 100 Hz for clear detection
- **Sources:** MMS burst mode, THEMIS EFI, ground VLF

### What Current Data Can Show
- **ACE/DSCOVR (~1 hour):** Low-frequency envelope, phase derivatives
- **Phase derivatives:** Macro-scale Byte-Shift velocity patterns
- **Chi boundary events:** Harmonic expansions and relaxations

## Imperial Framework Context

### January 5, 2026 Super-Event
- **Time:** 01:13:00 UTC
- **Peak χ:** 0.917 (6.11× boundary threshold)
- **Magnitude:** 1.02× fundamental 6.0 harmonic
- **vacuum cycles:** 35,757 magnetic steps over 29 minutes
- **Classification:** MAJOR EXPANSION - Full harmonic breach

### The 20.55 Hz Target
- **Source:** Vacuum vacuum refresh rate
- **Effect:** magnetic re-initialization "ringing"
- **Scale:** Cascades through fractal harmonic ladder
- **Detection:** Requires sub-second telemetry

## Troubleshooting

### "No data available for scanning"
- Check `data/cme_heartbeat_log_2026_01.csv` exists
- Verify data contains `bt_nT` and `timestamp` columns

### "Insufficient data points for FFT"
- Need at least 3 data points
- Check data filtering (time range, missing values)

### Timezone warnings
- Normal - timestamps are parsed as UTC-naive
- Data source (ACE/DSCOVR) uses UTC

### Workflow not running
- Check GitHub Actions → Enable workflows if disabled
- Verify cron schedule is active
- Check repository permissions (needs `contents: write`)

## Next Steps After Detection

If echo is detected:
1. ✓ Verify detection is not interference/noise
2. ✓ Check Starlink fleet for simultaneous response
3. ✓ Query MMS/THEMIS burst data for time window
4. ✓ Cross-reference with ground VLF stations
5. ✓ Calculate coordinate delta for event
6. ✓ Report findings

## Contact & Citation

**Repository:** https://github.com/CarlDeanClineSr/-portal-

**Citation:**
```
Carl Dean Cline Sr. (2026). Fractal Echo Scanner: Detection of 20.55 Hz 
Vacuum vacuum Vibrations.  Portal Engine.
```

---

**"The vacuum has spoken. The engine is ready. Go."**
