#!/usr/bin/env python3
"""
LUFT Bow Pattern Analyzer
===========================

Statistical analysis and reporting for detected bow patterns.

Discovery: Carl Dean Cline Sr., 2025-12-31
Location: Lincoln, Nebraska, USA
Email: CARLDCLINE@GMAIL.COM

Generates:
- Summary statistics
- Temporal distributions
- Solar wind correlations
- Markdown reports
- Visualizations

Usage:
    python bow_pattern_analyzer.py --events reports/bow_patterns/bow_events_2026-01-01.json
    python bow_pattern_analyzer.py --config configs/bow_detection_config.yaml
"""

import argparse
import json
import yaml
import glob
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


class BowPatternAnalyzer:
    """Analyzes detected bow pattern events and generates reports."""
    
    def __init__(self, config_path: str = "configs/bow_detection_config.yaml"):
        """
        Initialize the analyzer.
        
        Args:
            config_path: Path to configuration YAML file
        """
        self.config = self._load_config(config_path)
        self.events: List[Dict] = []
        self.df_events: Optional[pd.DataFrame] = None
        
        # Set plotting style
        sns.set_style("whitegrid")
        sns.set_palette("husl")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def load_events(self, event_files: List[str]):
        """
        Load bow events from JSON file(s).
        
        Args:
            event_files: List of JSON file paths or patterns
        """
        all_events = []
        
        for pattern in event_files:
            files = glob.glob(pattern)
            for filepath in files:
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        if 'events' in data:
                            all_events.extend(data['events'])
                        elif isinstance(data, list):
                            all_events.extend(data)
                except Exception as e:
                    print(f"Warning: Could not load {filepath}: {e}")
                    continue
        
        self.events = all_events
        
        if all_events:
            self.df_events = pd.DataFrame(all_events)
            # Convert timestamp strings to datetime
            for col in ['start_time', 'end_time', 'peak_time', 'loading_start', 
                       'loading_end', 'relaxation_start', 'relaxation_end',
                       'reload_start', 'reload_end']:
                if col in self.df_events.columns:
                    self.df_events[col] = pd.to_datetime(self.df_events[col])
        
        print(f"Loaded {len(all_events)} bow pattern events")
    
    def generate_statistics(self) -> Dict[str, Any]:
        """
        Generate summary statistics for all detected bow patterns.
        
        Returns:
            Dictionary containing statistical summaries
        """
        if not self.events:
            return {'total_events': 0}
        
        df = self.df_events
        
        # Count by type
        type_counts = df['event_type'].value_counts().to_dict()
        
        # Loading phase statistics
        loading_stats = {
            'mean_duration_hours': df['loading_duration_hours'].mean(),
            'median_duration_hours': df['loading_duration_hours'].median(),
            'std_duration_hours': df['loading_duration_hours'].std(),
            'mean_chi_rise': df['loading_chi_rise'].mean(),
            'median_chi_rise': df['loading_chi_rise'].median(),
            'max_chi_rise': df['loading_chi_rise'].max()
        }
        
        # Peak statistics
        peak_stats = {
            'mean_chi': df['peak_chi'].mean(),
            'median_chi': df['peak_chi'].median(),
            'max_chi': df['peak_chi'].max(),
            'min_chi': df['peak_chi'].min(),
            'mean_distance_from_boundary': df['distance_from_boundary'].mean()
        }
        
        # Relaxation phase statistics
        relaxation_stats = {
            'mean_duration_hours': df['relaxation_duration_hours'].mean(),
            'median_duration_hours': df['relaxation_duration_hours'].median(),
            'std_duration_hours': df['relaxation_duration_hours'].std(),
            'mean_chi_drop': df['relaxation_chi_drop'].mean(),
            'median_chi_drop': df['relaxation_chi_drop'].median(),
            'max_chi_drop': df['relaxation_chi_drop'].max()
        }
        
        # Reload phase statistics (for events with reload)
        reload_df = df[df['reload_duration_hours'].notna()]
        if len(reload_df) > 0:
            reload_stats = {
                'count': len(reload_df),
                'mean_duration_hours': reload_df['reload_duration_hours'].mean(),
                'median_duration_hours': reload_df['reload_duration_hours'].median(),
                'mean_chi_rise': reload_df['reload_chi_rise'].mean(),
                'median_chi_rise': reload_df['reload_chi_rise'].median()
            }
        else:
            reload_stats = {'count': 0}
        
        # Overall statistics
        statistics = {
            'total_events': len(self.events),
            'event_types': type_counts,
            'loading_phase': loading_stats,
            'peak': peak_stats,
            'relaxation_phase': relaxation_stats,
            'reload_phase': reload_stats,
            'date_range': {
                'start': df['start_time'].min().isoformat(),
                'end': df['end_time'].max().isoformat()
            }
        }
        
        return statistics
    
    def temporal_distribution(self) -> Dict[str, Any]:
        """
        Analyze temporal distribution of bow patterns.
        
        Returns:
            Dictionary with hourly, daily, and monthly distributions
        """
        if not self.events or self.df_events is None:
            return {}
        
        df = self.df_events
        
        # Extract temporal features
        df['hour'] = df['peak_time'].dt.hour
        df['day_of_week'] = df['peak_time'].dt.dayofweek
        df['month'] = df['peak_time'].dt.month
        
        # Hourly distribution
        hourly = df['hour'].value_counts().sort_index().to_dict()
        
        # Daily distribution
        daily = df['day_of_week'].value_counts().sort_index().to_dict()
        
        # Monthly distribution
        monthly = df['month'].value_counts().sort_index().to_dict()
        
        return {
            'hourly': hourly,
            'daily': daily,
            'monthly': monthly
        }
    
    def correlate_with_solar_wind(self, sw_data_paths: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Correlate bow patterns with solar wind parameters.
        
        Args:
            sw_data_paths: List of solar wind data file paths
            
        Returns:
            Dictionary containing correlation results
        """
        if not self.events:
            return {}
        
        # This is a placeholder - would need actual solar wind data loading
        # For now, return structure for the report
        correlations = {
            'note': 'Solar wind correlation analysis requires aligned timeseries data',
            'parameters_analyzed': self.config['correlation']['parameters'],
            'time_windows': self.config['correlation']['time_windows'],
            'results': {}
        }
        
        # Try to load solar wind data if paths provided
        if sw_data_paths:
            try:
                # Load and analyze - implementation would go here
                correlations['results'] = {
                    'speed': {'correlation': 0.0, 'p_value': 1.0},
                    'bz': {'correlation': 0.0, 'p_value': 1.0},
                    'density': {'correlation': 0.0, 'p_value': 1.0}
                }
            except Exception as e:
                correlations['error'] = str(e)
        
        return correlations
    
    def create_visualizations(self, output_dir: Path):
        """
        Create visualization plots.
        
        Args:
            output_dir: Directory to save plots
        """
        if not self.events or self.df_events is None:
            print("No events to visualize")
            return
        
        df = self.df_events
        output_dir.mkdir(parents=True, exist_ok=True)
        
        dpi = self.config['output']['plot_dpi']
        plot_format = self.config['output']['plot_format']
        
        # 1. Loading times distribution
        plt.figure(figsize=(10, 6))
        plt.hist(df['loading_duration_hours'], bins=20, alpha=0.7, edgecolor='black')
        plt.xlabel('Loading Duration (hours)', fontsize=12)
        plt.ylabel('Count', fontsize=12)
        plt.title('Distribution of Bow Pattern Loading Times', fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_dir / f'loading_times_dist.{plot_format}', dpi=dpi)
        plt.close()
        
        # 2. Peak χ values distribution
        plt.figure(figsize=(10, 6))
        plt.hist(df['peak_chi'], bins=25, alpha=0.7, edgecolor='black', color='coral')
        plt.axvline(x=0.15, color='red', linestyle='--', linewidth=2, label='χ = 0.15 Boundary')
        plt.xlabel('Peak χ Value', fontsize=12)
        plt.ylabel('Count', fontsize=12)
        plt.title('Distribution of Bow Pattern Peak χ Values', fontsize=14, fontweight='bold')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_dir / f'peak_chi_dist.{plot_format}', dpi=dpi)
        plt.close()
        
        # 3. Relaxation times distribution
        plt.figure(figsize=(10, 6))
        plt.hist(df['relaxation_duration_hours'], bins=20, alpha=0.7, edgecolor='black', color='lightgreen')
        plt.xlabel('Relaxation Duration (hours)', fontsize=12)
        plt.ylabel('Count', fontsize=12)
        plt.title('Distribution of Bow Pattern Relaxation Times', fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_dir / f'relaxation_times_dist.{plot_format}', dpi=dpi)
        plt.close()
        
        # 4. Hourly distribution
        if 'hour' not in df.columns:
            df['hour'] = df['peak_time'].dt.hour
        
        plt.figure(figsize=(12, 6))
        hourly_counts = df['hour'].value_counts().sort_index()
        plt.bar(hourly_counts.index, hourly_counts.values, alpha=0.7, edgecolor='black')
        plt.xlabel('Hour of Day (UTC)', fontsize=12)
        plt.ylabel('Number of Bow Patterns', fontsize=12)
        plt.title('Bow Pattern Occurrence by Hour of Day', fontsize=14, fontweight='bold')
        plt.xticks(range(0, 24))
        plt.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        plt.savefig(output_dir / f'hourly_distribution.{plot_format}', dpi=dpi)
        plt.close()
        
        # 5. Pattern type distribution
        plt.figure(figsize=(10, 6))
        type_counts = df['event_type'].value_counts()
        colors = ['skyblue', 'lightcoral', 'lightgreen']
        plt.bar(type_counts.index, type_counts.values, color=colors[:len(type_counts)], 
               alpha=0.7, edgecolor='black')
        plt.xlabel('Pattern Type', fontsize=12)
        plt.ylabel('Count', fontsize=12)
        plt.title('Distribution of Bow Pattern Types', fontsize=14, fontweight='bold')
        plt.xticks(rotation=15)
        plt.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        plt.savefig(output_dir / f'pattern_types.{plot_format}', dpi=dpi)
        plt.close()
        
        print(f"✓ Created visualizations in {output_dir}")
    
    def generate_report(self, output_path: Path):
        """
        Generate markdown report.
        
        Args:
            output_path: Path for output markdown file
        """
        if not self.events:
            print("No events to report")
            return
        
        stats = self.generate_statistics()
        temporal = self.temporal_distribution()
        
        # Load template
        template_path = Path(self.config['output']['report_path']) / 'BOW_PATTERN_REPORT_TEMPLATE.md'
        
        if template_path.exists():
            with open(template_path, 'r') as f:
                template = f.read()
        else:
            # Use inline template
            template = self._get_default_template()
        
        # Replace placeholders
        report = template
        report = report.replace('{{GENERATION_DATE}}', datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'))
        report = report.replace('{{TOTAL_EVENTS}}', str(stats['total_events']))
        report = report.replace('{{SINGLE_BOWS}}', str(stats['event_types'].get('single_bow', 0)))
        report = report.replace('{{FAILED_BOWS}}', str(stats['event_types'].get('failed_bow', 0)))
        report = report.replace('{{DOUBLE_BOWS}}', str(stats['event_types'].get('double_bow', 0)))
        
        report = report.replace('{{AVG_LOADING_TIME}}', f"{stats['loading_phase']['mean_duration_hours']:.2f}")
        report = report.replace('{{AVG_RELAXATION_TIME}}', f"{stats['relaxation_phase']['mean_duration_hours']:.2f}")
        report = report.replace('{{AVG_PEAK_CHI}}', f"{stats['peak']['mean_chi']:.4f}")
        report = report.replace('{{MAX_PEAK_CHI}}', f"{stats['peak']['max_chi']:.4f}")
        
        report = report.replace('{{DATE_RANGE_START}}', stats['date_range']['start'])
        report = report.replace('{{DATE_RANGE_END}}', stats['date_range']['end'])
        
        # Add top events section
        top_events = self._format_top_events(20)
        report = report.replace('{{TOP_EVENTS_TABLE}}', top_events)
        
        # Write report
        with open(output_path, 'w') as f:
            f.write(report)
        
        print(f"✓ Generated report: {output_path}")
    
    def _format_top_events(self, n: int = 20) -> str:
        """Format top N events as markdown table."""
        if not self.events or self.df_events is None:
            return "No events detected."
        
        df = self.df_events.copy()
        
        # Sort by peak_chi descending
        df_sorted = df.sort_values('peak_chi', ascending=False).head(n)
        
        lines = [
            "| Rank | Peak Time | Peak χ | Type | Loading (h) | Relaxation (h) |",
            "|------|-----------|--------|------|-------------|----------------|"
        ]
        
        for i, (_, row) in enumerate(df_sorted.iterrows(), 1):
            peak_time = pd.to_datetime(row['peak_time']).strftime('%Y-%m-%d %H:%M')
            lines.append(
                f"| {i} | {peak_time} | {row['peak_chi']:.4f} | {row['event_type']} | "
                f"{row['loading_duration_hours']:.2f} | {row['relaxation_duration_hours']:.2f} |"
            )
        
        return '\n'.join(lines)
    
    def _get_default_template(self) -> str:
        """Get default report template."""
        return """# Bow Pattern Analysis Report

**Generated:** {{GENERATION_DATE}}

## Summary Statistics

### Overview
- **Total Bow Patterns Detected:** {{TOTAL_EVENTS}}
- **Date Range:** {{DATE_RANGE_START}} to {{DATE_RANGE_END}}

### Pattern Classification
- **Single Bows:** {{SINGLE_BOWS}} (complete loading-relaxation-reload cycles)
- **Failed Bows:** {{FAILED_BOWS}} (loading-relaxation without reload)
- **Double Bows:** {{DOUBLE_BOWS}} (consecutive bow patterns)

### Characteristic Measurements
- **Average Loading Time:** {{AVG_LOADING_TIME}} hours
- **Average Relaxation Time:** {{AVG_RELAXATION_TIME}} hours
- **Average Peak χ:** {{AVG_PEAK_CHI}}
- **Maximum Peak χ:** {{MAX_PEAK_CHI}}

## Physical Interpretation

Bow patterns represent energy absorption cycles in Earth's magnetosphere:
1. **Loading Phase:** System absorbs energy, χ rises toward 0.15 boundary
2. **Peak:** Approaches boundary, reaches local maximum
3. **Relaxation:** Snaps back, releases energy, χ drops
4. **Reload:** System reloads energy, χ rises again

## Notable Events (Top 20)

{{TOP_EVENTS_TABLE}}

## Visualizations

See the `visualizations/` directory for detailed plots:
- Loading time distributions
- Peak χ value distributions
- Relaxation time distributions
- Hourly occurrence patterns
- Pattern type breakdowns

---

**Discovery:** Carl Dean Cline Sr., 2025-12-31  
**Location:** Lincoln, Nebraska, USA  
**Email:** CARLDCLINE@GMAIL.COM
"""


def main():
    """Main entry point for the bow pattern analyzer."""
    parser = argparse.ArgumentParser(
        description='Analyze detected bow patterns and generate reports'
    )
    parser.add_argument('--config', default='configs/bow_detection_config.yaml',
                       help='Path to configuration file')
    parser.add_argument('--events', nargs='+',
                       help='Event file paths or patterns')
    parser.add_argument('--output-report', default=None,
                       help='Output report markdown file path')
    parser.add_argument('--visualizations', action='store_true',
                       help='Generate visualization plots')
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = BowPatternAnalyzer(args.config)
    
    # Determine event sources
    if args.events:
        event_files = args.events
    else:
        # Look for recent event files
        report_path = Path(analyzer.config['output']['report_path'])
        event_files = [str(report_path / 'bow_events_*.json')]
    
    # Load events
    analyzer.load_events(event_files)
    
    if not analyzer.events:
        print("Error: No events loaded")
        return 1
    
    # Generate statistics
    print("\nGenerating statistics...")
    stats = analyzer.generate_statistics()
    
    print(f"\n📊 Analysis Summary:")
    print(f"  Total events: {stats['total_events']}")
    for event_type, count in stats['event_types'].items():
        print(f"  - {event_type}: {count}")
    
    # Generate report
    output_dir = Path(analyzer.config['output']['report_path'])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    
    if args.output_report:
        report_path = Path(args.output_report)
    else:
        report_path = output_dir / f'bow_pattern_summary_{timestamp}.md'
    
    print("\nGenerating report...")
    analyzer.generate_report(report_path)
    
    # Generate visualizations
    if args.visualizations or analyzer.config['output']['create_plots']:
        print("\nCreating visualizations...")
        viz_dir = output_dir / 'visualizations'
        analyzer.create_visualizations(viz_dir)
    
    print(f"\n✓ Analysis complete!")
    print(f"  Report: {report_path}")
    if analyzer.config['output']['create_plots']:
        print(f"  Visualizations: {output_dir / 'visualizations'}")
    
    return 0


if __name__ == '__main__':
    exit(main())
