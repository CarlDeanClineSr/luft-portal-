#!/usr/bin/env python3
"""
Query the 58,263-link knowledge graph for discovery patterns
"""
import json
import os
from pathlib import Path
from collections import defaultdict

def load_network_data():
    """Load the link intelligence data"""
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    
    link_file = repo_root / 'data' / 'link_intelligence' / 'links_extracted_latest.json'
    
    if not link_file.exists():
        print(f"❌ Error: Could not find {link_file}")
        return None
    
    with open(link_file) as f:
        return json.load(f)

def find_chi_cluster(data):
    """Find all entries related to χ = 0.15"""
    chi_files = []
    
    # Check in categories and recent additions
    if 'categories' in data:
        for category, links in data['categories'].items():
            if any(term in category.lower() for term in ['chi', 'plasma', 'boundary']):
                chi_files.append(f"Category: {category} ({links} links)")
    
    if 'recent_additions' in data:
        for addition in data['recent_additions'][:20]:
            if isinstance(addition, dict):
                file_path = addition.get('file', '')
                if any(term in file_path.lower() for term in ['chi', '015', '0.15', 'boundary']):
                    chi_files.append(file_path)
    
    return chi_files

def find_cross_domain_links(data):
    """Find files linking NASA + CERN + other domains"""
    cross_domain = []
    
    # Note: unique_domains might be an integer count, not a list
    # Check categories for domain indicators instead
    
    # Check categories for cross-domain content
    if 'categories' in data:
        for category in data['categories'].keys():
            domains_in_cat = []
            cat_lower = category.lower()
            
            if any(term in cat_lower for term in ['nasa', 'noaa', 'space weather']):
                domains_in_cat.append('NASA/NOAA')
            if any(term in cat_lower for term in ['cern', 'lhc', 'particle']):
                domains_in_cat.append('CERN')
            if any(term in cat_lower for term in ['maven', 'mars', 'planetary']):
                domains_in_cat.append('Planetary')
            
            if len(domains_in_cat) >= 2:
                cross_domain.append((category, domains_in_cat))
    
    return cross_domain

def find_critical_nodes(data):
    """Find most important nodes in the network"""
    critical = []
    
    if 'categories' in data:
        # Sort categories by number of links
        sorted_cats = sorted(data['categories'].items(), 
                           key=lambda x: x[1], 
                           reverse=True)
        
        for category, count in sorted_cats[:10]:
            critical.append((category, count))
    
    return critical

def analyze_health_status(data):
    """Analyze network health"""
    health = {}
    
    if 'health_status' in data:
        health = data['health_status'].copy() if isinstance(data['health_status'], dict) else {'status': data['health_status']}
    
    if 'broken_links' in data:
        broken = data['broken_links']
        health['broken_links_count'] = broken if isinstance(broken, int) else len(broken)
    
    return health

def find_temporal_correlations(data):
    """Look for temporal patterns in the data"""
    temporal_files = []
    
    if 'categories' in data:
        for category in data['categories'].keys():
            if any(term in category.lower() for term in ['temporal', 'time', 'period', 'cycle', 'heartbeat']):
                temporal_files.append(category)
    
    if 'recent_additions' in data:
        for addition in data['recent_additions'][:50]:
            if isinstance(addition, dict):
                file_path = addition.get('file', '')
                if any(term in file_path.lower() for term in ['temporal', 'heartbeat', 'correlation']):
                    temporal_files.append(file_path)
    
    return temporal_files

if __name__ == '__main__':
    print("📊 Loading link intelligence network...")
    data = load_network_data()
    
    if not data:
        print("❌ Failed to load network data")
        exit(1)
    
    print(f"\n✅ Network loaded:")
    print(f"   Total links: {data.get('total_links', 0):,}")
    print(f"   Files analyzed: {data.get('total_files_analyzed', 0):,}")
    unique_domains = data.get('unique_domains', 0)
    print(f"   Unique domains: {unique_domains if isinstance(unique_domains, int) else len(unique_domains)}")
    print(f"   Timestamp: {data.get('timestamp', 'unknown')}")
    
    print("\n🔬 χ = 0.15 CLUSTER:")
    chi_cluster = find_chi_cluster(data)
    print(f"   {len(chi_cluster)} files/categories in χ cluster")
    for item in chi_cluster[:10]:
        print(f"   - {item}")
    
    print("\n🌐 CROSS-DOMAIN LINKS:")
    cross = find_cross_domain_links(data)
    print(f"   {len(cross)} cross-domain connections found")
    for item, domains in cross[:5]:
        print(f"   - {item}: {' + '.join(domains)}")
    
    print("\n⚠️ CRITICAL NODES (Top Categories by Link Count):")
    critical = find_critical_nodes(data)
    print("   These categories contain the most links:")
    for category, count in critical[:10]:
        print(f"   - {category}: {count:,} links")
    
    print("\n⏰ TEMPORAL CORRELATION FILES:")
    temporal = find_temporal_correlations(data)
    print(f"   {len(temporal)} temporal-related items found")
    for item in temporal[:10]:
        print(f"   - {item}")
    
    print("\n🏥 NETWORK HEALTH:")
    health = analyze_health_status(data)
    for key, value in health.items():
        print(f"   - {key}: {value}")
    
    # Save analysis results
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    output_dir = repo_root / 'data' / 'link_intelligence'
    
    unique_domains = data.get('unique_domains', 0)
    unique_domains_count = unique_domains if isinstance(unique_domains, int) else len(unique_domains)
    
    analysis_results = {
        'timestamp': data.get('timestamp'),
        'network_stats': {
            'total_links': data.get('total_links', 0),
            'total_files': data.get('total_files_analyzed', 0),
            'unique_domains': unique_domains_count
        },
        'chi_cluster': chi_cluster,
        'cross_domain_links': [{'item': item, 'domains': domains} for item, domains in cross],
        'critical_nodes': [{'category': cat, 'link_count': count} for cat, count in critical],
        'temporal_correlations': temporal,
        'health_status': health
    }
    
    output_file = output_dir / 'network_analysis.json'
    with open(output_file, 'w') as f:
        json.dump(analysis_results, f, indent=2)
    
    print(f"\n📊 Analysis saved to: {output_file}")
