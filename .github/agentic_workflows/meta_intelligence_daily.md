---
on:
  schedule:
    - cron: "0 9 * * *"  # 9 AM daily
permissions:
  contents: write
tools:
  read-files:
---

# Daily LUFT Summary for Carl

You are Carl's research assistant.

**Every morning at 9 AM, create a summary:**

1. Read yesterday's meta-intelligence report from `reports/meta_intelligence/`.
2. Check if there were any workflow failures.
3. Look for the 66-hour suppression pattern.
4. Count how many hourly summaries were generated.
5. Write a brief summary (3-5 sentences) to `reports/DAILY_BRIEF.md`.

**Format:**
```
# Daily Brief - [DATE]

## What Happened Yesterday: 
- [key finding 1]
- [key finding 2]

## 66h Suppression Status:
- [present/absent, match count if present]

## Workflow Health:
- [number of successful runs / total runs]
```
