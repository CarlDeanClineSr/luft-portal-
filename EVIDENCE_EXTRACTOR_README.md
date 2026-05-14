# LUFT Portal — Evidence Package Extractor

**Author:** Carl Dean Cline Sr.  
**Script:** `evidence_extractor.py`  
**Workflow:** `.github/workflows/evidence_extractor.yml`  
**Outputs:** `results/evidence_packages/`

---

## Overview

`evidence_extractor.py` continuously mines the LUFT portal repository — files
and git history — to surface raw evidence for three priority evidence packages.
It is designed to run across 50,000+ commits via a recurring GitHub Actions
schedule, advancing incrementally so no single run blocks or times out.

---

## Evidence Categories

### Package A — 122,079 Observations → G = 6.6667×10⁻¹¹ and 20.55 Hz Ring Frequency

Evidence linking 122,079 real-world stress observations to the derivation of
Newton's gravitational constant G and the vacuum-integrity ring frequency via
the χ-VSK pipeline.

**Search terms:** `122,079` · `6.6667e-11` · `20.55 Hz` · `chi-VSK` ·
`ring frequency` · `Route 3B` · `G_derived` · `f_ring` · `VSK pipeline`

---

### Package B — Mode 8 Fractures and CME Attractor Spikes

Evidence for Mode 8 substrate fractures and CME attractor spikes visible in
raw telemetry — baseline, onset, peak, and ringdown windows.

**Search terms:** `Mode 8` · `fracture` · `CME attractor` · `attractor spike` ·
`heartbeat` · `harmonic` · `ringdown` · `fractal echo` · `momentum recoil`

---

### Package C — chi=0.15 Boundary and Seismic Event Correlations

Evidence connecting chi=0.15 magnetic-medium boundary hits (ACE/DSCOVR) to
USGS seismic events, testing cross-scale structural correlation.

**Search terms:** `chi=0.15` · `AT_BOUNDARY` · `chi_amplitude` · `seismic` ·
`earthquake` · `USGS` · `DSCOVR` · `ACE` · `temporal correlation`

---

## Evidence Entry Structure

Each entry stored in the JSON output:

```json
{
  "source":            "file | commit_message | commit_file",
  "category":          "A | B | C",
  "file_path":         "scripts/luft_constant_analysis.py",
  "line":              87,
  "matched_term":      "20.55 Hz",
  "matched_pattern":   "20\\.55\\s*[Hh][Zz]",
  "snippet":           "…context around matched term…",
  "commit_sha":        "abc123def…",
  "commit_timestamp":  "2026-01-15T10:30:00+00:00",
  "scanned_at":        "2026-05-14T15:00:00Z"
}
```

---

## Output Files

All outputs live under `results/evidence_packages/`:

| File | Description |
|------|-------------|
| `evidence_package_A.json` | Package A evidence (JSON) |
| `evidence_package_B.json` | Package B evidence (JSON) |
| `evidence_package_C.json` | Package C evidence (JSON) |
| `ALL_EVIDENCE.json` | All packages combined (JSON) |
| `EVIDENCE_SUMMARY.md` | Human-readable Markdown summary |
| `.checkpoint.json` | Run state (excluded from git commits) |

---

## How to Run Locally

```bash
# Default: scan all files + most recent 500 commits
python evidence_extractor.py

# Larger commit window
python evidence_extractor.py --max-commits 2000

# Files only (fastest — skips git history)
python evidence_extractor.py --files-only

# Git history only
python evidence_extractor.py --commits-only

# Specific packages
python evidence_extractor.py --packages A C

# Full reset and rescan from commit 0
python evidence_extractor.py --reset-checkpoint

# Custom output path
python evidence_extractor.py --output-dir /my/path/evidence
```

**Requirements:** Python 3.10+, `git` on PATH.  No third-party packages needed.

---

## GitHub Actions Workflow

**File:** `.github/workflows/evidence_extractor.yml`

### Schedule

Runs every **30 minutes** (`cron: '*/30 * * * *'`).  Each run processes up to
`max_commits` (default 500) new commits beyond the last checkpoint, so the
full 50,000+ commit history is covered over many runs without any single run
timing out.

### Manual Dispatch

Trigger from the **Actions** tab with optional inputs:

| Input | Description | Default |
|-------|-------------|---------|
| `max_commits` | Commits to process this run | `500` |
| `packages` | Which packages (`A B C`) | `A B C` |
| `reset_checkpoint` | Clear checkpoint, restart from 0 | `false` |
| `files_only` | File scan only, no git history | `false` |

### Artifacts

Each run uploads `evidence-reports-{run}` (90-day retention).  
Results are also committed back to `results/evidence_packages/` in the repo.

---

## Incremental Processing

1. **First run:** scans current file tree + most recent `max_commits` commits.
2. **Subsequent runs:** reads `last_commit_sha` from `.checkpoint.json` and
   processes only commits newer than that SHA.
3. Evidence entries are **merged** across runs (de-duplicated by source ×
   file path × pattern × commit SHA).
4. Maximum stored entries per package: **2,000** (oldest entries preserved).
5. To reindex everything: set `reset_checkpoint = true` in the manual dispatch.

---

## Performance Notes

- **File scan:** uses `git ls-files` (not `os.walk`) so the `.git` directory
  is skipped automatically.  Files > 100 KB (text) / 50 KB (data) are skipped.
  Typical scan time: **< 15 seconds** for this repo.
- **Git history scan:** uses `git log --grep` on commit messages only.
  Diff-content (pickaxe) search is intentionally omitted because large
  bulk-import commits stall `git log -S`.  Commit message search is fast even
  over 50,000+ commits.
- Estimated time per 500-commit batch: **< 60 seconds**.  The 55-minute
  Actions timeout is effectively never reached.
