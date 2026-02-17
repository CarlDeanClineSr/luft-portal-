#!/usr/bin/env python3
"""
LUFT Link Graph Analyzer
=========================

Network analysis and visualization tool for the LUFT Portal link intelligence system.
Builds knowledge graphs from harvested links and computes network metrics.

Author: Carl Dean Cline Sr.
Created: December 2025
Location: Lincoln, Nebraska, USA
Email: CARLDCLINE@GMAIL.COM

Mission: Analyze and visualize the connections between LUFT and the scientific ecosystem.

Usage:
    python link_graph_analyzer.py --input links.json
    python link_graph_analyzer.py --input links.json --output-graph network.json
    python link_graph_analyzer.py --input links.json --visualize
"""

import json
import argparse
from collections import defaultdict
from typing import Dict, List, Set, Tuple
from pathlib import Path


class LinkGraphAnalyzer:
    """
    Network analysis for LUFT link intelligence.
    
    Capabilities:
    - Build directed graph from harvested links
    - Compute network metrics (centrality, clustering, etc.)
    - Identify communities and clusters
    - Export visualization-ready data
    """
    
    def __init__(self, links_data: Dict = None):
        """Initialize the analyzer with harvested links data."""
        self.links_data = links_data or {}
        self.nodes = {}  # node_id -> node_data
        self.edges = []  # list of {source, target, data}
        self.domain_to_node = {}  # domain -> node_id
        self.file_to_node = {}  # file -> node_id
        self.next_node_id = 0
        
    def load_from_json(self, json_path: str):
        """Load harvested links from JSON file."""
        with open(json_path, 'r', encoding='utf-8') as f:
            self.links_data = json.load(f)
        print(f"Loaded {self.links_data['metadata']['total_links']} links from {json_path}")
    
    def _get_or_create_node(self, node_type: str, identifier: str, **attributes) -> int:
        """Get existing node or create new one."""
        if node_type == 'domain':
            if identifier in self.domain_to_node:
                return self.domain_to_node[identifier]
        elif node_type == 'file':
            if identifier in self.file_to_node:
                return self.file_to_node[identifier]
        
        # Create new node
        node_id = self.next_node_id
        self.next_node_id += 1
        
        self.nodes[node_id] = {
            'id': node_id,
            'type': node_type,
            'identifier': identifier,
            **attributes
        }
        
        # Update index
        if node_type == 'domain':
            self.domain_to_node[identifier] = node_id
        elif node_type == 'file':
            self.file_to_node[identifier] = node_id
        
        return node_id
    
    def build_graph(self, graph_type: str = 'file-domain'):
        """
        Build graph from harvested links.
        
        Args:
            graph_type: Type of graph to build
                - 'file-domain': Files linked to domains
                - 'domain-only': Only domains and their relationships
                - 'file-only': Only files and their relationships
        """
        print(f"Building {graph_type} graph...")
        
        links_by_file = self.links_data.get('links_by_file', {})
        
        if graph_type == 'file-domain':
            # Create nodes for files and domains
            for file_path, file_links in links_by_file.items():
                # Create file node
                file_node = self._get_or_create_node(
                    'file', 
                    file_path,
                    label=Path(file_path).name,
                    path=file_path,
                    link_count=len(file_links)
                )
                
                # Create domain nodes and edges
                for link in file_links:
                    domain = link['domain']
                    domain_node = self._get_or_create_node(
                        'domain',
                        domain,
                        label=domain,
                        category=link.get('category', 'Other')
                    )
                    
                    # Create edge from file to domain
                    self.edges.append({
                        'source': file_node,
                        'target': domain_node,
                        'url': link['url'],
                        'category': link.get('category', 'Other')
                    })
        
        elif graph_type == 'domain-only':
            # Build co-occurrence graph of domains
            # Domains that appear in the same file are connected
            for file_path, file_links in links_by_file.items():
                domains = set(link['domain'] for link in file_links)
                
                for domain in domains:
                    self._get_or_create_node(
                        'domain',
                        domain,
                        label=domain,
                        category=next((link['category'] for link in file_links 
                                     if link['domain'] == domain), 'Other')
                    )
                
                # Create edges between co-occurring domains
                domains_list = list(domains)
                for i, domain1 in enumerate(domains_list):
                    for domain2 in domains_list[i+1:]:
                        node1 = self.domain_to_node[domain1]
                        node2 = self.domain_to_node[domain2]
                        
                        self.edges.append({
                            'source': node1,
                            'target': node2,
                            'weight': 1,
                            'co_occurrence': file_path
                        })
        
        elif graph_type == 'file-only':
            # Build file similarity graph based on shared domains
            domain_to_files = defaultdict(set)
            
            for file_path, file_links in links_by_file.items():
                # Create file node
                self._get_or_create_node(
                    'file',
                    file_path,
                    label=Path(file_path).name,
                    path=file_path,
                    link_count=len(file_links)
                )
                
                # Track which files reference which domains
                for link in file_links:
                    domain_to_files[link['domain']].add(file_path)
            
            # Create edges between files that share domains
            for domain, files in domain_to_files.items():
                files_list = list(files)
                for i, file1 in enumerate(files_list):
                    for file2 in files_list[i+1:]:
                        node1 = self.file_to_node[file1]
                        node2 = self.file_to_node[file2]
                        
                        self.edges.append({
                            'source': node1,
                            'target': node2,
                            'weight': 1,
                            'shared_domain': domain
                        })
        
        print(f"Graph built: {len(self.nodes)} nodes, {len(self.edges)} edges")
    
    def compute_metrics(self) -> Dict:
        """Compute basic network metrics."""
        # Compute degree for each node
        out_degree = defaultdict(int)
        in_degree = defaultdict(int)
        
        for edge in self.edges:
            out_degree[edge['source']] += 1
            in_degree[edge['target']] += 1
        
        # Update node data with degrees
        for node_id in self.nodes:
            self.nodes[node_id]['out_degree'] = out_degree[node_id]
            self.nodes[node_id]['in_degree'] = in_degree[node_id]
            self.nodes[node_id]['total_degree'] = out_degree[node_id] + in_degree[node_id]
        
        # Find top nodes by degree
        sorted_nodes = sorted(
            self.nodes.items(),
            key=lambda x: x[1]['total_degree'],
            reverse=True
        )
        
        metrics = {
            'node_count': len(self.nodes),
            'edge_count': len(self.edges),
            'nodes_by_type': {},
            'top_nodes': []
        }
        
        # Count nodes by type
        for node_data in self.nodes.values():
            node_type = node_data['type']
            metrics['nodes_by_type'][node_type] = metrics['nodes_by_type'].get(node_type, 0) + 1
        
        # Top 20 nodes by degree
        for node_id, node_data in sorted_nodes[:20]:
            metrics['top_nodes'].append({
                'id': node_id,
                'identifier': node_data['identifier'],
                'type': node_data['type'],
                'degree': node_data['total_degree'],
                'category': node_data.get('category', 'N/A')
            })
        
        return metrics
    
    def export_to_json(self, output_path: str):
        """Export graph to JSON format for visualization."""
        graph_data = {
            'metadata': {
                'source': 'LUFT Link Harvester',
                'node_count': len(self.nodes),
                'edge_count': len(self.edges)
            },
            'nodes': [node_data for node_data in self.nodes.values()],
            'edges': self.edges,
            'metrics': self.compute_metrics()
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, indent=2, ensure_ascii=False)
        
        print(f"Exported graph to: {output_path}")
    
    def print_summary(self):
        """Print a summary of the network."""
        metrics = self.compute_metrics()
        
        print("\n" + "="*60)
        print("LUFT LINK GRAPH ANALYSIS")
        print("="*60)
        print(f"Nodes: {metrics['node_count']}")
        print(f"Edges: {metrics['edge_count']}")
        print()
        
        print("Nodes by Type:")
        for node_type, count in metrics['nodes_by_type'].items():
            print(f"  {node_type:15s}: {count:4d}")
        print()
        
        print("Top 10 Most Connected Nodes:")
        for i, node in enumerate(metrics['top_nodes'][:10], 1):
            print(f"  {i:2d}. {node['identifier']:40s} "
                  f"(degree={node['degree']}, type={node['type']}, "
                  f"category={node['category']})")
        print("="*60)
    
    def generate_visualization_html(self, output_path: str, graph_json_path: str):
        """Generate simple HTML visualization using vis.js."""
        html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>LUFT Link Intelligence Network</title>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #1a1a2e;
            color: #eee;
        }
        h1 {
            text-align: center;
            color: #16c9f6;
        }
        #network {
            width: 100%;
            height: 600px;
            border: 2px solid #16c9f6;
            background: #0f0f1e;
            border-radius: 8px;
        }
        #info {
            margin-top: 20px;
            padding: 15px;
            background: #16213e;
            border-radius: 8px;
        }
        .metric {
            display: inline-block;
            margin: 10px 20px;
            padding: 10px;
            background: #0f3460;
            border-radius: 5px;
        }
        .metric span {
            font-weight: bold;
            color: #16c9f6;
        }
    </style>
</head>
<body>
    <h1>🌐 LUFT Link Intelligence Network</h1>
    <div id="network"></div>
    <div id="info">
        <h2>Network Statistics</h2>
        <div class="metric">Nodes: <span id="node-count">-</span></div>
        <div class="metric">Edges: <span id="edge-count">-</span></div>
        <div class="metric">Selected: <span id="selected">None</span></div>
    </div>

    <script>
        // Load graph data
        fetch('{{GRAPH_JSON_PATH}}')
            .then(response => response.json())
            .then(data => {
                // Update metrics
                document.getElementById('node-count').textContent = data.metadata.node_count;
                document.getElementById('edge-count').textContent = data.metadata.edge_count;
                
                // Prepare nodes for vis.js
                const nodes = data.nodes.map(node => ({
                    id: node.id,
                    label: node.label || node.identifier,
                    title: `${node.type}: ${node.identifier}`,
                    group: node.type,
                    value: (node.total_degree || 1),
                    font: { color: '#eee' }
                }));
                
                // Prepare edges for vis.js
                const edges = data.edges.map((edge, idx) => ({
                    id: idx,
                    from: edge.source,
                    to: edge.target,
                    arrows: 'to',
                    color: { color: '#16c9f6', opacity: 0.3 }
                }));
                
                // Create network
                const container = document.getElementById('network');
                const networkData = {
                    nodes: new vis.DataSet(nodes),
                    edges: new vis.DataSet(edges)
                };
                
                const options = {
                    nodes: {
                        shape: 'dot',
                        scaling: {
                            min: 10,
                            max: 30
                        }
                    },
                    edges: {
                        smooth: {
                            type: 'continuous'
                        }
                    },
                    physics: {
                        stabilization: false,
                        barnesHut: {
                            gravitationalConstant: -8000,
                            springConstant: 0.001,
                            springLength: 200
                        }
                    },
                    groups: {
                        file: { color: '#16c9f6' },
                        domain: { color: '#e94560' }
                    }
                };
                
                const network = new vis.Network(container, networkData, options);
                
                // Handle selection
                network.on('selectNode', function(params) {
                    const nodeId = params.nodes[0];
                    const node = data.nodes.find(n => n.id === nodeId);
                    if (node) {
                        document.getElementById('selected').textContent = 
                            `${node.type}: ${node.identifier}`;
                    }
                });
                
                network.on('deselectNode', function() {
                    document.getElementById('selected').textContent = 'None';
                });
            })
            .catch(error => {
                console.error('Error loading graph data:', error);
                document.getElementById('network').innerHTML = 
                    '<p style="color: red; text-align: center; padding: 50px;">' +
                    'Error loading graph data. Please ensure the JSON file exists.</p>';
            });
    </script>
</body>
</html>
"""
        html_content = html_template.replace('{{GRAPH_JSON_PATH}}', graph_json_path)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Generated visualization HTML: {output_path}")


def main():
    """Main entry point for link graph analyzer."""
    parser = argparse.ArgumentParser(
        description='LUFT Link Graph Analyzer - Network analysis and visualization',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python link_graph_analyzer.py --input links.json
  python link_graph_analyzer.py --input links.json --output network.json
  python link_graph_analyzer.py --input links.json --type domain-only
  python link_graph_analyzer.py --input links.json --visualize
        """
    )
    
    parser.add_argument('--input', required=True, metavar='FILE',
                       help='Input JSON file from link harvester')
    parser.add_argument('--output', metavar='FILE',
                       help='Output graph JSON file')
    parser.add_argument('--type', default='file-domain',
                       choices=['file-domain', 'domain-only', 'file-only'],
                       help='Type of graph to build (default: file-domain)')
    parser.add_argument('--visualize', action='store_true',
                       help='Generate HTML visualization')
    parser.add_argument('--viz-output', default='link_network_visualization.html',
                       help='Output HTML file for visualization')
    
    args = parser.parse_args()
    
    # Create analyzer
    analyzer = LinkGraphAnalyzer()
    
    # Load data
    analyzer.load_from_json(args.input)
    
    # Build graph
    analyzer.build_graph(args.type)
    
    # Print summary
    analyzer.print_summary()
    
    # Export graph
    output_file = args.output or 'link_network.json'
    analyzer.export_to_json(output_file)
    
    # Generate visualization if requested
    if args.visualize:
        analyzer.generate_visualization_html(args.viz_output, output_file)
        print(f"\nOpen {args.viz_output} in a web browser to view the network.")


if __name__ == '__main__':
    main()
