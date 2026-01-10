# Building the Paper PDFs

Two versions:
- papers/CLINE_CONVERGENCE_2026.md — plain‑text safe (ideal for Google Docs/Word). CI builds CLINE_CONVERGENCE_2026.pdf.
- papers/CLINE_CONVERGENCE_2026_math.md — long‑form math with LaTeX. CI builds CLINE_CONVERGENCE_2026_math.pdf.

## Local build
Linux/macOS:
- Install pandoc + tectonic (tiny TeX).
- Run: `bash tools/build_paper_pdf.sh`

Windows:
- In PowerShell (Admin): 
  - `winget install --id JohnMacFarlane.Pandoc -e`
  - `winget install --id Tectonic.Tectonic -e`
- Run: `powershell -ExecutionPolicy Bypass -File tools/build_paper_pdf.ps1`

## CI build
Any push to papers/** or the build scripts triggers the workflow. PDFs are committed back to papers/.

## Zenodo
Upload either PDF to Zenodo (Publication → Preprint). After DOI is assigned, paste it into README.md, CITATION.cff, and papers/README_ZENODO.md.
