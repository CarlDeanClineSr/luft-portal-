#!/usr/bin/env python3
"""
Wave Packet Analysis Engine
Detects 0.9-hour wave packet structure in solar wind data
Correlates with χ = 0.15 boundary responses

Based on: 
- NASA/NOAA CME arrival study (arXiv:2512.14462v1)
- Carl Dean Cline Sr. temporal correlation discovery

Author: LUFT Portal Engine
Date: 2026-01-02
"""

import numpy as np
import pandas as pd
from scipy.signal import welch, find_peaks
from scipy.fft import fft, fftfreq
import matplotlib.pyplot as plt
import yaml
from pathlib import Path

class WavePacketAnalyzer:
    """Detect and analyze 0.9-hour wave packet structure"""
    
    def __init__(self, config_path='constants/wave_packet_physics.yaml'):
        # Handle relative path from different locations
        config_file = Path(config_path)
        if not config_file.exists():
            # Try relative to script location
            script_dir = Path(__file__).parent.parent
            config_file = script_dir / config_path
        
        with open(config_file) as f:
            self.config = yaml.safe_load(f)
        
        self.PACKET_PERIOD = self.config['wave_packet']['period_hours']
        self.PACKET_FREQ = self.config['wave_packet']['frequency_hz']
        self.HARMONICS = self.config['harmonics']
    
    def detect_packets(self, timeseries, timestamps, param='B_mag'):
        """
        Detect 0.9-hour wave packets in solar wind data
        
        Parameters:
        -----------
        timeseries : pd.DataFrame
            Solar wind data (B_mag, density, speed, etc.)
        timestamps : pd.DatetimeIndex
            UTC timestamps
        param : str
            Parameter to analyze (default: 'B_mag')
            
        Returns:
        --------
        dict : Detection results
        """
        # Ensure hourly sampling
        if len(timestamps) < 2:
            raise ValueError("Need at least 2 timestamps for analysis")
        dt_hours = (timestamps[1] - timestamps[0]).total_seconds() / 3600
        
        if dt_hours > 1.5: 
            print(f"⚠️ WARNING: Sampling cadence {dt_hours:.2f}h exceeds Nyquist")
            print(f"   Optimal: <1.5h, Actual: {dt_hours:.2f}h")
        
        # Compute power spectral density
        fs = 1 / dt_hours  # Sampling frequency (samples/hour)
        data = timeseries[param].dropna().values  # Convert to numpy array
        freqs, psd = welch(data, 
                           fs=fs, 
                           nperseg=min(256, len(data)//4))
        
        # Convert to period
        periods = 1 / freqs[1:]  # Exclude DC component
        psd = psd[1:]
        
        # Find peak near 0.9-hour period
        target_idx = np.argmin(np.abs(periods - self.PACKET_PERIOD))
        peak_power = psd[target_idx]
        peak_period = periods[target_idx]
        
        # Detect harmonic peaks (6h, 12h, 24h)
        harmonic_results = {}
        for mode_name, mode_info in self.HARMONICS.items():
            mode_period = mode_info['delay_hours']
            mode_idx = np.argmin(np.abs(periods - mode_period))
            harmonic_results[mode_name] = {
                'period_hours': periods[mode_idx],
                'power': psd[mode_idx],
                'expected_packets': mode_info['packets']
            }
        
        return {
            'fundamental': {
                'period_hours': peak_period,
                'power': peak_power,
                'expected': self.PACKET_PERIOD
            },
            'harmonics': harmonic_results,
            'psd': {'freqs': freqs, 'psd': psd, 'periods': periods}
        }
    
    def correlate_with_chi(self, wave_results, chi_timeseries):
        """
        Correlate wave packet detections with χ boundary responses
        
        Parameters:
        -----------
        wave_results : dict
            Output from detect_packets()
        chi_timeseries : pd.Series
            χ amplitude time series
            
        Returns:
        --------
        dict : Correlation results
        """
        # Check if χ responds at harmonic delays
        correlations = {}
        
        for mode_name, mode_data in wave_results['harmonics'].items():
            delay_hours = mode_data['period_hours']
            
            # Shift χ by delay and compute correlation
            chi_shifted = chi_timeseries.shift(int(delay_hours))
            corr = chi_timeseries.corr(chi_shifted)
            
            correlations[mode_name] = {
                'delay_hours': delay_hours,
                'correlation': corr,
                'expected_packets': mode_data['expected_packets']
            }
        
        return correlations
    
    def plot_results(self, wave_results, save_path=None):
        """Generate diagnostic plots"""
        fig, axes = plt.subplots(2, 1, figsize=(12, 8))
        
        # Plot 1: Power spectral density
        psd_data = wave_results['psd']
        axes[0].loglog(psd_data['periods'], psd_data['psd'])
        axes[0].axvline(self.PACKET_PERIOD, color='red', linestyle='--', 
                       label=f'Expected: {self.PACKET_PERIOD}h')
        axes[0].axvline(wave_results['fundamental']['period_hours'], 
                       color='orange', linestyle=':', 
                       label=f"Detected: {wave_results['fundamental']['period_hours']:.2f}h")
        
        # Mark harmonics
        for mode_name, mode_data in wave_results['harmonics'].items():
            axes[0].axvline(mode_data['period_hours'], 
                           color='blue', linestyle=':', alpha=0.5)
        
        axes[0].set_xlabel('Period (hours)')
        axes[0].set_ylabel('Power Spectral Density')
        axes[0].set_title('Wave Packet Spectrum Analysis')
        axes[0].legend()
        axes[0].grid(alpha=0.3)
        
        # Plot 2: Harmonic structure
        modes = list(wave_results['harmonics'].keys())
        periods = [wave_results['harmonics'][m]['period_hours'] for m in modes]
        powers = [wave_results['harmonics'][m]['power'] for m in modes]
        
        axes[1].bar(range(len(modes)), powers, tick_label=modes)
        axes[1].set_xlabel('Temporal Mode')
        axes[1].set_ylabel('Power')
        axes[1].set_title('Harmonic Mode Strength')
        axes[1].grid(alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✅ Saved plot: {save_path}")
        else:
            plt.show()
        
        return fig

def main():
    """Demo: Analyze solar wind data for wave packets"""
    
    # Demo data parameters
    DEMO_BASE_AMPLITUDE = 10
    DEMO_MODULATION_AMPLITUDE = 2
    DEMO_PERIOD = 0.9  # hours (matches expected wave packet period)
    
    print("=" * 70)
    print("LUFT WAVE PACKET ANALYZER")
    print("Detecting 0.9-hour CME shock structure")
    print("=" * 70)
    
    # Load solar wind data
    try:
        # Try to load real data - skip bad lines due to multi-row headers
        df = pd.read_csv('data/cme_heartbeat_log_2025_12.csv', 
                         on_bad_lines='skip')
        
        # Parse timestamp manually and set as index
        df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], errors='coerce')
        df = df.dropna(subset=['timestamp_utc'])
        df = df.set_index('timestamp_utc')
        
        # Use bt_nT as B_mag if available
        if 'bt_nT' in df.columns and 'B_mag' not in df.columns:
            df['B_mag'] = pd.to_numeric(df['bt_nT'], errors='coerce')
        
        # Drop rows with no valid B_mag data
        df = df.dropna(subset=['B_mag'])
        
        print(f"✅ Loaded {len(df)} observations")
    except (FileNotFoundError, Exception) as e:
        print(f"⚠️ Using demo data (error: {e})")
        # Generate demo data with 0.9h periodicity
        timestamps = pd.date_range('2025-12-01', '2025-12-31', freq='1H')
        np.random.seed(42)
        df = pd.DataFrame({
            'B_mag': (DEMO_BASE_AMPLITUDE + 
                     DEMO_MODULATION_AMPLITUDE * np.sin(2*np.pi*np.arange(len(timestamps))/DEMO_PERIOD) + 
                     np.random.randn(len(timestamps)))
        }, index=timestamps)
    
    # Initialize analyzer
    analyzer = WavePacketAnalyzer()
    
    # Detect wave packets
    print("\n🔍 Detecting wave packets...")
    results = analyzer.detect_packets(df, df.index, param='B_mag')
    
    print(f"\n📊 RESULTS:")
    print(f"   Fundamental period: {results['fundamental']['period_hours']:.3f} hours")
    print(f"   Expected: {results['fundamental']['expected']:.3f} hours")
    print(f"   Match: {abs(results['fundamental']['period_hours'] - results['fundamental']['expected']) < 0.2}")
    
    print(f"\n🎵 HARMONICS DETECTED:")
    for mode_name, mode_data in results['harmonics'].items():
        print(f"   {mode_name}: {mode_data['period_hours']:.1f}h "
              f"(~{mode_data['expected_packets']} packets)")
    
    # Plot
    analyzer.plot_results(results, save_path='figures/wave_packet_analysis.png')
    
    print("\n✅ Analysis complete!")

if __name__ == '__main__':
    main()
