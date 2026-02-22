#!/usr/bin/env python3
"""
LUFT Portal - INSPIRE-HEP Paper Harvester
Fetches recent papers from plasma physics and related fields.
"""

import math
import requests
import json
from datetime import datetime, timezone
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

MAX_RESULTS_PER_TOPIC = 10

RECENCY_WEIGHT = 40
CITATION_WEIGHT = 30
AUTHOR_WEIGHT = 15
ABSTRACT_WEIGHT = 15

MAX_CITATIONS = 500
MAX_ABSTRACT_CHARS = 500
MAX_AUTHOR_COUNT = 10
RECENCY_WINDOW_DAYS = 3650


def fetch_inspire_papers(query, max_results=MAX_RESULTS_PER_TOPIC):
    """Fetch papers from INSPIRE-HEP API"""
    params = {
        'q': query,
        'sort': 'mostrecent',
        'size': max_results,
        'fields': 'titles,authors,arxiv_eprints,publication_info,abstracts,control_number,citation_count,created'
    }
    
    try:
        response = requests.get(INSPIRE_API, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get('hits', {}).get('hits', [])
    except Exception as e:
        print(f"  Error fetching {query}: {e}")
        return []


def parse_created_date(created_value):
    """Parse INSPIRE created date safely."""
    if not created_value:
        return None
    try:
        parsed = datetime.fromisoformat(created_value.replace('Z', '+00:00'))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def get_paper_key(paper):
    """Return a stable paper key for deduplication."""
    metadata = paper.get('metadata', {})
    control_number = metadata.get('control_number')
    return str(control_number) if control_number is not None else paper.get('id')


def calculate_relevance_score(paper, reference_time=None):
    """Calculate relevance score based on recency, citations, authors, and abstract."""
    metadata = paper.get('metadata', {})
    now = reference_time or datetime.now(timezone.utc)

    created_value = paper.get('created') or metadata.get('created')
    created_date = parse_created_date(created_value)
    recency_score = 0.0
    if created_date:
        age_days = max((now - created_date).days, 0)
        recency_ratio = max(0.0, 1 - (age_days / RECENCY_WINDOW_DAYS))
        recency_score = recency_ratio * RECENCY_WEIGHT

    citation_count = metadata.get('citation_count') or 0
    try:
        citation_count = max(int(citation_count), 0)
    except (TypeError, ValueError):
        citation_count = 0
    # Use log1p scaling so zero citations remain valid while dampening outliers
    # relative to MAX_CITATIONS (a soft saturation point for relevance).
    citation_ratio = min(math.log1p(citation_count) / math.log1p(MAX_CITATIONS), 1.0)
    citation_score = citation_ratio * CITATION_WEIGHT

    authors = metadata.get('authors') or []
    # Modest weight for collaborative work while capping large author lists.
    author_ratio = min(len(authors), MAX_AUTHOR_COUNT) / MAX_AUTHOR_COUNT if authors else 0.0
    author_score = author_ratio * AUTHOR_WEIGHT

    abstract_text = ""
    abstracts = metadata.get('abstracts') or []
    if isinstance(abstracts, list) and abstracts:
        abstract_text = abstracts[0].get('value') or ""
    # Reward presence of an abstract without treating abstract length as quality.
    abstract_score = ABSTRACT_WEIGHT if abstract_text.strip() else 0.0

    return recency_score + citation_score + author_score + abstract_score


def main():
    print("=" * 60)
    print("LUFT Portal - INSPIRE-HEP Paper Harvester")
    print("=" * 60)
    
    paper_map = {}
    topic_stats = []
    total_fetched = 0
    
    for topic in TOPICS:
        print(f"Fetching INSPIRE papers: {topic}...")
        papers = fetch_inspire_papers(topic, max_results=MAX_RESULTS_PER_TOPIC)
        total_fetched += len(papers)
        print(f"  Found {len(papers)} papers")
        
        scored_papers = []
        for paper in papers:
            paper['relevance_score'] = calculate_relevance_score(paper)
            scored_papers.append(paper)

        scored_papers.sort(key=lambda p: p.get('relevance_score', 0), reverse=True)
        top_papers = scored_papers[:MAX_RESULTS_PER_TOPIC]
        topic_stats.append((topic, len(papers), len(top_papers)))

        # Deduplicate by control_number (fallback to id)
        for paper in top_papers:
            paper_key = get_paper_key(paper)
            if not paper_key:
                continue
            existing = paper_map.get(paper_key)
            if not existing or paper.get('relevance_score', 0) > existing.get('relevance_score', 0):
                paper_map[paper_key] = paper

    all_papers = sorted(
        paper_map.values(),
        key=lambda p: p.get('relevance_score', 0),
        reverse=True
    )

    avg_score = (
        sum(p.get('relevance_score', 0) for p in all_papers) / len(all_papers)
        if all_papers else 0.0
    )
    
    output_dir = 'data/papers'
    os.makedirs(output_dir, exist_ok=True)
    
    # Delete all old harvest files
    old_files = glob.glob(f'{output_dir}/inspire_papers_*.json')
    for old_file in old_files:
        os.remove(old_file)
        print(f"🗑️  Deleted old harvest: {old_file}")

    # Save new harvest
    output_file = f'{output_dir}/inspire_latest.json'
    
    with open(output_file, 'w') as f:
        json.dump(all_papers, f, indent=2)
    
    print(f"\n✅ Saved {len(all_papers)} papers to {output_file}")
    
    print("\nSummary by topic:")
    for topic, fetched, retained in topic_stats:
        print(f"  • {topic}: {retained} of {fetched} retained")

    print(f"\nTotal fetched: {total_fetched}")
    print(f"Total unique papers: {len(all_papers)}")
    print(f"Average relevance score: {avg_score:.2f}")

    # Print sample titles
    print("\nTop papers:\n")
    for paper in all_papers[:10]:
        title = paper.get('metadata', {}).get('titles', [{}])[0].get('title', 'No title')
        authors = paper.get('metadata', {}).get('authors', [])
        author_names = ', '.join([a.get('full_name', '') for a in authors[:3]])
        score = paper.get('relevance_score', 0)
        print(f"  • {title} (score: {score:.2f})")
        print(f"    Authors: {author_names}")
        print()

if __name__ == '__main__':
    main()
