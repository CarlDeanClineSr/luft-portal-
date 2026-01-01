#!/usr/bin/env python3
"""
LUFT Bow Pattern Detector
==========================

Detects loading-relaxation-reload cycles (bow patterns) in χ amplitude data.

Discovery: Carl Dean Cline Sr., 2025-12-31
Location: Lincoln, Nebraska, USA
Email: CARLDCLINE@GMAIL.COM

Physical Interpretation:
The bow pattern represents energy absorption cycles in the magnetosphere:
1. Loading: System absorbs energy, χ rises toward 0.15 boundary
2. Peak: Approaches boundary, reaches local maximum
3. Relaxation: Snaps back, releases energy, χ drops
4. Reload: System reloads energy, χ rises again

Example bow pattern (2025-12-31 17:19-22:19 UTC):
Time:      17:19    18:20    19:19    20:21    21:19    22:19
χ value:  ~0.115 → 0.130 → 0.140 → 0.135 → 0.120 → 0.145

Usage:
    python bow_pattern_detector.py --config configs/bow_detection_config.yaml
    python bow_pattern_detector.py --data data/chi_analysis_*.csv
"""

import argparse
import json
import yaml
import csv
import glob
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
import numpy as np
import pandas as pd
from scipy import signal


@dataclass
class BowEvent:
    """Represents a detected bow pattern event."""
    
    # Event identification
    event_id: str
    event_type: str  # "single_bow", "double_bow", "failed_bow"
    
    # Timing
    start_time: str
    end_time: str
    duration_hours: float
    
    # Loading phase
    loading_start: str
    loading_end: str
    loading_duration_hours: float
    loading_chi_rise: float
    
    # Peak
    peak_time: str
    peak_chi: float
    distance_from_boundary: float
    
    # Relaxation phase
    relaxation_start: str
    relaxation_end: str
    relaxation_duration_hours: float
    relaxation_chi_drop: float
    
    # Reload phase (if present)
    reload_start: Optional[str] = None
    reload_end: Optional[str] = None
    reload_duration_hours: Optional[float] = None
    reload_chi_rise: Optional[float] = None
    
    # Additional metadata
    confidence: float = 1.0
    notes: str = ""


class BowPatternDetector:
    """Detects bow patterns in χ amplitude timeseries data."""
    
    def __init__(self, config_path: str = "configs/bow_detection_config.yaml"):
        """
        Initialize the bow pattern detector.
        
        Args:
            config_path: Path to configuration YAML file
        """
        self.config = self._load_config(config_path)
        self.events: List[BowEvent] = []
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def load_chi_data(self, data_paths: List[str]) -> pd.DataFrame:
        """
        Load χ amplitude data from multiple sources.
        
        Args:
            data_paths: List of file paths or glob patterns
            
        Returns:
            DataFrame with columns: timestamp, chi_amplitude
        """
        all_data = []
        
        for pattern in data_paths:
            files = glob.glob(pattern)
            for filepath in files:
                try:
                    if filepath.endswith('.csv'):
                        df = pd.read_csv(filepath)
                        if 'chi_amplitude' in df.columns and 'timestamp' in df.columns:
                            all_data.append(df[['timestamp', 'chi_amplitude']])
                    elif filepath.endswith('.json'):
                        with open(filepath, 'r') as f:
                            data = json.load(f)
                            # Handle different JSON structures
                            if isinstance(data, list):
                                df = pd.DataFrame(data)
                            elif isinstance(data, dict) and 'data' in data:
                                df = pd.DataFrame(data['data'])
                            else:
                                continue
                            if 'chi_amplitude' in df.columns and 'timestamp' in df.columns:
                                all_data.append(df[['timestamp', 'chi_amplitude']])
                    elif filepath.endswith('.jsonl'):
                        df = pd.read_json(filepath, lines=True)
                        if 'chi_amplitude' in df.columns and 'timestamp' in df.columns:
                            all_data.append(df[['timestamp', 'chi_amplitude']])
                except Exception as e:
                    print(f"Warning: Could not load {filepath}: {e}")
                    continue
        
        if not all_data:
            print("Warning: No data loaded")
            return pd.DataFrame(columns=['timestamp', 'chi_amplitude'])
        
        # Combine all data
        combined = pd.concat(all_data, ignore_index=True)
        
        # Convert timestamp to datetime
        combined['timestamp'] = pd.to_datetime(combined['timestamp'])
        
        # Sort by timestamp and remove duplicates
        combined = combined.sort_values('timestamp').drop_duplicates(subset=['timestamp'])
        
        # Remove invalid chi values
        combined = combined[combined['chi_amplitude'].notna()]
        combined = combined[combined['chi_amplitude'] >= 0]
        
        return combined.reset_index(drop=True)
    
    def detect_peaks(self, chi_series: pd.Series, timestamps: pd.Series) -> List[int]:
        """
        Detect peaks in χ timeseries using scipy.signal.
        
        Args:
            chi_series: Series of χ amplitude values
            timestamps: Series of corresponding timestamps
            
        Returns:
            List of peak indices
        """
        params = self.config['detection_parameters']
        
        # Find peaks with prominence and distance requirements
        peaks, properties = signal.find_peaks(
            chi_series.values,
            prominence=params['peak_prominence'],
            distance=params['peak_distance']
        )
        
        # Filter peaks by minimum chi value
        valid_peaks = []
        for peak_idx in peaks:
            if chi_series.iloc[peak_idx] >= params['peak_min_chi']:
                valid_peaks.append(peak_idx)
        
        return valid_peaks
    
    def detect_loading_phase(self, chi_series: pd.Series, timestamps: pd.Series,
                            peak_idx: int) -> Optional[Tuple[int, int, float]]:
        """
        Detect loading phase before a peak.
        
        Args:
            chi_series: Series of χ amplitude values
            timestamps: Series of corresponding timestamps
            peak_idx: Index of the peak
            
        Returns:
            Tuple of (start_idx, end_idx, chi_rise) or None if not found
        """
        params = self.config['detection_parameters']
        peak_chi = chi_series.iloc[peak_idx]
        peak_time = timestamps.iloc[peak_idx]
        
        # Search backwards from peak
        min_duration = timedelta(hours=params['loading_min_duration'])
        max_duration = timedelta(hours=params['loading_max_duration'])
        
        for start_idx in range(peak_idx - 1, -1, -1):
            time_diff = peak_time - timestamps.iloc[start_idx]
            
            if time_diff > max_duration:
                break
            
            if time_diff >= min_duration:
                chi_rise = peak_chi - chi_series.iloc[start_idx]
                
                if chi_rise >= params['loading_min_rise']:
                    return (start_idx, peak_idx, chi_rise)
        
        return None
    
    def detect_relaxation_phase(self, chi_series: pd.Series, timestamps: pd.Series,
                               peak_idx: int) -> Optional[Tuple[int, int, float]]:
        """
        Detect relaxation phase after a peak.
        
        Args:
            chi_series: Series of χ amplitude values
            timestamps: Series of corresponding timestamps
            peak_idx: Index of the peak
            
        Returns:
            Tuple of (start_idx, end_idx, chi_drop) or None if not found
        """
        params = self.config['detection_parameters']
        peak_chi = chi_series.iloc[peak_idx]
        peak_time = timestamps.iloc[peak_idx]
        
        # Search forward from peak
        min_duration = timedelta(hours=params['relaxation_min_duration'])
        max_duration = timedelta(hours=params['relaxation_max_duration'])
        
        for end_idx in range(peak_idx + 1, len(chi_series)):
            time_diff = timestamps.iloc[end_idx] - peak_time
            
            if time_diff > max_duration:
                break
            
            if time_diff >= min_duration:
                chi_drop = peak_chi - chi_series.iloc[end_idx]
                
                if chi_drop >= params['relaxation_min_drop']:
                    return (peak_idx, end_idx, chi_drop)
        
        return None
    
    def detect_reload_phase(self, chi_series: pd.Series, timestamps: pd.Series,
                           relaxation_end_idx: int) -> Optional[Tuple[int, int, float]]:
        """
        Detect reload phase after relaxation.
        
        Args:
            chi_series: Series of χ amplitude values
            timestamps: Series of corresponding timestamps
            relaxation_end_idx: Index where relaxation ended
            
        Returns:
            Tuple of (start_idx, end_idx, chi_rise) or None if not found
        """
        params = self.config['detection_parameters']
        relaxation_chi = chi_series.iloc[relaxation_end_idx]
        relaxation_time = timestamps.iloc[relaxation_end_idx]
        
        # Search forward from relaxation end
        min_duration = timedelta(hours=params['reload_min_duration'])
        max_duration = timedelta(hours=params['reload_max_duration'])
        
        for end_idx in range(relaxation_end_idx + 1, len(chi_series)):
            time_diff = timestamps.iloc[end_idx] - relaxation_time
            
            if time_diff > max_duration:
                break
            
            if time_diff >= min_duration:
                chi_rise = chi_series.iloc[end_idx] - relaxation_chi
                
                if chi_rise >= params['reload_min_rise']:
                    return (relaxation_end_idx, end_idx, chi_rise)
        
        return None
    
    def classify_bow(self, has_loading: bool, has_peak: bool, has_relaxation: bool,
                    has_reload: bool) -> str:
        """
        Classify bow pattern type.
        
        Args:
            has_loading: Whether loading phase was detected
            has_peak: Whether peak was detected
            has_relaxation: Whether relaxation phase was detected
            has_reload: Whether reload phase was detected
            
        Returns:
            Classification string: "single_bow", "double_bow", or "failed_bow"
        """
        if has_loading and has_peak and has_relaxation and has_reload:
            return "single_bow"
        elif has_loading and has_peak and has_relaxation and not has_reload:
            return "failed_bow"
        else:
            return "incomplete"
    
    def detect_bows(self, df: pd.DataFrame) -> List[BowEvent]:
        """
        Detect all bow patterns in the data.
        
        Args:
            df: DataFrame with timestamp and chi_amplitude columns
            
        Returns:
            List of detected BowEvent objects
        """
        if df.empty:
            print("Warning: No data to analyze")
            return []
        
        chi_series = df['chi_amplitude']
        timestamps = df['timestamp']
        
        # Detect peaks
        peak_indices = self.detect_peaks(chi_series, timestamps)
        print(f"Detected {len(peak_indices)} potential peaks")
        
        events = []
        boundary = 0.15
        
        for peak_idx in peak_indices:
            peak_chi = chi_series.iloc[peak_idx]
            peak_time = timestamps.iloc[peak_idx]
            
            # Check if peak is close to boundary
            distance_from_boundary = abs(boundary - peak_chi)
            max_distance = self.config['detection_parameters']['peak_max_distance_from_boundary']
            
            if distance_from_boundary > max_distance:
                continue
            
            # Detect phases
            loading_result = self.detect_loading_phase(chi_series, timestamps, peak_idx)
            relaxation_result = self.detect_relaxation_phase(chi_series, timestamps, peak_idx)
            
            if loading_result is None or relaxation_result is None:
                continue
            
            loading_start_idx, loading_end_idx, loading_rise = loading_result
            relax_start_idx, relax_end_idx, relax_drop = relaxation_result
            
            # Detect reload
            reload_result = self.detect_reload_phase(chi_series, timestamps, relax_end_idx)
            
            has_reload = reload_result is not None
            classification = self.classify_bow(True, True, True, has_reload)
            
            if classification == "incomplete":
                continue
            
            # Create event
            event_id = f"BOW_{peak_time.strftime('%Y%m%d_%H%M%S')}"
            
            # Calculate durations
            loading_duration = (timestamps.iloc[loading_end_idx] - 
                              timestamps.iloc[loading_start_idx]).total_seconds() / 3600
            relaxation_duration = (timestamps.iloc[relax_end_idx] - 
                                  timestamps.iloc[relax_start_idx]).total_seconds() / 3600
            
            event = BowEvent(
                event_id=event_id,
                event_type=classification,
                start_time=timestamps.iloc[loading_start_idx].isoformat(),
                end_time=(timestamps.iloc[reload_result[1]] if has_reload 
                         else timestamps.iloc[relax_end_idx]).isoformat(),
                duration_hours=((timestamps.iloc[reload_result[1]] if has_reload 
                               else timestamps.iloc[relax_end_idx]) - 
                              timestamps.iloc[loading_start_idx]).total_seconds() / 3600,
                loading_start=timestamps.iloc[loading_start_idx].isoformat(),
                loading_end=timestamps.iloc[loading_end_idx].isoformat(),
                loading_duration_hours=loading_duration,
                loading_chi_rise=loading_rise,
                peak_time=peak_time.isoformat(),
                peak_chi=peak_chi,
                distance_from_boundary=distance_from_boundary,
                relaxation_start=timestamps.iloc[relax_start_idx].isoformat(),
                relaxation_end=timestamps.iloc[relax_end_idx].isoformat(),
                relaxation_duration_hours=relaxation_duration,
                relaxation_chi_drop=relax_drop
            )
            
            # Add reload information if present
            if has_reload:
                reload_start_idx, reload_end_idx, reload_rise = reload_result
                event.reload_start = timestamps.iloc[reload_start_idx].isoformat()
                event.reload_end = timestamps.iloc[reload_end_idx].isoformat()
                event.reload_duration_hours = (timestamps.iloc[reload_end_idx] - 
                                              timestamps.iloc[reload_start_idx]).total_seconds() / 3600
                event.reload_chi_rise = reload_rise
            
            events.append(event)
        
        self.events = events
        return events
    
    def export_to_csv(self, output_path: str):
        """Export detected events to CSV file."""
        if not self.events:
            print("No events to export")
            return
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=asdict(self.events[0]).keys())
            writer.writeheader()
            for event in self.events:
                writer.writerow(asdict(event))
        
        print(f"Exported {len(self.events)} events to {output_path}")
    
    def export_to_json(self, output_path: str):
        """Export detected events to JSON file."""
        if not self.events:
            print("No events to export")
            return
        
        output_data = {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'total_events': len(self.events),
            'events': [asdict(event) for event in self.events]
        }
        
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"Exported {len(self.events)} events to {output_path}")


def main():
    """Main entry point for the bow pattern detector."""
    parser = argparse.ArgumentParser(
        description='Detect bow patterns in χ amplitude data'
    )
    parser.add_argument('--config', default='configs/bow_detection_config.yaml',
                       help='Path to configuration file')
    parser.add_argument('--data', nargs='+',
                       help='Data file paths or patterns (overrides config)')
    parser.add_argument('--output-csv', default=None,
                       help='Output CSV file path')
    parser.add_argument('--output-json', default=None,
                       help='Output JSON file path')
    
    args = parser.parse_args()
    
    # Initialize detector
    detector = BowPatternDetector(args.config)
    
    # Determine data sources
    if args.data:
        data_paths = args.data
    else:
        data_paths = detector.config['data_sources']['chi_data']
    
    print(f"Loading χ amplitude data from {len(data_paths)} source(s)...")
    df = detector.load_chi_data(data_paths)
    print(f"Loaded {len(df)} data points")
    
    if df.empty:
        print("Error: No data loaded")
        return 1
    
    print(f"Data range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    
    # Detect bow patterns
    print("\nDetecting bow patterns...")
    events = detector.detect_bows(df)
    
    print(f"\n✓ Detected {len(events)} bow patterns")
    
    # Print summary
    if events:
        single_bows = sum(1 for e in events if e.event_type == 'single_bow')
        failed_bows = sum(1 for e in events if e.event_type == 'failed_bow')
        double_bows = sum(1 for e in events if e.event_type == 'double_bow')
        
        print(f"  - Single bows: {single_bows}")
        print(f"  - Failed bows: {failed_bows}")
        print(f"  - Double bows: {double_bows}")
    
    # Export results
    output_dir = Path(detector.config['output']['report_path'])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    
    if args.output_csv:
        csv_path = args.output_csv
    else:
        csv_path = output_dir / f"bow_events_{timestamp}.csv"
    
    if args.output_json:
        json_path = args.output_json
    else:
        json_path = output_dir / f"bow_events_{timestamp}.json"
    
    if detector.config['output']['save_csv']:
        detector.export_to_csv(str(csv_path))
    
    if detector.config['output']['save_json']:
        detector.export_to_json(str(json_path))
    
    return 0


if __name__ == '__main__':
    exit(main())
