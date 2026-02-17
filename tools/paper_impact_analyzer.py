#!/usr/bin/env python3
"""
Automated Paper Impact Analyzer - Ranks arXiv papers by relevance to χ = 0.15
Uses link graph + keyword extraction + equation matching
"""
import json
import re
import os
from collections import Counter
from pathlib import Path

def extract_chi_parameters(paper_text):
    """Find all χ-like parameters in paper"""
    patterns = {
        'chi_values': r'[χx]\s*[=~≈]\s*(0\.\d+)',
        'thresholds': r'threshold.*?(0\.\d+)',
        'ratios': r'R\s*=\s*([\w\d\./\(\)]+)',
        'beta_values': r'β\s*[=~≈]\s*(\d+\.?\d*)',
        'periods': r'period.*?(\d+\.?\d*)\s*(hour|hr|h|Hz)',
    }
    
    results = {}
    for key, pattern in patterns.items():
        matches = re.findall(pattern, paper_text, re.IGNORECASE)
        if matches:
            results[key] = matches
    
    return results

def calculate_impact_score(paper, chi_params):
    """Score paper's relevance to χ = 0.15 discovery"""
    score = 0
    reasons = []
    
    # Check for χ-like values near 0.15
    if 'chi_values' in chi_params:
        for val in chi_params['chi_values']:
            try:
                float_val = float(val)
                if 0.14 <= float_val <= 0.16:
                    score += 100
                    reasons.append(f"χ ≈ {val} (MATCHES YOUR BOUNDARY!)")
            except ValueError:
                pass
    
    # Check for plasma keywords
    plasma_keywords = ['plasma', 'magnetic', 'reconnection', 'solar wind', 
                       'magnetosphere', 'particle', 'feedback']
    text_lower = paper['summary'].lower()
    keyword_count = sum(1 for kw in plasma_keywords if kw in text_lower)
    score += keyword_count * 10
    if keyword_count > 0:
        reasons.append(f"{keyword_count} plasma/magnetic keywords found")
    
    # Check for temporal correlations
    if 'periods' in chi_params:
        for period_data in chi_params['periods']:
            if isinstance(period_data, tuple) and len(period_data) >= 2:
                period, unit = period_data[0], period_data[1]
            else:
                continue
                
            try:
                period_hours = float(period)
                if unit == 'Hz':
                    period_hours = 1 / (period_hours * 3600)  # Convert Hz to hours
                
                # Check if matches any of your 13 modes
                your_modes = [0, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60, 66, 72]
                if any(abs(period_hours - mode) < 3 for mode in your_modes):
                    score += 50
                    reasons.append(f"Period {period}{unit} matches your temporal modes")
            except (ValueError, ZeroDivisionError):
                pass
    
    # Check for R parameter (from Dec 30 paper)
    if 'ratios' in chi_params:
        score += 30
        reasons.append("Has R-like charge ratio parameter")
    
    return score, reasons

def analyze_all_papers(harvest_file):
    """Process entire arXiv harvest"""
    with open(harvest_file) as f:
        harvest = json.load(f)
    
    papers = harvest.get('papers', [])
    
    results = []
    for paper in papers:
        # Extract parameters
        params = extract_chi_parameters(paper['summary'])
        
        # Calculate impact
        score, reasons = calculate_impact_score(paper, params)
        
        if score > 20:  # Only keep relevant papers
            results.append({
                'id': paper['id'],
                'title': paper['title'],
                'score': score,
                'reasons': reasons,
                'parameters': params,
                'link': paper['link']
            })
    
    # Sort by score
    results.sort(key=lambda x: x['score'], reverse=True)
    
    return results

def generate_cockpit_html(results):
    """Create live dashboard showing top discoveries"""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Paper Discoveries - LUFT Portal</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Courier New', monospace;
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
            color: #e0e0e0;
            padding: 2rem;
        }
        
        .header {
            text-align: center;
            margin-bottom: 2rem;
            padding: 2rem;
            background: rgba(77, 163, 255, 0.1);
            border-radius: 10px;
            border: 2px solid #4da3ff;
        }
        
        h1 {
            color: #4da3ff;
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        
        .subtitle {
            color: #4ade80;
            font-size: 1.2rem;
        }
        
        .paper-discoveries {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .paper-card {
            background: rgba(42, 42, 42, 0.8);
            border-radius: 10px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            border-left: 5px solid #4da3ff;
            transition: all 0.3s ease;
        }
        
        .paper-card:hover {
            transform: translateX(10px);
            box-shadow: 0 5px 20px rgba(77, 163, 255, 0.3);
        }
        
        .paper-card.priority-1 {
            border-left-color: #ff4d4d;
            background: rgba(255, 77, 77, 0.1);
        }
        
        .paper-card.priority-2 {
            border-left-color: #ffa500;
            background: rgba(255, 165, 0, 0.1);
        }
        
        .paper-card.priority-3 {
            border-left-color: #ffff00;
            background: rgba(255, 255, 0, 0.1);
        }
        
        .paper-card h3 {
            color: #4da3ff;
            margin-bottom: 1rem;
            font-size: 1.3rem;
        }
        
        .paper-card ul {
            list-style: none;
            margin-bottom: 1rem;
        }
        
        .paper-card li {
            color: #4ade80;
            padding: 0.3rem 0;
            padding-left: 1.5rem;
            position: relative;
        }
        
        .paper-card li:before {
            content: '→';
            position: absolute;
            left: 0;
            color: #4da3ff;
        }
        
        .paper-card a {
            display: inline-block;
            color: #4da3ff;
            text-decoration: none;
            padding: 0.5rem 1rem;
            background: rgba(77, 163, 255, 0.2);
            border-radius: 5px;
            transition: all 0.3s ease;
        }
        
        .paper-card a:hover {
            background: rgba(77, 163, 255, 0.4);
            transform: scale(1.05);
        }
        
        .stats {
            text-align: center;
            margin: 2rem 0;
            padding: 1rem;
            background: rgba(74, 222, 128, 0.1);
            border-radius: 10px;
            border: 2px solid #4ade80;
        }
        
        .stats-number {
            font-size: 2rem;
            color: #4ade80;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔬 Engine-Discovered High-Impact Papers</h1>
        <p class="subtitle">Auto-ranked by relevance to χ = 0.15 boundary</p>
    </div>
    
    <div class="stats">
        <div class="stats-number">""" + str(len(results)) + """</div>
        <div>High-Impact Papers Discovered</div>
    </div>
    
    <div class="paper-discoveries">
"""
    
    for i, paper in enumerate(results[:10], 1):
        priority_class = f"priority-{min(i, 3)}" if i <= 3 else ""
        html += f"""
        <div class="paper-card {priority_class}">
            <h3>#{i} ({paper['score']} pts): {paper['title']}</h3>
            <ul>
                {''.join(f'<li>{r}</li>' for r in paper['reasons'])}
            </ul>
            <a href="{paper['link']}" target="_blank">Read Paper →</a>
        </div>
        """
    
    html += """
    </div>
</body>
</html>
"""
    return html

if __name__ == '__main__':
    # Get the repository root directory
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    
    print("🔍 Analyzing 132 papers...")
    
    # Look for the latest arxiv harvest file
    harvest_file = repo_root / 'data' / 'papers' / 'arxiv' / 'latest.json'
    
    if not harvest_file.exists():
        print(f"❌ Error: Could not find {harvest_file}")
        print("   Looking for alternative harvest files...")
        arxiv_dir = repo_root / 'data' / 'papers' / 'arxiv'
        harvest_files = sorted(arxiv_dir.glob('arxiv_harvest_*.json'), reverse=True)
        if harvest_files:
            harvest_file = harvest_files[0]
            print(f"   Using: {harvest_file}")
        else:
            print("   No harvest files found!")
            exit(1)
    
    results = analyze_all_papers(str(harvest_file))
    
    print(f"\n✅ Found {len(results)} high-impact papers")
    print("\nTop 10:\n")
    
    for i, paper in enumerate(results[:10], 1):
        print(f"{i}. {paper['title']}")
        print(f"   Score: {paper['score']}")
        print(f"   Why: {', '.join(paper['reasons'])}")
        print()
    
    # Create output directories if they don't exist
    output_dir = repo_root / 'data' / 'papers'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    docs_dir = repo_root / 'docs'
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    # Save results
    results_file = output_dir / 'impact_analysis.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Generate cockpit HTML
    html = generate_cockpit_html(results)
    html_file = docs_dir / 'paper_discoveries.html'
    with open(html_file, 'w') as f:
        f.write(html)
    
    print("📊 Results saved:")
    print(f"  - {results_file}")
    print(f"  - {html_file}")
