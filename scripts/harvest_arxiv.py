#!/usr/bin/env python3
"""
arXiv Paper Harvester for LUFT Portal
Fetches recent physics papers from arXiv API and filters for LUFT-relevant topics.
"""

import os
import json
import requests
import feedparser
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# LUFT-relevant categories and keywords
ARXIV_CATEGORIES = [
    'astro-ph.HE',  # High Energy Astrophysical Phenomena
    'astro-ph.CO',  # Cosmology and Nongalactic Astrophysics
    'physics.plasm-ph',  # Plasma Physics
    'physics.space-ph',  # Space Physics
    'hep-ph',  # High Energy Physics - Phenomenology
    'gr-qc',  # General Relativity and Quantum Cosmology
]

LUFT_KEYWORDS = [
    'plasma',
    'magnetohydrodynamic',
    'MHD',
    'solar wind',
    'cosmic ray',
    'magnetic field',
    'coherence',
    'oscillation',
    'cosmology',
    'dark energy',
    'gravitational wave',
    'unified field',
    'field theory',
    'plasma instability',
    'coronal mass ejection',
    'CME',
    'space weather',
    'heliosphere',
]


def fetch_arxiv_papers(category, max_results=50):
    """Fetch recent papers from arXiv for a given category."""
    base_url = 'https://export.arxiv.org/api/query'
    
    # Search for papers from the last 7 days
    query = f'cat:{category}'
    params = {
        'search_query': query,
        'start': 0,
        'max_results': max_results,
        'sortBy': 'submittedDate',
        'sortOrder': 'descending'
    }
    
    print(f"Fetching arXiv papers for category: {category}")
    feed = feedparser.parse(requests.get(base_url, params=params).url)
    
    papers = []
    for entry in feed.entries:
        paper = {
            'id': entry.id.split('/abs/')[-1],
            'title': entry.title.replace('\n', ' ').strip(),
            'authors': [author.name for author in entry.authors],
            'summary': entry.summary.replace('\n', ' ').strip(),
            'published': entry.published,
            'updated': entry.updated,
            'categories': [tag.term for tag in entry.tags],
            'link': entry.link,
            'pdf_link': entry.link.replace('/abs/', '/pdf/'),
        }
        papers.append(paper)
    
    return papers


def is_luft_relevant(paper):
    """Check if a paper is relevant to LUFT research based on keywords."""
    text_to_search = (paper['title'] + ' ' + paper['summary']).lower()
    
    for keyword in LUFT_KEYWORDS:
        if keyword.lower() in text_to_search:
            return True
    
    return False


def save_papers(papers, output_dir):
    """Save papers to JSON files."""
    now = datetime.now(timezone.utc)
    timestamp = now.strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f'arxiv_harvest_{timestamp}.json'
    
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': timestamp,
            'harvest_date': now.isoformat(),
            'total_papers': len(papers),
            'papers': papers
        }, f, indent=2)
    
    print(f"Saved {len(papers)} papers to {output_file}")
    
    # Also save a latest.json for easy access
    latest_file = output_dir / 'latest.json'
    with open(latest_file, 'w') as f:
        json.dump({
            'timestamp': timestamp,
            'harvest_date': now.isoformat(),
            'total_papers': len(papers),
            'papers': papers
        }, f, indent=2)
    
    return output_file


def main():
    """Main harvesting function."""
    print("=" * 60)
    print("LUFT Portal - arXiv Paper Harvester")
    print("=" * 60)
    
    # Set up output directory
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    output_dir = repo_root / 'data' / 'papers' / 'arxiv'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    all_papers = []
    
    # Fetch papers from each category
    for category in ARXIV_CATEGORIES:
        papers = fetch_arxiv_papers(category, max_results=50)
        print(f"  Found {len(papers)} papers in {category}")
        all_papers.extend(papers)
    
    # Remove duplicates based on paper ID
    unique_papers = {}
    for paper in all_papers:
        unique_papers[paper['id']] = paper
    all_papers = list(unique_papers.values())
    
    print(f"\nTotal unique papers: {len(all_papers)}")
    
    # Filter for LUFT-relevant papers
    relevant_papers = [p for p in all_papers if is_luft_relevant(p)]
    print(f"LUFT-relevant papers: {len(relevant_papers)}")
    
    # Save papers
    if relevant_papers:
        output_file = save_papers(relevant_papers, output_dir)
        print(f"\n✅ Harvest complete!")
        print(f"📄 Output: {output_file}")
    else:
        print("\n⚠️  No relevant papers found in this harvest.")
    
    # Print sample of papers
    if relevant_papers:
        print("\nSample of harvested papers:")
        for paper in relevant_papers[:3]:
            print(f"\n  • {paper['title']}")
            print(f"    Authors: {', '.join(paper['authors'][:3])}")
            print(f"    Categories: {', '.join(paper['categories'][:3])}")
            print(f"    Link: {paper['link']}")


if __name__ == '__main__':
    main()
