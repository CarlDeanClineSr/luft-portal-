# LUFT Capsule Manifest System

## Overview

The LUFT Portal Capsule Manifest System provides automated indexing, validation, and visualization of all research capsules in the repository. This system maintains a living index of capsule metadata and generates a color-coded dashboard for quick status overview.

## System Components

### 1. Capsule Index Job (`scripts/capsule_index_job.py`)

**Purpose**: Scans, validates, and indexes all capsule manifests.

**Features**:
- Recursively scans `capsules/` directory for manifest files
- Supports both standalone YAML/JSON files and markdown frontmatter
- Validates required fields (id, title) and optional fields (status, version, date, author, tags)
- Deduplicates by capsule ID, keeping highest semantic version
- Generates statistics (by status, by author, tag counts)
- Outputs to `docs/manifest_master_index.yaml`

**Usage**:
```bash
python scripts/capsule_index_job.py
```

**Output**: `docs/manifest_master_index.yaml` with structure:
```yaml
metadata:
  generated_at: "2025-12-16T02:42:00Z"
  generator: "capsule_index_job.py"
  total_capsules: 15
  version: "1.0.0"

statistics:
  by_status:
    active: 1
    adopted: 9
    draft: 3
  by_author:
    "Carl Dean Cline Sr.": 12
  total_tags: 50

capsules:
  - id: "CAPSULE_EXAMPLE"
    title: "Example Capsule"
    status: "active"
    version: "1.0.0"
    ...
```

### 2. Dashboard Generator (`scripts/generate_dashboard.py`)

**Purpose**: Renders a visual HTML dashboard from the master index.

**Features**:
- Parses `manifest_master_index.yaml`
- Color-codes capsules by status (green, yellow, blue, red, purple, gray)
- Sorts by status priority and date (newest first)
- Responsive design with modern CSS
- Shows summary statistics at top
- Displays tags, authors, versions, and file paths
- Outputs to `docs/manifest_dashboard.html`

**Usage**:
```bash
python scripts/generate_dashboard.py
```

**Output**: `docs/manifest_dashboard.html` - Interactive HTML dashboard

### 3. Automation Workflow (`.github/workflows/index-job.yml`)

**Purpose**: Runs the index job and dashboard generator automatically.

**Triggers**:
- **Schedule**: Daily at 06:00 UTC
- **Push**: When files in `capsules/` are modified
- **Manual**: Via workflow_dispatch

**Process**:
1. Checkout repository
2. Set up Python 3.11
3. Install PyYAML
4. Run `capsule_index_job.py`
5. Run `generate_dashboard.py`
6. Commit and push changes to `docs/`

**Permissions**: `contents: write` (to commit generated files)

## Capsule Manifest Format

### Markdown Frontmatter (Recommended)

```yaml
---
id: "CAPSULE_UNIQUE_IDENTIFIER"
title: "Human Readable Title"
status: "active"
version: "1.0.0"
date: "2025-12-16"
author: "Author Name"
tags: ["tag1", "tag2"]
description: "Brief description"
---

# Capsule Content

Your markdown content here...
```

### Standalone YAML

```yaml
# capsules/subdirectory/manifest.yaml
id: "CAPSULE_UNIQUE_IDENTIFIER"
title: "Human Readable Title"
status: "active"
version: "1.0.0"
date: "2025-12-16"
author: "Author Name"
tags:
  - "tag1"
  - "tag2"
description: |
  Multi-line description
  can go here.
```

## Status Types and Colors

| Status | Color | Meaning |
|--------|-------|---------|
| `active` | 🟢 Green | Currently maintained and updated |
| `adopted` | 🟢 Green | Officially adopted into LUFT framework |
| `final` | 🔵 Blue | Complete and finalized |
| `draft` | 🟡 Yellow | Work in progress |
| `template` | 🟣 Purple | Template for creating new capsules |
| `archived` | 🔵 Blue | Preserved for historical reference |
| `deprecated` | 🔴 Red | No longer recommended for use |
| `experimental` | ⚪ Gray | Exploratory research |

## Validation Rules

The system validates:

1. **Required Fields**:
   - `id`: Must be present and unique
   - `title`: Must be present

2. **Status Values**: Must be one of the 8 valid status types

3. **Version Format**: Must follow semantic versioning (MAJOR.MINOR.PATCH)
   - Auto-converts `1.0` → `1.0.0` and `1` → `1.0.0`

4. **Deduplication**: When multiple manifests share the same `id`, keeps the one with highest version number

## Versioning Logic

When updating a capsule:
- **Patch** (x.y.Z): Bug fixes, typos, minor corrections
- **Minor** (x.Y.z): New sections, additional content
- **Major** (X.y.z): Complete rewrites, structural changes

Example progression: `1.0.0` → `1.0.1` → `1.1.0` → `2.0.0`

## Accessing the Dashboard

### Local Access
After running the scripts, open:
```
docs/manifest_dashboard.html
```

### GitHub Pages
If GitHub Pages is enabled, the dashboard is available at:
```
https://[username].github.io/luft-portal-/manifest_dashboard.html
```

### Direct Repository
View the raw HTML in your browser:
```
https://github.com/CarlDeanClineSr/luft-portal-/blob/main/docs/manifest_dashboard.html
```

## Best Practices

### 1. Consistent ID Format
Use descriptive, ALL_CAPS identifiers with underscores:
- ✅ `CAPSULE_CME_BOUNDARY_CEILING_2025-12`
- ✅ `CAPSULE_METHODS_HEARTBEAT`
- ❌ `my-capsule` (too generic)
- ❌ `test123` (not descriptive)

### 2. Keep Descriptions Concise
Aim for 1-2 paragraphs that explain:
- What the capsule covers
- Key findings or methods
- Context or significance

### 3. Use Meaningful Tags
Choose specific, searchable tags:
- ✅ `["heartbeat", "cme", "december", "2025"]`
- ❌ `["data", "analysis", "science"]` (too generic)

### 4. Update Versions on Changes
Increment version numbers when updating content:
- Small fixes → patch version
- New content → minor version
- Major rewrites → major version

### 5. Transition Through Status Stages
Follow a logical lifecycle:
```
draft → experimental → active → adopted/final → archived
```

## Troubleshooting

### No Manifests Found
- Check that manifest files are named `manifest.yaml`, `manifest.yml`, or `manifest.json`
- Or ensure markdown files have valid YAML frontmatter (between `---` markers)

### Validation Errors
- Check console output for specific error messages
- Verify all required fields are present
- Ensure status values match the approved list

### Dashboard Not Generating
- Run `capsule_index_job.py` first to create the index
- Check that `docs/manifest_master_index.yaml` exists
- Verify PyYAML is installed: `pip install pyyaml`

### Workflow Failures
- Check workflow logs in GitHub Actions tab
- Verify Python and PyYAML installation succeeded
- Check for file permission issues

## File Structure

```
luft-portal-/
├── .github/
│   └── workflows/
│       └── index-job.yml          # Automation workflow
├── capsules/
│   ├── manifest.yaml              # Example manifest
│   ├── CAPSULE_*.md               # Capsules with frontmatter
│   └── subdirectories/            # Organized capsules
├── docs/
│   ├── manifest_master_index.yaml # Generated index
│   ├── manifest_dashboard.html    # Generated dashboard
│   ├── MANIFEST_FORMAT.md         # Format specification
│   └── MANIFEST_SYSTEM_README.md  # This file
└── scripts/
    ├── capsule_index_job.py       # Index generator
    └── generate_dashboard.py      # Dashboard generator
```

## Dependencies

- **Python**: 3.11 or higher
- **PyYAML**: For YAML parsing
  ```bash
  pip install pyyaml
  ```

## Future Enhancements

Potential improvements for the manifest system:

- [ ] JSON Schema validation for manifests
- [ ] Search functionality in dashboard
- [ ] Filter by status, author, or tags
- [ ] Export to CSV/JSON for external analysis
- [ ] Cross-reference checker (detect references between capsules)
- [ ] Broken link detection in capsule content
- [ ] Automatic tag suggestions based on content
- [ ] Timeline view of capsule creation/updates

## Contributing

To add a new capsule to the index:

1. Create your capsule markdown file with YAML frontmatter
2. OR create a standalone `manifest.yaml` in your capsule directory
3. Ensure all required fields are present and valid
4. Commit to the `capsules/` directory
5. The index job will automatically run and update the dashboard

## Support

For questions or issues:

1. Review this documentation
2. Check [MANIFEST_FORMAT.md](MANIFEST_FORMAT.md) for detailed format spec
3. Examine existing capsules for examples
4. Review validation output for specific error messages
5. Open an issue in the repository

## License

This manifest system is part of the LUFT Portal project and follows the same license as the main repository.

---

**Last Updated**: 2025-12-16  
**System Version**: 1.0.0  
**Maintained by**: LUFT Portal Contributors
