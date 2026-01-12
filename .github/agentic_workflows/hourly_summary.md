---
on:
  schedule:
    - cron: "0 * * * *"  # Every hour
    - cron: "*/15 * * * *" # High-frequency updates every 15 minutes
permissions:
  contents: write
tools:
  read-files:
  git:
---

# Hourly Status Logger

You are a status bot for LUFT Portal.

_Dual cadence is intentional: 15-minute runs provide high-frequency updates while the hourly entry guarantees a top-of-hour summary if higher-cadence runs are throttled._

**Each hour:**
1. Read the latest datasets in `data/` and any updates in `reports/meta_intelligence/`.
2. Capture key metrics: newest timestamp, record counts, and any anomaly flags mentioned.
3. Append a concise entry to `reports/HOURLY_SUMMARY.md` with timestamped bullet points.
4. Keep the file lightweight (target <5KB) by pruning oldest entries if needed.
5. Commit the refreshed summary to the repository.
