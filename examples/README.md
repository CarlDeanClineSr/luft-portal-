# LUFT Data Transcription Examples

This directory contains example files demonstrating the proper usage of LUFT (Lattice Unified Field Theory) data transcription standards.

## Files

### Data Examples
- **`luft_chi_log_2026-01-05.csv`** - CSV format example showing proper timestamp and precision formatting
- **`luft_event_2026-01-05.json`** - JSON format example for API/machine-readable data
- **`luft_event_summary_2026-01-05.md`** - Markdown format example for human-readable reports

### Templates
- **`cline_convergence_latex_template.tex`** - LaTeX template for arXiv/Zenodo submissions

### Scripts
- **`luft_transcription_examples.py`** - Comprehensive Python script demonstrating:
  - Event validation using imperial constants
  - Display of fundamental constants and unifications
  - CSV export with proper formatting
  - JSON export with proper structure
  - Timestamp formatting with millisecond precision

## Usage

### Running the Example Script

```bash
# From the repository root
python3 examples/luft_transcription_examples.py
```

This will:
1. Validate χ measurements from the January 5, 2026 event
2. Display fundamental constants and unifications
3. Create example CSV file at `/tmp/luft_chi_log_example.csv`
4. Create example JSON file at `/tmp/luft_event_example.json`
5. Demonstrate proper timestamp formatting

### Importing Constants in Your Code

```python
# Add the repository root to your Python path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import LUFT Imperial Constants
from imperial_constants_v1_0 import (
    CHI_LIMIT,
    COUPLING_FREQ_HZ,
    validate_chi,
    get_fundamental_unifications
)

# Use the constants
result = validate_chi(0.1498, "2026-01-05T00:45:00.000Z")
print(result['status'])  # AT_BOUNDARY
```

## Standards Reference

All examples follow the standards defined in:
- **`LUFT_DATA_TRANSCRIPTION_MASTER_REFERENCE.md`** (repository root)
- **`imperial_constants_v1_0.py`** (repository root)

## Data Format Standards

### CSV Format
- Timestamps in ISO 8601 format with `.000` millisecond precision
- Status codes in uppercase (e.g., `AT_BOUNDARY`, `BELOW_LIMIT`)
- Decimal precision: 4 places for χ values
- File naming: `luft_chi_log_YYYY-MM-DD.csv`

### JSON Format
- ISO 8601 timestamps with `Z` suffix for UTC
- Structured with `event_metadata`, `observations`, and `summary` sections
- All numeric values preserve full precision
- File naming: `luft_event_YYYY-MM-DD.json`

### Markdown Format
- Tables use pipe `|` delimiters
- Timestamps formatted as `YYYY-MM-DD HH:MM:SS`
- Bold formatting for boundary events
- File naming: `luft_event_summary_YYYY-MM-DD.md`

## LaTeX Template

The LaTeX template (`cline_convergence_latex_template.tex`) includes:
- Proper Unicode support for χ symbol
- `siunitx` package for unit formatting
- Equation environments for mathematical expressions
- Example table showing χ evolution during an event
- Bibliography setup (commented out)

Compile with:
```bash
pdflatex cline_convergence_latex_template.tex
```

## Core Imperial Metrics

| Constant | Symbol | Value | ASCII Safe |
|----------|--------|-------|------------|
| Universal Boundary | χ | 0.15 | chi |
| Coupling Frequency | Λ | 20.55 Hz | Lambda |
| Gravity Relation | 1/χ | 6.6667 | 1/chi |
| Mass Ratio Root | (mₑ/mₚ)^(1/4) | 0.1528 | (m_e/m_p)^(1/4) |

## Support

For questions or issues:
- See `LUFT_DATA_TRANSCRIPTION_MASTER_REFERENCE.md` for complete documentation
- Review the troubleshooting matrix in the master reference
- Check the example scripts for working implementations

---

**Version:** 1.0  
**Date:** 2026-01-23  
**Author:** Carl Dean Cline Sr.  
**License:** CC BY 4.0
