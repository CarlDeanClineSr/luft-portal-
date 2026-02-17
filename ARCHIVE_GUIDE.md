#  Archive Guide

## Purpose
This guide explains the archive layout and how to find, request, and cite raw data and historic materials that are not present in the Portal.

## Archive Strategy (Updated January 2026)

### Active Repository Goals
- **Current Size:** ~1.3GB
- **Target Size:** ~100-300MB (fast clone, lean working copy)
- **Strategy:** Archive historical transcripts and large data files separately
- **Benefit:** Faster clones, cleaner structure, easier for new contributors

### What Stays in Active Repo
✅ **Keep These:**
- Current heartbeat logs (last 30-60 days)
- Live dashboards and HTML pages
- Core analysis scripts (chi_calculator.py, temporal_miner.py, etc.)
- Essential proof pack and documentation
- Published papers and capsules
- Workflow configurations (.github/workflows)
- Latest data snapshots for dashboards

### What Gets Archived
📦 **Move to Archive Repo:**
- Historical "New Text Document" transcripts (22 files, ~50MB)
  - These document Carl's discovery process with AI assistants
  - Valuable historical record but not needed for daily operations
- Old CSV data (>6 months old)
- Raw audio recordings (WAV files, ~80MB)
- Historical figures and charts (old versions)
- Backup data files
- Large external dataset caches

### Archive Repository Plan
**New Archive Repo:** `CarlDeanClineSr/-portal-archive`
- **Purpose:** Long-term storage of historical data and transcripts
- **Access:** Public (for transparency) or private (if preferred)
- **Size:** ~1GB of historical materials
- **Organization:**
  ```
  /transcripts/          - "New Text Document" chat logs
  /data/historical/      - Old CSVs and data files
  /recordings/           - WAV files from SDR work
  /figures/archive/      - Old visualizations
  /backups/              - Historical backups
  README.md              - Index and citation guide
  ```

## Top-level Organization (Active Repo)

- `/data/` — Current instrument logs, CSVs, experimental outputs (last 30-60 days)
- `/scripts/` — All analysis scripts and automation
- `/docs/` — Documentation, proof packs, guides
- `/capsules/` — Current discovery capsules
- `index.html` + dashboards — Live web interface
- `.github/workflows/` — Automation workflows
- `README.md` — Main entry point

## How to Access Archive Materials

### Option 1: Clone Archive Repository
```bash
git clone https://github.com/CarlDeanClineSr/-portal-archive.git
```

### Option 2: Request Specific Files
1. Search the archive repo's README or index file
2. Open an Issue in the main Portal repository with label `data-request` and include:
   - File path or capsule ID
   - Intended use / reproduction steps
   - Desired delivery format
3. Archive maintainers will provide download links

### Option 3: Zenodo DOI Access
For published datasets with DOIs, cite the DOI directly:
- Main Portal DOI: https://doi.org/10.17605/OSF.IO/FXHMK
- Archive snapshots will have separate DOIs when published

## Historical Transcript Files

The 22 "New Text Document" files contain Carl's raw discovery process:
- **Total Size:** ~50MB
- **Content:** Chat transcripts with AI assistants (Claude, GPT, Copilot)
- **Value:** Shows real scientific method, iterative discovery
- **Location (after archival):** `-portal-archive/transcripts/`

These files document:
- Years of data collection conversations
- The discovery of the χ ≤ 0.15 pattern
- Development of analysis scripts
- Validation across datasets
- Complete audit trail

**To access:** See archive repository or request via Issue.

## Large File Handling

- Files >50MB use Git LFS or external hosting
- WAV recordings stored in archive repo
- External datasets cached with links in `external_data_sources_registry.yaml`
- Dashboard data files kept minimal (<5MB each)

## Snapshot Policy

- Monthly archive snapshots tagged as `archive-YYYY-MM`
- Active repo snapshots for releases: `v1.0.0`, `v1.1.0`, etc.
- Cite specific tags for reproducibility

## Citation and DOIs

When citing  Portal data:
```
Cline, C.D. Sr. (2026).  Portal: Universal χ=0.15 Boundary Observatory.
DOI: 10.17605/OSF.IO/FXHMK
```

For archived materials:
```
Cline, C.D. Sr. (2026).  Portal Historical Archive [snapshot-date].
Repository: https://github.com/CarlDeanClineSr/-portal-archive
```

## Governance

- Archive requests triaged weekly
- Urgent requests (review/replication deadlines): Use `priority:high` label
- Historical materials maintained for transparency and reproducibility

## Migration Plan (In Progress)

### Phase 1: Preparation ✅
- [x] Document archive strategy
- [x] Identify files for archival (~50MB transcripts, ~80MB audio, historical data)
- [x] Update .gitignore patterns

### Phase 2: Archive Repo Creation (Pending)
- [ ] Create `-portal-archive` repository
- [ ] Move historical transcripts
- [ ] Move old audio recordings
- [ ] Move historical CSV data (>6 months)
- [ ] Create comprehensive index/README

### Phase 3: Active Repo Cleanup (Pending)
- [ ] Remove archived files from active repo
- [ ] Update references in documentation
- [ ] Test all dashboards still work
- [ ] Verify clone speed improvement

### Phase 4: Verification (Pending)
- [ ] Confirm archive repo accessible
- [ ] Update all documentation links
- [ ] Announce migration complete
- [ ] Monitor for any broken references

## Contact & Support

- Open an Issue with label `archive-support`
- Email: CARLDCLINE@GMAIL.COM
- For urgent archive requests: Label `priority:high`

---

**Note:** The archive strategy prioritizes accessibility while keeping the active repository lean and fast to clone. All historical materials remain available through the archive repository.

