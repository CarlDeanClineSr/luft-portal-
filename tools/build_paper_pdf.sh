#!/usr/bin/env bash
set -euo pipefail

# Build PDFs for plain-text and long-form math papers using Pandoc + Tectonic
mkdir -p papers

pandoc \
  --from=gfm \
  --pdf-engine=tectonic \
  -V geometry:margin=1in \
  papers/CLINE_CONVERGENCE_2026.md \
  -o papers/CLINE_CONVERGENCE_2026.pdf

pandoc \
  --from=gfm \
  --pdf-engine=tectonic \
  -V geometry:margin=1in \
  papers/CLINE_CONVERGENCE_2026_math.md \
  -o papers/CLINE_CONVERGENCE_2026_math.pdf

echo "Built papers/CLINE_CONVERGENCE_2026.pdf and papers/CLINE_CONVERGENCE_2026_math.pdf"
