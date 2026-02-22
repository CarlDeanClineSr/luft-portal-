#!/usr/bin/env python3
"""
LUFT Portal - INSPIRE-HEP Paper Harvester (v2)
Fetches recent papers from plasma physics and related fields.

Improvements over v1:
- Limits total results to top 10 most relevant papers
- Adds timestamp to output JSON filename to track harvests
- Deletes old harvest files before creating a new one
- Improved console output: shows titles only, not full metadata
- Sorts results by date for relevance
"""

import requests
import json
import glob
import os
from datetime import datetime

# INSPIRE API endpoint
INSPIRE_API = "https://inspirehep.net/api/literature"

# Research topics to monitor
TOPICS = [
    "plasma physics",
    "magnetohydrodynamics",
    "quark-gluon plasma",
    "heavy ion collisions",
    "particle detector plasma",
    "tokamak plasma"
]

# Maximum total papers to retain after deduplication and sorting
MAX_TOTAL_PAPERS = 10


def fetch_inspire_papers(query, max_results=10):
    """Fetch papers from INSPIRE-HEP API for a single topic."""
    params = {
        'q': query,
        'sort': 'mostrecent',
        'size': max_results,
        'fields': 'titles,authors,arxiv_eprints,publication_info,abstracts,control_number,created'
    }

    try:
        response = requests.get(INSPIRE_API, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get('hits', {}).get('hits', [])
    except Exception as e:
        print(f"  Error fetching '{query}': {e}")
        return []


def main():
    print("=" * 60)
    print("LUFT Portal - INSPIRE-HEP Paper Harvester")
    print("=" * 60)

    all_papers = []
    seen_ids = set()

    for topic in TOPICS:
        print(f"Fetching: {topic}...")
        papers = fetch_inspire_papers(topic, max_results=10)
        for paper in papers:
            paper_id = paper.get('id')
            if paper_id and paper_id not in seen_ids:
                seen_ids.add(paper_id)
                all_papers.append(paper)

    # Sort by creation date (most recent first) and limit to top MAX_TOTAL_PAPERS
    all_papers = sorted(
        all_papers,
        key=lambda p: p.get('created', ''),
        reverse=True
    )[:MAX_TOTAL_PAPERS]

    output_dir = 'data/papers'
    os.makedirs(output_dir, exist_ok=True)

    # Delete old harvest files before creating a new one
    old_files = glob.glob(f'{output_dir}/inspire_papers_*.json')
    for old_file in old_files:
        os.remove(old_file)
        print(f"Deleted old harvest: {old_file}")

    # Save new harvest with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'{output_dir}/inspire_papers_{timestamp}.json'

    with open(output_file, 'w') as f:
        json.dump(all_papers, f, indent=2)

    print(f"\nTop {len(all_papers)} most relevant papers:\n")
    for i, paper in enumerate(all_papers, 1):
        title = paper.get('metadata', {}).get('titles', [{}])[0].get('title', 'No title')
        date = paper.get('created', 'No date')
        print(f"{i}. {title} ({date})")

    print(f"\nSaved {len(all_papers)} papers to {output_file}")


if __name__ == '__main__':
    main()
