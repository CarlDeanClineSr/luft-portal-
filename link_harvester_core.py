#!/usr/bin/env python3
"""
LUFT Link Harvester Core
========================

Comprehensive link extraction and intelligence gathering system for the LUFT Portal ecosystem.
This tool mines internal repository links and builds a knowledge graph of connections across
scientific data sources.

Author: Carl Dean Cline Sr.
Created: December 2025
Location: Lincoln, Nebraska, USA
Email: CARLDCLINE@GMAIL.COM

Mission: Build the universal link intelligence network that connects LUFT to the entire
         scientific data ecosystem.

Usage:
    python link_harvester_core.py --scan-repo
    python link_harvester_core.py --output-json links_data.json
    python link_harvester_core.py --output-csv links_data.csv
"""

import re
import os
import json
import csv
from pathlib import Path
from urllib.parse import urlparse
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import argparse


class LinkHarvester:
    """
    Comprehensive link extraction engine for LUFT Portal.
    
    Capabilities:
    - Scan all repository files for URLs
    - Categorize links by domain and type
    - Extract internal cross-references
    - Build relationship maps
    - Export to multiple formats
    """
    
    # File extensions to scan
    TEXT_EXTENSIONS = {
        '.md', '.txt', '.html', '.htm', '.yaml', '.yml', 
        '.json', '.py', '.js', '.css', '.sh', '.csv',
        '.xml', '.tex', '.rst', '.org'
    }
    
    # Binary files to skip
    SKIP_EXTENSIONS = {
        '.h5', '.wav', '.mp4', '.png', '.jpg', '.jpeg', 
        '.gif', '.pdf', '.zip', '.tar', '.gz', '.bz2',
        '.exe', '.bin', '.dat', '.pyc'
    }
    
    # URL pattern for comprehensive link extraction
    # Note: This regex is intentionally permissive to catch various URL formats
    # found in documentation, config files, and comments. For stricter validation,
    # use urllib.parse after extraction.
    URL_PATTERN = re.compile(
        r'(?:http|https|ftp)://(?:[a-zA-Z0-9\-._~:/?#\[\]@!$&\'()*+,;=%]+)',
        re.IGNORECASE
    )
    
    # Domain categories for classification
    DOMAIN_CATEGORIES = {
        'nasa.gov': 'NASA',
        'noaa.gov': 'NOAA',
        'usgs.gov': 'USGS',
        'cern.ch': 'CERN',
        'esa.int': 'ESA',
        'jaxa.jp': 'JAXA',
        'isro.gov.in': 'ISRO',
        'spacex.com': 'SpaceX',
        'starlink.com': 'SpaceX',
        'github.com': 'GitHub',
        'arxiv.org': 'arXiv',
        'harvard.edu': 'Harvard',
        'caltech.edu': 'Caltech',
        'colorado.edu': 'University',
        'ac.cn': 'China',
        'gov.cn': 'China',
        'ligo.org': 'LIGO',
        'almaobservatory.org': 'ALMA',
        'breakthroughinitiatives.org': 'Breakthrough',
        'zooniverse.org': 'Zooniverse',
        'spaceweatherlive.com': 'Space Weather',
    }
    
    def __init__(self, repo_path: str = '.'):
        """Initialize the link harvester."""
        self.repo_path = Path(repo_path)
        self.links: Dict[str, List[Dict]] = defaultdict(list)
        self.file_count = 0
        self.link_count = 0
        self.domains: Set[str] = set()
        
    def should_scan_file(self, file_path: Path) -> bool:
        """Determine if a file should be scanned for links."""
        # Skip hidden files and directories
        if any(part.startswith('.') for part in file_path.parts):
            # Allow .github directory
            if '.github' not in file_path.parts:
                return False
        
        # Skip based on extension
        suffix = file_path.suffix.lower()
        if suffix in self.SKIP_EXTENSIONS:
            return False
            
        # Only scan text files
        if suffix and suffix not in self.TEXT_EXTENSIONS:
            return False
            
        return True
    
    def extract_links_from_file(self, file_path: Path) -> List[Dict]:
        """Extract all URLs from a file."""
        links = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                
            # Find all URLs
            matches = self.URL_PATTERN.finditer(content)
            
            for match in matches:
                url = match.group(0)
                # Clean up trailing punctuation
                url = re.sub(r'[.,;:)\]}>]+$', '', url)
                
                # Parse URL
                parsed = urlparse(url)
                domain = parsed.netloc.lower()
                
                # Categorize domain
                category = 'Other'
                for pattern, cat in self.DOMAIN_CATEGORIES.items():
                    if pattern in domain:
                        category = cat
                        break
                
                link_data = {
                    'url': url,
                    'domain': domain,
                    'category': category,
                    'scheme': parsed.scheme,
                    'path': parsed.path,
                    'file': str(file_path.relative_to(self.repo_path))
                }
                
                links.append(link_data)
                self.domains.add(domain)
                
        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}")
            
        return links
    
    def scan_repository(self) -> Dict[str, any]:
        """Scan the entire repository for links."""
        print(f"Scanning repository: {self.repo_path}")
        print(f"Looking for text files with extensions: {', '.join(sorted(self.TEXT_EXTENSIONS))}")
        print()
        
        for file_path in self.repo_path.rglob('*'):
            if not file_path.is_file():
                continue
                
            if not self.should_scan_file(file_path):
                continue
            
            self.file_count += 1
            file_links = self.extract_links_from_file(file_path)
            
            if file_links:
                rel_path = str(file_path.relative_to(self.repo_path))
                self.links[rel_path].extend(file_links)
                self.link_count += len(file_links)
                
                if len(file_links) > 5:  # Report files with many links
                    print(f"✓ {rel_path}: {len(file_links)} links")
        
        print()
        print(f"Scan complete!")
        print(f"Files scanned: {self.file_count}")
        print(f"Total links found: {self.link_count}")
        print(f"Unique domains: {len(self.domains)}")
        
        return self.get_statistics()
    
    def get_statistics(self) -> Dict[str, any]:
        """Generate statistics about harvested links."""
        # Count by category
        category_counts = defaultdict(int)
        domain_counts = defaultdict(int)
        
        for file_links in self.links.values():
            for link in file_links:
                category_counts[link['category']] += 1
                domain_counts[link['domain']] += 1
        
        # Top domains
        top_domains = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)[:20]
        
        stats = {
            'files_scanned': self.file_count,
            'total_links': self.link_count,
            'unique_domains': len(self.domains),
            'categories': dict(category_counts),
            'top_domains': dict(top_domains)
        }
        
        return stats
    
    def export_to_json(self, output_path: str):
        """Export harvested links to JSON format."""
        data = {
            'metadata': {
                'repository': str(self.repo_path),
                'files_scanned': self.file_count,
                'total_links': self.link_count,
                'unique_domains': len(self.domains)
            },
            'statistics': self.get_statistics(),
            'links_by_file': dict(self.links),
            'domains': sorted(list(self.domains))
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Exported to JSON: {output_path}")
    
    def export_to_csv(self, output_path: str):
        """Export harvested links to CSV format."""
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['File', 'URL', 'Domain', 'Category', 'Scheme', 'Path'])
            
            for file_path, file_links in sorted(self.links.items()):
                for link in file_links:
                    writer.writerow([
                        link['file'],
                        link['url'],
                        link['domain'],
                        link['category'],
                        link['scheme'],
                        link['path']
                    ])
        
        print(f"Exported to CSV: {output_path}")
    
    def print_summary(self):
        """Print a summary of harvested links."""
        stats = self.get_statistics()
        
        print("\n" + "="*60)
        print("LUFT LINK HARVESTER SUMMARY")
        print("="*60)
        print(f"Repository: {self.repo_path}")
        print(f"Files scanned: {stats['files_scanned']}")
        print(f"Total links found: {stats['total_links']}")
        print(f"Unique domains: {stats['unique_domains']}")
        print()
        
        print("Links by Category:")
        for category, count in sorted(stats['categories'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {category:20s}: {count:4d} links")
        print()
        
        print("Top 10 Domains:")
        for domain, count in list(stats['top_domains'].items())[:10]:
            print(f"  {domain:40s}: {count:4d} links")
        print("="*60)


def main():
    """Main entry point for link harvester."""
    parser = argparse.ArgumentParser(
        description='LUFT Link Harvester - Extract and analyze links from repository',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python link_harvester_core.py --scan-repo
  python link_harvester_core.py --output-json data/links.json
  python link_harvester_core.py --output-json links.json --output-csv links.csv
        """
    )
    
    parser.add_argument('--repo-path', default='.',
                       help='Path to repository (default: current directory)')
    parser.add_argument('--scan-repo', action='store_true',
                       help='Scan repository and print summary')
    parser.add_argument('--output-json', metavar='FILE',
                       help='Export results to JSON file')
    parser.add_argument('--output-csv', metavar='FILE',
                       help='Export results to CSV file')
    
    args = parser.parse_args()
    
    # Create harvester
    harvester = LinkHarvester(args.repo_path)
    
    # Scan repository
    harvester.scan_repository()
    
    # Print summary if requested
    if args.scan_repo or (not args.output_json and not args.output_csv):
        harvester.print_summary()
    
    # Export to JSON
    if args.output_json:
        harvester.export_to_json(args.output_json)
    
    # Export to CSV
    if args.output_csv:
        harvester.export_to_csv(args.output_csv)


if __name__ == '__main__':
    main()
