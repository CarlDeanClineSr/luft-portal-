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
- GSE historical vectors remain labeled GSE.
- Values above 0.15, 1.0, and 2.0 are preserved.
- The old composite score is tagged `legacy_composite_score_v1`.
- Downstream users of the old score are listed in `DOWNSTREAM_RERUN_MANIFEST.yaml`.
- `downstream_input_guard.py` fails closed when a canonical analysis is pointed at a legacy-only or generic `chi` column.

## Test

```bash
python -m pip install -r requirements.txt
python -m pytest -q tests
```

## Historical data stress runs

CDAWeb sources and variables are frozen in `HISTORICAL_INGEST_PROTOCOL_V1.md` and `historical/epochs.yaml`.

Run the May 2024 storm interval:

```bash
python historical/run_epoch_batch.py \
  --run gannon_storm_may_2024 \
  --outdir runs/historical
```

Select a quiet 30-day window from kinetics only, then run it:

```bash
python historical/run_epoch_batch.py \
  --run quiet_solar_minimum_scan \
  --outdir runs/historical
```

The historical downloader requires network access and installs `cdasws`, `cdflib`, and `xarray`. Magnetic data are downloaded from definitive one-second DSCOVR MAG data, quality-checked, and reduced to one-minute GSE component means. Plasma uses the one-minute DSCOVR Faraday-cup product with strict `DQF == 0` selection.

## Existing V1 audit record

- `EXAMINATION_PASS_2.md`
- `CLINE_L1_BASELINE_PROTOCOL_V1.md`
- `audit/legacy_estimator_audit.md`

The full timestamped V1 package is also preserved separately in the `LUFT_CLINE/rebuild_v1_audit` Google Drive folder.
