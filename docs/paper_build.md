# Building the Paper PDFs

Two versions of the Cline Convergence paper are maintained:

1. **`papers/CLINE_CONVERGENCE_2026.md`** — plain-text-safe version (ideal for Google Docs/Word)
   - No LaTeX equations (uses Unicode math symbols)
   - Can be copy-pasted into Google Docs without rendering issues
   - CI builds `CLINE_CONVERGENCE_2026.pdf`

2. **`papers/CLINE_CONVERGENCE_2026_math.md`** — long-form math version with LaTeX
   - Full LaTeX equation blocks for publication
   - Professional typesetting with proper mathematical notation
   - CI builds `CLINE_CONVERGENCE_2026_math.pdf`

---

## Automated CI Build

The PDFs are **automatically built and committed** on every change to:
- Any file in `papers/**`
- The build script `tools/build_paper_pdf.sh`

**Workflow:** `.github/workflows/build_papers.yml`

The workflow:
1. Installs `pandoc` and `tectonic` (lightweight TeX engine)
2. Runs `tools/build_paper_pdf.sh`
3. Commits both PDFs back to the repository

You can also **manually trigger** the workflow from the GitHub Actions tab.

---

## Local Build (Optional)

If you want to build PDFs locally:

### 1. Install Dependencies

**Pandoc:**
- Ubuntu/Debian: `sudo apt-get install pandoc`
- macOS: `brew install pandoc`
- Windows: Download from https://pandoc.org/installing.html

**Tectonic** (lightweight TeX engine):
- All platforms: https://tectonic-typesetting.github.io/install.html
- Ubuntu/Debian: Download from GitHub releases and extract to PATH
- macOS: `brew install tectonic`
- Windows: Download installer from https://github.com/tectonic-typesetting/tectonic/releases

### 2. Run the Build Script

```bash
bash tools/build_paper_pdf.sh
```

This generates:
- `papers/CLINE_CONVERGENCE_2026.pdf` (plain-text)
- `papers/CLINE_CONVERGENCE_2026_math.pdf` (long-form math)

---

## Troubleshooting

### Issue: "pandoc: command not found"
**Solution:** Install pandoc using your package manager (see above)

### Issue: "tectonic: command not found"
**Solution:** Install tectonic from https://tectonic-typesetting.github.io/

### Issue: PDF build fails with LaTeX errors
**Solution:** Check the markdown syntax in the paper files. Pandoc requires:
- Proper YAML frontmatter (enclosed in `---`)
- Valid LaTeX syntax in math blocks (`$$...$$` for display math)
- Proper escaping of special characters

### Issue: Unicode symbols don't render in PDF
**Solution:** This affects the plain-text version. The math version uses LaTeX and should render all symbols correctly. If issues persist, update the font configuration in the pandoc command (add `-V mainfont="DejaVu Sans"` or similar).

---

## Publishing to Zenodo

To upload a preprint to Zenodo:

1. Choose which PDF to upload:
   - **Plain-text PDF** (`CLINE_CONVERGENCE_2026.pdf`) — for widest compatibility
   - **Math PDF** (`CLINE_CONVERGENCE_2026_math.pdf`) — for publication-quality typesetting

2. Upload to Zenodo: https://zenodo.org/deposit

3. After DOI assignment, update:
   - `README.md` — Add DOI badge
   - `CITATION.cff` — Update DOI field
   - `papers/README_ZENODO.md` — Document the preprint

---

## File Organization

```
papers/
├── CLINE_CONVERGENCE_2026.md          # Plain-text source
├── CLINE_CONVERGENCE_2026.pdf         # Plain-text PDF (auto-built)
├── CLINE_CONVERGENCE_2026_math.md     # Long-form math source
├── CLINE_CONVERGENCE_2026_math.pdf    # Long-form math PDF (auto-built)
├── CLINE_CONVERGENCE_SECTION.md       # Section draft
├── README_ZENODO.md                   # Zenodo documentation
├── chi_015_discovery.tex              # LaTeX source (legacy)
└── references.bib                     # BibTeX references
```

---

## Notes for Collaborators

- **Plain-text version:** Keep this file free of LaTeX! Use Unicode symbols (χ, ≤, ×, etc.) so it can be copied into Google Docs.
- **Math version:** Use proper LaTeX equations. This is the publication-ready version.
- **Both versions:** Maintain the same narrative structure and scientific content. Only the math notation should differ.
- **CI will auto-build:** You don't need to manually build PDFs. Just push changes to the `.md` files.

---

## Contact

For build issues or questions about the paper formatting:
- Open an issue: https://github.com/CarlDeanClineSr/luft-portal-/issues
- Check workflow logs: https://github.com/CarlDeanClineSr/luft-portal-/actions
