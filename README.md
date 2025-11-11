 This repository (LUFT Portal) is the compact, curated entry point for the LUFT program — the things we are actively working on this month and today. It intentionally contains only the highest‑priority experiments, capsule summaries, and small reproducible demos so collaborators and reviewers can get started quickly.

What lives here
- /capsules — high‑priority knowledge capsules (current work)
- /notebooks — runnable, small notebooks that reproduce core figures
- /scripts — analysis scripts for WAV processing and signal validation
- /src — minimal scripts to run canonical checks (e.g., lattice_lambda.py)
- README (this file) — quick status and how to get involved

Top priorities (this month)
1. JJ Foam Auditor — reproduce synthetic tests and run an MLE on digitized MIT histograms. (CAPSULE-JJ-002)
2. Lattice → Λ note — finalize and submit the short preprint (CAPSULE-LAMBDA-001)
3. 7,468 Hz signal validation — cross-site spectrogram replication (CAPSULE-7468-003)

How to reproduce the 7,468 Hz validation
1. Install dependencies: `pip install -r requirements.txt`
2. Generate a test sample: `python scripts/generate_sample_wav.py`
3. Analyze the WAV file: `python scripts/analyze_wav_luft.py recordings/sample.wav`
4. Review outputs in `results/` directory:
   - Spectrogram image showing frequency content over time
   - CSV file with peak frequencies and their distance from 7,468 Hz target

