#!/usr/bin/env python3
"""
LUFT Portal - INSPIRE-HEP Paper Harvester
Fetches recent papers from plasma physics and related fields
"""

import requests
import json
from datetime import datetime
import os
import glob

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

def fetch_papers(query, max_results=10):
    """Fetch papers from INSPIRE-HEP API"""
    params = {
        'q': query,
        'sort': 'mostrecent',
        'size': max_results,
        'fields': 'titles,authors,arxiv_eprints,publication_info,abstracts,control_number'
    }
    
    try:
        response = requests.get(INSPIRE_API, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get('hits', {}).get('hits', [])
    except Exception as e:
        print(f"  Error fetching {query}: {e}")
        return []

def main():
    print("=" * 60)
    print("LUFT Portal - INSPIRE-HEP Paper Harvester")
    print("=" * 60)
    
    all_papers = []
    seen_ids = set()
    
    for topic in TOPICS:
        print(f"Fetching INSPIRE papers: {topic}...")
        papers = fetch_papers(topic, max_results=10)
        print(f"  Found {len(papers)} papers")
        
        # Deduplicate by control_number
        for paper in papers:
            paper_id = paper.get('id')
            if paper_id and paper_id not in seen_ids:
                seen_ids.add(paper_id)
                all_papers.append(paper)
    
    print(f"\nTotal unique papers: {len(all_papers)}")
    
    output_dir = 'data/papers'
    os.makedirs(output_dir, exist_ok=True)
    
    # Delete all old harvest files
    old_files = glob.glob(f'{output_dir}/inspire_papers_*.json')
    for old_file in old_files:
        os.remove(old_file)
        print(f"🗑️  Deleted old harvest: {old_file}")
    
    # Save new harvest with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'{output_dir}/inspire_papers_{timestamp}.json'
    
    with open(output_file, 'w') as f:
        json.dump(all_papers, f, indent=2)
    
    print(f"\n✅ Saved {len(all_papers)} papers to {output_file}")
    
    # Print sample titles
    print("\nSample of harvested papers:\n")
    for paper in all_papers[:3]:
        title = paper.get('metadata', {}).get('titles', [{}])[0].get('title', 'No title')
        authors = paper.get('metadata', {}).get('authors', [])
        author_names = ', '.join([a.get('full_name', '') for a in authors[:3]])
        print(f"  • {title}")
        print(f"    Authors: {author_names}")
        print()

if __name__ == '__main__':
    main()