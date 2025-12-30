#!/usr/bin/env python3
"""
INSPIRE-HEP Paper Harvester
Fetches plasma physics papers from INSPIRE (no 403 blocks)
"""

import requests
import json
import os
from datetime import datetime, timezone
from pathlib import Path

# INSPIRE-HEP API (open, no auth needed)
BASE_URL = "https://inspirehep.net/api"

# Fields to retrieve from INSPIRE-HEP API
INSPIRE_FIELDS = 'titles,authors,arxiv_eprints,publication_info,abstracts,urls'

QUERIES = [
    "plasma physics",
    "magnetohydrodynamics",
    "quark-gluon plasma",
    "heavy ion collisions",
    "particle detector plasma",
    "tokamak plasma"
]

def fetch_inspire_papers(query, max_results=50):
    """Fetch papers from INSPIRE-HEP"""
    print(f"Fetching INSPIRE papers: {query}...")
    
    url = f"{BASE_URL}/literature"
    params = {
        'q': query,
        'size': max_results,
        'sort': 'mostrecent',
        'fields': INSPIRE_FIELDS
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        papers = data.get('hits', {}).get('hits', [])
        
        print(f"  Found {len(papers)} papers")
        return papers
        
    except requests.exceptions.RequestException as e:
        print(f"  Error: {e}")
        return []

def save_papers(all_papers, output_dir='data/papers'):
    """Save papers to JSON"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    output_file = output_path / f"inspire_papers_{timestamp}.json"
    
    with open(output_file, 'w') as f:
        json.dump(all_papers, f, indent=2)
    
    print(f"\nSaved {len(all_papers)} papers to {output_file}")
    
    # Also save a latest.json for easy access
    latest_file = output_path / 'inspire_latest.json'
    with open(latest_file, 'w') as f:
        json.dump(all_papers, f, indent=2)
    
    return output_file

def main():
    print("="*60)
    print("LUFT Portal - INSPIRE-HEP Paper Harvester")
    print("="*60)
    
    all_papers = []
    
    for query in QUERIES:
        papers = fetch_inspire_papers(query)
        all_papers.extend(papers)
    
    # Remove duplicates
    unique_papers = []
    seen_ids = set()
    
    for paper in all_papers: 
        paper_id = paper.get('id')
        if paper_id and paper_id not in seen_ids:
            unique_papers.append(paper)
            seen_ids.add(paper_id)
    
    print(f"\nTotal unique papers: {len(unique_papers)}")
    
    output_file = save_papers(unique_papers)
    
    print("\n✅ Paper harvest complete!")
    
    # Print sample of papers
    if unique_papers:
        print("\nSample of harvested papers:")
        for paper in unique_papers[:3]:
            metadata = paper.get('metadata', {})
            titles = metadata.get('titles', [])
            title = titles[0].get('title', 'No title') if titles else 'No title'
            authors = metadata.get('authors', [])
            author_names = ', '.join([a.get('full_name', '') for a in authors[:3]])
            print(f"\n  • {title}")
            if author_names:
                print(f"    Authors: {author_names}")

if __name__ == "__main__":
    main()
