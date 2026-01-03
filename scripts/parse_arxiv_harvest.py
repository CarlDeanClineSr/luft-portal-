#!/usr/bin/env python3
"""
parse_arxiv_harvest.py - LUFT Portal arXiv Paper Relevance Analysis

Analyzes harvested arXiv papers and ranks them by relevance using weighted keywords
and author names. Generates markdown reports and BibTeX files for top papers.

Requirements:
- Python 3.10+
- No external dependencies required (uses only standard library)
"""

import json
import re
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict
from typing import List, Dict, Tuple

# ============================================================
# CONFIGURATION
# ============================================================

# Weighted keywords for relevance scoring
KEYWORD_WEIGHTS = {
    # High priority physics concepts
    "plasma boundary": 10,
    "causality constraint": 10,
    
    # Chi-related terms
    "chi": 9,
    "χ": 9,
    
    # MHD and plasma physics
    "magnetohydrodynamics": 8,
    "MHD": 8,
    "firehose instability": 8,
    
    # Anomalous phenomena
    "anomalous": 7,
}

# Weighted author names
AUTHOR_WEIGHTS = {
    "Cordeiro": 8,
    "Giovannini": 8,
    "Hoult": 7,
}

# Number of top papers to include in report
TOP_N_PAPERS = 20

# ============================================================
# PAPER SCORING
# ============================================================

def score_paper(paper: Dict) -> Tuple[int, Dict[str, List[str]]]:
    """
    Score a paper based on keyword and author matches.
    
    Args:
        paper: Dictionary containing paper metadata
        
    Returns:
        Tuple of (total_score, breakdown_dict)
        breakdown_dict contains matched keywords and authors
    """
    total_score = 0
    breakdown = {
        "keywords": [],
        "authors": [],
    }
    
    # Prepare searchable text
    title = paper.get("title", "").lower()
    summary = paper.get("summary", "").lower()
    authors = paper.get("authors", [])
    
    searchable_text = f"{title} {summary}"
    
    # Score keywords
    for keyword, weight in KEYWORD_WEIGHTS.items():
        keyword_lower = keyword.lower()
        if keyword_lower in searchable_text:
            total_score += weight
            breakdown["keywords"].append(f"{keyword} ({weight})")
    
    # Score authors
    for author in authors:
        for target_author, weight in AUTHOR_WEIGHTS.items():
            if target_author.lower() in author.lower():
                total_score += weight
                breakdown["authors"].append(f"{author} ({weight})")
                break  # Only count each author once
    
    return total_score, breakdown

# ============================================================
# FILE OPERATIONS
# ============================================================

def load_latest_harvest(data_dir: Path) -> Dict:
    """
    Load the most recent arXiv harvest file.
    
    Args:
        data_dir: Path to arxiv data directory
        
    Returns:
        Dictionary containing harvest data
    """
    harvest_files = sorted(data_dir.glob("arxiv_harvest_*.json"), reverse=True)
    
    if not harvest_files:
        raise FileNotFoundError(f"No harvest files found in {data_dir}")
    
    latest_file = harvest_files[0]
    print(f"Loading: {latest_file.name}")
    
    with open(latest_file, 'r') as f:
        return json.load(f)

def generate_markdown_report(
    ranked_papers: List[Tuple[Dict, int, Dict]],
    output_path: Path,
    harvest_info: Dict
) -> None:
    """
    Generate a markdown report of ranked papers.
    
    Args:
        ranked_papers: List of (paper, score, breakdown) tuples
        output_path: Path where report should be saved
        harvest_info: Metadata from the harvest file
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    total_papers = harvest_info.get("total_papers", len(harvest_info.get("papers", [])))
    
    lines = []
    lines.append("=" * 60)
    lines.append("LUFT Portal - arXiv Paper Relevance Analysis")
    lines.append("=" * 60)
    lines.append(f"Generated: {timestamp}")
    lines.append(f"Loaded {total_papers} papers from harvest file")
    lines.append("")
    lines.append(f"Top {TOP_N_PAPERS} Most Relevant Papers:")
    lines.append("-" * 60)
    lines.append("")
    
    # Add each paper
    for i, (paper, score, breakdown) in enumerate(ranked_papers[:TOP_N_PAPERS], 1):
        title = paper.get("title", "Untitled")
        authors = paper.get("authors", [])
        link = paper.get("link", "")
        
        # Format authors (show first 5, then et al.)
        if len(authors) <= 5:
            author_str = ", ".join(authors)
        else:
            author_str = ", ".join(authors[:5]) + ", et al."
        
        lines.append(f"{i}. [Score: {score}] {title}")
        lines.append(f"   Authors: {author_str}")
        lines.append(f"   Link: {link}")
        
        # Add score breakdown if there are matches
        if breakdown["keywords"]:
            lines.append(f"   Keywords: {', '.join(breakdown['keywords'])}")
        if breakdown["authors"]:
            lines.append(f"   Author Matches: {', '.join(breakdown['authors'])}")
        
        lines.append("")
    
    # Add summary statistics
    lines.append("-" * 60)
    lines.append("Score Breakdown by Category:")
    lines.append("-" * 60)
    lines.append("")
    
    # Count keyword and author matches
    keyword_counts = defaultdict(int)
    author_counts = defaultdict(int)
    
    for paper, score, breakdown in ranked_papers[:TOP_N_PAPERS]:
        for kw_match in breakdown["keywords"]:
            # Extract keyword name from "keyword (weight)" format
            keyword = kw_match.split(" (")[0]
            keyword_counts[keyword] += 1
        for auth_match in breakdown["authors"]:
            author_counts[auth_match] += 1
    
    lines.append("Keyword Matches in Top Papers:")
    for keyword, count in sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"  - {keyword}: {count} papers")
    
    if author_counts:
        lines.append("")
        lines.append("Author Matches in Top Papers:")
        for author, count in sorted(author_counts.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  - {author}: {count}")
    
    lines.append("")
    lines.append("-" * 60)
    lines.append("Summary Statistics:")
    lines.append("-" * 60)
    lines.append(f"Total papers analyzed: {total_papers}")
    lines.append(f"Papers with non-zero scores: {sum(1 for _, s, _ in ranked_papers if s > 0)}")
    if ranked_papers:
        scores = [s for _, s, _ in ranked_papers]
        lines.append(f"Highest score: {max(scores)}")
        lines.append(f"Average score: {sum(scores) / len(scores):.2f}")
    lines.append("")
    
    # Write to file
    with open(output_path, 'w') as f:
        f.write("\n".join(lines))

def generate_bibtex(
    ranked_papers: List[Tuple[Dict, int, Dict]],
    output_path: Path
) -> None:
    """
    Generate a BibTeX file for top papers.
    
    Args:
        ranked_papers: List of (paper, score, breakdown) tuples
        output_path: Path where BibTeX file should be saved
    """
    entries = []
    
    for i, (paper, score, breakdown) in enumerate(ranked_papers[:TOP_N_PAPERS], 1):
        # Extract arXiv ID for citation key
        arxiv_id = paper.get("id", f"paper{i}")
        # Clean up the ID for use in citation key
        citation_key = arxiv_id.replace(".", "_").replace("v", "_v")
        
        title = paper.get("title", "Untitled")
        authors = paper.get("authors", [])
        
        # Format authors for BibTeX
        author_str = " and ".join(authors)
        
        # Extract year from published date
        published = paper.get("published", "")
        year = published[:4] if published else "YYYY"
        
        # Get arXiv info
        link = paper.get("link", "")
        
        # Create BibTeX entry
        entry = f"""@article{{{citation_key},
  title = {{{{{title}}}}},
  author = {{{author_str}}},
  journal = {{arXiv preprint arXiv:{arxiv_id}}},
  year = {{{year}}},
  url = {{{link}}},
  note = {{LUFT Relevance Score: {score}}}
}}"""
        
        entries.append(entry)
    
    # Write to file
    with open(output_path, 'w') as f:
        f.write("\n\n".join(entries))
        f.write("\n")

# ============================================================
# MAIN EXECUTION
# ============================================================

def main():
    """Main execution function."""
    print("=" * 60)
    print("LUFT Portal - arXiv Paper Relevance Analysis")
    print("=" * 60)
    
    # Set up paths
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    data_dir = repo_root / "data" / "papers" / "arxiv"
    output_dir = repo_root / "reports" / "arxiv_analysis"
    
    # Create output directory if needed
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {output_dir}")
    
    # Load harvest data
    try:
        harvest_data = load_latest_harvest(data_dir)
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("Please run harvest_arxiv.py first to collect papers.")
        return 1
    
    papers = harvest_data.get("papers", [])
    print(f"Loaded {len(papers)} papers from harvest file")
    print("")
    
    # Score all papers
    print("Scoring papers...")
    scored_papers = []
    for paper in papers:
        score, breakdown = score_paper(paper)
        scored_papers.append((paper, score, breakdown))
    
    # Sort by score (highest first)
    ranked_papers = sorted(scored_papers, key=lambda x: x[1], reverse=True)
    
    # Show top papers
    print(f"\nTop {min(TOP_N_PAPERS, len(ranked_papers))} Most Relevant Papers:")
    print("-" * 60)
    for i, (paper, score, breakdown) in enumerate(ranked_papers[:TOP_N_PAPERS], 1):
        title = paper.get("title", "Untitled")
        # Truncate long titles
        if len(title) > 70:
            title = title[:67] + "..."
        print(f"{i:2d}. [Score: {score:2d}] {title}")
    
    # Generate output files with timestamp
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    
    markdown_path = output_dir / f"relevance_ranking_{timestamp}.md"
    bibtex_path = output_dir / f"top_papers_{timestamp}.bib"
    
    print("\nGenerating reports...")
    generate_markdown_report(ranked_papers, markdown_path, harvest_data)
    generate_bibtex(ranked_papers, bibtex_path)
    
    print(f"\n✅ Analysis complete!")
    print(f"📄 Saved report to: {markdown_path}")
    print(f"📚 Saved BibTeX to: {bibtex_path}")
    print("")
    
    return 0

if __name__ == "__main__":
    exit(main())
