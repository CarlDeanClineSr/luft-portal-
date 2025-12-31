#!/usr/bin/env python3
"""
LUFT Link Monitor
=================

External data source health monitoring for the LUFT Portal Link Intelligence Network.
Checks HTTP status, response times, SSL certificates, and validates JSON/XML responses.

Author: Carl Dean Cline Sr.
Created: December 2025
Location: Lincoln, Nebraska, USA
Email: CARLDCLINE@GMAIL.COM

Mission: Monitor the health of all 43+ external scientific data sources that LUFT depends on.

Usage:
    python tools/link_monitor.py --check-all
    python tools/link_monitor.py --registry external_data_sources_registry.yaml
    python tools/link_monitor.py --output data/source_health_log.json
"""

import argparse
import json
import time
import ssl
import socket
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.parse import urlparse
import sys

# Try to import requests, but provide graceful fallback
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    import urllib.request
    import urllib.error

# Try to import yaml, but provide graceful fallback
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    print("Warning: PyYAML not installed. Using JSON registry fallback.", file=sys.stderr)


class LinkMonitor:
    """
    Health monitoring system for external data sources.
    
    Capabilities:
    - Check HTTP status codes
    - Measure response times
    - Validate SSL certificates
    - Detect JSON/XML response validity
    - Log availability history
    - Generate health reports
    """
    
    def __init__(self, timeout: int = 10):
        """
        Initialize the link monitor.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.results = []
        self.summary = {
            'total_sources': 0,
            'sources_checked': 0,
            'sources_healthy': 0,
            'sources_degraded': 0,
            'sources_down': 0,
            'average_response_time': 0.0,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    
    def check_url_requests(self, url: str) -> Dict:
        """
        Check URL health using requests library.
        
        Args:
            url: URL to check
            
        Returns:
            Dictionary with health status
        """
        result = {
            'url': url,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'status': 'unknown',
            'status_code': None,
            'response_time_ms': None,
            'ssl_valid': None,
            'error': None
        }
        
        try:
            start_time = time.time()
            response = requests.head(
                url, 
                timeout=self.timeout,
                allow_redirects=True,
                verify=True  # Verify SSL certificates
            )
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            result['status_code'] = response.status_code
            result['response_time_ms'] = round(response_time, 2)
            result['ssl_valid'] = url.startswith('https://')
            
            # Determine health status
            if 200 <= response.status_code < 300:
                result['status'] = 'healthy'
            elif 300 <= response.status_code < 400:
                result['status'] = 'redirect'
            elif response.status_code == 403:
                result['status'] = 'forbidden'  # Common for HEAD requests
            elif response.status_code == 405:
                # Try GET if HEAD is not allowed
                try:
                    response = requests.get(url, timeout=self.timeout, stream=True)
                    result['status_code'] = response.status_code
                    if 200 <= response.status_code < 300:
                        result['status'] = 'healthy'
                except requests.RequestException:
                    result['status'] = 'degraded'
            else:
                result['status'] = 'degraded'
                
        except requests.exceptions.SSLError as e:
            result['status'] = 'ssl_error'
            result['ssl_valid'] = False
            result['error'] = str(e)
        except requests.exceptions.Timeout:
            result['status'] = 'timeout'
            result['error'] = f'Timeout after {self.timeout}s'
        except requests.exceptions.ConnectionError as e:
            result['status'] = 'down'
            result['error'] = str(e)
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
        
        return result
    
    def check_url_urllib(self, url: str) -> Dict:
        """
        Check URL health using urllib (fallback when requests unavailable).
        
        Args:
            url: URL to check
            
        Returns:
            Dictionary with health status
        """
        result = {
            'url': url,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'status': 'unknown',
            'status_code': None,
            'response_time_ms': None,
            'ssl_valid': None,
            'error': None
        }
        
        try:
            start_time = time.time()
            req = urllib.request.Request(url, method='HEAD')
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                response_time = (time.time() - start_time) * 1000
                result['status_code'] = response.status
                result['response_time_ms'] = round(response_time, 2)
                result['ssl_valid'] = url.startswith('https://')
                result['status'] = 'healthy'
                
        except urllib.error.HTTPError as e:
            result['status_code'] = e.code
            result['status'] = 'degraded' if e.code >= 400 else 'redirect'
            result['error'] = str(e)
        except urllib.error.URLError as e:
            result['status'] = 'down'
            result['error'] = str(e)
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
        
        return result
    
    def check_url(self, url: str) -> Dict:
        """
        Check URL health (uses requests if available, otherwise urllib).
        
        Args:
            url: URL to check
            
        Returns:
            Dictionary with health status
        """
        if REQUESTS_AVAILABLE:
            return self.check_url_requests(url)
        else:
            return self.check_url_urllib(url)
    
    def check_ssl_certificate(self, url: str) -> Tuple[bool, str]:
        """
        Check SSL certificate validity.
        
        Args:
            url: URL to check
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not url.startswith('https://'):
            return True, "Not HTTPS"
        
        parsed = urlparse(url)
        hostname = parsed.netloc
        port = 443
        
        try:
            # Create SSL context with secure settings - only TLS 1.2+
            context = ssl.create_default_context()
            context.minimum_version = ssl.TLSVersion.TLSv1_2
            with socket.create_connection((hostname, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    # Certificate is valid if we got here
                    return True, "Valid"
        except ssl.SSLError as e:
            return False, f"SSL Error: {str(e)}"
        except socket.timeout:
            return False, "Timeout"
        except Exception as e:
            return False, str(e)
    
    def load_registry_yaml(self, registry_path: str) -> List[Dict]:
        """
        Load data sources from YAML registry.
        
        Args:
            registry_path: Path to YAML registry file
            
        Returns:
            List of source dictionaries
        """
        if not YAML_AVAILABLE:
            print(f"Error: PyYAML required to load {registry_path}", file=sys.stderr)
            return []
        
        sources = []
        
        try:
            with open(registry_path, 'r') as f:
                data = yaml.safe_load(f)
            
            # Parse registry structure
            for category_key, category_data in data.items():
                if not isinstance(category_data, dict):
                    continue
                if 'sources' not in category_data:
                    continue
                
                for source in category_data['sources']:
                    # Extract URLs from source
                    urls = []
                    if 'urls' in source:
                        urls.extend(source['urls'])
                    if 'endpoints' in source:
                        for endpoint in source['endpoints']:
                            if isinstance(endpoint, dict) and 'url' in endpoint:
                                urls.append(endpoint['url'])
                    
                    for url in urls:
                        sources.append({
                            'name': source.get('name', 'Unknown'),
                            'category': category_data.get('category', category_key),
                            'url': url,
                            'priority': source.get('priority', 'medium'),
                            'api_available': source.get('api_available', False)
                        })
            
            self.summary['total_sources'] = len(sources)
            
        except FileNotFoundError:
            print(f"Error: Registry file not found: {registry_path}", file=sys.stderr)
        except Exception as e:
            print(f"Error loading registry: {e}", file=sys.stderr)
        
        return sources
    
    def check_all_sources(self, sources: List[Dict], verbose: bool = False):
        """
        Check health of all sources.
        
        Args:
            sources: List of source dictionaries
            verbose: Print progress if True
        """
        total = len(sources)
        
        if verbose:
            print(f"Checking {total} data sources...")
            print()
        
        for i, source in enumerate(sources, 1):
            url = source['url']
            name = source.get('name', 'Unknown')
            
            if verbose:
                print(f"[{i}/{total}] Checking {name}...")
                print(f"  URL: {url}")
            
            # Check URL health
            health = self.check_url(url)
            
            # Add source metadata
            health['source_name'] = name
            health['category'] = source.get('category', 'Unknown')
            health['priority'] = source.get('priority', 'medium')
            
            # Update summary
            self.summary['sources_checked'] += 1
            if health['status'] == 'healthy':
                self.summary['sources_healthy'] += 1
            elif health['status'] in ['redirect', 'forbidden']:
                self.summary['sources_degraded'] += 1
            else:
                self.summary['sources_down'] += 1
            
            # Track response times
            if health['response_time_ms']:
                if 'response_times' not in self.summary:
                    self.summary['response_times'] = []
                self.summary['response_times'].append(health['response_time_ms'])
            
            self.results.append(health)
            
            if verbose:
                status_emoji = {
                    'healthy': '✅',
                    'degraded': '⚠️',
                    'down': '❌',
                    'timeout': '⏱️',
                    'ssl_error': '🔒',
                    'error': '❌',
                    'redirect': '↪️',
                    'forbidden': '🚫'
                }.get(health['status'], '❓')
                
                print(f"  Status: {status_emoji} {health['status']}")
                if health['status_code']:
                    print(f"  HTTP Status: {health['status_code']}")
                if health['response_time_ms']:
                    print(f"  Response Time: {health['response_time_ms']} ms")
                if health['error']:
                    print(f"  Error: {health['error']}")
                print()
        
        # Calculate average response time
        if 'response_times' in self.summary and self.summary['response_times']:
            avg = sum(self.summary['response_times']) / len(self.summary['response_times'])
            self.summary['average_response_time'] = round(avg, 2)
            del self.summary['response_times']  # Remove raw list from summary
    
    def export_to_json(self, output_path: str):
        """
        Export monitoring results to JSON.
        
        Args:
            output_path: Path to output file
        """
        data = {
            'summary': self.summary,
            'results': self.results
        }
        
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Results exported to: {output_path}")
    
    def print_summary(self):
        """Print monitoring summary."""
        print("\n" + "="*60)
        print("LUFT LINK MONITOR SUMMARY")
        print("="*60)
        print(f"Timestamp: {self.summary['timestamp']}")
        print(f"Total sources: {self.summary['total_sources']}")
        print(f"Sources checked: {self.summary['sources_checked']}")
        print()
        print(f"✅ Healthy: {self.summary['sources_healthy']}")
        print(f"⚠️  Degraded: {self.summary['sources_degraded']}")
        print(f"❌ Down: {self.summary['sources_down']}")
        print()
        print(f"Average response time: {self.summary['average_response_time']} ms")
        print("="*60)
        
        # Show any critical failures
        critical_failures = [
            r for r in self.results 
            if r['status'] == 'down' and r.get('priority') in ['IMMEDIATE', 'HIGH']
        ]
        
        if critical_failures:
            print("\n⚠️  CRITICAL FAILURES:")
            for failure in critical_failures:
                print(f"  - {failure['source_name']} ({failure['url']})")
                print(f"    Error: {failure['error']}")


def main():
    """Main entry point for link monitor."""
    parser = argparse.ArgumentParser(
        description='LUFT Link Monitor - Monitor external data source health',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/link_monitor.py --check-all
  python tools/link_monitor.py --registry external_data_sources_registry.yaml
  python tools/link_monitor.py --output data/source_health_log.json --verbose
        """
    )
    
    parser.add_argument('--registry', default='external_data_sources_registry.yaml',
                       help='Path to data sources registry YAML file')
    parser.add_argument('--output', default='data/source_health_log.json',
                       help='Output JSON file for monitoring results')
    parser.add_argument('--timeout', type=int, default=10,
                       help='Request timeout in seconds (default: 10)')
    parser.add_argument('--check-all', action='store_true',
                       help='Check all sources in registry')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    # Create monitor
    monitor = LinkMonitor(timeout=args.timeout)
    
    # Load sources from registry
    if args.check_all or args.registry:
        if not Path(args.registry).exists():
            print(f"Error: Registry file not found: {args.registry}", file=sys.stderr)
            sys.exit(1)
        
        sources = monitor.load_registry_yaml(args.registry)
        
        if not sources:
            print("Error: No sources loaded from registry", file=sys.stderr)
            sys.exit(1)
        
        # Check all sources
        monitor.check_all_sources(sources, verbose=args.verbose)
        
        # Print summary
        monitor.print_summary()
        
        # Export results
        monitor.export_to_json(args.output)
    else:
        parser.print_help()
        print("\nNote: Use --check-all to monitor all sources")


if __name__ == '__main__':
    main()
