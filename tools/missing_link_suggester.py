#!/usr/bin/env python3
"""
Missing Link Suggester for LUFT Documentation
Analyzes markdown files to suggest missing internal links between concepts.
"""

import os
import re
from pathlib import Path
from collections import defaultdict
import argparse


class MissingLinkSuggester:
    def __init__(self, docs_dir):
        self.docs_dir = Path(docs_dir)
        self.concepts = {}  # concept_name -> file_path
        self.concept_stats = defaultdict(lambda: {
            'file': '',
            'mentions': 0,
            'linked_mentions': 0,
            'concepts_linked_count': 0,
            'concepts_linked_list': []
        })
        self.suggestions = []

    def scan_markdown_files(self):
        """Scan all markdown files and extract concepts."""
        print(f"Scanning markdown files in {self.docs_dir}...")
        
        for md_file in self.docs_dir.rglob("*.md"):
            try:
                self._process_file(md_file)
            except Exception as e:
                print(f"Warning: Error processing {md_file}: {e}")
                continue

    def _process_file(self, file_path):
        """Process a single markdown file to extract concepts."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}")
            return

        relative_path = file_path.relative_to(self.docs_dir)
        
        # Extract concepts from headers
        headers = re.findall(r'^#+\s+(.+)$', content, re.MULTILINE)
        for header in headers:
            # Clean header text
            concept = self._clean_concept(header)
            if concept and len(concept) > 3:  # Avoid very short concepts
                self.concepts[concept.lower()] = str(relative_path)
                self.concept_stats[concept.lower()]['file'] = str(relative_path)

        # Extract concepts from bold text (potential important terms)
        bold_terms = re.findall(r'\*\*([^*]+)\*\*', content)
        for term in bold_terms:
            concept = self._clean_concept(term)
            if concept and len(concept) > 3:
                concept_lower = concept.lower()
                if concept_lower not in self.concepts:
                    self.concepts[concept_lower] = str(relative_path)
                    self.concept_stats[concept_lower]['file'] = str(relative_path)

    def _clean_concept(self, text):
        """Clean concept text by removing special characters and extra whitespace."""
        # Remove markdown links
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        # Remove special characters but keep spaces and hyphens
        text = re.sub(r'[^a-zA-Z0-9\s\-]', '', text)
        # Normalize whitespace
        text = ' '.join(text.split())
        return text.strip()

    def analyze_links(self):
        """Analyze existing links and find missing link opportunities."""
        print("Analyzing existing links and finding opportunities...")
        
        for md_file in self.docs_dir.rglob("*.md"):
            try:
                self._analyze_file_links(md_file)
            except Exception as e:
                print(f"Warning: Error analyzing links in {md_file}: {e}")
                continue

    def _analyze_file_links(self, file_path):
        """Analyze links in a single file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}")
            return

        relative_path = file_path.relative_to(self.docs_dir)
        
        # Find all existing markdown links
        existing_links = set()
        for match in re.finditer(r'\[([^\]]+)\]\(([^\)]+)\)', content):
            link_text = match.group(1).lower()
            existing_links.add(self._clean_concept(link_text))

        # Check for mentions of other concepts
        for concept, concept_file in self.concepts.items():
            if str(relative_path) == concept_file:
                continue  # Skip self-references

            # Count mentions of this concept in the file
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(concept) + r'\b'
            mentions = re.findall(pattern, content, re.IGNORECASE)
            
            if mentions:
                self.concept_stats[concept]['mentions'] += len(mentions)
                
                # Check if any mentions are already linked
                linked_count = 0
                for match in re.finditer(r'\[([^\]]+)\]\([^\)]+\)', content):
                    link_text = self._clean_concept(match.group(1))
                    if concept in link_text.lower() or link_text.lower() in concept:
                        linked_count += 1

                self.concept_stats[concept]['linked_mentions'] += linked_count
                unlinked_mentions = len(mentions) - linked_count

                # If there are unlinked mentions, create a suggestion
                if unlinked_mentions > 0:
                    # Check if we've already linked from this file to the concept
                    if concept not in self.concept_stats[str(relative_path)]['concepts_linked_list']:
                        self.suggestions.append({
                            'from_file': str(relative_path),
                            'to_concept': concept,
                            'to_file': concept_file,
                            'unlinked_mentions': unlinked_mentions,
                            'priority': self._calculate_priority(unlinked_mentions, concept)
                        })
                        self.concept_stats[str(relative_path)]['concepts_linked_list'].append(concept)
                        self.concept_stats[str(relative_path)]['concepts_linked_count'] += 1

    def _calculate_priority(self, mentions, concept):
        """Calculate priority score for a suggestion."""
        # Higher priority for more mentions and longer concept names
        score = mentions * 10
        score += len(concept.split()) * 5  # Multi-word concepts get bonus
        return score

    def generate_report(self, output_file=None):
        """Generate a comprehensive report of missing link suggestions."""
        print("\n" + "="*80)
        print("MISSING LINK SUGGESTIONS REPORT")
        print("="*80)

        # Sort suggestions by priority
        sorted_suggestions = sorted(
            self.suggestions,
            key=lambda x: x['priority'],
            reverse=True
        )

        print(f"\nTotal concepts identified: {len(self.concepts)}")
        print(f"Total link suggestions: {len(sorted_suggestions)}")
        print("\n" + "-"*80)

        # Group suggestions by source file
        suggestions_by_file = defaultdict(list)
        for suggestion in sorted_suggestions:
            suggestions_by_file[suggestion['from_file']].append(suggestion)

        report_lines = []
        report_lines.append("="*80)
        report_lines.append("MISSING LINK SUGGESTIONS REPORT")
        report_lines.append("="*80)
        report_lines.append(f"\nTotal concepts identified: {len(self.concepts)}")
        report_lines.append(f"Total link suggestions: {len(sorted_suggestions)}")
        report_lines.append("\n" + "-"*80)

        # Display suggestions grouped by file
        for file_path in sorted(suggestions_by_file.keys()):
            file_suggestions = suggestions_by_file[file_path]
            print(f"\n📄 File: {file_path}")
            print(f"   Suggested links: {len(file_suggestions)}")
            
            report_lines.append(f"\n📄 File: {file_path}")
            report_lines.append(f"   Suggested links: {len(file_suggestions)}")

            for suggestion in sorted(file_suggestions, key=lambda x: x['priority'], reverse=True):
                print(f"   → Link to: {suggestion['to_concept']}")
                print(f"      Target: {suggestion['to_file']}")
                print(f"      Unlinked mentions: {suggestion['unlinked_mentions']}")
                print(f"      Priority: {suggestion['priority']}")
                
                report_lines.append(f"   → Link to: {suggestion['to_concept']}")
                report_lines.append(f"      Target: {suggestion['to_file']}")
                report_lines.append(f"      Unlinked mentions: {suggestion['unlinked_mentions']}")
                report_lines.append(f"      Priority: {suggestion['priority']}")

        # Statistics section
        print("\n" + "="*80)
        print("CONCEPT STATISTICS")
        print("="*80)
        
        report_lines.append("\n" + "="*80)
        report_lines.append("CONCEPT STATISTICS")
        report_lines.append("="*80)

        # Sort concepts by mention count
        sorted_concepts = sorted(
            self.concept_stats.items(),
            key=lambda x: x[1]['mentions'],
            reverse=True
        )

        print(f"\nTop 20 Most Mentioned Concepts:")
        report_lines.append(f"\nTop 20 Most Mentioned Concepts:")
        
        for concept, stats in sorted_concepts[:20]:
            if stats['mentions'] > 0:
                linked_percentage = (stats['linked_mentions'] / stats['mentions'] * 100) if stats['mentions'] > 0 else 0
                print(f"  • {concept}")
                print(f"      Mentions: {stats['mentions']} | Linked: {stats['linked_mentions']} ({linked_percentage:.1f}%)")
                print(f"      Defined in: {stats['file']}")
                
                report_lines.append(f"  • {concept}")
                report_lines.append(f"      Mentions: {stats['mentions']} | Linked: {stats['linked_mentions']} ({linked_percentage:.1f}%)")
                report_lines.append(f"      Defined in: {stats['file']}")

        # Concepts with low link coverage
        print(f"\nConcepts with Low Link Coverage (< 50%):")
        report_lines.append(f"\nConcepts with Low Link Coverage (< 50%):")
        
        low_coverage = [
            (concept, stats) for concept, stats in sorted_concepts
            if stats['mentions'] >= 3 and 
               (stats['linked_mentions'] / stats['mentions'] * 100 if stats['mentions'] > 0 else 0) < 50
        ]

        for concept, stats in low_coverage[:15]:
            linked_percentage = (stats['linked_mentions'] / stats['mentions'] * 100) if stats['mentions'] > 0 else 0
            print(f"  • {concept}")
            print(f"      Mentions: {stats['mentions']} | Linked: {stats['linked_mentions']} ({linked_percentage:.1f}%)")
            
            report_lines.append(f"  • {concept}")
            report_lines.append(f"      Mentions: {stats['mentions']} | Linked: {stats['linked_mentions']} ({linked_percentage:.1f}%)")

        # Write to file if specified
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(report_lines))
                print(f"\n✅ Report saved to: {output_file}")
            except Exception as e:
                print(f"\n⚠️ Warning: Could not save report to {output_file}: {e}")

        print("\n" + "="*80)
        print("END OF REPORT")
        print("="*80)

    def run(self, output_file=None):
        """Run the complete analysis."""
        self.scan_markdown_files()
        self.analyze_links()
        self.generate_report(output_file)


def main():
    parser = argparse.ArgumentParser(
        description='Analyze LUFT documentation for missing internal links'
    )
    parser.add_argument(
        '--docs-dir',
        default='docs',
        help='Directory containing markdown documentation (default: docs)'
    )
    parser.add_argument(
        '--output',
        '-o',
        help='Output file for the report (optional)'
    )

    args = parser.parse_args()

    # Check if docs directory exists
    if not os.path.isdir(args.docs_dir):
        print(f"Error: Documentation directory '{args.docs_dir}' not found.")
        print("Please specify a valid directory with --docs-dir")
        return 1

    # Run the analysis
    suggester = MissingLinkSuggester(args.docs_dir)
    suggester.run(args.output)

    return 0


if __name__ == '__main__':
    exit(main())
