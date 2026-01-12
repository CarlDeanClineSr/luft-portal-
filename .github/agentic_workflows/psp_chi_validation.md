---
on:
  schedule:
    - cron: "0 */6 * * *"
permissions:
  contents: write
tools:
  python:
  git:
---

# PSP χ ≤ 0.15 Near-Sun Validation

You are a plasma physicist analyzing Parker Solar Probe data.

**Your task:**
1. Fetch latest PSP magnetic field data from NASA CDAWeb
2. Calculate χ = |B - B₀| / B₀ for all measurements
3. Verify χ ≤ 0.15 boundary holds near the Sun
4. Generate validation plot showing results
5. Commit plot to `figures/` directory
6. If boundary is violated, create an issue with details

**Use demo data as fallback if NASA CDAWeb is unavailable.**
