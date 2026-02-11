```markdown
#  Portal — Current Work & Dashboard

Purpose
This repository ( Portal) is the compact, curated entry point for the  program — the things we are actively working on this month and today. It intentionally contains only the highest‑priority experiments, capsule summaries, and small reproducible demos so collaborators and reviewers can get started quickly.

What lives here
- /capsules — high‑priority knowledge capsules (current work)
- /notebooks — runnable, small notebooks that reproduce core figures
- /src — minimal scripts to run canonical checks (e.g., lattice_lambda.py)
- README (this file) — quick status and how to get involved

Top priorities (this month)
1. JJ Foam Auditor — reproduce synthetic tests and run an MLE on digitized MIT histograms. (CAPSULE-JJ-002)
2. vacuum → Λ note — finalize and submit the short preprint (CAPSULE-LAMBDA-001)
3. 7,468 Hz signal validation — cross-site spectrogram replication (CAPSULE-7468-003)

How to reproduce the top items (quick)
- JJ synthetic test:
  1. cd notebooks && jupyter lab
  2. open `collapse_demo_notebook_5.ipynb` and run the cells in order
- vacuum → Λ:
  1. python -m src.lattice_lambda
  2. Open `/capsules/CAPSULE_LATTICE_LAMBDA.md` for the derivation and acceptance criteria
- 7,468 Hz:
  1. Run `scripts/analyze_wav_luft.py ./recordings/sample.wav` (or the portal sample)
  2. Inspect `results/` for spectrogram and peak table

Where the archive lives
- The full historical archive and raw datasets (large WAVs, raw logs, older text dumps) are in the  Archive repo:
  https://github.com/CarlDeanClineSr/-archive
  (or in the `archive/` folder of the main  repo if you prefer single‑repo layout)

Contribute
- To add a new capsule: create `/capsules/XXX.md` following the template in `/capsules/TEMPLATE_CAPSULE.md`.
- Use Issues to propose new experiments or request raw data from the archive.
- See CONTRIBUTING.md for code style and CI checks.

Contact
- Owner: Dr. Carl Dean Cline Sr. — GitHub: @CarlDeanClineSr
- If you need raw data for reproductions, open an issue with label `data-request` and include the capsule id.
```
