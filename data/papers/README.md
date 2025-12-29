# Physics Paper Harvesting Pipeline

This directory contains automated harvesting scripts for collecting recent physics papers relevant to LUFT Portal research.

## Overview

The paper harvesting system automatically fetches and filters physics papers from major repositories:
- **arXiv**: Comprehensive physics preprint server
- **CERN Document Server**: High-energy physics and related fields

Papers are filtered for LUFT-relevant topics including:
- Plasma physics and magnetohydrodynamics
- Cosmology and unified field theory
- Space weather and solar wind
- Gravitational waves
- Magnetic field dynamics and coherence

## Automation

The harvesting runs automatically via GitHub Actions:
- **Schedule**: Every 6 hours (0 */6 * * *)
- **Workflow**: `.github/workflows/physics_paper_harvester.yml`
- **Manual trigger**: Available via workflow_dispatch

## Output Structure

Harvested papers are stored in structured JSON format:

```
data/papers/
├── arxiv/
│   ├── latest.json                        # Most recent harvest
│   └── arxiv_harvest_YYYYMMDD_HHMMSS.json # Timestamped archives
└── cern/
    ├── latest.json                         # Most recent harvest
    └── cern_harvest_YYYYMMDD_HHMMSS.json   # Timestamped archives
```

### JSON Format

```json
{
  "timestamp": "20251229_220000",
  "harvest_date": "2025-12-29T22:00:00Z",
  "total_papers": 150,
  "papers": [
    {
      "id": "2512.12345v1",
      "title": "Paper Title",
      "authors": ["Author 1", "Author 2"],
      "summary": "Paper abstract...",
      "published": "2025-12-29T00:00:00Z",
      "updated": "2025-12-29T00:00:00Z",
      "categories": ["astro-ph.HE", "physics.plasm-ph"],
      "link": "https://arxiv.org/abs/2512.12345v1",
      "pdf_link": "https://arxiv.org/pdf/2512.12345v1"
    }
  ]
}
```

## Manual Usage

To run the harvesters manually:

```bash
# Install dependencies
pip install requests feedparser beautifulsoup4 pandas

# Harvest from arXiv
python scripts/harvest_arxiv.py

# Harvest from CERN (may be rate-limited)
python scripts/harvest_cern.py
```

## LUFT-Relevant Keywords

Papers are filtered based on these keywords:
- plasma, magnetohydrodynamic, MHD
- solar wind, cosmic ray
- magnetic field, coherence, oscillation
- cosmology, dark energy
- gravitational wave, unified field
- field theory, plasma instability
- coronal mass ejection (CME)
- space weather, heliosphere

## arXiv Categories Monitored

- `astro-ph.HE`: High Energy Astrophysical Phenomena
- `astro-ph.CO`: Cosmology and Nongalactic Astrophysics
- `physics.plasm-ph`: Plasma Physics
- `physics.space-ph`: Space Physics
- `hep-ph`: High Energy Physics - Phenomenology
- `gr-qc`: General Relativity and Quantum Cosmology

## CERN Document Server

Note: CERN CDS may block automated requests. The harvester handles this gracefully with appropriate error messages. When available, it searches for:
- Plasma physics
- Cosmology
- Gravitational waves
- Unified field theory
- Magnetohydrodynamics
- Space physics

## Downstream Usage

The harvested papers can be used for:
- Literature review and research monitoring
- AI-powered paper analysis and summarization
- Trend detection in LUFT-relevant research areas
- Citation network analysis
- Automated research updates

## Maintenance

The system requires minimal maintenance:
- Dependencies are installed automatically in the workflow
- Failed harvests are logged but don't stop the workflow
- Each harvest creates both timestamped and `latest.json` files
- Old harvest files can be archived or removed as needed

## Contributing

To add new paper sources:
1. Create a new harvester script in `scripts/harvest_*.py`
2. Add the harvester to `.github/workflows/physics_paper_harvester.yml`
3. Ensure output follows the standard JSON format
4. Add appropriate error handling
5. Update this README with the new source

---

**Last Updated**: 2025-12-29  
**Maintained by**: LUFT Portal Team
