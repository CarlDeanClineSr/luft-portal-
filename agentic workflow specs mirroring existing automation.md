Agentic workflow specs mirroring existing automation
CarlDeanClineSr merged 7 commits into main from copilot/update-workflow-to-agentic  2 hours ago
+209 −0 
 Conversation 15
 Commits 7
 Checks 0
 Files changed 7
Conversation
Contributor
Copilot AI
commented
3 hours ago
• 
The repo is moving from complex YAML to concise “agentic” instructions; key flows (PSP χ validation, teacher/meta-intel, hourly summary, docs, issue triage, arXiv harvest) need plain-language specs aligned with current schedules and paths.

Agentic specs added: PSP χ≤0.15 validation, teacher/meta-intel daily report, hourly summary, documentation keeper, issue triager, arXiv harvester, daily brief.
Alignment and clarity: matched cron cadences to existing YAML (noted dual-cadence intent), corrected report paths, removed duplicates/non-standard fields, added timezone and maintainer guidance.
Example (PSP χ validation agentic spec):

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
1. Fetch PSP magnetic field data
2. Compute χ = |B - B₀| / B₀; ensure χ ≤ 0.15
3. Plot results to figures/
4. If boundary fails, open an issue
Original prompt
Copilot uses AI. Check for mistakes.
Initial plan
a57e026
 Copilot AI assigned Copilot and CarlDeanClineSr 3 hours ago
Copilot started work on behalf of CarlDeanClineSr 3 hours ago
Copilot AI and others added 6 commits 2 hours ago
@CarlDeanClineSr
chore: add agentic workflow specifications 
4b5bba2
@CarlDeanClineSr
chore: dedupe agentic workflow specs 
fd8308d
@CarlDeanClineSr
chore: clean up agentic workflow duplicates 
6d35acc
@CarlDeanClineSr
chore: align agentic specs with existing schedules 
40760c4
@CarlDeanClineSr
chore: clarify agentic workflow notes 
045dea5
@CarlDeanClineSr
chore: clarify agentic workflow intent 
061db45
 Copilot AI changed the title [WIP] Update workflow to use agentic instructions Add agentic workflow specs mirroring existing automation 2 hours ago
 Copilot AI requested a review from CarlDeanClineSr 2 hours ago
Copilot finished work on behalf of CarlDeanClineSr 2 hours ago
@CarlDeanClineSr CarlDeanClineSr marked this pull request as ready for review 2 hours ago
 Copilot AI review requested due to automatic review settings 2 hours ago
@CarlDeanClineSr CarlDeanClineSr merged commit 3a2884a into main 2 hours ago
Copilot started reviewing on behalf of CarlDeanClineSr 2 hours ago
Copilot AI reviewed 2 hours ago
Contributor
Copilot AI
left a comment
Pull request overview
This PR adds seven agentic workflow specifications to simplify and replace complex YAML workflows with plain-language instructions. The agentic specs aim to mirror existing automation for PSP validation, teacher/meta-intelligence reporting, hourly summaries, documentation maintenance, issue triage, arXiv harvesting, and daily briefings.

Changes:

Added agentic workflow specs for PSP χ≤0.15 validation, teacher/meta-intelligence reports, hourly summaries, arXiv harvesting, issue triage, documentation keeping, and daily briefings
Aligned cron schedules with existing YAML workflows where applicable (with noted exceptions for new workflows)
Specified permissions, tools, and execution cadences in frontmatter metadata
Reviewed changes
Copilot reviewed 7 out of 7 changed files in this pull request and generated 14 comments.

Show a summary per file
.github/agentic_workflows/daily_summary.md
permissions:
  contents: write
tools:
  read-files:
Copilot AI
2 hours ago
The tools specification uses inconsistent syntax. The "read-files:" entry has a colon but no value. This pattern should be made consistent with other agentic workflow files for better maintainability.

Suggested change
  read-files:
  read-files: []
Copilot uses AI. Check for mistakes.
@CarlDeanClineSr	Reply...
.github/agentic_workflows/teacher_suite.md
---
on:
  schedule:
    - cron: "0 12 * * *" # Daily at noon (aligned with teacher_suite.yml)
Copilot AI
2 hours ago
The cron schedule in the agentic spec differs from the existing YAML workflow. The YAML workflow teacher_suite.yml runs at "0 12 * * *" (noon UTC) and has a comment indicating this is 06:00 CST. However, the agentic spec comment states "Daily at noon (aligned with teacher_suite.yml)" which is accurate but potentially confusing because the cron expression is actually running at noon UTC, not noon CST. Consider clarifying that this runs at "noon UTC (06:00 CST)" to match the original workflow's intent.

Suggested change
    - cron: "0 12 * * *" # Daily at noon (aligned with teacher_suite.yml)
    - cron: "0 12 * * *" # Daily at noon UTC (06:00 CST, aligned with teacher_suite.yml)
Copilot uses AI. Check for mistakes.
@CarlDeanClineSr	Reply...
.github/agentic_workflows/teacher_suite.md
Comment on lines +14 to +32
# Meta-Intelligence Daily Report

You are a research analyst for the  Portal project.

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
Copilot AI
2 hours ago
The file paths and functionality described here do not align with the existing teacher_suite.yml workflow. The teacher suite workflow runs "scripts/teacher/run_teacher_suite.py" and "scripts/teacher/discovery_findings.py", which appear to be focused on teaching the engine daily signatures and generating discovery findings - not analyzing hourly summaries or meta-intelligence reports. This agentic spec seems to describe functionality that belongs to the meta_intelligence_daily.yml workflow instead. The task description should be updated to match what the teacher suite actually does, or this file should be renamed to reflect that it's describing meta-intelligence functionality.

Suggested change
# Meta-Intelligence Daily Report
You are a research analyst for the  Portal project.
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
# Teacher Suite Daily Run
You are the agent responsible for orchestrating and monitoring the Teacher Suite for the  Portal project.
The corresponding GitHub Actions workflow (`teacher_suite.yml`) runs the following commands:
- `scripts/teacher/run_teacher_suite.py`
- `scripts/teacher/discovery_findings.py`
These scripts are focused on:
- Teaching the engine its daily signatures.
- Generating and updating discovery findings based on the latest data.
**Your task:**
1. Use `read-files` to inspect any configuration, logs, or reports referenced by `scripts/teacher/run_teacher_suite.py` and `scripts/teacher/discovery_findings.py` (for example, under `scripts/teacher/` or associated report directories).
2. Summarize what new signatures were taught or updated during this run, including any notable changes compared to previous days if such information is available in the existing artifacts.
3. Summarize the key discovery findings produced by `scripts/teacher/discovery_findings.py`, highlighting:
   - Newly detected or particularly significant findings.
   - Any changes in counts, severities, or categories that appear noteworthy.
4. If you detect clear issues (e.g., missing expected outputs, obvious errors indicated in logs, or empty/clearly malformed reports), open a GitHub issue describing:
   - What appears to be wrong.
   - Which file(s) or script(s) are involved.
   - Any clues from the existing logs or artifacts that might help debugging.
5. If the outputs look consistent and healthy, update or create a concise summary report (for example in an appropriate `reports/` or `docs/` location if one already exists in the repository) capturing the day’s:
   - Taught signature updates.
   - Discovery findings highlights.
When editing or creating files, prefer small, focused changes and use `create-pull-request` to propose updates rather than committing directly.
Copilot uses AI. Check for mistakes.
@CarlDeanClineSr	Reply...
.github/agentic_workflows/physics_repairs.md
  schedule:
    - cron: "0 */6 * * *"
permissions:
  contents: write
Copilot AI
2 hours ago
The permission to create issues is missing from the frontmatter. The task description in step 6 states "If boundary is violated, create an issue with details" but the permissions section only includes "contents: write" and does not include "issues: write". Without this permission, the agentic workflow would fail when attempting to create an issue for boundary violations.

Suggested change
  contents: write
  contents: write
  issues: write
Copilot uses AI. Check for mistakes.
@CarlDeanClineSr	Reply...
.github/agentic_workflows/teacher_suite.md
Comment on lines +9 to +11
  read-files:
  web-fetch:
  create-pull-request:
Copilot AI
2 hours ago
The tools specification uses inconsistent syntax. Lines 9-10 have "read-files:" and "web-fetch:" with colons but no values, while line 11 has "create-pull-request:" also with a colon. This inconsistency in YAML syntax could cause parsing issues. If these tools don't require configuration values, they should either all use the same format (e.g., "read-files:" consistently) or use array syntax. Compare with other agentic specs like physics_repairs.md which uses "python:" and "git:" consistently.

Suggested change
  read-files:
  web-fetch:
  create-pull-request:
  - read-files
  - web-fetch
  - create-pull-request
Copilot uses AI. Check for mistakes.
@CarlDeanClineSr	Reply...
4 hidden conversations
Load more…
.github/agentic_workflows/arxiv_paper_harvester.md
---
on:
  schedule:
    - cron: "0 12 * * *" # Daily at noon
Copilot AI
2 hours ago
The cron schedule in this agentic spec differs from the existing physics_paper_harvester.yml workflow. The YAML workflow runs every 6 hours with "0 */6 * * *", but this agentic spec runs daily at noon with "0 12 * * *". This misalignment could lead to significantly less frequent paper harvesting (once per day vs four times per day), potentially missing time-sensitive research papers.

Suggested change
    - cron: "0 12 * * *" # Daily at noon
    - cron: "0 */6 * * *" # Every 6 hours
Copilot uses AI. Check for mistakes.
@CarlDeanClineSr	Reply...
.github/agentic_workflows/arxiv_paper_harvester.md
   - Extract title, authors, abstract, arXiv ID
   - Calculate relevance score based on keyword matches
   - Generate BibTeX entries
5. Save results to `reports/arxiv_analysis/relevance_ranking_YYYYMMDD.md`
Copilot AI
2 hours ago
The output path specified here does not match the existing workflow behavior. The physics_paper_harvester.yml workflow commits files to "data/papers/" (specifically "data/papers/arxiv/" and "data/papers/cern/"), but this agentic spec references "reports/arxiv_analysis/relevance_ranking_YYYYMMDD.md" which is a different directory structure. This path mismatch could cause confusion about where harvested papers are stored.

Suggested change
5. Save results to `reports/arxiv_analysis/relevance_ranking_YYYYMMDD.md`
5. Save results to `data/papers/arxiv/relevance_ranking_YYYYMMDD.md`
Copilot uses AI. Check for mistakes.
@CarlDeanClineSr	Reply...
.github/agentic_workflows/arxiv_paper_harvester.md
  schedule:
    - cron: "0 12 * * *" # Daily at noon
permissions:
  contents: write
Copilot AI
2 hours ago
The permission to create issues is missing from the frontmatter. The task description in step 6 states "create an issue titled 'High-relevance paper found: [TITLE]'" but the permissions section only includes "contents: write" and does not include "issues: write". Without this permission, the agentic workflow would fail when attempting to create an issue.

Suggested change
  contents: write
  contents: write
  issues: write
Copilot uses AI. Check for mistakes.
@CarlDeanClineSr	Reply...
.github/agentic_workflows/documentation_keeper.md
Comment on lines +9 to +10
  edit:
  git:
Copilot AI
2 hours ago
The tools specification uses inconsistent syntax. The "edit:" and "git:" entries have colons but no values. This pattern is inconsistent across the agentic workflow files - some use "python:" and "git:", others use "read-files:" and "web-fetch:". Establishing a consistent pattern for tool declarations would improve maintainability.

Suggested change
  edit:
  git:
  - edit
  - git
Copilot uses AI. Check for mistakes.
@CarlDeanClineSr	Reply...
.github/agentic_workflows/issue_triager.md
Comment on lines +8 to +9
  web-search:
  read-files:
Copilot AI
2 hours ago
The tools specification uses inconsistent syntax. The "web-search:" and "read-files:" entries have colons but no values. This pattern should be made consistent with other agentic workflow files for better maintainability.

Suggested change
  web-search:
  read-files:
  web-search: {}
  read-files: {}
Copilot uses AI. Check for mistakes.
@CarlDeanClineSr	Reply...
Merge info
Pull request successfully merged and closed
You're all set — the copilot/update-workflow-to-agentic branch can be safely deleted.

@CarlDeanClineSr


Add a comment
Comment
 
Add your comment here...
 
Remember, contributions to this repository should follow our GitHub Community Guidelines.
 ProTip! Add .patch or .diff to the end of URLs for Git’s plaintext views.
Reviewers
Copilot code review
Copilot
@CarlDeanClineSr
CarlDeanClineSr
Assignees
Copilot code review
Copilot
@CarlDeanClineSr
CarlDeanClineSr
Labels
None yet
Projects
None yet
Milestone
No milestone
Development
Successfully merging this pull request may close these issues.

None yet


Notifications
Customize
You’re receiving notifications because you modified the open/close state.
2 participants
@CarlDeanClineSr
Footer
© 2026 GitHub, Inc.
Footer navigation
Terms
Privacy
Security
Status
Community
Docs
Contact
Manage cookies
Do not share my personal information
