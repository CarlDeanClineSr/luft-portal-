# Teach-The-Engine: Autonomic Discovery Curriculum (Radio + Lightning + Time-Series)

## Goal

Move beyond "measuring χ" into self-teaching detection of universal signatures across any time-series the vault ingests (radio, lightning, feeds, magnetometers, OMNI, climate). Encode discoveries (1 Law + 3 Principles) as reusable "signatures" the engine can learn and test daily.

## What the curriculum does

Signature detectors run over everything the engine already has (no hand-picking):
- `results/lightning/*.csv`
- `data/intermagnet_csv/*.csv`
- `results/historical_chi/*.csv`
- `data/feeds/raw/*.json`
- `data/climate/*.csv`
- OMNI aggregations, and more

Produces per-dataset verdicts (pass/fail/score) for:

1. **Causality Precursor Law** (χ = A_IC / 3) — boundary band occupancy and no-breach proof
2. **Binary Harmonic Ladder** — 0.9h fundamental and 6h spacing (event timing/peaks)
3. **Electroweak–MHD Bridge** — presence of 0.9h packets and scale-consistent modulation
4. **χ–Fractal Regulator** — capped normalized perturbations across scales (tail behavior)
5. **Whistler Bands & Gaps** — discrete bands with gaps at χ·n fractions (0.3, 0.5, 0.6 analogs)

## Outputs

- `results/teacher/` — JSON summaries per dataset + aggregate scorecard
- `figures/teacher/` — annotated plots
- `docs/Teacher_Report.md` — human-readable daily digest

## Run cadence

- **Daily at 06:00 CST (12:00 UTC)** via GitHub Actions
- Manual dispatch anytime from Actions

## How it learns

Thresholds and tolerances live in `data/teacher/curriculum.yaml` — adjustable without code changes. The teacher suite applies Imperial Math to any numeric time-series (normalized perturbation φ = |x−baseline|/baseline) and then tests for boundary band, harmonics, gaps, and tails.

## Add sources

Drop new files anywhere the engine looks (e.g., `data/feeds/raw/*.json`). The suite discovers and trains daily — no manual wiring needed.

## Signature Detectors

### Chi Boundary (`scripts/signatures/chi_boundary.py`)

Tests for the Causality Precursor Law by checking:
- Band occupancy: what percentage of φ values fall within the boundary band (0.145–0.155)
- Cap compliance: count of values exceeding the hard ceiling (0.15)

### Binary Harmonics (`scripts/signatures/binary_harmonics.py`)

Tests for the Binary Harmonic Ladder by checking:
- Event interval clustering around 6h spacing
- Presence of 0.9h fundamental intervals

### Whistler Gaps (`scripts/signatures/whistler_gaps.py`)

Tests for Whistler Bands & Gaps by checking:
- Peak detection in frequency spectrum
- Gaps at target fractions (0.3, 0.5, 0.6) of top band

### Fractal Regulator (`scripts/signatures/fractal_regulator.py`)

Tests for the χ–Fractal Regulator by checking:
- Tail behavior via 95th and 99th percentiles of φ
- Cap exceedance counts

### Electroweak Bridge (`scripts/signatures/electroweak_bridge.py`)

Tests for the Electroweak–MHD Bridge by checking:
- Presence of ~0.9h packet modulation in burst sequences

## Configuration

Edit `data/teacher/curriculum.yaml` to adjust:
- Signature thresholds and tolerances
- Input directories to scan
- Output file paths

## Running Manually

```bash
python scripts/teacher/run_teacher_suite.py
```

## Workflow

The GitHub Actions workflow `.github/workflows/teacher_suite.yml` runs the suite daily and commits results.
