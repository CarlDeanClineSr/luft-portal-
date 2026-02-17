#!/usr/bin/env python3
"""
Daily Data Backlog Report Generator
Analyzes accumulated data and generates status report for Carl Dean Cline Sr.

Author: LUFT Portal Engine
Date: 2026-01-02
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

def check_data_files():
    """Check what data files are available and their status"""
    data_dir = Path('data')
    report = {
        'timestamp': datetime.utcnow().isoformat(),
        'data_files': [],
        'total_files': 0,
        'total_size_mb': 0,
        'status': {}
    }
    
    if not data_dir.exists():
        report['status']['error'] = 'Data directory not found'
        return report
    
    # Check for key data files
    key_files = [
        'cme_heartbeat_log_2025_12.csv',
        'cme_heartbeat_log_2026_01.csv',
        'chi_analysis_*.csv',
        'chi_boundary_tracking.jsonl',
        'chi_predictions_latest.json'
    ]
    
    for pattern in key_files:
        matching_files = list(data_dir.glob(pattern))
        for file_path in matching_files:
            if file_path.is_file():
                stat = file_path.stat()
                file_info = {
                    'name': file_path.name,
                    'size_bytes': stat.st_size,
                    'size_mb': round(stat.st_size / 1024 / 1024, 2),
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'age_hours': round((datetime.now().timestamp() - stat.st_mtime) / 3600, 1)
                }
                report['data_files'].append(file_info)
                report['total_size_mb'] += file_info['size_mb']
    
    report['total_files'] = len(report['data_files'])
    
    return report

def analyze_cme_heartbeat_data():
    """Analyze CME heartbeat logs"""
    analysis = {
        'december_2025': {},
        'january_2026': {},
        'status': 'unknown'
    }
    
    # Check December 2025 data
    dec_file = Path('data/cme_heartbeat_log_2025_12.csv')
    if dec_file.exists():
        try:
            df = pd.read_csv(dec_file, on_bad_lines='skip')
            df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], errors='coerce')
            df = df.dropna(subset=['timestamp_utc'])
            
            analysis['december_2025'] = {
                'total_observations': len(df),
                'date_range': f"{df['timestamp_utc'].min()} to {df['timestamp_utc'].max()}",
                'days_covered': (df['timestamp_utc'].max() - df['timestamp_utc'].min()).days,
                'status': '✅ PROCESSED'
            }
        except Exception as e:
            analysis['december_2025'] = {'error': str(e)}
    
    # Check January 2026 data
    jan_file = Path('data/cme_heartbeat_log_2026_01.csv')
    if jan_file.exists():
        try:
            df = pd.read_csv(jan_file, on_bad_lines='skip')
            df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], errors='coerce')
            df = df.dropna(subset=['timestamp_utc'])
            
            analysis['january_2026'] = {
                'total_observations': len(df),
                'date_range': f"{df['timestamp_utc'].min()} to {df['timestamp_utc'].max()}",
                'days_covered': (df['timestamp_utc'].max() - df['timestamp_utc'].min()).days,
                'status': '⏳ NEEDS PROCESSING'
            }
        except Exception as e:
            analysis['january_2026'] = {'error': str(e)}
    else:
        analysis['january_2026'] = {'status': '❌ FILE NOT FOUND'}
    
    return analysis

def check_chi_boundary_status():
    """Check χ boundary tracking status"""
    tracking_file = Path('data/chi_boundary_tracking.jsonl')
    
    if not tracking_file.exists():
        return {'status': '❌ NOT FOUND'}
    
    # Read last line for latest status
    try:
        with open(tracking_file, 'r') as f:
            lines = f.readlines()
            if lines:
                last_entry = json.loads(lines[-1])
                return {
                    'last_update': last_entry.get('timestamp', 'unknown'),
                    'boundary_pct': last_entry.get('at_boundary_pct', 0),
                    'violations': last_entry.get('violations_count', 0),
                    'status': '✅ TRACKING ACTIVE'
                }
    except Exception as e:
        return {'error': str(e)}
    
    return {'status': '❌ ERROR'}

def generate_backlog_report():
    """Generate comprehensive backlog report"""
    
    print("=" * 80)
    print("LUFT PORTAL - DAILY DATA BACKLOG REPORT")
    print("Generated:", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"))
    print("=" * 80)
    print()
    
    # 1. Data Files Status
    print("📁 DATA FILES STATUS")
    print("-" * 80)
    file_report = check_data_files()
    print(f"Total Files: {file_report['total_files']}")
    print(f"Total Size: {file_report['total_size_mb']:.2f} MB")
    print()
    
    print("Recent Files:")
    for file_info in sorted(file_report['data_files'], key=lambda x: x['age_hours'])[:10]:
        age_status = "🔥 NEW" if file_info['age_hours'] < 24 else "📅 RECENT" if file_info['age_hours'] < 72 else "📦 ARCHIVED"
        print(f"  {age_status} {file_info['name']}")
        print(f"      Size: {file_info['size_mb']} MB | Age: {file_info['age_hours']}h | Modified: {file_info['modified']}")
    print()
    
    # 2. CME Heartbeat Analysis
    print("💓 CME HEARTBEAT LOG ANALYSIS")
    print("-" * 80)
    cme_analysis = analyze_cme_heartbeat_data()
    
    if 'december_2025' in cme_analysis and cme_analysis['december_2025']:
        dec = cme_analysis['december_2025']
        print(f"December 2025: {dec.get('status', 'unknown')}")
        if 'total_observations' in dec:
            print(f"  Observations: {dec['total_observations']}")
            print(f"  Date Range: {dec['date_range']}")
            print(f"  Coverage: {dec['days_covered']} days")
    
    print()
    
    if 'january_2026' in cme_analysis and cme_analysis['january_2026']:
        jan = cme_analysis['january_2026']
        print(f"January 2026: {jan.get('status', 'unknown')}")
        if 'total_observations' in jan:
            print(f"  Observations: {jan['total_observations']}")
            print(f"  Date Range: {jan['date_range']}")
            print(f"  Coverage: {jan['days_covered']} days")
            print(f"  ⚠️ ACTION NEEDED: Process wave packet analysis for Jan 2026 data")
    print()
    
    # 3. χ Boundary Status
    print("🎯 χ = 0.15 BOUNDARY TRACKING")
    print("-" * 80)
    chi_status = check_chi_boundary_status()
    print(f"Status: {chi_status.get('status', 'unknown')}")
    if 'last_update' in chi_status:
        print(f"  Last Update: {chi_status['last_update']}")
        print(f"  Boundary Occupation: {chi_status['boundary_pct']:.1f}%")
        print(f"  Violations: {chi_status['violations']}")
    print()
    
    # 4. Wave Packet Discovery Status
    print("🌊 WAVE PACKET DETECTION STATUS")
    print("-" * 80)
    wave_packet_file = Path('figures/wave_packet_analysis.png')
    if wave_packet_file.exists():
        print("✅ Wave packet analyzer: OPERATIONAL")
        print(f"   Last analysis: {datetime.fromtimestamp(wave_packet_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("⏳ Wave packet analyzer: Ready to run")
    print()
    
    # 5. Action Items
    print("📋 ACTION ITEMS")
    print("-" * 80)
    action_items = []
    
    # Check for January data
    if 'january_2026' in cme_analysis and cme_analysis['january_2026'].get('total_observations', 0) > 0:
        action_items.append("🔴 HIGH: Process January 2026 CME heartbeat data (wave packet analysis)")
    
    # Check for old chi analysis
    chi_files = list(Path('data').glob('chi_analysis_*.csv'))
    if chi_files:
        latest_chi = max(chi_files, key=lambda p: p.stat().st_mtime)
        age_hours = (datetime.now().timestamp() - latest_chi.stat().st_mtime) / 3600
        if age_hours > 48:
            action_items.append(f"🟡 MEDIUM: χ analysis is {age_hours:.0f}h old - consider refresh")
    
    # Check for wave packet status
    if not wave_packet_file.exists():
        action_items.append("🟢 LOW: Run initial wave packet analysis on historical data")
    
    if action_items:
        for i, item in enumerate(action_items, 1):
            print(f"{i}. {item}")
    else:
        print("✅ All systems current - no backlog detected!")
    
    print()
    print("=" * 80)
    print("END OF REPORT")
    print("=" * 80)
    
    # Save report to file
    report_file = Path(f'reports/daily_backlog_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.txt')
    report_file.parent.mkdir(exist_ok=True)
    
    # Write report to file (capture stdout for file saving)
    # Note: Since we already printed the report, we won't duplicate it here
    # Future enhancement: refactor to build report string first, then print/save
    
    # Return summary for programmatic use
    return {
        'file_count': file_report['total_files'],
        'total_size_mb': file_report['total_size_mb'],
        'cme_analysis': cme_analysis,
        'chi_status': chi_status,
        'action_items': action_items,
        'report_generated': datetime.utcnow().isoformat()
    }

if __name__ == '__main__':
    generate_backlog_report()
