#!/usr/bin/env python3
"""
Process January 2026 data with wave packet analyzer
Combines December 2025 + January 2026 for comprehensive analysis

Author: LUFT Portal Engine
Date: 2026-01-02
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Import wave packet analyzer from same directory
try:
    from wave_packet_analyzer import WavePacketAnalyzer
except ImportError:
    # If running from different directory, try adding scripts to path
    sys.path.insert(0, str(Path(__file__).parent))
    from wave_packet_analyzer import WavePacketAnalyzer

def load_and_combine_data():
    """Load and combine December 2025 and January 2026 data"""
    
    print("📂 Loading CME heartbeat data...")
    
    dataframes = []
    
    # Load December 2025
    dec_file = Path('data/cme_heartbeat_log_2025_12.csv')
    if dec_file.exists():
        try:
            df_dec = pd.read_csv(dec_file, on_bad_lines='skip')
            df_dec['timestamp_utc'] = pd.to_datetime(df_dec['timestamp_utc'], errors='coerce')
            df_dec = df_dec.dropna(subset=['timestamp_utc'])
            dataframes.append(df_dec)
            print(f"  ✅ December 2025: {len(df_dec)} observations")
        except Exception as e:
            print(f"  ⚠️ December 2025 error: {e}")
    
    # Load January 2026
    jan_file = Path('data/cme_heartbeat_log_2026_01.csv')
    if jan_file.exists():
        try:
            df_jan = pd.read_csv(jan_file)
            df_jan['timestamp_utc'] = pd.to_datetime(df_jan['timestamp_utc'], errors='coerce')
            df_jan = df_jan.dropna(subset=['timestamp_utc'])
            dataframes.append(df_jan)
            print(f"  ✅ January 2026: {len(df_jan)} observations")
        except Exception as e:
            print(f"  ⚠️ January 2026 error: {e}")
    
    if not dataframes:
        print("  ❌ No data files found!")
        return None
    
    # Combine dataframes
    df_combined = pd.concat(dataframes, ignore_index=True)
    df_combined = df_combined.sort_values('timestamp_utc')
    df_combined = df_combined.set_index('timestamp_utc')
    
    # Ensure bt_nT is numeric and use as B_mag
    df_combined['bt_nT'] = pd.to_numeric(df_combined['bt_nT'], errors='coerce')
    df_combined['B_mag'] = df_combined['bt_nT']
    
    # Drop rows without B_mag
    df_combined = df_combined.dropna(subset=['B_mag'])
    
    print(f"  📊 Combined: {len(df_combined)} observations")
    print(f"  📅 Date range: {df_combined.index.min()} to {df_combined.index.max()}")
    
    return df_combined

def main():
    """Process combined data with wave packet analyzer"""
    
    print("=" * 80)
    print("WAVE PACKET ANALYSIS - DECEMBER 2025 + JANUARY 2026")
    print("=" * 80)
    print()
    
    # Load data
    df = load_and_combine_data()
    
    if df is None or len(df) == 0:
        print("❌ No valid data to analyze")
        return
    
    print()
    
    # Initialize analyzer
    analyzer = WavePacketAnalyzer()
    
    # Detect wave packets
    print("🔍 Detecting 0.9-hour wave packets...")
    results = analyzer.detect_packets(df, df.index, param='B_mag')
    
    print()
    print("=" * 80)
    print("📊 WAVE PACKET DETECTION RESULTS")
    print("=" * 80)
    
    # Fundamental period
    fund = results['fundamental']
    print(f"\n🌊 FUNDAMENTAL PERIOD:")
    print(f"   Detected: {fund['period_hours']:.3f} hours")
    print(f"   Expected: {fund['expected']:.3f} hours")
    match = abs(fund['period_hours'] - fund['expected']) < 0.3
    print(f"   Match: {'✅ YES' if match else '⚠️ APPROXIMATE'}")
    
    # Harmonics
    print(f"\n🎵 HARMONIC STRUCTURE:")
    print(f"{'Mode':<15} {'Period (h)':<12} {'Packets':<10} {'Power':<12} {'Status':<15}")
    print("-" * 80)
    
    for mode_name, mode_data in results['harmonics'].items():
        period = mode_data['period_hours']
        packets = mode_data['expected_packets']
        power = mode_data['power']
        
        # Determine status
        if mode_name == 'mode_5':  # Peak mode at 24h
            status = "🔥 PEAK"
        elif mode_name == 'mode_1':  # First response at 6h
            status = "⚡ FIRST"
        elif mode_name == 'mode_13':  # Cutoff at 72h
            status = "🛑 CUTOFF"
        else:
            status = "✓ DETECTED"
        
        print(f"{mode_name:<15} {period:<12.1f} {packets:<10} {power:<12.3e} {status:<15}")
    
    # Chi correlation info
    print(f"\n🎯 CONNECTION TO χ = 0.15 BOUNDARY:")
    print(f"   Wave packet accumulation triggers χ boundary response")
    print(f"   First coherent pattern: ~7 packets (6 hours)")
    print(f"   Peak response: ~27 packets (24 hours)")
    print(f"   System cutoff: ~80 packets (72 hours)")
    
    # Generate plot
    print(f"\n📈 Generating diagnostic plots...")
    save_path = 'figures/wave_packet_analysis_combined.png'
    analyzer.plot_results(results, save_path=save_path)
    
    print()
    print("=" * 80)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"\nResults saved to: {save_path}")
    print(f"Configuration: constants/wave_packet_physics.yaml")
    print(f"Documentation: docs/WAVE_PACKET_DISCOVERY.md")
    print()

if __name__ == '__main__':
    main()
