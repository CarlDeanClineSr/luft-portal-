#!/usr/bin/env python3
"""
arXiv Paper Parser & Relevance Ranker
Analyzes harvested papers and ranks by relevance to LUFT research
Author: Carl Dean Cline Sr. / LUFT Portal
Date: 2026-01-03
"""

import json
import re
from pathlib import Path
from collections import defaultdict
import datetime

# Keywords for relevance scoring (weighted by importance)
RELEVANCE_KEYWORDS = {
    # Core discovery keywords (highest weight)
    'plasma boundary': 10,
    'universal constant': 10,
    'causality constraint': 10,
    'chi': 9,
    'χ': 9,
    
    # Primary physics keywords
    'magnetohydrodynamics': 8,
    'mhd': 8,
    'firehose instability': 8,
    'plasma instability': 7,
    'relativistic plasma': 7,
    'magnetized plasma': 7,
    
    # Theoretical framework
    'causality': 6,
    'anomalous mhd': 7,
    'electroweak': 6,
    'pseudoscalar': 6,
    'temporal correlation': 6,
    
    # Observational domains
    'solar wind': 5,
    'magnetosphere': 5,
    'mars': 5,
    'parker solar probe': 6,
    'maven': 5,
    
    # Related phenomena
    'shock': 5,
    'turbulence': 4,
    'magnetic field': 4,
    'wave packet': 5,
    'harmonic': 5,
    
    # Astrophysical connections
    'black hole': 4,
    'accretion disk': 5,
    'neutron star': 4,
    'gravitational wave': 4,
    
    # Authors we care about
    'cordeiro': 8,
    'giovannini': 8,
    'hoult': 7,
    'kovtun': 7,
    'speranza': 7,
    'noronha': 7,
}

def load_harvest_json(filepath):
    """Load the arXiv harvest JSON file"""
    with open(filepath, 'r') as f:
        return json.load(f)

def calculate_relevance_score(paper):
    """Calculate relevance score for a paper"""
    score = 0
    text = f"{paper.get('title', '')} {paper.get('summary', '')} {' '.join(paper.get('authors', []))}".lower()
    
    # Check each keyword
    matches = []
    for keyword, weight in RELEVANCE_KEYWORDS.items():
        if keyword.lower() in text:
            count = text.count(keyword.lower())
            contribution = weight * count
            score += contribution
            if count > 0:
                matches.append(f"{keyword} (×{count}, +{contribution})")
    
    return score, matches

def rank_papers(papers):
    """Rank papers by relevance score"""
    ranked = []
    for paper in papers:
        score, matches = calculate_relevance_score(paper)
        if score > 0:  # Only include papers with some relevance
            paper['relevance_score'] = score
            paper['keyword_matches'] = matches
            ranked.append(paper)
    
    # Sort by score descending
    ranked.sort(key=lambda x: x['relevance_score'], reverse=True)
    return ranked

def format_paper_summary(paper, rank):
    """Format a paper for display"""
    title = paper.get('title', 'Unknown Title')
    authors = paper.get('authors', [])
    author_str = ', '.join(authors[:3])
    if len(authors) > 3:
        author_str += f" et al. ({len(authors)} total)"
    
    categories = ', '.join(paper.get('categories', []))
    score = paper.get('relevance_score', 0)
    link = paper.get('link', '')
    published = paper.get('published', '')[:10]  # Just date
    
    matches = paper.get('keyword_matches', [])
    match_summary = ', '.join(matches[:5])
    if len(matches) > 5:
        match_summary += f" (+{len(matches)-5} more)"
    
    return f"""
{'='*80}
RANK #{rank} - RELEVANCE SCORE: {score}
{'='*80}
Title: {title}
Authors: {author_str}
Published: {published}
Categories: {categories}
Link: {link}

Key Matches: {match_summary}

Abstract: {paper.get('summary', 'N/A')[:300]}...

"""

def generate_bibtex(paper):
    """Generate BibTeX entry for a paper"""
    # Extract arXiv ID from link
    arxiv_id = paper.get('link', '').split('/')[-1].replace('v1', '')
    
    # Clean title
    title = paper.get('title', 'Unknown').replace('\n', ' ').strip()
    
    # Format authors
    authors = paper.get('authors', [])
    author_str = ' and '.join(authors)
    
    # Extract year
    published = paper.get('published', '')[:4]
    
    # Create citation key
    first_author = authors[0].split()[-1].lower() if authors else 'unknown'
    cite_key = f"{first_author}{published}"
    
    return f"""@article{{{cite_key},
    title = {{{title}}},
    author = {{{author_str}}},
    journal = {{arXiv preprint arXiv:{arxiv_id}}},
    year = {{{published}}},
    eprint = {{{arxiv_id}}},
    archivePrefix = {{arXiv}},
    primaryClass = {{{paper.get('categories', [''])[0]}}},
    url = {{{paper.get('link', '')}}}
}}"""

def main():
    print("="*80)
    print("LUFT PORTAL - arXiv Paper Relevance Analyzer")
    print("="*80)
    print()
    
    # Find most recent harvest file
    data_dir = Path('data/papers/arxiv')
    harvest_files = sorted(data_dir.glob('arxiv_harvest_*.json'), reverse=True)
    
    if not harvest_files:
        print("❌ No harvest files found!")
        return
    
    harvest_file = harvest_files[0]
    print(f"📂 Loading: {harvest_file}")
    
    # Load and rank papers
    data = load_harvest_json(harvest_file)
    papers = data if isinstance(data, list) else data.get('papers', [])
    
    print(f"📊 Total papers in harvest: {len(papers)}")
    print(f"🔍 Analyzing relevance...")
    print()
    
    ranked = rank_papers(papers)
    
    print(f"✅ Found {len(ranked)} relevant papers")
    print()
    
    # Generate report
    report_dir = Path('reports/arxiv_analysis')
    report_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = report_dir / f'relevance_ranking_{timestamp}.md'
    bibtex_file = report_dir / f'top_papers_{timestamp}.bib'
    
    with open(report_file, 'w') as f:
        f.write("# arXiv Paper Relevance Analysis\n\n")
        f.write(f"**Generated:** {datetime.datetime.now().isoformat()}\n")
        f.write(f"**Source:** {harvest_file.name}\n")
        f.write(f"**Total Papers:** {len(papers)}\n")
        f.write(f"**Relevant Papers:** {len(ranked)}\n\n")
        f.write("---\n\n")
        f.write("## Top 20 Most Relevant Papers\n\n")
        
        for i, paper in enumerate(ranked[:20], 1):
            f.write(format_paper_summary(paper, i))
    
    # Generate BibTeX for top 20
    with open(bibtex_file, 'w') as f:
        f.write("% Top 20 Most Relevant Papers from arXiv Harvest\n")
        f.write(f"% Generated: {datetime.datetime.now().isoformat()}\n\n")
        for paper in ranked[:20]:
            f.write(generate_bibtex(paper))
            f.write("\n\n")
    
    print(f"📝 Report saved: {report_file}")
    print(f"📚 BibTeX saved: {bibtex_file}")
    print()
    
    # Display top 10 in console
    print("="*80)
    print("TOP 10 MOST RELEVANT PAPERS")
    print("="*80)
    print()
    
    for i, paper in enumerate(ranked[:10], 1):
        print(f"#{i} - Score: {paper['relevance_score']}")
        print(f"    {paper.get('title', 'Unknown')}")
        print(f"    {paper.get('link', '')}")
        print()
    
    # Statistics
    print("="*80)
    print("STATISTICS")
    print("="*80)
    print()
    
    if ranked:
        scores = [p['relevance_score'] for p in ranked]
        print(f"Score range: {min(scores)} - {max(scores)}")
        print(f"Average score: {sum(scores)/len(scores):.1f}")
        print(f"Papers with score > 50: {len([s for s in scores if s > 50])}")
        print(f"Papers with score > 100: {len([s for s in scores if s > 100])}")
    
    print()
    print("✅ Analysis complete!")

if __name__ == '__main__':
    main()
