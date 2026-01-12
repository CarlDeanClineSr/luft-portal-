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
1. **FIRST: Fetch fresh data** from ACE/DSCOVR (last 2 hours)
   - Pull latest ACE plasma data
   - Pull latest ACE magnetometer data
   - Update `data/cme_heartbeat_log_2026_01.csv` with new observations
2. Read the latest datasets in `data/` and any updates in `reports/meta_intelligence/`.
3. **Verify data freshness:** Check that latest timestamp is < 15 minutes old
4. Capture key metrics: newest timestamp, record counts, and any anomaly flags mentioned.
5. Append a concise entry to `reports/HOURLY_SUMMARY.md` with timestamped bullet points showing:
   - Current timestamp
   - Latest observation timestamp (must be < 15 min old)
   - Total observations count
   - Current χ value
   - Solar wind parameters
   - Data age indicator
6. Keep the file lightweight (target <5KB) by pruning oldest entries if needed.
7. Commit the refreshed summary and updated data to the repository.
