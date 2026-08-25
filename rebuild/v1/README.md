# CLINE L1 Rebuild — Clean Branch

This isolated branch carries the corrected NOAA/DSCOVR-to-CME chain without overwriting any legacy LUFT file.

## Frozen analysis observable

- Protocol: `CLINE-L1-B24M-TRAIL-v1`
- Code version: `1.1.0`
- Observable: `chi_B24M`
- Baseline: prior-only trailing 24-hour median
- Coverage gate: 95%
- Clipping: none
- Supported magnetic frames: truthful GSM or truthful GSE inputs, one frame per file

## What changed

- NOAA fields are read by header name, never by row position.
- Historical GSE vectors remain labeled GSE.
- Values above 0.15, 1.0, and 2.0 are preserved.
- The old composite score is tagged `legacy_composite_score_v1`.
- Downstream users of the old score are listed in `DOWNSTREAM_RERUN_MANIFEST.yaml`.
- `downstream_input_guard.py` fails closed when a canonical analysis is pointed at a legacy-only or generic `chi` column.
- Source coverage is checked before epochs are paired.

## Test

```bash
python -m pip install -r requirements.txt
python -m pytest -q tests
```

The current package passes **23 tests**.

## Historical stress runs

NASA archive coverage is not identical for the two definitive DSCOVR products:

- definitive `DSCOVR_H0_MAG` continues through the May 2024 event;
- definitive `DSCOVR_H1_FC` Faraday-cup files in the frozen V1 inventory span 2016–2019.

Therefore the run plan is:

### 1. May 2024 magnetic-only stress test

```bash
python historical/run_epoch_batch.py \
  --run gannon_may_2024_dscovr_mag_only \
  --outdir runs/historical
```

No kinetic label is invented for this run.

### 2. September 2017 paired active-event test

```bash
python historical/run_epoch_batch.py \
  --run september_2017_dscovr_full \
  --outdir runs/historical
```

### 3. Data-selected quiet 30-day paired test

```bash
python historical/run_epoch_batch.py \
  --run quiet_dscovr_scan \
  --outdir runs/historical
```

The quiet selector uses plasma kinetics and coverage only; it never looks at magnetic χ while selecting the interval.

The historical downloader uses NASA CDAWeb REST CSV, preserves request descriptors and raw files, records SHA-256 hashes, and writes truthful one-minute GSE inputs. See `DATA_AVAILABILITY_AUDIT.md`, `HISTORICAL_INGEST_PROTOCOL_V1.md`, and `historical/epochs.yaml`.

## Existing audit record

- `EXAMINATION_PASS_2.md`
- `CLINE_L1_BASELINE_PROTOCOL_V1.md`
- `audit/legacy_estimator_audit.md`
- `runs/regression_7day_v11/`

The original timestamped V1 ZIP is preserved separately in the `LUFT_CLINE/rebuild_v1_audit` Google Drive folder. This clean package is commit-ready for `rebuild-v1-clean`; `main` remains untouched.
