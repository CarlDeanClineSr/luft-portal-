#!/usr/bin/env python3
"""
Paper Parameter Extractor
==========================

Extracts specific parameters, periods, and thresholds from arXiv paper
abstracts and titles. Searches for mentions of 0.9-hour wave packets,
temporal correlations, and chi-like thresholds.

Author: Carl Dean Cline Sr.
Created: January 3, 2026
Location: Lincoln, Nebraska, USA
Email: CARLDCLINE@GMAIL.COM

Purpose:
    The LUFT system discovered a 0.9-hour fundamental wave packet and
    13 temporal correlation modes. This tool scans harvested arXiv papers
    to find related mentions of:
    - 0.9-hour periods or ~54-minute oscillations
    - Temporal correlations and time delays
    - Thresholds around 0.15 or similar critical values
    - Wave packets, harmonics, and periodicities

Usage:
    python tools/paper_param_extractor.py
    python tools/paper_param_extractor.py --search-term "0.9"
    python tools/paper_param_extractor.py --harvest-file data/papers/arxiv/arxiv_harvest_20260102_061437.json
    python tools/paper_param_extractor.py --full-abstracts
"""

import json
import re
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any


def load_arxiv_harvest(json_path: str) -> List[Dict[str, Any]]:
    """
    Load arXiv harvest JSON file.
    
    Args:
        json_path: Path to the JSON file
    
    Returns:
        List of paper dictionaries
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both direct list and dictionary with 'papers' key
    if isinstance(data, dict) and 'papers' in data:
        return data['papers']
    elif isinstance(data, list):
        return data
    else:
        raise ValueError(f"Unexpected JSON structure in {json_path}")


def search_for_patterns(paper: Dict[str, Any], patterns: List[str]) -> Dict[str, List[str]]:
    """
    Search paper title and abstract for specific patterns.
    
    Args:
        paper: Paper dictionary with 'title' and 'summary' keys
        patterns: List of regex patterns to search for
    
    Returns:
        Dictionary of pattern matches
    """
    results = {}
    
    # Combine title and abstract for searching
    text = paper.get('title', '') + ' ' + paper.get('summary', '')
    text_lower = text.lower()
    
    for pattern in patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        if matches:
            results[pattern] = matches
    
    return results


def extract_time_periods(text: str) -> List[str]:
    """
    Extract mentions of time periods from text.
    
    Args:
        text: Text to search
    
    Returns:
        List of time period mentions
    """
    # Patterns for time periods with improved regex
    patterns = [
        r'\d+(?:\.\d+)?\s*(?:hour|hr|h)\b',
        r'\d+(?:\.\d+)?\s*(?:minute|min|m)\b',
        r'\d+(?:\.\d+)?\s*(?:second|sec|s)\b',
        r'\d+(?:\.\d+)?\s*(?:day|d)\b',
        r'\bperiod[s]?\s+of\s+\d+(?:\.\d+)?',
        r'\boscillation[s]?\s+(?:of|at|with)\s+\d+(?:\.\d+)?',
    ]
    
    periods = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        periods.extend(matches)
    
    return periods


def extract_thresholds(text: str) -> List[str]:
    """
    Extract mentions of numerical thresholds.
    
    Args:
        text: Text to search
    
    Returns:
        List of threshold mentions
    """
    patterns = [
        r'\b0\.\d+\b',  # Decimal numbers like 0.15, 0.9
        r'\bthreshold[s]?\s+(?:of|at|near|around)\s+\d+(?:\.\d+)?',
        r'\bcritical\s+(?:value|threshold|point)[s]?\s+(?:of|at)?\s*\d+(?:\.\d+)?',
        r'\bsaturate[s]?\s+at\s+\d+(?:\.\d+)?',
        r'\blimit[s]?\s+(?:of|at)\s+\d+(?:\.\d+)?',
    ]
    
    thresholds = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        thresholds.extend(matches)
    
    return thresholds


def main():
    parser = argparse.ArgumentParser(
        description='Extract parameters and patterns from arXiv papers')
    parser.add_argument('--harvest-file',
                       default=None,
                       help='Specific arXiv harvest JSON file to analyze')
    parser.add_argument('--harvest-dir',
                       default='data/papers/arxiv',
                       help='Directory containing arXiv harvest files')
    parser.add_argument('--search-term',
                       default=None,
                       help='Specific term to search for (e.g., "0.9", "period")')
    parser.add_argument('--full-abstracts',
                       action='store_true',
                       help='Display full abstracts instead of excerpts')
    parser.add_argument('--max-papers',
                       type=int,
                       default=None,
                       help='Maximum number of papers to display')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("LUFT Paper Parameter Extractor")
    print("=" * 70)
    print(f"Analysis Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print()
    
    # Load harvest files
    harvest_files = []
    if args.harvest_file:
        harvest_files = [Path(args.harvest_file)]
    else:
        harvest_dir = Path(args.harvest_dir)
        if harvest_dir.exists():
            harvest_files = sorted(harvest_dir.glob('arxiv_harvest_*.json'))
        else:
            print(f"Error: Directory {harvest_dir} not found!")
            return
    
    if not harvest_files:
        print(f"No harvest files found!")
        return
    
    print(f"Found {len(harvest_files)} harvest file(s):")
    for f in harvest_files:
        print(f"  - {f.name}")
    print()
    
    # Load all papers
    all_papers = []
    for harvest_file in harvest_files:
        try:
            papers = load_arxiv_harvest(harvest_file)
            all_papers.extend(papers)
            print(f"Loaded {len(papers)} papers from {harvest_file.name}")
        except Exception as e:
            print(f"Error loading {harvest_file}: {e}")
    
    print(f"\nTotal papers: {len(all_papers)}")
    print()
    
    # Define search categories
    print("=" * 70)
    print("SEARCHING FOR LUFT-RELEVANT PATTERNS")
    print("=" * 70)
    
    # Category 1: 0.9-hour wave packets and harmonics
    print("\n1. Papers mentioning 0.9-hour periods or ~54-minute oscillations:")
    print("-" * 70)
    
    patterns_09h = [r'0\.9\s*h', r'54\s*min', r'0\.9[\s-]*hour', r'54[\s-]*minute']
    papers_09h = []
    
    for paper in all_papers:
        text = paper.get('title', '') + ' ' + paper.get('summary', '')
        matches = []
        for pattern in patterns_09h:
            if re.search(pattern, text, re.IGNORECASE):
                matches.append(pattern)
        
        if matches:
            papers_09h.append((paper, matches))
    
    if papers_09h:
        for i, (paper, matches) in enumerate(papers_09h[:args.max_papers], 1):
            print(f"\n[{i}] {paper['title']}")
            print(f"    arXiv: {paper['id']}")
            print(f"    Categories: {', '.join(paper.get('categories', []))}")
            print(f"    Matched patterns: {', '.join(matches)}")
            
            if args.full_abstracts:
                print(f"    Abstract: {paper.get('summary', 'N/A')}")
            else:
                abstract = paper.get('summary', 'N/A')
                print(f"    Abstract excerpt: {abstract[:300]}...")
    else:
        print("  No papers found with explicit 0.9-hour mentions.")
    
    # Category 2: Period/Periodicity mentions
    print("\n\n2. Papers mentioning periods, periodicities, or oscillations:")
    print("-" * 70)
    
    period_keywords = ['period', 'periodic', 'oscillation', 'harmonic', 'wave packet', 'frequency']
    papers_periods = []
    
    for paper in all_papers:
        text_lower = (paper.get('title', '') + ' ' + paper.get('summary', '')).lower()
        
        # Check for period keywords
        found_keywords = [kw for kw in period_keywords if kw in text_lower]
        
        if found_keywords:
            # Extract time periods
            periods = extract_time_periods(text_lower)
            if periods:
                papers_periods.append((paper, found_keywords, periods))
    
    # Sort by number of period mentions
    papers_periods.sort(key=lambda x: len(x[2]), reverse=True)
    
    display_count = min(10, len(papers_periods))
    if args.max_papers:
        display_count = min(args.max_papers, len(papers_periods))
    
    if papers_periods:
        for i, (paper, keywords, periods) in enumerate(papers_periods[:display_count], 1):
            print(f"\n[{i}] {paper['title']}")
            print(f"    arXiv: {paper['id']}")
            print(f"    Categories: {', '.join(paper.get('categories', []))}")
            print(f"    Keywords found: {', '.join(keywords)}")
            print(f"    Time periods mentioned: {', '.join(set(periods[:5]))}")
            
            if args.full_abstracts:
                print(f"    Abstract: {paper.get('summary', 'N/A')}")
            else:
                abstract = paper.get('summary', 'N/A')
                print(f"    Abstract excerpt: {abstract[:250]}...")
    else:
        print("  No papers found with period mentions.")
    
    # Category 3: Threshold/critical value mentions
    print("\n\n3. Papers mentioning thresholds or critical values:")
    print("-" * 70)
    
    threshold_keywords = ['threshold', 'critical', 'saturate', 'limit', 'boundary']
    papers_thresholds = []
    
    for paper in all_papers:
        text_lower = (paper.get('title', '') + ' ' + paper.get('summary', '')).lower()
        
        found_keywords = [kw for kw in threshold_keywords if kw in text_lower]
        
        if found_keywords:
            thresholds = extract_thresholds(text_lower)
            if thresholds:
                papers_thresholds.append((paper, found_keywords, thresholds))
    
    papers_thresholds.sort(key=lambda x: len(x[2]), reverse=True)
    
    display_count = min(10, len(papers_thresholds))
    if args.max_papers:
        display_count = min(args.max_papers, len(papers_thresholds))
    
    if papers_thresholds:
        for i, (paper, keywords, thresholds) in enumerate(papers_thresholds[:display_count], 1):
            print(f"\n[{i}] {paper['title']}")
            print(f"    arXiv: {paper['id']}")
            print(f"    Categories: {', '.join(paper.get('categories', []))}")
            print(f"    Keywords found: {', '.join(keywords)}")
            print(f"    Thresholds mentioned: {', '.join(set(thresholds[:5]))}")
            
            if args.full_abstracts:
                print(f"    Abstract: {paper.get('summary', 'N/A')}")
            else:
                abstract = paper.get('summary', 'N/A')
                print(f"    Abstract excerpt: {abstract[:250]}...")
    else:
        print("  No papers found with threshold mentions.")
    
    # Category 4: Temporal correlation mentions
    print("\n\n4. Papers mentioning temporal correlations or time delays:")
    print("-" * 70)
    
    temporal_keywords = ['temporal', 'correlation', 'delay', 'lag', 'time-dependent', 
                        'causality', 'precedence']
    papers_temporal = []
    
    for paper in all_papers:
        text_lower = (paper.get('title', '') + ' ' + paper.get('summary', '')).lower()
        
        found_keywords = [kw for kw in temporal_keywords if kw in text_lower]
        
        if found_keywords:
            papers_temporal.append((paper, found_keywords))
    
    papers_temporal.sort(key=lambda x: len(x[1]), reverse=True)
    
    display_count = min(10, len(papers_temporal))
    if args.max_papers:
        display_count = min(args.max_papers, len(papers_temporal))
    
    if papers_temporal:
        for i, (paper, keywords) in enumerate(papers_temporal[:display_count], 1):
            print(f"\n[{i}] {paper['title']}")
            print(f"    arXiv: {paper['id']}")
            print(f"    Categories: {', '.join(paper.get('categories', []))}")
            print(f"    Keywords found: {', '.join(keywords)}")
            
            if args.full_abstracts:
                print(f"    Abstract: {paper.get('summary', 'N/A')}")
            else:
                abstract = paper.get('summary', 'N/A')
                print(f"    Abstract excerpt: {abstract[:250]}...")
    else:
        print("  No papers found with temporal correlation mentions.")
    
    # Custom search term
    if args.search_term:
        print(f"\n\n5. Papers mentioning custom search term: '{args.search_term}'")
        print("-" * 70)
        
        papers_custom = []
        for paper in all_papers:
            text = paper.get('title', '') + ' ' + paper.get('summary', '')
            if args.search_term.lower() in text.lower():
                papers_custom.append(paper)
        
        display_count = min(10, len(papers_custom))
        if args.max_papers:
            display_count = min(args.max_papers, len(papers_custom))
        
        if papers_custom:
            for i, paper in enumerate(papers_custom[:display_count], 1):
                print(f"\n[{i}] {paper['title']}")
                print(f"    arXiv: {paper['id']}")
                print(f"    Categories: {', '.join(paper.get('categories', []))}")
                
                if args.full_abstracts:
                    print(f"    Abstract: {paper.get('summary', 'N/A')}")
                else:
                    abstract = paper.get('summary', 'N/A')
                    print(f"    Abstract excerpt: {abstract[:250]}...")
        else:
            print(f"  No papers found mentioning '{args.search_term}'.")
    
    # Summary statistics
    print("\n\n" + "=" * 70)
    print("SUMMARY STATISTICS")
    print("=" * 70)
    print(f"Total papers analyzed: {len(all_papers)}")
    print(f"Papers with 0.9-hour mentions: {len(papers_09h)}")
    print(f"Papers with period/oscillation mentions: {len(papers_periods)}")
    print(f"Papers with threshold mentions: {len(papers_thresholds)}")
    print(f"Papers with temporal correlation mentions: {len(papers_temporal)}")
    if args.search_term:
        print(f"Papers matching '{args.search_term}': {len(papers_custom)}")
    
    # Save results summary
    results_dir = Path('plots')
    results_dir.mkdir(exist_ok=True)
    
    summary_file = results_dir / 'paper_extraction_summary.json'
    
    summary = {
        'timestamp': datetime.utcnow().isoformat(),
        'total_papers': len(all_papers),
        'categories': {
            '0.9_hour_mentions': len(papers_09h),
            'period_mentions': len(papers_periods),
            'threshold_mentions': len(papers_thresholds),
            'temporal_correlation_mentions': len(papers_temporal)
        },
        'papers_with_09h': [
            {
                'id': p[0]['id'],
                'title': p[0]['title'],
                'categories': p[0].get('categories', [])
            }
            for p in papers_09h
        ],
        'top_period_papers': [
            {
                'id': p[0]['id'],
                'title': p[0]['title'],
                'categories': p[0].get('categories', []),
                'periods': list(set(p[2]))
            }
            for p in papers_periods[:10]
        ]
    }
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nSummary saved to: {summary_file}")
    
    print("\n" + "=" * 70)
    print("Analysis complete!")
    print("=" * 70)


if __name__ == '__main__':
    main()
