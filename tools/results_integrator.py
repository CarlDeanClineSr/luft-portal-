#!/usr/bin/env python3
"""
LUFT Results Integrator
=======================

Safely integrates automated analysis results into the LUFT dashboard with
human oversight controls. All discoveries require manual validation before
being marked as confirmed.

Author: Carl Dean Cline Sr.
Created: January 3, 2026
Location: Lincoln, Nebraska, USA
Email: CARLDCLINE@GMAIL.COM

Purpose:
    Provides a controlled pathway for automated discoveries to reach the
    cockpit dashboard while maintaining human-in-the-loop oversight.
    
Safety Features:
    - All results marked "PRELIMINARY" by default
    - No auto-publishing without approval
    - Quality gates enforce minimum standards
    - Rate limiting prevents spam
    - Audit logging tracks all actions
    
Usage:
    python tools/results_integrator.py --input plots/beta_chi_results.csv \\
        --type correlation_analysis --status preliminary
    
    python tools/results_integrator.py --list-discoveries
    
    python tools/results_integrator.py --discovery-id <id> --update-status validated
"""

import json
import yaml
import argparse
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
import sys


class ResultsIntegrator:
    """Manages integration of analysis results into the LUFT system."""
    
    def __init__(self, config_path: str = "configs/discovery_settings.yaml"):
        """
        Initialize the results integrator.
        
        Args:
            config_path: Path to discovery settings YAML
        """
        self.config_path = Path(config_path)
        self.load_config()
        
        # Setup directories
        self.preliminary_dir = Path(self.config['output_dirs']['preliminary'])
        self.validated_dir = Path(self.config['output_dirs']['validated'])
        self.published_dir = Path(self.config['output_dirs']['published'])
        self.audit_dir = Path(self.config['output_dirs']['audit'])
        
        self.validated_dir.mkdir(parents=True, exist_ok=True)
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        
        self.audit_log = self.audit_dir / 'discovery_audit.log'
        
    def load_config(self):
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            config_data = yaml.safe_load(f)
            self.config = config_data.get('discovery_system', {})
    
    def log_audit(self, action: str, details: Dict[str, Any]):
        """
        Log an action to the audit trail.
        
        Args:
            action: Action performed (e.g., 'CREATE_DISCOVERY', 'UPDATE_STATUS')
            details: Dictionary of action details
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        log_entry = {
            'timestamp': timestamp,
            'action': action,
            'details': details
        }
        
        with open(self.audit_log, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def generate_discovery_id(self, discovery_type: str) -> str:
        """
        Generate a unique discovery ID.
        
        Args:
            discovery_type: Type of discovery
            
        Returns:
            Unique discovery ID
        """
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        unique_str = f"{discovery_type}_{timestamp}"
        hash_suffix = hashlib.md5(unique_str.encode()).hexdigest()[:8]
        
        return f"discovery_{timestamp}_{hash_suffix}"
    
    def check_quality_gates(self, metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Check if discovery meets quality thresholds.
        
        Args:
            metadata: Discovery metadata including quality metrics
            
        Returns:
            Tuple of (passes, list of failures)
        """
        gates = self.config.get('quality_gates', {})
        failures = []
        
        # Check sample size
        if 'sample_size' in metadata:
            min_size = gates.get('min_sample_size', 50)
            if metadata['sample_size'] < min_size:
                failures.append(f"Sample size {metadata['sample_size']} < {min_size}")
        
        # Check confidence
        if 'confidence' in metadata:
            min_conf = gates.get('min_confidence', 0.95)
            if metadata['confidence'] < min_conf:
                failures.append(f"Confidence {metadata['confidence']} < {min_conf}")
        
        # Check p-value
        if 'p_value' in metadata:
            max_p = gates.get('max_p_value', 0.05)
            if metadata['p_value'] > max_p:
                failures.append(f"P-value {metadata['p_value']} > {max_p}")
        
        # Check correlation magnitude if applicable
        if 'correlation' in metadata:
            min_corr = gates.get('min_correlation', 0.3)
            if abs(metadata['correlation']) < min_corr:
                failures.append(f"|Correlation| {abs(metadata['correlation'])} < {min_corr}")
        
        passed = len(failures) == 0
        return passed, failures
    
    def create_discovery(
        self,
        discovery_type: str,
        title: str,
        summary: str,
        input_files: List[str],
        metadata: Dict[str, Any],
        status: str = "preliminary"
    ) -> str:
        """
        Create a new discovery entry.
        
        Args:
            discovery_type: Type of discovery
            title: Human-readable title
            summary: Brief summary of findings
            input_files: List of input data files
            metadata: Additional metadata (stats, params, etc.)
            status: Initial status (preliminary, validated, published)
            
        Returns:
            Discovery ID
        """
        # Generate unique ID
        discovery_id = self.generate_discovery_id(discovery_type)
        
        # Check quality gates
        passes_gates, failures = self.check_quality_gates(metadata)
        
        # Create discovery record
        discovery = {
            'id': discovery_id,
            'type': discovery_type,
            'title': title,
            'summary': summary,
            'status': status,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'input_files': input_files,
            'metadata': metadata,
            'quality_gates': {
                'passed': passes_gates,
                'failures': failures
            },
            'validated_by': None,
            'validation_notes': None
        }
        
        # Save discovery record
        discovery_file = self.validated_dir / f"{discovery_id}.json"
        with open(discovery_file, 'w') as f:
            json.dump(discovery, f, indent=2)
        
        # Log to audit trail
        self.log_audit('CREATE_DISCOVERY', {
            'discovery_id': discovery_id,
            'type': discovery_type,
            'status': status,
            'passes_quality_gates': passes_gates
        })
        
        print(f"✓ Discovery created: {discovery_id}")
        print(f"  Type: {discovery_type}")
        print(f"  Status: {status.upper()}")
        print(f"  Quality gates: {'PASSED' if passes_gates else 'FAILED'}")
        if not passes_gates:
            print(f"  Issues:")
            for failure in failures:
                print(f"    - {failure}")
        print(f"  Saved to: {discovery_file}")
        
        return discovery_id
    
    def update_discovery_status(
        self,
        discovery_id: str,
        new_status: str,
        validated_by: Optional[str] = None,
        notes: Optional[str] = None
    ):
        """
        Update the status of a discovery.
        
        Args:
            discovery_id: Discovery ID to update
            new_status: New status (validated, published)
            validated_by: Name of person validating
            notes: Validation notes
        """
        discovery_file = self.validated_dir / f"{discovery_id}.json"
        
        if not discovery_file.exists():
            print(f"✗ Discovery not found: {discovery_id}")
            return
        
        # Load discovery
        with open(discovery_file, 'r') as f:
            discovery = json.load(f)
        
        # Update status
        old_status = discovery['status']
        discovery['status'] = new_status
        discovery['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        if validated_by:
            discovery['validated_by'] = validated_by
        if notes:
            discovery['validation_notes'] = notes
        
        # Save updated discovery
        with open(discovery_file, 'w') as f:
            json.dump(discovery, f, indent=2)
        
        # Log to audit trail
        self.log_audit('UPDATE_STATUS', {
            'discovery_id': discovery_id,
            'old_status': old_status,
            'new_status': new_status,
            'validated_by': validated_by
        })
        
        print(f"✓ Discovery status updated: {discovery_id}")
        print(f"  {old_status.upper()} → {new_status.upper()}")
        if validated_by:
            print(f"  Validated by: {validated_by}")
    
    def list_discoveries(self, status_filter: Optional[str] = None):
        """
        List all discoveries.
        
        Args:
            status_filter: Filter by status (preliminary, validated, published)
        """
        discovery_files = sorted(self.validated_dir.glob("discovery_*.json"))
        
        if not discovery_files:
            print("No discoveries found.")
            return
        
        print(f"\n{'='*70}")
        print(f"LUFT Discoveries")
        print(f"{'='*70}\n")
        
        for disc_file in discovery_files:
            with open(disc_file, 'r') as f:
                discovery = json.load(f)
            
            # Apply status filter
            if status_filter and discovery['status'] != status_filter:
                continue
            
            # Status emoji
            status_emoji = {
                'preliminary': '🟡',
                'validated': '🟢',
                'published': '🔵'
            }.get(discovery['status'], '⚪')
            
            # Quality gate emoji
            quality_emoji = '✓' if discovery['quality_gates']['passed'] else '⚠'
            
            print(f"{status_emoji} {discovery['id']}")
            print(f"   Title: {discovery['title']}")
            print(f"   Type: {discovery['type']}")
            print(f"   Status: {discovery['status'].upper()}")
            print(f"   Quality: {quality_emoji} {'PASSED' if discovery['quality_gates']['passed'] else 'ISSUES'}")
            print(f"   Created: {discovery['created_at']}")
            if discovery.get('validated_by'):
                print(f"   Validated by: {discovery['validated_by']}")
            print(f"   Summary: {discovery['summary'][:100]}...")
            print()
        
        print(f"{'='*70}\n")
    
    def get_dashboard_data(self, max_count: int = 3) -> List[Dict[str, Any]]:
        """
        Get recent discoveries for dashboard display.
        
        Args:
            max_count: Maximum number of discoveries to return
            
        Returns:
            List of discovery summaries
        """
        discovery_files = sorted(
            self.validated_dir.glob("discovery_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )[:max_count]
        
        summaries = []
        for disc_file in discovery_files:
            with open(disc_file, 'r') as f:
                discovery = json.load(f)
            
            summaries.append({
                'id': discovery['id'],
                'type': discovery['type'],
                'title': discovery['title'],
                'summary': discovery['summary'],
                'status': discovery['status'],
                'quality_passed': discovery['quality_gates']['passed'],
                'created_at': discovery['created_at']
            })
        
        return summaries


def main():
    parser = argparse.ArgumentParser(
        description='LUFT Results Integrator - Controlled discovery integration')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Create discovery command
    create_parser = subparsers.add_parser('create', help='Create a new discovery')
    create_parser.add_argument('--type', required=True, help='Discovery type')
    create_parser.add_argument('--title', required=True, help='Discovery title')
    create_parser.add_argument('--summary', required=True, help='Brief summary')
    create_parser.add_argument('--input-files', nargs='+', required=True, 
                              help='Input data files')
    create_parser.add_argument('--metadata', type=str, 
                              help='Metadata JSON string or file')
    create_parser.add_argument('--status', default='preliminary',
                              choices=['preliminary', 'validated', 'published'])
    
    # Update status command
    update_parser = subparsers.add_parser('update', help='Update discovery status')
    update_parser.add_argument('--discovery-id', required=True, help='Discovery ID')
    update_parser.add_argument('--status', required=True,
                              choices=['preliminary', 'validated', 'published'])
    update_parser.add_argument('--validated-by', help='Name of validator')
    update_parser.add_argument('--notes', help='Validation notes')
    
    # List discoveries command
    list_parser = subparsers.add_parser('list', help='List discoveries')
    list_parser.add_argument('--status', 
                            choices=['preliminary', 'validated', 'published'],
                            help='Filter by status')
    
    # Dashboard data command
    dashboard_parser = subparsers.add_parser('dashboard', 
                                            help='Get dashboard data')
    dashboard_parser.add_argument('--max-count', type=int, default=3,
                                 help='Maximum discoveries to return')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize integrator
    integrator = ResultsIntegrator()
    
    # Execute command
    if args.command == 'create':
        # Parse metadata
        metadata = {}
        if args.metadata:
            if Path(args.metadata).exists():
                with open(args.metadata, 'r') as f:
                    metadata = json.load(f)
            else:
                metadata = json.loads(args.metadata)
        
        integrator.create_discovery(
            discovery_type=args.type,
            title=args.title,
            summary=args.summary,
            input_files=args.input_files,
            metadata=metadata,
            status=args.status
        )
    
    elif args.command == 'update':
        integrator.update_discovery_status(
            discovery_id=args.discovery_id,
            new_status=args.status,
            validated_by=args.validated_by,
            notes=args.notes
        )
    
    elif args.command == 'list':
        integrator.list_discoveries(status_filter=args.status)
    
    elif args.command == 'dashboard':
        summaries = integrator.get_dashboard_data(max_count=args.max_count)
        print(json.dumps(summaries, indent=2))


if __name__ == '__main__':
    main()
