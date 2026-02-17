param()
$ErrorActionPreference = "Stop"

# Requires pandoc and tectonic in PATH
# Windows install (one-time):
#  winget install --id JohnMacFarlane.Pandoc -e
#  winget install --id Tectonic.Tectonic -e

Write-Host "Building plain-text PDF..."
pandoc --from=gfm --pdf-engine=tectonic -V geometry:margin=1in `
  papers/CLINE_CONVERGENCE_2026.md `
  -o papers/CLINE_CONVERGENCE_2026.pdf

Write-Host "Building long-form math PDF..."
pandoc --from=gfm --pdf-engine=tectonic -V geometry:margin=1in `
  papers/CLINE_CONVERGENCE_2026_math.md `
  -o papers/CLINE_CONVERGENCE_2026_math.pdf

Write-Host "Done."
