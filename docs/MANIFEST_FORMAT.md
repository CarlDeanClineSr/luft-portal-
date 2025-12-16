# LUFT Capsule Manifest Format

## Overview

The LUFT Portal uses a manifest system to track and organize all research capsules. Manifests can be embedded in markdown files as YAML frontmatter or stored as standalone YAML/JSON files.

## Quick Start

### Option 1: Markdown Frontmatter (Recommended)

Add YAML frontmatter to your capsule markdown files:

```yaml
---
id: "CAPSULE_YOUR_UNIQUE_ID"
title: "Your Capsule Title"
status: "draft"
version: "1.0.0"
date: "2025-12-16"
author: "Your Name"
tags: ["tag1", "tag2", "tag3"]
description: "Brief description of your capsule's purpose and findings"
---

# Your Capsule Content

Your markdown content goes here...
```

### Option 2: Standalone Manifest Files

Create a `manifest.yaml` file in your capsule directory:

```yaml
id: "CAPSULE_YOUR_UNIQUE_ID"
title: "Your Capsule Title"
status: "draft"
version: "1.0.0"
date: "2025-12-16"
author: "Your Name"
tags:
  - "tag1"
  - "tag2"
  - "tag3"
description: |
  Brief description of your capsule's purpose and findings.
  Can be multi-line.
```

## Field Reference

### Required Fields

- **id** (string): Unique identifier for the capsule. Format: `CAPSULE_DESCRIPTIVE_NAME`
  - Example: `CAPSULE_CME_BOUNDARY_CEILING_2025-12`
  - Must be unique across all capsules
  - Used for deduplication and versioning

- **title** (string): Human-readable title
  - Example: "CME Boundary Ceiling Observation — December 2025"

### Recommended Fields

- **status** (string): Current status of the capsule. Valid values:
  - `active` — Currently maintained and updated
  - `adopted` — Officially adopted into LUFT framework
  - `final` — Complete and finalized
  - `draft` — Work in progress
  - `template` — Template for creating new capsules
  - `archived` — Preserved for historical reference
  - `deprecated` — No longer recommended for use
  - `experimental` — Exploratory research

- **version** (string): Semantic version (e.g., "1.0.0", "2.1.3")
  - Format: MAJOR.MINOR.PATCH
  - Auto-converted if only MAJOR or MAJOR.MINOR provided

- **date** (string): Publication or last update date
  - Format: "YYYY-MM-DD"
  - Example: "2025-12-16"

- **author** (string): Primary author name
  - Example: "Carl Dean Cline Sr."

- **tags** (array): List of keywords for categorization
  - Example: `["heartbeat", "cme", "boundary_recoil", "december"]`
  - Helps with searching and organization

- **description** (string): Brief summary of the capsule
  - 1-2 paragraphs recommended
  - Explains purpose, methods, and key findings

### Optional Fields

You can add custom fields as needed:

```yaml
---
id: "CAPSULE_EXAMPLE"
title: "Example Capsule"
status: "active"
version: "1.0.0"
date: "2025-12-16"
author: "Carl Dean Cline Sr."
tags: ["example"]
description: "Example capsule with custom fields"

# Custom fields
data_source: "ACE/DSCOVR satellites"
analysis_script: "scripts/example_analysis.py"
related_capsules:
  - "CAPSULE_HEARTBEAT_CATALOG_2025"
  - "CAPSULE_CME_BOUNDARY_CEILING_2025-12"
---
```

## Status Colors in Dashboard

The manifest dashboard uses color coding for quick status identification:

- 🟢 **Green** (Active, Adopted, Final) — Ready for use
- 🟡 **Yellow** (Draft) — Work in progress
- 🟣 **Purple** (Template) — Reference template
- 🔵 **Blue** (Archived) — Historical reference
- 🔴 **Red** (Deprecated) — No longer recommended
- ⚪ **Gray** (Experimental) — Exploratory work

## Versioning Logic

When multiple manifests have the same `id`, the system keeps the one with the highest semantic version number:

- `1.0.0` < `1.0.1` < `1.1.0` < `2.0.0`

This allows you to update capsules while maintaining their identity.

## Best Practices

### 1. Use Consistent ID Format

```yaml
# Good
id: "CAPSULE_CME_BOUNDARY_CEILING_2025-12"
id: "CAPSULE_HEARTBEAT_CATALOG_2025"
id: "CAPSULE_METHODS_HEARTBEAT"

# Avoid
id: "my-capsule"
id: "test123"
```

### 2. Keep Descriptions Concise

```yaml
# Good
description: |
  Analysis of CME boundary ceiling observations during December 2025.
  Confirms χ = 0.15 as hard upper limit across 77 observations.

# Too verbose
description: |
  This capsule presents a comprehensive analysis of coronal mass ejection
  boundary ceiling observations conducted during the month of December 2025
  utilizing data from multiple satellite sources including... [continues for pages]
```

### 3. Use Meaningful Tags

```yaml
# Good
tags: ["heartbeat", "cme", "boundary_recoil", "december", "2025"]

# Less useful
tags: ["data", "analysis", "science", "research"]
```

### 4. Update Versions When Changing Content

If you make significant updates to a capsule:
- Increment PATCH for bug fixes or minor corrections (1.0.0 → 1.0.1)
- Increment MINOR for new content or sections (1.0.1 → 1.1.0)
- Increment MAJOR for complete rewrites (1.1.0 → 2.0.0)

### 5. Transition Through Status Stages

Typical lifecycle:
1. `draft` — Initial work
2. `experimental` — Testing ideas
3. `active` — Regular use and updates
4. `adopted` or `final` — Officially complete
5. `archived` — Preserved for history
6. `deprecated` — Superseded by newer work

## Automation

The manifest system runs automatically:

- **Daily** at 06:00 UTC via GitHub Actions
- **On push** to `capsules/` directory
- **Manual trigger** via workflow_dispatch

Generated files:
- `docs/manifest_master_index.yaml` — Complete index with statistics
- `docs/manifest_dashboard.html` — Visual HTML dashboard

## Manual Execution

To run the tools locally:

```bash
# Install dependencies
pip install pyyaml

# Generate manifest index
python scripts/capsule_index_job.py

# Generate HTML dashboard
python scripts/generate_dashboard.py
```

## Validation

The system automatically validates:

1. **Required fields** — `id` and `title` must be present
2. **Status values** — Must be from the approved list
3. **Version format** — Must be semantic versioning (or auto-corrected)
4. **Duplicate IDs** — Warns if multiple capsules share an ID (keeps latest version)

Invalid manifests are reported in the console output but don't stop processing.

## Examples

### Example 1: Research Capsule

```yaml
---
id: "CAPSULE_DECEMBER_BASELINE_SHIFT"
title: "December 2025 Baseline Shift Analysis"
status: "active"
version: "1.2.0"
date: "2025-12-15"
author: "Carl Dean Cline Sr."
tags: ["baseline", "chi", "december", "2025", "shift"]
description: |
  Tracks the χ baseline shift from 0.055 to 0.12 during December 2025.
  Documents CONFIRMED SHIFT threshold crossings and their persistence.
---
```

### Example 2: Methods Capsule

```yaml
---
id: "CAPSULE_METHODS_HEARTBEAT"
title: "Methods — Heartbeat Detection and Analysis"
status: "final"
version: "2.0.0"
date: "2025-12-05"
author: "Carl Dean Cline Sr."
tags: ["methods", "heartbeat", "analysis", "documentation"]
description: |
  Complete methodology for detecting and analyzing the ~2.4 hour
  cosmic heartbeat in LUFT data. Includes data sources, algorithms,
  and validation procedures.
---
```

### Example 3: Template Capsule

```yaml
---
id: "CAPSULE_REPLICATION_RESULT_TEMPLATE"
title: "Replication Result Template"
status: "template"
version: "1.0.0"
date: "2025-12-05"
author: "LUFT System"
tags: ["template", "replication", "documentation"]
description: |
  Template for documenting replication attempts of LUFT experiments.
  Copy this template and fill in your own results.
---
```

## Support

For questions or issues with the manifest system:

1. Check this documentation
2. Review existing capsules for examples
3. Examine the validation output from `capsule_index_job.py`
4. Open an issue in the repository

## See Also

- [Manifest Dashboard](manifest_dashboard.html) — View all capsules
- [Master Index](manifest_master_index.yaml) — Raw manifest data
- Main README — Repository overview and getting started
