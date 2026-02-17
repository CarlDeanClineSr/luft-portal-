#!/usr/bin/env python3
"""
Extract key data from arXiv papers in harvest JSON.
Searches for: χ, plasma parameters, thresholds, periodicities.

Usage:
    python tools/extract_paper_data.py
    python tools/extract_paper_data.py --output custom_output.json
    python tools/extract_paper_data.py --paper-id 2512.24054v1
"""

import json
import re
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


def load_latest_harvest() -> Dict[str, Any]:
    """Load the latest arXiv paper harvest."""
    harvest_path = Path('data/papers/arxiv/latest.json')
    
    if not harvest_path.exists():
        print(f"❌ Error: {harvest_path} not found")
        print("   Run paper harvest first or check your working directory")
        return {"papers": []}
    
    with open(harvest_path, 'r') as f:
        return json.load(f)


def search_for_chi_parameters(text: str) -> Dict[str, List[str]]:
    """
    Search paper text for χ-like parameters and relevant physics quantities.
    
    Returns dictionary with parameter types and their found values.
    """
    if not text:
        return {}
    
    # Convert to lowercase for case-insensitive search
    text_lower = text.lower()
    
    results = {}
    
    # Pattern 1: Chi values (χ, chi)
    chi_patterns = [
        r'χ\s*[=~≈≃]\s*(0\.\d+)',
        r'\bchi\s*[=~≈≃]\s*(0\.\d+)',
        r'perturbation.*?(0\.1[0-5]\d?)',
        r'normalized.*?amplitude.*?(0\.1[0-5]\d?)',
    ]
    chi_matches = []
    for pattern in chi_patterns:
        matches = re.findall(pattern, text_lower)
        chi_matches.extend(matches)
    if chi_matches:
        results['chi_values'] = list(set(chi_matches))
    
    # Pattern 2: Thresholds
    threshold_patterns = [
        r'threshold\s+(?:of|at|near)?\s*(0\.\d+)',
        r'critical\s+(?:value|threshold).*?(0\.\d+)',
        r'boundary\s+(?:at|of).*?(0\.\d+)',
    ]
    threshold_matches = []
    for pattern in threshold_patterns:
        matches = re.findall(pattern, text_lower)
        threshold_matches.extend(matches)
    if threshold_matches:
        results['thresholds'] = list(set(threshold_matches))
    
    # Pattern 3: Periodicities and time scales
    period_patterns = [
        r'period\s+(?:of|~|≈)?\s*(\d+\.?\d*)\s*(hour|hr|h|day|min)',
        r'timescale\s+(?:of|~|≈)?\s*(\d+\.?\d*)\s*(hour|hr|h|day|min)',
        r'(\d+\.?\d*)\s*(hour|hr|h)\s+delay',
    ]
    period_matches = []
    for pattern in period_patterns:
        matches = re.findall(pattern, text_lower)
        period_matches.extend([f"{m[0]} {m[1]}" for m in matches])
    if period_matches:
        results['periodicities'] = list(set(period_matches))
    
    # Pattern 4: Beta values (plasma β)
    beta_patterns = [
        r'β\s*[=~≈]\s*(\d+\.?\d*)',
        r'\bbeta\s*[=~≈]\s*(\d+\.?\d*)',
        r'plasma\s+beta.*?(\d+\.?\d*)',
    ]
    beta_matches = []
    for pattern in beta_patterns:
        matches = re.findall(pattern, text_lower)
        beta_matches.extend(matches)
    if beta_matches:
        results['beta_values'] = list(set(beta_matches))
    
    # Pattern 5: R parameter (charge fraction)
    r_patterns = [
        r'\bR\s*[=~≈]\s*(0\.\d+)',
        r'charge\s+fraction.*?(0\.\d+)',
        r'particle.*?fraction.*?(0\.\d+)',
    ]
    r_matches = []
    for pattern in r_patterns:
        matches = re.findall(pattern, text_lower)
        r_matches.extend(matches)
    if r_matches:
        results['R_parameter'] = list(set(r_matches))
    
    # Pattern 6: Magnetic field values
    b_patterns = [
        r'B[_\s]*(?:0|baseline)\s*[=~≈]\s*(\d+\.?\d*)',
        r'magnetic\s+field.*?(\d+\.?\d*)\s*(?:nT|G|T)',
    ]
    b_matches = []
    for pattern in b_patterns:
        matches = re.findall(pattern, text_lower)
        b_matches.extend(matches)
    if b_matches:
        results['magnetic_field'] = list(set(b_matches))
    
    # Pattern 7: Reconnection rates
    reconnection_patterns = [
        r'reconnection\s+rate.*?(0\.\d+)',
        r'inflow\s+(?:rate|velocity).*?(0\.\d+)',
    ]
    reconnection_matches = []
    for pattern in reconnection_patterns:
        matches = re.findall(pattern, text_lower)
        reconnection_matches.extend(matches)
    if reconnection_matches:
        results['reconnection_rates'] = list(set(reconnection_matches))
    
    return results


def extract_keywords(paper: Dict[str, Any]) -> List[str]:
    """Extract relevant keywords from paper title and summary."""
    text = f"{paper.get('title', '')} {paper.get('summary', '')}".lower()
    
    keywords = []
    keyword_list = [
        'reconnection', 'magnetic', 'plasma', 'particle', 'feedback',
        'acceleration', 'shock', 'solar wind', 'magnetosphere',
        'boundary', 'threshold', 'perturbation', 'chi', 'χ',
        'heliosphere', 'cme', 'solar flare', 'storm',
        'temporal', 'correlation', 'periodicity', 'delay'
    ]
    
    for keyword in keyword_list:
        if keyword in text:
            keywords.append(keyword)
    
    return keywords


def analyze_paper(paper: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Analyze a single paper for χ-relevant parameters.
    
    Returns analysis results if relevant parameters found, None otherwise.
    """
    # Combine title and summary for analysis
    text = f"{paper.get('title', '')} {paper.get('summary', '')}"
    
    # Search for parameters
    params = search_for_chi_parameters(text)
    
    # Extract keywords
    keywords = extract_keywords(paper)
    
    # Only return if we found something interesting
    if params or len(keywords) >= 3:
        return {
            'paper_id': paper.get('id', 'unknown'),
            'title': paper.get('title', ''),
            'authors': paper.get('authors', []),
            'link': paper.get('link', ''),
            'pdf_link': paper.get('pdf_link', ''),
            'published': paper.get('published', ''),
            'parameters_found': params,
            'keywords': keywords,
            'relevance_score': len(params) * 2 + len(keywords)
        }
    
    return None


def analyze_all_papers(harvest: Dict[str, Any], paper_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Analyze all papers in harvest or a specific paper by ID.
    
    Args:
        harvest: Paper harvest data
        paper_id: Optional specific paper ID to analyze
    
    Returns:
        List of analysis results
    """
    papers = harvest.get('papers', [])
    
    if paper_id:
        # Filter to specific paper
        papers = [p for p in papers if p.get('id') == paper_id]
        if not papers:
            print(f"⚠️  Paper {paper_id} not found in harvest")
            return []
    
    results = []
    analyzed = 0
    found = 0
    
    print(f"🔍 Analyzing {len(papers)} papers...")
    
    for i, paper in enumerate(papers):
        analyzed += 1
        
        # Show progress every 10 papers
        if analyzed % 10 == 0:
            print(f"   Processed {analyzed}/{len(papers)} papers, found {found} relevant...")
        
        result = analyze_paper(paper)
        if result:
            found += 1
            results.append(result)
    
    print(f"✅ Complete: Analyzed {analyzed} papers, found {found} with relevant parameters")
    
    # Sort by relevance score
    results.sort(key=lambda x: x['relevance_score'], reverse=True)
    
    return results


def save_results(results: List[Dict[str, Any]], output_path: Path):
    """Save extraction results to JSON file."""
    output = {
        'extraction_date': datetime.utcnow().isoformat() + 'Z',
        'total_analyzed': len(results),
        'papers_with_parameters': len([r for r in results if r.get('parameters_found')]),
        'results': results
    }
    
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"💾 Saved results to: {output_path}")


def print_summary(results: List[Dict[str, Any]]):
    """Print a summary of extraction results."""
    if not results:
        print("\n📊 No relevant papers found")
        return
    
    print(f"\n📊 EXTRACTION SUMMARY")
    print(f"=" * 60)
    print(f"Total papers with relevant content: {len(results)}")
    
    # Count parameter types
    param_counts = {}
    for result in results:
        for param_type in result.get('parameters_found', {}).keys():
            param_counts[param_type] = param_counts.get(param_type, 0) + 1
    
    if param_counts:
        print(f"\nParameter types found:")
        for param_type, count in sorted(param_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  • {param_type}: {count} papers")
    
    # Top 5 most relevant papers
    print(f"\n🌟 TOP 5 MOST RELEVANT PAPERS:")
    print(f"-" * 60)
    for i, result in enumerate(results[:5], 1):
        print(f"\n{i}. {result['paper_id']}: {result['title'][:60]}...")
        print(f"   Relevance Score: {result['relevance_score']}")
        if result.get('parameters_found'):
            print(f"   Parameters: {', '.join(result['parameters_found'].keys())}")
        print(f"   Link: {result['link']}")
    
    # Papers with chi values
    chi_papers = [r for r in results if 'chi_values' in r.get('parameters_found', {})]
    if chi_papers:
        print(f"\n🎯 PAPERS WITH χ VALUES ({len(chi_papers)}):")
        print(f"-" * 60)
        for result in chi_papers[:3]:
            print(f"  • {result['paper_id']}: {result['title'][:50]}...")
            chi_vals = result['parameters_found']['chi_values']
            print(f"    χ values found: {', '.join(chi_vals)}")
    
    # Papers with thresholds near 0.15
    threshold_papers = [r for r in results if 'thresholds' in r.get('parameters_found', {})]
    if threshold_papers:
        print(f"\n🎯 PAPERS WITH THRESHOLD VALUES ({len(threshold_papers)}):")
        for result in threshold_papers[:3]:
            thresholds = result['parameters_found']['thresholds']
            # Check if any threshold is near 0.15
            near_015 = [t for t in thresholds if 0.10 <= float(t) <= 0.20]
            if near_015:
                print(f"  • {result['paper_id']}: {result['title'][:50]}...")
                print(f"    Thresholds: {', '.join(near_015)} ⭐ NEAR χ=0.15!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Extract χ-relevant parameters from arXiv papers',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze all papers in latest harvest
  python tools/extract_paper_data.py
  
  # Analyze specific paper
  python tools/extract_paper_data.py --paper-id 2512.24054v1
  
  # Save to custom location
  python tools/extract_paper_data.py --output my_results.json
        """
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='data/papers/extracted_parameters.json',
        help='Output file path (default: data/papers/extracted_parameters.json)'
    )
    
    parser.add_argument(
        '--paper-id',
        type=str,
        help='Analyze specific paper by ID (e.g., 2512.24054v1)'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("LUFT PORTAL - PAPER PARAMETER EXTRACTOR")
    print("=" * 60)
    print(f"Searching for: χ values, thresholds, periodicities, β, R parameter")
    print()
    
    # Load harvest
    harvest = load_latest_harvest()
    if not harvest.get('papers'):
        print("❌ No papers found in harvest")
        return 1
    
    # Analyze papers
    results = analyze_all_papers(harvest, paper_id=args.paper_id)
    
    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_results(results, output_path)
    
    # Print summary
    print_summary(results)
    
    print(f"\n" + "=" * 60)
    print(f"✅ EXTRACTION COMPLETE")
    print(f"   Results saved to: {output_path}")
    print(f"   Total relevant papers: {len(results)}")
    print(f"=" * 60)
    
    return 0


if __name__ == '__main__':
    exit(main())
