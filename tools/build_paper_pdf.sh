#!/usr/bin/env bash
set -euo pipefail

# Build PDFs for plain-text and long-form math papers using Pandoc + Tectonic
# This script should be run from the repository root directory

# Get script directory and change to repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$REPO_ROOT"

mkdir -p papers

# This script generates two PDFs:
#   1. papers/CLINE_CONVERGENCE_2026.pdf (plain-text manuscript)
#   2. papers/CLINE_CONVERGENCE_2026_math.pdf (long-form math with LaTeX)

echo "Building paper PDFs..."

# Ensure papers directory exists
mkdir -p papers

# Build plain-text version
echo "Building plain-text version: CLINE_CONVERGENCE_2026.pdf"
pandoc \
  --from=gfm \
  --pdf-engine=tectonic \
  -V geometry:margin=1in \
  papers/CLINE_CONVERGENCE_2026.md \
  -o papers/CLINE_CONVERGENCE_2026.pdf

echo "✓ Built papers/CLINE_CONVERGENCE_2026.pdf"

# Build long-form math version
echo "Building long-form math version: CLINE_CONVERGENCE_2026_math.pdf"
pandoc \
  --from=gfm \
  --pdf-engine=tectonic \
  -V geometry:margin=1in \
  papers/CLINE_CONVERGENCE_2026_math.md \
  -o papers/CLINE_CONVERGENCE_2026_math.pdf

echo "Built papers/CLINE_CONVERGENCE_2026.pdf and papers/CLINE_CONVERGENCE_2026_math.pdf"
echo "✓ Built papers/CLINE_CONVERGENCE_2026_math.pdf"

echo ""
echo "✅ Both PDFs built successfully!"
echo "   - papers/CLINE_CONVERGENCE_2026.pdf (plain-text)"
echo "   - papers/CLINE_CONVERGENCE_2026_math.pdf (long-form math)"
