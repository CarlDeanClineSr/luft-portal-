#!/usr/bin/env python3
"""
LUFT Missing Link Suggester
============================

Layer 4 Intelligence: Identifies gaps in the knowledge network by finding
concepts mentioned but not linked to data sources, and suggests missing sources.

Author: Carl Dean Cline Sr.
Created: December 31, 2025
Location: Lincoln, Nebraska, USA
Email: CARLDCLINE@GMAIL.COM

Mission: Find the missing connections that make the LUFT knowledge graph complete.

Usage:
    python missing_link_suggester.py --scan-concepts
    python missing_link_suggester.py --suggest-sources
    python missing_link_suggester.py --full-analysis
"""

import json
import yaml
import re
import argparse
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict, Counter


class ConceptMapper:
    """
    Track which concepts are mentioned vs. which are actually linked to data sources.
    """
    
    # Key scientific concepts and their associated data sources
    CONCEPT_SOURCE_MAP = {
        'parker solar probe': ['https://spdf.gsfc.nasa.gov/pub/data/psp/', 'https://parkersolarprobe.jhuapl.edu/'],
        'psp': ['https://spdf.gsfc.nasa.gov/pub/data/psp/'],
        'solar orbiter': ['https://soar.esac.esa.int/soar/', 'https://www.cosmos.esa.int/web/soar'],
        'hinode': ['https://hinode.isas.jaxa.jp/', 'https://www.isas.jaxa.jp/en/missions/spacecraft/current/hinode.html'],
        'aditya-l1': ['https://www.isro.gov.in/Aditya_L1.html'],
        'ligo': ['https://www.ligo.caltech.edu/', 'https://gwosc.org/'],
        'virgo': ['https://www.virgo-gw.eu/', 'http://public.virgo-gw.eu/'],
        'gravitational wave': ['https://gwosc.org/', 'https://www.ligo.org/'],
        'cern': ['https://home.cern/', 'http://opendata.cern.ch/'],
        'lhc': ['https://home.cern/science/accelerators/large-hadron-collider', 'http://opendata.cern.ch/'],
        'fast': ['https://fast.bao.ac.cn/', 'http://crafts.bao.ac.cn/'],
        'alma': ['https://www.almaobservatory.org/', 'https://almascience.org/'],
        'jwst': ['https://www.stsci.edu/jwst', 'https://mast.stsci.edu/'],
        'hubble': ['https://hubblesite.org/', 'https://archive.stsci.edu/'],
        'dscovr': ['https://www.ngdc.noaa.gov/dscovr/', 'https://services.swpc.noaa.gov/'],
        'maven': ['https://pds-ppi.igpp.ucla.edu/', 'https://lasp.colorado.edu/maven/'],
        'ace': ['https://www.srl.caltech.edu/ACE/', 'https://www.swpc.noaa.gov/products/ace-real-time-solar-wind'],
        'wind': ['https://wind.nasa.gov/', 'https://cdaweb.gsfc.nasa.gov/'],
        'voyager': ['https://voyager.jpl.nasa.gov/', 'https://spdf.gsfc.nasa.gov/pub/data/voyager/'],
        'magnetosphere': ['https://www.usgs.gov/programs/geomagnetism'],
        'cosmic ray': ['https://www.nmdb.eu/', 'https://cosmicrays.oulu.fi/'],
        'neutron monitor': ['https://www.nmdb.eu/'],
        'dst index': ['https://wdc.kugi.kyoto-u.ac.jp/dstdir/', 'https://www.usgs.gov/programs/geomagnetism'],
        'kp index': ['https://www.swpc.noaa.gov/products/planetary-k-index'],
        'solar flare': ['https://www.swpc.noaa.gov/products/solar-and-geophysical-event-reports'],
        'cme': ['https://www.swpc.noaa.gov/products/wsa-enlil-solar-wind-prediction'],
        'chi boundary': [],  # Internal LUFT concept
        'graviton': ['https://gwosc.org/'],  # Theoretical, but gravity wave data relevant
    }
    
    def __init__(self, repo_path: str = '.'):
        """Initialize concept mapper."""
        self.repo_path = Path(repo_path)
        self.concept_mentions = defaultdict(list)  # concept -> list of files
        self.concept_links = defaultdict(set)  # concept -> set of URLs
        self.files_scanned = 0
        
    def scan_repository(self):
        """Scan repository for concept mentions and links."""
        print("🔍 Scanning repository for concepts and links...")
        
        # File extensions to scan
        text_extensions = {'.md', '.txt', '.py', '.yaml', '.yml', '.json', '.html'}
        
        for file_path in self.repo_path.rglob('*'):
            if not file_path.is_file():
                continue
            
            if file_path.suffix not in text_extensions:
                continue
            
            # Skip hidden files
            if any(part.startswith('.') for part in file_path.parts if part != '.github'):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read().lower()
                
                self.files_scanned += 1
                rel_path = str(file_path.relative_to(self.repo_path))
                
                # Check for concept mentions
                for concept in self.CONCEPT_SOURCE_MAP.keys():
                    if concept in content:
                        self.concept_mentions[concept].append(rel_path)
                
                # Extract URLs from file
                url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
                urls = re.findall(url_pattern, content)
                
                # Match URLs to concepts
                for url in urls:
                    url_lower = url.lower()
                    for concept, concept_urls in self.CONCEPT_SOURCE_MAP.items():
                        for concept_url in concept_urls:
                            if concept_url.lower() in url_lower or url_lower in concept_url.lower():
                                self.concept_links[concept].add(url)
                
            except Exception as e:
                pass
        
        print(f"   ✓ Scanned {self.files_scanned} files")
        print(f"   ✓ Found {len(self.concept_mentions)} concepts mentioned")
        print(f"   ✓ Found {len(self.concept_links)} concepts with links")
    
    def get_concept_statistics(self) -> Dict:
        """Generate statistics about concept coverage."""
        stats = {
            'concepts_mentioned': len(self.concept_mentions),
            'concepts_linked': len(self.concept_links),
            'concepts_mentioned_not_linked': [],
            'top_mentioned_concepts': [],
            'total_mentions': sum(len(files) for files in self.concept_mentions.values()),
            'total_links': sum(len(urls) for urls in self.concept_links.values())
        }
        
        # Find concepts mentioned but not linked
        for concept in self.concept_mentions.keys():
            if concept not in self.concept_links or len(self.concept_links[concept]) == 0:
                mention_count = len(self.concept_mentions[concept])
                stats['concepts_mentioned_not_linked'].append({
                    'concept': concept,
                    'mentions': mention_count,
                    'files': self.concept_mentions[concept][:5]  # Show first 5 files
                })
        
        # Sort by mention count
        stats['concepts_mentioned_not_linked'].sort(key=lambda x: x['mentions'], reverse=True)
        
        # Top mentioned concepts
        concept_counts = [(c, len(files)) for c, files in self.concept_mentions.items()]
        stats['top_mentioned_concepts'] = sorted(concept_counts, key=lambda x: x[1], reverse=True)[:10]
        
        return stats


class MissingLinkSuggester:
    """
    Propose sources you SHOULD be linking but aren't.
    """
    
    def __init__(self, repo_path: str = '.', registry_file: str = 'external_data_sources_registry.yaml'):
        """Initialize missing link suggester."""
        self.repo_path = Path(repo_path)
        self.registry_file = Path(registry_file)
        self.concept_mapper = ConceptMapper(repo_path)
        self.registry_sources = {}
        self.suggestions = []
        
    def load_registry(self):
        """Load external data source registry."""
        if not self.registry_file.exists():
            print(f"⚠️  Warning: Registry file not found: {self.registry_file}")
            return
        
        with open(self.registry_file, 'r') as f:
            registry = yaml.safe_load(f)
        
        # Extract all sources
        for category_key, category_data in registry.items():
            if isinstance(category_data, dict) and 'sources' in category_data:
                for source in category_data['sources']:
                    name = source.get('name', 'unknown')
                    self.registry_sources[name.lower()] = {
                        'name': source.get('name'),
                        'description': source.get('description', ''),
                        'urls': source.get('urls', []),
                        'category': category_data.get('category', 'Unknown'),
                        'data_types': source.get('data_types', [])
                    }
    
    def suggest_missing_sources(self, concept: str = None) -> List[Dict]:
        """
        Suggest sources that should be added based on concept mentions.
        
        Args:
            concept: Specific concept to check (default: check all)
            
        Returns:
            List of suggestions with rationale
        """
        self.suggestions = []
        
        # Scan repository for concepts
        self.concept_mapper.scan_repository()
        stats = self.concept_mapper.get_concept_statistics()
        
        # Generate suggestions for concepts mentioned but not linked
        for item in stats['concepts_mentioned_not_linked']:
            concept_name = item['concept']
            mention_count = item['mentions']
            
            # Get recommended sources for this concept
            recommended_urls = self.concept_mapper.CONCEPT_SOURCE_MAP.get(concept_name, [])
            
            if not recommended_urls:
                # This is an internal concept, no external source needed
                continue
            
            # Create suggestion
            suggestion = {
                'concept': concept_name,
                'mention_count': mention_count,
                'example_files': item['files'],
                'recommended_sources': recommended_urls,
                'priority': 'HIGH' if mention_count >= 10 else 'MEDIUM' if mention_count >= 5 else 'LOW',
                'rationale': f"'{concept_name}' is mentioned {mention_count} times but has no links to data sources. " +
                            f"This suggests missing validation opportunities.",
                'action': f"Add links to {recommended_urls[0]} and validate chi boundary with {concept_name} data."
            }
            
            self.suggestions.append(suggestion)
        
        # Sort by priority and mention count
        priority_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        self.suggestions.sort(key=lambda x: (priority_order[x['priority']], -x['mention_count']))
        
        return self.suggestions


class CitationValidator:
    """
    Check that claims in documentation are backed by linked data sources.
    """
    
    def __init__(self, repo_path: str = '.'):
        """Initialize citation validator."""
        self.repo_path = Path(repo_path)
        self.uncited_claims = []
        
    def validate_citations(self) -> List[Dict]:
        """
        Find claims that lack supporting data source citations.
        
        Returns:
            List of uncited claims with context
        """
        # Claim indicators (phrases that suggest a claim is being made)
        claim_patterns = [
            r'(proves?|demonstrates?|shows?|validates?|confirms?)\s+that\s+[\w\s]+',
            r'(evidence|data|results?)\s+(shows?|indicates?|suggests?)\s+[\w\s]+',
            r'(discovered|found|observed)\s+[\w\s]+',
            r'chi\s*(=|≤|>=|<|>)\s*0\.15',
            r'universal(ly)?\s+(bound|boundary|constraint|limit)',
        ]
        
        # URL pattern to check for nearby citations
        url_pattern = r'https?://[^\s<>")]+|www\.[^\s<>")]+|\[[^\]]+\]\([^\)]+\)'
        
        markdown_files = list(self.repo_path.glob('**/*.md'))
        
        for file_path in markdown_files:
            # Skip hidden directories
            if any(part.startswith('.') for part in file_path.parts if part != '.github'):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                
                lines = content.split('\n')
                
                for i, line in enumerate(lines):
                    for pattern in claim_patterns:
                        matches = re.finditer(pattern, line, re.IGNORECASE)
                        
                        for match in matches:
                            # Check if there's a URL within 3 lines
                            context_start = max(0, i - 3)
                            context_end = min(len(lines), i + 4)
                            context = '\n'.join(lines[context_start:context_end])
                            
                            has_citation = bool(re.search(url_pattern, context))
                            
                            if not has_citation:
                                self.uncited_claims.append({
                                    'file': str(file_path.relative_to(self.repo_path)),
                                    'line': i + 1,
                                    'claim': match.group(0),
                                    'context': line.strip(),
                                    'suggestion': 'Add link to supporting data source or analysis script'
                                })
            
            except Exception as e:
                pass
        
        return self.uncited_claims


def generate_missing_link_report(suggestions: List[Dict], 
                                 uncited_claims: List[Dict],
                                 concept_stats: Dict,
                                 output_path: str = None) -> str:
    """
    Generate comprehensive missing link report.
    
    Args:
        suggestions: Missing source suggestions
        uncited_claims: Claims without citations
        concept_stats: Concept coverage statistics
        output_path: Path to save report (optional)
        
    Returns:
        Report content as markdown string
    """
    from datetime import datetime
    
    report_date = datetime.now().strftime('%Y-%m-%d')
    
    report = f"""# 🔗 LUFT MISSING LINK INTELLIGENCE REPORT
**Date:** {report_date}  
**Files Scanned:** {concept_stats.get('total_mentions', 0)}  
**Concepts Tracked:** {len(ConceptMapper.CONCEPT_SOURCE_MAP)}

---

## 🎯 EXECUTIVE SUMMARY

"""
    
    high_priority = [s for s in suggestions if s['priority'] == 'HIGH']
    medium_priority = [s for s in suggestions if s['priority'] == 'MEDIUM']
    
    report += f"""- **High Priority Gaps:** {len(high_priority)} concepts need data source links
- **Medium Priority Gaps:** {len(medium_priority)} concepts could benefit from validation
- **Uncited Claims:** {len(uncited_claims)} claims found without supporting citations
- **Coverage:** {concept_stats['concepts_linked']}/{concept_stats['concepts_mentioned']} concepts have data links

---

## 🚨 HIGH PRIORITY: Missing Data Sources

"""
    
    if high_priority:
        for i, suggestion in enumerate(high_priority[:5], 1):
            report += f"""### {i}. {suggestion['concept'].upper()}
**Mentions:** {suggestion['mention_count']} times across {len(suggestion['example_files'])} files  
**Status:** ❌ NO DATA SOURCE LINKS FOUND

**Example Files:**
"""
            for file in suggestion['example_files'][:3]:
                report += f"- `{file}`\n"
            
            report += f"""
**Recommended Action:**
```
{suggestion['action']}
```

**Data Sources to Add:**
"""
            for url in suggestion['recommended_sources']:
                report += f"- {url}\n"
            
            report += f"""
**Rationale:**  
{suggestion['rationale']}

---

"""
    else:
        report += "✅ No high-priority missing links detected!\n\n"
    
    report += """## 🟡 MEDIUM PRIORITY: Suggested Enhancements

"""
    
    if medium_priority:
        for i, suggestion in enumerate(medium_priority[:5], 1):
            report += f"""### {i}. {suggestion['concept'].title()}
Mentioned {suggestion['mention_count']} times. Consider adding: {suggestion['recommended_sources'][0] if suggestion['recommended_sources'] else 'N/A'}

"""
    else:
        report += "ℹ️ No medium-priority suggestions at this time.\n\n"
    
    report += """## 📝 UNCITED CLAIMS REQUIRING VALIDATION

"""
    
    if uncited_claims:
        # Group by file
        by_file = defaultdict(list)
        for claim in uncited_claims:
            by_file[claim['file']].append(claim)
        
        for file, file_claims in sorted(by_file.items())[:10]:
            report += f"""### File: `{file}`
Found {len(file_claims)} claim(s) without citations:

"""
            for claim in file_claims[:3]:
                report += f"""- **Line {claim['line']}:** "{claim['context'][:80]}..."
  - Suggestion: {claim['suggestion']}

"""
        
        if len(by_file) > 10:
            report += f"\n... and {len(by_file) - 10} more files with uncited claims.\n\n"
    else:
        report += "✅ All major claims appear to have supporting citations.\n\n"
    
    report += f"""---

## 📊 CONCEPT COVERAGE STATISTICS

**Total Concepts Mentioned:** {concept_stats['concepts_mentioned']}  
**Concepts with Data Links:** {concept_stats['concepts_linked']}  
**Coverage Rate:** {(concept_stats['concepts_linked'] / max(concept_stats['concepts_mentioned'], 1) * 100):.1f}%

### Top Mentioned Concepts:
"""
    
    for concept, count in concept_stats['top_mentioned_concepts'][:10]:
        linked = '✅' if concept in concept_stats.get('concepts_linked', []) else '❌'
        report += f"{linked} **{concept}**: {count} mentions\n"
    
    report += """

---

## 🎯 RECOMMENDED ACTIONS

1. **Immediate:** Address HIGH priority missing links (concepts mentioned 10+ times)
2. **This Week:** Add citations to major claims in documentation
3. **This Month:** Enhance MEDIUM priority concept coverage
4. **Ongoing:** Maintain citation discipline for new claims

---

*Report generated by LUFT Missing Link Intelligence*  
*Carl Dean Cline Sr. - Lincoln, Nebraska, USA*
"""
    
    # Save report if output path provided
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"Report saved to: {output_file}")
    
    return report


def main():
    """Main entry point for missing link suggester."""
    parser = argparse.ArgumentParser(
        description='LUFT Missing Link Suggester - Find gaps in knowledge network',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--scan-concepts', action='store_true',
                       help='Scan repository for concept mentions')
    parser.add_argument('--suggest-sources', action='store_true',
                       help='Suggest missing data sources')
    parser.add_argument('--validate-citations', action='store_true',
                       help='Find claims without citations')
    parser.add_argument('--full-analysis', action='store_true',
                       help='Run complete missing link analysis')
    parser.add_argument('--repo-path', default='.',
                       help='Path to repository')
    parser.add_argument('--registry', default='external_data_sources_registry.yaml',
                       help='Path to data source registry')
    parser.add_argument('--output', default=None,
                       help='Output file for report')
    
    args = parser.parse_args()
    
    # Default to full analysis
    if not (args.scan_concepts or args.suggest_sources or 
            args.validate_citations or args.full_analysis):
        args.full_analysis = True
    
    print("="*70)
    print("🔗 LUFT MISSING LINK INTELLIGENCE ENGINE")
    print("="*70)
    print()
    
    suggester = MissingLinkSuggester(args.repo_path, args.registry)
    validator = CitationValidator(args.repo_path)
    
    suggestions = []
    uncited_claims = []
    concept_stats = {}
    
    # Load registry
    suggester.load_registry()
    print(f"📚 Loaded {len(suggester.registry_sources)} sources from registry")
    print()
    
    # Run analyses
    if args.suggest_sources or args.full_analysis:
        print("🔍 Analyzing concept coverage and suggesting missing sources...")
        suggestions = suggester.suggest_missing_sources()
        concept_stats = suggester.concept_mapper.get_concept_statistics()
        
        print(f"   ✓ Found {len(suggestions)} missing link opportunities")
        print(f"   ✓ Coverage: {concept_stats['concepts_linked']}/{concept_stats['concepts_mentioned']} concepts linked")
        print()
    
    if args.validate_citations or args.full_analysis:
        print("📝 Validating citations in documentation...")
        uncited_claims = validator.validate_citations()
        
        print(f"   ✓ Found {len(uncited_claims)} uncited claims")
        print()
    
    # Generate report
    if args.full_analysis:
        print("📊 Generating missing link intelligence report...")
        
        if args.output is None:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            args.output = f'reports/meta_intelligence/missing_links_{timestamp}.md'
        
        report = generate_missing_link_report(
            suggestions, uncited_claims, concept_stats, args.output
        )
        
        print()
        print("="*70)
        print(report[:2000] + "\n... (truncated for display)")
        print("="*70)
    
    print()
    print("✨ Missing link analysis complete!")
    
    # Print summary statistics
    if suggestions:
        high_pri = len([s for s in suggestions if s['priority'] == 'HIGH'])
        if high_pri > 0:
            print(f"⚠️  {high_pri} HIGH PRIORITY gaps need immediate attention!")


if __name__ == '__main__':
    main()
