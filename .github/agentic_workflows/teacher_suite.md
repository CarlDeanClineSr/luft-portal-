---
on:
  schedule:
    - cron: "0 12 * * *" # Daily at noon (aligned with teacher_suite.yml)
permissions:
  contents: write
  issues: write
tools:
  read-files:
  web-fetch:
  create-pull-request:
---

# Meta-Intelligence Daily Report

You are a research analyst for the LUFT Portal project.

**Your task:**
1. Read data from `reports/HOURLY_SUMMARY.md` and any `reports/hourly_summary_*.md` files from the last 24 hours.
2. Analyze temporal correlations between NOAA solar wind data and CHI_BOUNDARY matches.
3. Identify any multi-source anomaly events.
4. Check if the 66-hour suppression pattern is present in today's data.
5. Generate a comprehensive summary in `reports/meta_intelligence/LATEST_SUMMARY.md`.
6. If you find the 66h suppression (82,288 matches), highlight it as a key finding.
7. Compare today's results to yesterday's `report_YYYYMMDD_*.md` file.
8. If significant changes detected (>10% deviation), create an issue for review.

**Key metrics to track:**
- Total correlations detected
- 66-hour suppression match count (should be ~82,288)
- Peak at 24 hours (should be ~233,105)
- Peak at 72 hours (should be ~122,206)
