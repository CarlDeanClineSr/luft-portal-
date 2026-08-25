# Historical DSCOVR Ingest Protocol V1

## Identity

- Ingest ID: `CDAWEB-DSCOVR-RESTCSV-1M-v1`
- Analysis ID: `CLINE-L1-B24M-TRAIL-v1`
- Purpose: produce truthful, one-minute historical DSCOVR inputs for the frozen magnetic χ calculation.

## Authoritative sources

### Magnetic

- CDAWeb dataset: `DSCOVR_H0_MAG`
- Variables: `B1GSE`, `B1F1`, `FLAG1`
- Native cadence: one second
- Native coordinate frame: GSE

### Plasma

- CDAWeb dataset: `DSCOVR_H1_FC`
- Variables: `V_GSE`, `Np`, `THERMAL_TEMP`, `DQF`
- Native cadence: one minute
- Native coordinate frame: GSE

## Magnetic transformation

1. Download one day at a time.
2. Preserve a compressed row extraction for every chunk.
3. Retain only finite rows with `FLAG1 == 0` for the one-minute product.
4. At native cadence, compare `B1F1` with `sqrt(B1GSE_x²+B1GSE_y²+B1GSE_z²)` as a diagnostic, not as an equality filter. `B1F1` is an average of magnitudes while `B1GSE` is an averaged vector, so exact equality is not required. Large negative `B1F1 - |B1GSE|` values are flagged for inspection.
5. Compute arithmetic means of each GSE vector component by UTC minute.
6. Require at least 45 valid one-second rows in each emitted minute.
7. Name the output columns `bx_gse`, `by_gse`, and `bz_gse`.
8. Do not rename GSE to GSM.
9. Do not pass the mean of native magnitudes as provider `bt` to the analysis chain, because mean magnitude and magnitude of the mean vector are different operations.

## Plasma transformation

1. Preserve all extracted rows and `DQF` values in compressed chunk files.
2. The strict canonical plasma CSV retains `DQF == 0` only.
3. A separate sensitivity CSV retains non-fill `DQF` values 0–3; it is never silently pooled with the strict product.
4. Calculate scalar speed from the GSE velocity vector.
5. Retain density, temperature, vector components, source dataset, and quality flag.

## Quiet-window selection

The quiet interval is selected before magnetic χ is calculated. Candidate 30-day windows must pass the configured coverage gate. Eligible windows are ordered by:

1. kinetic transient fraction;
2. 95th-percentile speed;
3. 95th-percentile density;
4. median dynamic pressure.

The kinetic flag uses speed, density, and a time-aligned one-hour speed difference. No magnetic χ value is used in selection.

## Active-event intervals

### May 2024 magnetic-only stress test

`2024-05-08T00:00:00Z` through `2024-05-15T00:00:00Z` is retained as a DSCOVR MAG stress interval. It is magnetic-only because the frozen definitive H1 Faraday-cup inventory ends in 2019. No kinetic class is inferred for this run.

### September 2017 paired stress test

`2017-09-05T00:00:00Z` through `2017-09-12T00:00:00Z` is the first paired active-event interval because both definitive DSCOVR products coexist.

### Quiet scan

The kinetic-only selector searches `2018-04-01T00:00:00Z` through `2020-01-01T00:00:00Z` and chooses one complete 30-day interval before magnetic χ is evaluated.

## Preservation rule

Raw chunk extractions, download manifests, canonical input CSVs, row-level analysis output, summaries, and plots are append-only. A revised ingest method receives a new ingest ID; it does not replace V1.
