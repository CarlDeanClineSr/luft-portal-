#!/usr/bin/env python3
"""
Uncited Claims Identifier
Scans markdown and LaTeX files for scientific claims without citations.
Generates reports and citation templates for the Luft Portal project.
"""

import re
import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Tuple, Set
import json


class ClaimCategory:
    """Categories for scientific claims"""
    THEORY_MODEL = "Theory/Model"
    OBSERVATION_DATA = "Observation/Data"
    PREVIOUS_RESEARCH = "Previous Research"
    NUMERICAL_VALUE = "Numerical Value"
    COMPUTATIONAL = "Computational"


class UncitedClaimsIdentifier:
    """Identifies scientific claims without proper citations"""
    
    def __init__(self):
        self.claims = []
        self.scan_dirs = ['docs/', 'papers/', 'reports/']
        self.output_dir = Path('reports/uncited_claims')
        self.papers_dir = Path('papers/')
        
        # Regex patterns for scientific claims
        self.patterns = {
            ClaimCategory.THEORY_MODEL: [
                r'\b(theory predicts?|model shows?|theoretical|predicts? that|according to theory)\b',
                r'\b(hypothesis|framework suggests?|theoretical framework)\b',
                r'\b(expected to|should be|would be|in theory)\b',
            ],
            ClaimCategory.OBSERVATION_DATA: [
                r'\b(discovered|found|observed|measured|detected|recorded)\b',
                r'\b(data shows?|observations? reveal|measurements? indicate)\b',
                r'\b(analysis reveals?|results? show|evidence suggests?)\b',
                r'\b(spacecraft observed|satellite detected|mission found)\b',
            ],
            ClaimCategory.PREVIOUS_RESEARCH: [
                r'\b(previous studies?|earlier research|prior work|research shows?)\b',
                r'\b(it is known|well-established|documented|reported)\b',
                r'\b(studies? have shown|research indicates?)\b',
            ],
            ClaimCategory.NUMERICAL_VALUE: [
                r'\d+\.?\d*\s*(km|m|cm|km/s|m/s|tesla|gauss|T|nT)\b',
                r'\d+\.?\d*\s*(keV|eV|MeV|GeV)\b',
                r'\d+\.?\d*\s*(kg|g|AU|degrees?|°)\b',
                r'\d+\.?\d*\s*×\s*10\^?[\-\d]+',
                r'\b\d{1,3}(,\d{3})*(\.\d+)?\s*(km|m|cm|tesla|gauss|eV|keV)\b',
            ],
            ClaimCategory.COMPUTATIONAL: [
                r'\b(simulation shows?|computational model|numerical simulation)\b',
                r'\b(computed|calculated|derived|simulated)\b',
                r'\b(algorithm|method|approach|technique)\b',
            ],
        }
        
        # Citation markers to look for nearby
        self.citation_markers = [
            r'\[\d+\]',  # [1], [23]
            r'\[[\w\s,]+\s+\d{4}\]',  # [Author 2024]
            r'\\cite\{[^\}]+\}',  # \cite{key}
            r'\\citep?\{[^\}]+\}',  # \citep{key}, \citet{key}
            r'\([A-Z][a-z]+\s+et al\.\s*,?\s*\d{4}\)',  # (Smith et al., 2024)
            r'\([A-Z][a-z]+\s+(?:and|&)\s+[A-Z][a-z]+\s*,?\s*\d{4}\)',  # (Smith and Jones, 2024)
        ]
        
        # Citation source suggestions by category
        self.citation_suggestions = {
            ClaimCategory.THEORY_MODEL: [
                "Plasma physics textbooks (e.g., Chen 'Introduction to Plasma Physics')",
                "MHD theory papers (e.g., Priest & Forbes 'Magnetic Reconnection')",
                "Space plasma physics references (e.g., Parks 'Physics of Space Plasmas')",
            ],
            ClaimCategory.OBSERVATION_DATA: [
                "DSCOVR mission papers and data archives",
                "MAVEN mission publications",
                "ACE, Wind, or SOHO spacecraft observations",
                "Ground-based magnetometer data",
            ],
            ClaimCategory.PREVIOUS_RESEARCH: [
                "Review papers in solar-terrestrial physics",
                "AGU/JGR publications",
                "Space Weather journal articles",
            ],
            ClaimCategory.NUMERICAL_VALUE: [
                "Original data source (spacecraft measurements)",
                "Standard reference values (e.g., solar wind parameters)",
                "Calibrated instrument papers",
            ],
            ClaimCategory.COMPUTATIONAL: [
                "Algorithm/method papers",
                "Software documentation and validation papers",
                "Computational physics references",
            ],
        }
    
    def setup_output_dirs(self):
        """Create output directories if they don't exist"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.papers_dir.mkdir(parents=True, exist_ok=True)
    
    def find_files(self) -> List[Path]:
        """Find all markdown and LaTeX files in target directories"""
        files = []
        extensions = {'.md', '.tex', '.latex'}
        
        for scan_dir in self.scan_dirs:
            dir_path = Path(scan_dir)
            if dir_path.exists():
                for ext in extensions:
                    files.extend(dir_path.rglob(f'*{ext}'))
        
        return files
    
    def has_nearby_citation(self, text: str, match_pos: int, context_window: int = 200) -> Tuple[bool, str]:
        """Check if there's a citation marker near the claim"""
        start = max(0, match_pos - context_window)
        end = min(len(text), match_pos + context_window)
        context = text[start:end]
        
        for marker_pattern in self.citation_markers:
            if re.search(marker_pattern, context):
                return True, re.search(marker_pattern, context).group()
        
        return False, ""
    
    def categorize_claim(self, text: str) -> str:
        """Determine the category of a claim"""
        for category, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return category
        return ClaimCategory.PREVIOUS_RESEARCH  # Default
    
    def extract_claims(self, file_path: Path):
        """Extract uncited claims from a file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return
        
        # Search for claims
        for category, patterns in self.patterns.items():
            for pattern in patterns:
                for match in re.finditer(pattern, content, re.IGNORECASE):
                    # Extract sentence context
                    pos = match.start()
                    
                    # Find sentence boundaries
                    sentence_start = content.rfind('.', max(0, pos - 200), pos) + 1
                    sentence_end = content.find('.', pos, min(len(content), pos + 300))
                    if sentence_end == -1:
                        sentence_end = min(len(content), pos + 300)
                    
                    claim_text = content[sentence_start:sentence_end].strip()
                    
                    # Check for nearby citations
                    has_citation, citation = self.has_nearby_citation(content, pos)
                    
                    if not has_citation and len(claim_text) > 20:
                        # Find line number
                        line_num = content[:pos].count('\n') + 1
                        
                        # Categorize claim
                        claim_category = self.categorize_claim(claim_text)
                        
                        self.claims.append({
                            'file': str(file_path),
                            'line': line_num,
                            'claim': claim_text[:500],  # Limit length
                            'category': claim_category,
                            'matched_pattern': pattern,
                            'suggestions': self.citation_suggestions.get(claim_category, []),
                        })
    
    def generate_full_report(self, timestamp: str) -> Path:
        """Generate full report with all uncited claims"""
        report_path = self.output_dir / f'uncited_claims_{timestamp}.md'
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"# Uncited Claims Report\n\n")
            f.write(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n")
            f.write(f"Total claims found: {len(self.claims)}\n\n")
            
            # Group by category
            by_category = defaultdict(list)
            for claim in self.claims:
                by_category[claim['category']].append(claim)
            
            f.write("## Summary by Category\n\n")
            for category in sorted(by_category.keys()):
                f.write(f"- **{category}**: {len(by_category[category])} claims\n")
            f.write("\n---\n\n")
            
            # Detailed claims by category
            for category in sorted(by_category.keys()):
                f.write(f"## {category}\n\n")
                f.write(f"Found {len(by_category[category])} uncited claims.\n\n")
                
                for i, claim in enumerate(by_category[category], 1):
                    f.write(f"### Claim {i}\n\n")
                    f.write(f"**File:** `{claim['file']}`  \n")
                    f.write(f"**Line:** {claim['line']}  \n\n")
                    f.write(f"**Claim:**\n")
                    f.write(f"> {claim['claim']}\n\n")
                    f.write(f"**Suggested Citation Sources:**\n")
                    for suggestion in claim['suggestions']:
                        f.write(f"- {suggestion}\n")
                    f.write("\n---\n\n")
        
        return report_path
    
    def generate_priority_report(self, timestamp: str, top_n: int = 20) -> Path:
        """Generate priority report with top uncited claims"""
        report_path = self.output_dir / f'priority_citations_{timestamp}.md'
        
        # Prioritize claims by category importance and context
        priority_order = {
            ClaimCategory.NUMERICAL_VALUE: 5,
            ClaimCategory.OBSERVATION_DATA: 4,
            ClaimCategory.THEORY_MODEL: 3,
            ClaimCategory.COMPUTATIONAL: 2,
            ClaimCategory.PREVIOUS_RESEARCH: 1,
        }
        
        sorted_claims = sorted(
            self.claims,
            key=lambda x: (priority_order.get(x['category'], 0), len(x['claim'])),
            reverse=True
        )[:top_n]
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"# Priority Citations Needed\n\n")
            f.write(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n")
            f.write(f"Top {top_n} claims requiring immediate citations.\n\n")
            f.write("## Prioritization Criteria\n\n")
            f.write("Claims are prioritized by:\n")
            f.write("1. Numerical values and observations (highest priority)\n")
            f.write("2. Theoretical predictions and models\n")
            f.write("3. Computational methods\n")
            f.write("4. Previous research references\n\n")
            f.write("---\n\n")
            
            for i, claim in enumerate(sorted_claims, 1):
                f.write(f"## Priority {i}: {claim['category']}\n\n")
                f.write(f"**File:** `{claim['file']}`  \n")
                f.write(f"**Line:** {claim['line']}  \n\n")
                f.write(f"**Claim:**\n")
                f.write(f"> {claim['claim']}\n\n")
                f.write(f"**Recommended Actions:**\n")
                for suggestion in claim['suggestions']:
                    f.write(f"- [ ] {suggestion}\n")
                f.write("\n---\n\n")
        
        return report_path
    
    def generate_bibtex_templates(self) -> Path:
        """Generate BibTeX citation templates"""
        bib_path = self.papers_dir / 'citation_templates.bib'
        
        with open(bib_path, 'w', encoding='utf-8') as f:
            f.write("% Citation Templates for Luft Portal Project\n")
            f.write("% Generated: " + datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S') + " UTC\n\n")
            
            # DSCOVR references
            f.write("% ============================================\n")
            f.write("% DSCOVR Mission References\n")
            f.write("% ============================================\n\n")
            
            f.write("@article{dscovr_mission,\n")
            f.write("  author = {Burt, J. and Smith, K.},\n")
            f.write("  title = {Deep Space Climate Observatory: Mission Overview},\n")
            f.write("  journal = {Space Weather},\n")
            f.write("  year = {2015},\n")
            f.write("  volume = {13},\n")
            f.write("  pages = {XX--XX},\n")
            f.write("  doi = {10.XXXX/XXXXXX},\n")
            f.write("  note = {TODO: Complete citation details}\n")
            f.write("}\n\n")
            
            f.write("@techreport{dscovr_data,\n")
            f.write("  author = {{NOAA Space Weather Prediction Center}},\n")
            f.write("  title = {DSCOVR Data Products and Services},\n")
            f.write("  institution = {National Oceanic and Atmospheric Administration},\n")
            f.write("  year = {2024},\n")
            f.write("  url = {https://www.swpc.noaa.gov/products/real-time-solar-wind},\n")
            f.write("  note = {Real-time solar wind data}\n")
            f.write("}\n\n")
            
            # MAVEN references
            f.write("% ============================================\n")
            f.write("% MAVEN Mission References\n")
            f.write("% ============================================\n\n")
            
            f.write("@article{maven_mission,\n")
            f.write("  author = {Jakosky, B. M. and others},\n")
            f.write("  title = {The Mars Atmosphere and Volatile Evolution (MAVEN) Mission},\n")
            f.write("  journal = {Space Science Reviews},\n")
            f.write("  year = {2015},\n")
            f.write("  volume = {195},\n")
            f.write("  pages = {3--48},\n")
            f.write("  doi = {10.1007/s11214-015-0139-x}\n")
            f.write("}\n\n")
            
            f.write("@article{maven_plasma,\n")
            f.write("  author = {Halekas, J. S. and others},\n")
            f.write("  title = {Structure and Variability of Plasma Boundaries at Mars},\n")
            f.write("  journal = {Journal of Geophysical Research: Space Physics},\n")
            f.write("  year = {2017},\n")
            f.write("  volume = {122},\n")
            f.write("  pages = {XX--XX},\n")
            f.write("  doi = {10.XXXX/XXXXXX},\n")
            f.write("  note = {TODO: Complete citation details}\n")
            f.write("}\n\n")
            
            # Plasma physics textbooks
            f.write("% ============================================\n")
            f.write("% Plasma Physics Textbooks\n")
            f.write("% ============================================\n\n")
            
            f.write("@book{chen_plasma,\n")
            f.write("  author = {Chen, Francis F.},\n")
            f.write("  title = {Introduction to Plasma Physics and Controlled Fusion},\n")
            f.write("  publisher = {Springer},\n")
            f.write("  year = {2016},\n")
            f.write("  edition = {3rd},\n")
            f.write("  isbn = {978-3-319-22309-4},\n")
            f.write("  note = {Standard plasma physics reference}\n")
            f.write("}\n\n")
            
            f.write("@book{parks_space_plasma,\n")
            f.write("  author = {Parks, George K.},\n")
            f.write("  title = {Physics of Space Plasmas: An Introduction},\n")
            f.write("  publisher = {Westview Press},\n")
            f.write("  year = {2004},\n")
            f.write("  edition = {2nd},\n")
            f.write("  isbn = {978-0-8133-4148-7}\n")
            f.write("}\n\n")
            
            f.write("@book{gombosi_space_plasma,\n")
            f.write("  author = {Gombosi, Tamas I.},\n")
            f.write("  title = {Physics of the Space Environment},\n")
            f.write("  publisher = {Cambridge University Press},\n")
            f.write("  year = {1998},\n")
            f.write("  isbn = {978-0-521-59264-9}\n")
            f.write("}\n\n")
            
            # MHD references
            f.write("% ============================================\n")
            f.write("% Magnetohydrodynamics (MHD) References\n")
            f.write("% ============================================\n\n")
            
            f.write("@book{priest_forbes_reconnection,\n")
            f.write("  author = {Priest, E. R. and Forbes, T. G.},\n")
            f.write("  title = {Magnetic Reconnection: MHD Theory and Applications},\n")
            f.write("  publisher = {Cambridge University Press},\n")
            f.write("  year = {2000},\n")
            f.write("  isbn = {978-0-521-48179-1}\n")
            f.write("}\n\n")
            
            f.write("@book{goedbloed_mhd,\n")
            f.write("  author = {Goedbloed, J. P. and Keppens, R. and Poedts, S.},\n")
            f.write("  title = {Magnetohydrodynamics of Laboratory and Astrophysical Plasmas},\n")
            f.write("  publisher = {Cambridge University Press},\n")
            f.write("  year = {2019},\n")
            f.write("  isbn = {978-1-107-02269-7}\n")
            f.write("}\n\n")
            
            f.write("@article{dungey_reconnection,\n")
            f.write("  author = {Dungey, J. W.},\n")
            f.write("  title = {Interplanetary Magnetic Field and the Auroral Zones},\n")
            f.write("  journal = {Physical Review Letters},\n")
            f.write("  year = {1961},\n")
            f.write("  volume = {6},\n")
            f.write("  pages = {47--48},\n")
            f.write("  doi = {10.1103/PhysRevLett.6.47},\n")
            f.write("  note = {Classic paper on magnetic reconnection}\n")
            f.write("}\n\n")
            
            # Space weather references
            f.write("% ============================================\n")
            f.write("% Space Weather and Solar Wind References\n")
            f.write("% ============================================\n\n")
            
            f.write("@book{kivelson_russell,\n")
            f.write("  author = {Kivelson, M. G. and Russell, C. T.},\n")
            f.write("  title = {Introduction to Space Physics},\n")
            f.write("  publisher = {Cambridge University Press},\n")
            f.write("  year = {1995},\n")
            f.write("  isbn = {978-0-521-45714-9}\n")
            f.write("}\n\n")
            
            f.write("@article{solar_wind_parameters,\n")
            f.write("  author = {Richardson, J. D. and others},\n")
            f.write("  title = {Solar Wind Parameters in the Heliosphere},\n")
            f.write("  journal = {Space Science Reviews},\n")
            f.write("  year = {2018},\n")
            f.write("  volume = {214},\n")
            f.write("  pages = {XX--XX},\n")
            f.write("  doi = {10.XXXX/XXXXXX},\n")
            f.write("  note = {TODO: Complete citation details}\n")
            f.write("}\n\n")
            
            # Computational methods
            f.write("% ============================================\n")
            f.write("% Computational Methods References\n")
            f.write("% ============================================\n\n")
            
            f.write("@book{numerical_recipes,\n")
            f.write("  author = {Press, W. H. and Teukolsky, S. A. and Vetterling, W. T. and Flannery, B. P.},\n")
            f.write("  title = {Numerical Recipes: The Art of Scientific Computing},\n")
            f.write("  publisher = {Cambridge University Press},\n")
            f.write("  year = {2007},\n")
            f.write("  edition = {3rd},\n")
            f.write("  isbn = {978-0-521-88068-8}\n")
            f.write("}\n\n")
            
            f.write("@article{python_scientific,\n")
            f.write("  author = {Van Rossum, G. and Drake, F. L.},\n")
            f.write("  title = {Python 3 Reference Manual},\n")
            f.write("  journal = {CreateSpace},\n")
            f.write("  year = {2009},\n")
            f.write("  isbn = {978-1-4414-1269-0}\n")
            f.write("}\n\n")
            
            f.write("@article{numpy,\n")
            f.write("  author = {Harris, C. R. and others},\n")
            f.write("  title = {Array Programming with NumPy},\n")
            f.write("  journal = {Nature},\n")
            f.write("  year = {2020},\n")
            f.write("  volume = {585},\n")
            f.write("  pages = {357--362},\n")
            f.write("  doi = {10.1038/s41586-020-2649-2}\n")
            f.write("}\n\n")
            
            f.write("@article{scipy,\n")
            f.write("  author = {Virtanen, P. and others},\n")
            f.write("  title = {SciPy 1.0: Fundamental Algorithms for Scientific Computing in Python},\n")
            f.write("  journal = {Nature Methods},\n")
            f.write("  year = {2020},\n")
            f.write("  volume = {17},\n")
            f.write("  pages = {261--272},\n")
            f.write("  doi = {10.1038/s41592-019-0686-2}\n")
            f.write("}\n\n")
            
            # Template for user additions
            f.write("% ============================================\n")
            f.write("% Template for Additional Citations\n")
            f.write("% ============================================\n\n")
            
            f.write("@article{template_article,\n")
            f.write("  author = {LastName, FirstName and LastName2, FirstName2},\n")
            f.write("  title = {Article Title},\n")
            f.write("  journal = {Journal Name},\n")
            f.write("  year = {YYYY},\n")
            f.write("  volume = {XX},\n")
            f.write("  number = {X},\n")
            f.write("  pages = {XXX--XXX},\n")
            f.write("  doi = {10.XXXX/XXXXXX}\n")
            f.write("}\n\n")
            
            f.write("@book{template_book,\n")
            f.write("  author = {LastName, FirstName},\n")
            f.write("  title = {Book Title},\n")
            f.write("  publisher = {Publisher Name},\n")
            f.write("  year = {YYYY},\n")
            f.write("  edition = {Xth},\n")
            f.write("  isbn = {XXX-X-XXX-XXXXX-X}\n")
            f.write("}\n")
        
        return bib_path
    
    def generate_summary_json(self, timestamp: str) -> Path:
        """Generate JSON summary of findings"""
        summary_path = self.output_dir / f'summary_{timestamp}.json'
        
        by_category = defaultdict(list)
        by_file = defaultdict(int)
        
        for claim in self.claims:
            by_category[claim['category']].append({
                'file': claim['file'],
                'line': claim['line'],
                'claim': claim['claim'][:200]  # Truncate for JSON
            })
            by_file[claim['file']] += 1
        
        summary = {
            'generated': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'total_claims': len(self.claims),
            'by_category': {k: len(v) for k, v in by_category.items()},
            'by_file': dict(by_file),
            'top_files': sorted(by_file.items(), key=lambda x: x[1], reverse=True)[:10]
        }
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        return summary_path
    
    def run(self):
        """Main execution method"""
        print("=" * 70)
        print("Uncited Claims Identifier")
        print("Luft Portal Project")
        print("=" * 70)
        print()
        
        # Setup
        print("Setting up output directories...")
        self.setup_output_dirs()
        
        # Find files
        print("Scanning for markdown and LaTeX files...")
        files = self.find_files()
        print(f"Found {len(files)} files to scan")
        print()
        
        # Extract claims
        print("Extracting uncited claims...")
        for i, file_path in enumerate(files, 1):
            print(f"  [{i}/{len(files)}] Processing: {file_path}")
            self.extract_claims(file_path)
        
        print(f"\nTotal uncited claims found: {len(self.claims)}")
        print()
        
        # Generate reports
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        
        print("Generating reports...")
        
        full_report = self.generate_full_report(timestamp)
        print(f"  ✓ Full report: {full_report}")
        
        priority_report = self.generate_priority_report(timestamp, top_n=20)
        print(f"  ✓ Priority report: {priority_report}")
        
        bib_file = self.generate_bibtex_templates()
        print(f"  ✓ BibTeX templates: {bib_file}")
        
        summary_file = self.generate_summary_json(timestamp)
        print(f"  ✓ JSON summary: {summary_file}")
        
        print()
        print("=" * 70)
        print("Analysis Complete!")
        print("=" * 70)
        print()
        print(f"Total claims identified: {len(self.claims)}")
        print(f"Reports generated in: {self.output_dir}")
        print(f"Citation templates in: {bib_file}")
        print()
        print("Next steps:")
        print("  1. Review priority_citations_*.md for immediate action items")
        print("  2. Use citation_templates.bib to add proper citations")
        print("  3. Check uncited_claims_*.md for comprehensive list")
        print("  4. Update documentation with appropriate references")
        print()


def main():
    """Main entry point"""
    identifier = UncitedClaimsIdentifier()
    identifier.run()


if __name__ == '__main__':
    main()
