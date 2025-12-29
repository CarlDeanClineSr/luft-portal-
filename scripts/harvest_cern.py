#!/usr/bin/env python3
"""
CERN Document Server Paper Harvester for LUFT Portal
Fetches recent physics papers from CERN Document Server and filters for LUFT-relevant topics.
"""

import os
import json
import requests
import feedparser
from datetime import datetime, timedelta, timezone
from pathlib import Path

# LUFT-relevant keywords for filtering
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
    'particle physics',
    'high energy physics',
]

# CERN collections to search
CERN_COLLECTIONS = [
    'Preprints',
    'Published Articles',
    'CERN Yellow Reports',
]


def fetch_cern_papers(search_query, max_results=100):
    """Fetch recent papers from CERN Document Server API."""
    # CERN CDS often blocks automated requests to their JSON API
    # We'll use their RSS feed instead which is more accessible
    base_url = 'https://cds.cern.ch/rss'
    
    params = {
        'p': search_query,
        'rg': min(max_results, 100),  # RSS feeds typically limit to 100
        'ln': 'en',  # Language English
    }
    
    try:
        print(f"Fetching CERN papers with query: {search_query[:50]}...")
        response = requests.get(base_url, params=params, timeout=30, headers={
            'User-Agent': 'LUFT-Portal-Harvester/1.0 (Physics Research)'
        })
        response.raise_for_status()
        
        # Parse RSS feed using feedparser
        feed = feedparser.parse(response.content)
        papers = []
        
        for entry in feed.entries:
            # Extract paper information from RSS entry
            paper = {
                'id': entry.get('id', '').split('/')[-1],
                'title': entry.get('title', '').replace('\n', ' ').strip(),
                'authors': [],
                'summary': entry.get('summary', '').replace('\n', ' ').strip(),
                'published': entry.get('published', ''),
                'categories': [],
                'link': entry.get('link', ''),
                'source': 'cern',
            }
            
            # Extract authors if available
            if hasattr(entry, 'authors'):
                for author in entry.authors:
                    if hasattr(author, 'name'):
                        paper['authors'].append(author.name)
            elif 'author' in entry:
                paper['authors'].append(entry.author)
            
            # Extract categories from tags
            if hasattr(entry, 'tags'):
                paper['categories'] = [tag.term for tag in entry.tags]
            
            papers.append(paper)
        
        return papers
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching CERN papers: {e}")
        print(f"  Note: CERN API may be temporarily unavailable or blocking automated requests")
        return []
    except Exception as e:
        print(f"Error parsing CERN response: {e}")
        return []


def is_luft_relevant(paper):
    """Check if a paper is relevant to LUFT research based on keywords."""
    text_to_search = (
        str(paper.get('title', '')) + ' ' + 
        str(paper.get('summary', '')) + ' ' + 
        ' '.join(paper.get('categories', []))
    ).lower()
    
    for keyword in LUFT_KEYWORDS:
        if keyword.lower() in text_to_search:
            return True
    
    return False


def save_papers(papers, output_dir):
    """Save papers to JSON files."""
    now = datetime.now(timezone.utc)
    timestamp = now.strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f'cern_harvest_{timestamp}.json'
    
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
    print("LUFT Portal - CERN Paper Harvester")
    print("=" * 60)
    print("\nNote: CERN Document Server may block automated requests.")
    print("This is expected behavior and the script will handle it gracefully.\n")
    
    # Set up output directory
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    output_dir = repo_root / 'data' / 'papers' / 'cern'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Build search queries for LUFT-relevant topics
    search_queries = [
        'plasma physics',
        'cosmology',
        'gravitational waves',
        'unified field theory',
        'magnetohydrodynamics',
        'space physics',
    ]
    
    all_papers = []
    
    # Fetch papers for each query
    for query in search_queries:
        papers = fetch_cern_papers(query, max_results=50)
        print(f"  Found {len(papers)} papers for query: {query}")
        all_papers.extend(papers)
    
    # Remove duplicates based on paper ID
    unique_papers = {}
    for paper in all_papers:
        if paper['id']:
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
        
        # Print sample of papers
        print("\nSample of harvested papers:")
        for paper in relevant_papers[:3]:
            print(f"\n  • {paper.get('title', 'No title')}")
            print(f"    Authors: {', '.join(paper.get('authors', [])[:3])}")
            print(f"    Link: {paper.get('link', 'No link')}")
    else:
        print("\n⚠️  No relevant papers found in this harvest.")
        print("This may be due to API restrictions or no recent papers matching criteria.")
        print("The arXiv harvester will still provide physics papers for the LUFT Portal.")


if __name__ == '__main__':
    main()
