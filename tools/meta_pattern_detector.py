#!/usr/bin/env python3
"""
LUFT Meta-Pattern Detector
===========================

Layer 4 Meta-Intelligence Engine: Detects patterns across data sources, identifies
temporal correlations, and discovers cross-source anomalies.

Author: Carl Dean Cline Sr.
Created: December 31, 2025
Location: Lincoln, Nebraska, USA
Email: CARLDCLINE@GMAIL.COM

Mission: Build the meta-awareness layer that watches how LUFT watches the universe.

Usage:
    python meta_pattern_detector.py --detect-correlations
    python meta_pattern_detector.py --detect-anomalies
    python meta_pattern_detector.py --full-analysis
"""

import json
import yaml
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict
import re


class TemporalCorrelationEngine:
    """
    Detect time-delayed relationships between different data sources.
    
    Example: Solar flares (NOAA) predict chi boundary violations 
    with a specific time delay.
    """
    
    def __init__(self, data_dir: str = 'data', max_delay_hours: int = 72):
        """
        Initialize the temporal correlation engine.
        
        Args:
            data_dir: Directory containing data files
            max_delay_hours: Maximum time delay to check for correlations
        """
        self.data_dir = Path(data_dir)
        self.max_delay_hours = max_delay_hours
        self.correlations = []
        
    def detect_lead_lag(self, source_A: str, source_B: str, 
                        event_type_A: str = None, 
                        event_type_B: str = None) -> List[Dict]:
        """
        Check if changes in source_A predict changes in source_B.
        
        Args:
            source_A: Leading data source (e.g., "NOAA_SOHO")
            source_B: Lagging data source (e.g., "CHI_BOUNDARY")
            event_type_A: Type of event in source A (e.g., "X_CLASS_FLARE")
            event_type_B: Type of event in source B (e.g., "CHI_SPIKE")
            
        Returns:
            List of detected correlation patterns with time delays
        """
        patterns = []
        
        # Scan data directory for relevant files
        source_a_files = list(self.data_dir.glob(f'**/*{source_A.lower()}*'))
        source_b_files = list(self.data_dir.glob(f'**/*{source_B.lower()}*'))
        
        if not source_a_files or not source_b_files:
            return patterns
        
        # Extract timestamps and events from files
        events_a = self._extract_events_from_files(source_a_files, event_type_A)
        events_b = self._extract_events_from_files(source_b_files, event_type_B)
        
        # Look for temporal correlations
        for delay_hours in range(0, self.max_delay_hours + 1, 6):
            matches = 0
            examples = []
            
            for event_a in events_a:
                time_a = event_a['timestamp']
                expected_time = time_a + timedelta(hours=delay_hours)
                
                # Check if there's a matching event in source B
                for event_b in events_b:
                    time_b = event_b['timestamp']
                    time_diff = abs((time_b - expected_time).total_seconds() / 3600)
                    
                    if time_diff <= 6:  # Within 6-hour window
                        matches += 1
                        if len(examples) < 3:
                            examples.append({
                                'source_a_time': time_a.isoformat(),
                                'source_b_time': time_b.isoformat(),
                                'actual_delay_hours': round((time_b - time_a).total_seconds() / 3600, 1),
                                'source_a_data': event_a.get('data', {}),
                                'source_b_data': event_b.get('data', {})
                            })
                        break
            
            if matches >= 3:  # Require at least 3 matches to consider correlation
                confidence = min(95, 60 + (matches * 5))
                patterns.append({
                    'source_lead': source_A,
                    'source_lag': source_B,
                    'delay_hours': delay_hours,
                    'matches': matches,
                    'confidence': confidence,
                    'examples': examples,
                    'recommendation': f"When {source_A} shows activity, check {source_B} after ~{delay_hours} hours"
                })
        
        self.correlations.extend(patterns)
        return patterns
    
    def _extract_events_from_files(self, files: List[Path], 
                                   event_type: Optional[str] = None) -> List[Dict]:
        """
        Extract timestamped events from data files.
        
        This is a smart parser that handles various data formats.
        """
        events = []
        
        for file_path in files:
            try:
                # Try to parse as JSON
                if file_path.suffix == '.json':
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        events.extend(self._parse_json_events(data, event_type))
                
                # Try to parse as YAML
                elif file_path.suffix in ['.yaml', '.yml']:
                    with open(file_path, 'r') as f:
                        data = yaml.safe_load(f)
                        events.extend(self._parse_yaml_events(data, event_type))
                
                # Parse text files for timestamps and events
                else:
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                        events.extend(self._parse_text_events(content, event_type))
                        
            except (IOError, OSError, UnicodeDecodeError) as e:
                # Skip files that can't be read (permissions, binary data, etc.)
                # These are expected in a diverse repository
                pass
            except Exception as e:
                # Log unexpected errors but continue processing
                import sys
                print(f"Warning: Unexpected error parsing {file_path}: {type(e).__name__}", file=sys.stderr)
                pass
        
        return sorted(events, key=lambda x: x['timestamp'])
    
    def _parse_json_events(self, data: Any, event_type: Optional[str]) -> List[Dict]:
        """Extract events from JSON data structure."""
        events = []
        
        # Handle list of events
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and 'timestamp' in item:
                    try:
                        timestamp = self._parse_timestamp(item['timestamp'])
                        if timestamp:
                            events.append({
                                'timestamp': timestamp,
                                'data': item,
                                'type': item.get('type', 'unknown')
                            })
                    except (ValueError, TypeError, AttributeError, KeyError):
                        # Skip items with unparseable timestamps or invalid structure
                        pass
        
        # Handle dict with nested events
        elif isinstance(data, dict):
            if 'events' in data:
                return self._parse_json_events(data['events'], event_type)
            elif 'timestamp' in data:
                try:
                    timestamp = self._parse_timestamp(data['timestamp'])
                    if timestamp:
                        events.append({
                            'timestamp': timestamp,
                            'data': data,
                            'type': data.get('type', 'unknown')
                        })
                except (ValueError, TypeError, AttributeError, KeyError):
                    # Skip items with unparseable timestamps or invalid structure
                    pass
        
        return events
    
    def _parse_yaml_events(self, data: Any, event_type: Optional[str]) -> List[Dict]:
        """Extract events from YAML data structure."""
        # YAML and JSON have similar structure, reuse JSON parser
        return self._parse_json_events(data, event_type)
    
    def _parse_text_events(self, content: str, event_type: Optional[str]) -> List[Dict]:
        """Extract events from text content using pattern matching."""
        events = []
        
        # Look for ISO 8601 timestamps in text
        timestamp_pattern = r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}'
        matches = re.finditer(timestamp_pattern, content)
        
        for match in matches:
            try:
                timestamp_str = match.group(0).replace(' ', 'T')
                timestamp = datetime.fromisoformat(timestamp_str)
                
                # Make timezone-aware if naive
                if timestamp.tzinfo is None:
                    from datetime import timezone
                    timestamp = timestamp.replace(tzinfo=timezone.utc)
                
                # Get context around timestamp (100 chars before and after)
                start = max(0, match.start() - 100)
                end = min(len(content), match.end() + 100)
                context = content[start:end]
                
                events.append({
                    'timestamp': timestamp,
                    'data': {'context': context},
                    'type': 'text_event'
                })
            except (ValueError, AttributeError):
                # Skip malformed timestamps
                pass
        
        return events
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse various timestamp formats and ensure timezone awareness."""
        if isinstance(timestamp_str, datetime):
            # Make timezone-aware if naive
            if timestamp_str.tzinfo is None:
                from datetime import timezone
                return timestamp_str.replace(tzinfo=timezone.utc)
            return timestamp_str
        
        try:
            # Try ISO 8601 format
            dt = datetime.fromisoformat(str(timestamp_str).replace('Z', '+00:00'))
            # Make timezone-aware if naive
            if dt.tzinfo is None:
                from datetime import timezone
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, AttributeError):
            pass
        
        try:
            # Try common date formats using dateutil
            from dateutil import parser
            dt = parser.parse(str(timestamp_str))
            # Make timezone-aware if naive
            if dt.tzinfo is None:
                from datetime import timezone
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, parser.ParserError, TypeError):
            pass
        
        return None


class CrossSourceAnomalyDetector:
    """
    Alert when multiple sources show simultaneous anomalies.
    
    Example: DSCOVR + MAVEN + USGS all show anomalies within 6-hour window,
    AND chi approaches 0.15 -> HIGH-PRIORITY MULTI-SOURCE EVENT
    """
    
    def __init__(self, data_dir: str = 'data', time_window_hours: int = 6):
        """
        Initialize the cross-source anomaly detector.
        
        Args:
            data_dir: Directory containing data files
            time_window_hours: Time window for considering events simultaneous
        """
        self.data_dir = Path(data_dir)
        self.time_window_hours = time_window_hours
        self.anomaly_events = []
        
    def check_multi_source_events(self, sources: List[str] = None) -> List[Dict]:
        """
        Detect when multiple sources show anomalies within the time window.
        
        Args:
            sources: List of source names to check (default: all available)
            
        Returns:
            List of multi-source anomaly events
        """
        if sources is None:
            sources = ['DSCOVR', 'MAVEN', 'USGS', 'CHI_BOUNDARY', 'NOAA']
        
        # Collect anomalies from each source
        source_anomalies = {}
        for source in sources:
            anomalies = self._detect_source_anomalies(source)
            if anomalies:
                source_anomalies[source] = anomalies
        
        # Find overlapping time windows
        multi_source_events = []
        
        # Get all unique timestamps
        all_times = set()
        for anomalies in source_anomalies.values():
            for anomaly in anomalies:
                all_times.add(anomaly['timestamp'])
        
        # Check each time for multi-source convergence
        for base_time in sorted(all_times):
            window_start = base_time - timedelta(hours=self.time_window_hours / 2)
            window_end = base_time + timedelta(hours=self.time_window_hours / 2)
            
            sources_in_window = []
            anomalies_in_window = []
            
            for source, anomalies in source_anomalies.items():
                for anomaly in anomalies:
                    if window_start <= anomaly['timestamp'] <= window_end:
                        sources_in_window.append(source)
                        anomalies_in_window.append(anomaly)
                        break
            
            # If 2+ sources show anomalies, it's a multi-source event
            if len(set(sources_in_window)) >= 2:
                multi_source_events.append({
                    'timespan': {
                        'start': window_start.isoformat(),
                        'end': window_end.isoformat(),
                        'center': base_time.isoformat()
                    },
                    'sources_involved': list(set(sources_in_window)),
                    'source_count': len(set(sources_in_window)),
                    'anomalies': anomalies_in_window,
                    'severity': 'HIGH' if len(set(sources_in_window)) >= 3 else 'MEDIUM',
                    'recommendation': self._generate_recommendation(sources_in_window, anomalies_in_window)
                })
        
        # Remove duplicates and sort by time
        unique_events = self._deduplicate_events(multi_source_events)
        self.anomaly_events = unique_events
        return unique_events
    
    def _detect_source_anomalies(self, source: str) -> List[Dict]:
        """
        Detect anomalies in a specific data source.
        
        Uses heuristics specific to each source type.
        """
        anomalies = []
        
        # Find relevant data files
        source_files = list(self.data_dir.glob(f'**/*{source.lower()}*'))
        
        for file_path in source_files:
            try:
                # Parse file and look for anomaly indicators
                if file_path.suffix == '.json':
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        anomalies.extend(self._find_json_anomalies(data, source))
                
                elif file_path.suffix in ['.yaml', '.yml']:
                    with open(file_path, 'r') as f:
                        data = yaml.safe_load(f)
                        anomalies.extend(self._find_json_anomalies(data, source))
                
                else:
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                        anomalies.extend(self._find_text_anomalies(content, source))
                        
            except (IOError, OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
                # Skip files that can't be processed (permissions, binary, malformed)
                pass
        
        return anomalies
    
    def _find_json_anomalies(self, data: Any, source: str) -> List[Dict]:
        """Find anomaly indicators in JSON/YAML data."""
        anomalies = []
        
        # Look for chi boundary violations
        if 'chi' in str(data).lower():
            if isinstance(data, dict):
                chi_value = data.get('chi', data.get('chi_amplitude', data.get('chi_boundary')))
                if chi_value and isinstance(chi_value, (int, float)) and chi_value >= 0.15:
                    timestamp = self._parse_timestamp(data.get('timestamp', data.get('time', datetime.now().isoformat())))
                    if timestamp:
                        anomalies.append({
                            'timestamp': timestamp,
                            'source': source,
                            'type': 'chi_boundary_approach',
                            'value': chi_value,
                            'data': data
                        })
        
        # Recursive search for nested structures
        if isinstance(data, dict):
            for value in data.values():
                if isinstance(value, (dict, list)):
                    anomalies.extend(self._find_json_anomalies(value, source))
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    anomalies.extend(self._find_json_anomalies(item, source))
        
        return anomalies
    
    def _find_text_anomalies(self, content: str, source: str) -> List[Dict]:
        """Find anomaly indicators in text content."""
        anomalies = []
        
        # Look for anomaly keywords
        anomaly_keywords = [
            'anomaly', 'spike', 'alert', 'warning', 'violation', 
            'deviation', 'extreme', 'high', 'critical', 'storm'
        ]
        
        for keyword in anomaly_keywords:
            pattern = rf'({keyword}[\w\s:]*?\d{{4}}-\d{{2}}-\d{{2}})'
            matches = re.finditer(pattern, content, re.IGNORECASE)
            
            for match in matches:
                # Extract timestamp from context
                timestamp_pattern = r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}'
                timestamp_match = re.search(timestamp_pattern, match.group(0))
                
                if timestamp_match:
                    try:
                        timestamp_str = timestamp_match.group(0).replace(' ', 'T')
                        timestamp = datetime.fromisoformat(timestamp_str)
                        
                        anomalies.append({
                            'timestamp': timestamp,
                            'source': source,
                            'type': f'{keyword}_detected',
                            'context': match.group(0)[:200]
                        })
                    except (ValueError, AttributeError):
                        # Skip malformed timestamps
                        pass
        
        return anomalies
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse various timestamp formats and ensure timezone awareness."""
        if isinstance(timestamp_str, datetime):
            # Make timezone-aware if naive
            if timestamp_str.tzinfo is None:
                from datetime import timezone
                return timestamp_str.replace(tzinfo=timezone.utc)
            return timestamp_str
        
        try:
            dt = datetime.fromisoformat(str(timestamp_str).replace('Z', '+00:00'))
            # Make timezone-aware if naive
            if dt.tzinfo is None:
                from datetime import timezone
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, AttributeError, TypeError):
            # Skip invalid timestamp formats
            pass
        
        return None
    
    def _generate_recommendation(self, sources: List[str], anomalies: List[Dict]) -> str:
        """Generate actionable recommendation based on detected anomalies."""
        source_set = set(sources)
        
        if 'CHI_BOUNDARY' in source_set and 'DSCOVR' in source_set:
            return "Validate chi universality across heliosphere. Check MAVEN for Mars response."
        elif 'NOAA' in source_set and len(source_set) >= 2:
            return "Check solar flare data. Likely space weather event in progress."
        elif len(source_set) >= 3:
            return "Major multi-source event detected. Review all data sources for correlation."
        else:
            return "Monitor sources for continued anomalous behavior."
    
    def _deduplicate_events(self, events: List[Dict]) -> List[Dict]:
        """Remove duplicate events within overlapping time windows."""
        if not events:
            return []
        
        # Sort by timestamp
        sorted_events = sorted(events, key=lambda x: x['timespan']['center'])
        
        unique_events = []
        last_time = None
        
        for event in sorted_events:
            current_time = datetime.fromisoformat(event['timespan']['center'])
            
            # If this event is more than time_window away from last, it's unique
            if last_time is None or (current_time - last_time).total_seconds() / 3600 > self.time_window_hours:
                unique_events.append(event)
                last_time = current_time
            else:
                # Merge with last event if sources are different
                if set(event['sources_involved']) != set(unique_events[-1]['sources_involved']):
                    unique_events[-1]['sources_involved'].extend(event['sources_involved'])
                    unique_events[-1]['sources_involved'] = list(set(unique_events[-1]['sources_involved']))
                    unique_events[-1]['source_count'] = len(unique_events[-1]['sources_involved'])
        
        return unique_events


class DataSourceMonitor:
    """
    Monitor status and availability of all registered data sources.
    """
    
    def __init__(self, registry_file: str = 'external_data_sources_registry.yaml'):
        """Initialize with data source registry."""
        self.registry_file = Path(registry_file)
        self.sources = {}
        self.load_registry()
        
    def load_registry(self):
        """Load data source registry."""
        if not self.registry_file.exists():
            print(f"Warning: Registry file not found: {self.registry_file}")
            return
        
        with open(self.registry_file, 'r') as f:
            registry = yaml.safe_load(f)
        
        # Extract all sources from registry
        for category_key, category_data in registry.items():
            if isinstance(category_data, dict) and 'sources' in category_data:
                for source in category_data['sources']:
                    source_name = source.get('name', 'unknown')
                    self.sources[source_name] = {
                        'category': category_data.get('category', 'Unknown'),
                        'description': source.get('description', ''),
                        'urls': source.get('urls', []),
                        'status': source.get('status', 'unknown'),
                        'data_types': source.get('data_types', []),
                        'update_frequency': source.get('update_frequency', 'unknown')
                    }
    
    def get_active_sources(self) -> List[str]:
        """Get list of active data sources."""
        return [name for name, data in self.sources.items() 
                if data['status'] == 'active']
    
    def get_source_info(self, source_name: str) -> Optional[Dict]:
        """Get information about a specific source."""
        return self.sources.get(source_name)
    
    def get_sources_by_category(self, category: str) -> List[str]:
        """Get sources in a specific category."""
        return [name for name, data in self.sources.items() 
                if category.lower() in data['category'].lower()]


def generate_meta_intelligence_report(correlations: List[Dict], 
                                     anomalies: List[Dict],
                                     sources: Dict[str, Any],
                                     output_path: str = None) -> str:
    """
    Generate comprehensive meta-intelligence report.
    
    Args:
        correlations: Detected temporal correlations
        anomalies: Multi-source anomaly events
        sources: Data source information
        output_path: Path to save report (optional)
        
    Returns:
        Report content as markdown string
    """
    report_date = datetime.now().strftime('%Y-%m-%d')
    
    report = f"""# 🌟 LUFT META-INTELLIGENCE DAILY REPORT
**Date:** {report_date}  
**Sources Monitored:** {len(sources)}  
**Active Sources:** {len([s for s in sources.values() if s.get('status') == 'active'])}

---

## 🔴 MULTI-SOURCE ANOMALY ALERTS

"""
    
    if anomalies:
        for i, event in enumerate(anomalies, 1):
            severity_emoji = '🔴' if event['severity'] == 'HIGH' else '🟡'
            report += f"""### {severity_emoji} Alert #{i}: {event['severity']} Priority
**Timespan:** {event['timespan']['start']} → {event['timespan']['end']}  
**Sources Involved:** {', '.join(event['sources_involved'])}  
**Source Count:** {event['source_count']}

📈 **Recommendation:**  
{event['recommendation']}

---

"""
    else:
        report += "✅ No multi-source anomaly events detected in the current period.\n\n"
    
    report += """## 🔗 TEMPORAL CORRELATION ANALYSIS

"""
    
    if correlations:
        for i, corr in enumerate(correlations, 1):
            report += f"""### Correlation #{i}: {corr['source_lead']} → {corr['source_lag']}
**Time Delay:** {corr['delay_hours']} hours  
**Confidence:** {corr['confidence']}%  
**Matches Found:** {corr['matches']}

💡 **Pattern:**  
{corr['recommendation']}

**Example Cases:**
"""
            for j, example in enumerate(corr['examples'][:3], 1):
                report += f"""- Case {j}: {corr['source_lead']} event at {example['source_a_time']} → {corr['source_lag']} response at {example['source_b_time']} (delay: {example['actual_delay_hours']}h)
"""
            report += "\n"
    else:
        report += "ℹ️ No significant temporal correlations detected. More data collection needed.\n\n"
    
    report += """## 📊 DATA SOURCE STATUS

"""
    
    # Group sources by category
    by_category = defaultdict(list)
    for name, data in sources.items():
        by_category[data.get('category', 'Unknown')].append((name, data))
    
    for category, source_list in sorted(by_category.items()):
        active_count = len([s for _, s in source_list if s.get('status') == 'active'])
        report += f"""### {category}
Active: {active_count}/{len(source_list)} sources

"""
    
    report += f"""---

## 🎯 NEXT STEPS

Based on this analysis, recommended actions:

1. **Monitor Identified Patterns:** Continue tracking temporal correlations for validation
2. **Cross-Validate Anomalies:** When multi-source events occur, verify against additional sources
3. **Expand Coverage:** Consider adding data sources from underrepresented categories
4. **Refine Detection:** Adjust anomaly detection thresholds based on false positive rate

---

*Report generated by LUFT Meta-Intelligence Engine v4.0*  
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
    """Main entry point for meta-pattern detector."""
    parser = argparse.ArgumentParser(
        description='LUFT Meta-Pattern Detector - Layer 4 Intelligence Engine',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--detect-correlations', action='store_true',
                       help='Detect temporal correlations between sources')
    parser.add_argument('--detect-anomalies', action='store_true',
                       help='Detect multi-source anomaly events')
    parser.add_argument('--full-analysis', action='store_true',
                       help='Run complete meta-intelligence analysis')
    parser.add_argument('--data-dir', default='data',
                       help='Directory containing data files')
    parser.add_argument('--output', default=None,
                       help='Output file for report')
    parser.add_argument('--registry', default='external_data_sources_registry.yaml',
                       help='Path to data source registry')
    
    args = parser.parse_args()
    
    # Default to full analysis if no specific mode selected
    if not (args.detect_correlations or args.detect_anomalies or args.full_analysis):
        args.full_analysis = True
    
    print("="*70)
    print("🌟 LUFT META-INTELLIGENCE ENGINE v4.0")
    print("="*70)
    print()
    
    # Initialize components
    monitor = DataSourceMonitor(args.registry)
    sources = monitor.sources
    
    print(f"📡 Loaded {len(sources)} data sources from registry")
    print(f"✅ Active sources: {len(monitor.get_active_sources())}")
    print()
    
    correlations = []
    anomalies = []
    
    # Detect temporal correlations
    if args.detect_correlations or args.full_analysis:
        print("🔍 Analyzing temporal correlations...")
        engine = TemporalCorrelationEngine(args.data_dir)
        
        # Check key relationships
        active_sources = monitor.get_active_sources()
        
        # Prioritize known relationships
        priority_pairs = [
            ('NOAA', 'CHI_BOUNDARY'),
            ('DSCOVR', 'CHI_BOUNDARY'),
            ('NOAA', 'MAVEN'),
            ('DSCOVR', 'USGS'),
        ]
        
        for source_a, source_b in priority_pairs:
            patterns = engine.detect_lead_lag(source_a, source_b)
            if patterns:
                print(f"   ✓ Found {len(patterns)} correlation(s): {source_a} → {source_b}")
                correlations.extend(patterns)
        
        print(f"   Total correlations detected: {len(correlations)}")
        print()
    
    # Detect cross-source anomalies
    if args.detect_anomalies or args.full_analysis:
        print("🚨 Detecting cross-source anomalies...")
        detector = CrossSourceAnomalyDetector(args.data_dir)
        
        anomalies = detector.check_multi_source_events()
        print(f"   Multi-source events detected: {len(anomalies)}")
        
        for event in anomalies:
            print(f"   {event['severity']}: {event['source_count']} sources at {event['timespan']['center']}")
        print()
    
    # Generate report
    if args.full_analysis:
        print("📝 Generating meta-intelligence report...")
        
        if args.output is None:
            # Generate default filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            args.output = f'reports/meta_intelligence/report_{timestamp}.md'
        
        report = generate_meta_intelligence_report(
            correlations, anomalies, sources, args.output
        )
        
        print()
        print("="*70)
        print(report)
        print("="*70)
    
    print()
    print("✨ Meta-intelligence analysis complete!")


if __name__ == '__main__':
    main()
