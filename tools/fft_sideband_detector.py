#!/usr/bin/env python3
"""
FFT Sideband Detector for χ-Timeseries Analysis

This script performs Fast Fourier Transform (FFT) analysis on χ-timeseries data
to detect amplitude modulation signatures through sideband analysis.

Author: CarlDeanClineSr
Created: 2025-12-25
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from scipy.fft import fft, fftfreq, rfft, rfftfreq
from scipy.signal import find_peaks, welch, butter, filtfilt
import argparse
import json
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class FFTSidebandDetector:
    """
    A class for detecting amplitude modulation sidebands in χ-timeseries data
    using FFT analysis.
    """
    
    def __init__(self, sampling_rate: float = 1.0, window: str = 'hann'):
        """
        Initialize the FFT Sideband Detector.
        
        Parameters:
        -----------
        sampling_rate : float
            Sampling rate of the timeseries data (Hz)
        window : str
            Window function for FFT analysis ('hann', 'hamming', 'blackman', etc.)
        """
        self.sampling_rate = sampling_rate
        self.window = window
        self.timeseries = None
        self.frequencies = None
        self.fft_magnitude = None
        self.fft_phase = None
        self.sidebands = []
        self.carrier_frequency = None
        self.modulation_frequency = None
        
    def load_data(self, data: np.ndarray, time: Optional[np.ndarray] = None):
        """
        Load χ-timeseries data for analysis.
        
        Parameters:
        -----------
        data : np.ndarray
            The χ-timeseries data
        time : np.ndarray, optional
            Time array corresponding to data
        """
        self.timeseries = np.array(data)
        
        if time is not None:
            # Calculate sampling rate from time array
            dt = np.mean(np.diff(time))
            self.sampling_rate = 1.0 / dt
            
        # Remove DC component
        self.timeseries = self.timeseries - np.mean(self.timeseries)
        
    def compute_fft(self, use_window: bool = True, zero_padding: int = 0):
        """
        Compute the Fast Fourier Transform of the timeseries.
        
        Parameters:
        -----------
        use_window : bool
            Whether to apply window function
        zero_padding : int
            Number of zeros to pad (improves frequency resolution)
        """
        n = len(self.timeseries)
        
        # Apply window function
        if use_window:
            if self.window == 'hann':
                window_func = np.hanning(n)
            elif self.window == 'hamming':
                window_func = np.hamming(n)
            elif self.window == 'blackman':
                window_func = np.blackman(n)
            else:
                window_func = np.ones(n)
                
            windowed_data = self.timeseries * window_func
        else:
            windowed_data = self.timeseries
            
        # Apply zero padding
        if zero_padding > 0:
            windowed_data = np.pad(windowed_data, (0, zero_padding), mode='constant')
            
        # Compute FFT (using rfft for real-valued input)
        fft_complex = rfft(windowed_data)
        self.frequencies = rfftfreq(len(windowed_data), 1.0 / self.sampling_rate)
        
        # Store magnitude and phase
        self.fft_magnitude = np.abs(fft_complex)
        self.fft_phase = np.angle(fft_complex)
        
        # Normalize magnitude
        self.fft_magnitude = self.fft_magnitude / (len(windowed_data) / 2)
        
    def detect_carrier(self, freq_range: Optional[Tuple[float, float]] = None,
                      prominence: float = None) -> float:
        """
        Detect the carrier frequency (dominant peak in spectrum).
        
        Parameters:
        -----------
        freq_range : tuple, optional
            (min_freq, max_freq) to search for carrier
        prominence : float, optional
            Minimum prominence for peak detection
            
        Returns:
        --------
        float : Detected carrier frequency
        """
        if self.fft_magnitude is None:
            raise ValueError("Must run compute_fft() first")
            
        # Define search range
        if freq_range is not None:
            mask = (self.frequencies >= freq_range[0]) & (self.frequencies <= freq_range[1])
            search_freqs = self.frequencies[mask]
            search_magnitude = self.fft_magnitude[mask]
        else:
            search_freqs = self.frequencies
            search_magnitude = self.fft_magnitude
            
        # Find peaks
        if prominence is None:
            prominence = np.max(search_magnitude) * 0.1
            
        peaks, properties = find_peaks(search_magnitude, prominence=prominence)
        
        if len(peaks) == 0:
            # No peaks found, use maximum
            carrier_idx = np.argmax(search_magnitude)
        else:
            # Use highest peak
            carrier_idx = peaks[np.argmax(search_magnitude[peaks])]
            
        self.carrier_frequency = search_freqs[carrier_idx]
        
        return self.carrier_frequency
        
    def detect_sidebands(self, carrier_freq: Optional[float] = None,
                        sideband_threshold: float = 0.05,
                        max_modulation_freq: float = None) -> List[Dict]:
        """
        Detect amplitude modulation sidebands around the carrier frequency.
        
        Parameters:
        -----------
        carrier_freq : float, optional
            Carrier frequency (auto-detected if None)
        sideband_threshold : float
            Minimum relative amplitude for sideband detection (fraction of carrier)
        max_modulation_freq : float, optional
            Maximum modulation frequency to search
            
        Returns:
        --------
        List[Dict] : List of detected sidebands with their properties
        """
        if self.fft_magnitude is None:
            raise ValueError("Must run compute_fft() first")
            
        if carrier_freq is None:
            if self.carrier_frequency is None:
                carrier_freq = self.detect_carrier()
            else:
                carrier_freq = self.carrier_frequency
        else:
            self.carrier_frequency = carrier_freq
            
        # Get carrier amplitude
        carrier_idx = np.argmin(np.abs(self.frequencies - carrier_freq))
        carrier_amplitude = self.fft_magnitude[carrier_idx]
        
        # Set maximum modulation frequency
        if max_modulation_freq is None:
            max_modulation_freq = carrier_freq * 0.5
            
        # Define search range for sidebands
        lower_bound = max(0, carrier_freq - max_modulation_freq)
        upper_bound = carrier_freq + max_modulation_freq
        
        mask = (self.frequencies >= lower_bound) & (self.frequencies <= upper_bound)
        search_freqs = self.frequencies[mask]
        search_magnitude = self.fft_magnitude[mask]
        
        # Find all peaks above threshold
        threshold_amplitude = carrier_amplitude * sideband_threshold
        peaks, properties = find_peaks(search_magnitude, 
                                      height=threshold_amplitude,
                                      prominence=threshold_amplitude * 0.5)
        
        # Analyze sidebands
        self.sidebands = []
        
        for peak_idx in peaks:
            peak_freq = search_freqs[peak_idx]
            peak_amplitude = search_magnitude[peak_idx]
            
            # Skip if this is the carrier itself
            if np.abs(peak_freq - carrier_freq) < (self.frequencies[1] - self.frequencies[0]):
                continue
                
            # Calculate modulation frequency
            mod_freq = abs(peak_freq - carrier_freq)
            
            # Determine if lower or upper sideband
            sideband_type = 'upper' if peak_freq > carrier_freq else 'lower'
            
            # Calculate modulation index (amplitude ratio)
            modulation_index = peak_amplitude / carrier_amplitude
            
            sideband_info = {
                'frequency': peak_freq,
                'amplitude': peak_amplitude,
                'modulation_frequency': mod_freq,
                'type': sideband_type,
                'modulation_index': modulation_index,
                'relative_amplitude_db': 20 * np.log10(modulation_index)
            }
            
            self.sidebands.append(sideband_info)
            
        # Sort sidebands by modulation frequency
        self.sidebands = sorted(self.sidebands, key=lambda x: x['modulation_frequency'])
        
        return self.sidebands
        
    def find_sideband_pairs(self, freq_tolerance: float = None) -> List[Dict]:
        """
        Find matching upper and lower sideband pairs.
        
        Parameters:
        -----------
        freq_tolerance : float, optional
            Maximum frequency difference for matching pairs
            
        Returns:
        --------
        List[Dict] : Matched sideband pairs
        """
        if len(self.sidebands) == 0:
            return []
            
        if freq_tolerance is None:
            freq_tolerance = self.frequencies[1] - self.frequencies[0]
            
        lower_sidebands = [sb for sb in self.sidebands if sb['type'] == 'lower']
        upper_sidebands = [sb for sb in self.sidebands if sb['type'] == 'upper']
        
        pairs = []
        
        for lower_sb in lower_sidebands:
            for upper_sb in upper_sidebands:
                freq_diff = abs(lower_sb['modulation_frequency'] - 
                              upper_sb['modulation_frequency'])
                
                if freq_diff < freq_tolerance:
                    # Found a matching pair
                    avg_mod_freq = (lower_sb['modulation_frequency'] + 
                                   upper_sb['modulation_frequency']) / 2
                    
                    avg_mod_index = (lower_sb['modulation_index'] + 
                                    upper_sb['modulation_index']) / 2
                    
                    amplitude_asymmetry = abs(lower_sb['amplitude'] - 
                                             upper_sb['amplitude']) / \
                                         ((lower_sb['amplitude'] + 
                                           upper_sb['amplitude']) / 2)
                    
                    pair_info = {
                        'modulation_frequency': avg_mod_freq,
                        'lower_sideband': lower_sb,
                        'upper_sideband': upper_sb,
                        'avg_modulation_index': avg_mod_index,
                        'amplitude_asymmetry': amplitude_asymmetry
                    }
                    
                    pairs.append(pair_info)
                    
        return pairs
        
    def compute_spectrogram(self, nperseg: int = 256, noverlap: Optional[int] = None):
        """
        Compute spectrogram for time-frequency analysis.
        
        Parameters:
        -----------
        nperseg : int
            Length of each segment
        noverlap : int, optional
            Number of points to overlap
            
        Returns:
        --------
        tuple : (frequencies, times, spectrogram)
        """
        if self.timeseries is None:
            raise ValueError("Must load data first")
            
        if noverlap is None:
            noverlap = nperseg // 2
            
        f, t, Sxx = signal.spectrogram(self.timeseries, 
                                       fs=self.sampling_rate,
                                       nperseg=nperseg,
                                       noverlap=noverlap,
                                       window=self.window)
        
        return f, t, Sxx
        
    def compute_welch_psd(self, nperseg: int = 256):
        """
        Compute power spectral density using Welch's method.
        
        Parameters:
        -----------
        nperseg : int
            Length of each segment
            
        Returns:
        --------
        tuple : (frequencies, psd)
        """
        if self.timeseries is None:
            raise ValueError("Must load data first")
            
        f, psd = welch(self.timeseries, 
                      fs=self.sampling_rate,
                      nperseg=nperseg,
                      window=self.window)
        
        return f, psd
        
    def plot_spectrum(self, freq_range: Optional[Tuple[float, float]] = None,
                     log_scale: bool = True, show_sidebands: bool = True,
                     filename: Optional[str] = None):
        """
        Plot the frequency spectrum with detected sidebands.
        
        Parameters:
        -----------
        freq_range : tuple, optional
            (min_freq, max_freq) to display
        log_scale : bool
            Use logarithmic scale for amplitude
        show_sidebands : bool
            Annotate detected sidebands
        filename : str, optional
            Save plot to file
        """
        if self.fft_magnitude is None:
            raise ValueError("Must run compute_fft() first")
            
        plt.figure(figsize=(12, 6))
        
        if log_scale:
            plt.semilogy(self.frequencies, self.fft_magnitude, 'b-', alpha=0.7, linewidth=1)
            plt.ylabel('Amplitude (log scale)')
        else:
            plt.plot(self.frequencies, self.fft_magnitude, 'b-', alpha=0.7, linewidth=1)
            plt.ylabel('Amplitude')
            
        # Mark carrier frequency
        if self.carrier_frequency is not None:
            plt.axvline(self.carrier_frequency, color='r', linestyle='--', 
                       linewidth=2, label=f'Carrier: {self.carrier_frequency:.4f} Hz')
            
        # Mark sidebands
        if show_sidebands and len(self.sidebands) > 0:
            for sb in self.sidebands:
                color = 'g' if sb['type'] == 'upper' else 'm'
                plt.axvline(sb['frequency'], color=color, linestyle=':', 
                           alpha=0.6, linewidth=1.5)
                
                # Annotate
                plt.annotate(f"{sb['type'][0].upper()}: Δf={sb['modulation_frequency']:.4f}",
                           xy=(sb['frequency'], sb['amplitude']),
                           xytext=(10, 10), textcoords='offset points',
                           fontsize=8, color=color,
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))
                           
        plt.xlabel('Frequency (Hz)')
        plt.title('FFT Spectrum with Sideband Detection')
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        if freq_range is not None:
            plt.xlim(freq_range)
            
        plt.tight_layout()
        
        if filename:
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"Spectrum plot saved to: {filename}")
        else:
            plt.show()
            
    def plot_spectrogram(self, nperseg: int = 256, 
                        freq_range: Optional[Tuple[float, float]] = None,
                        filename: Optional[str] = None):
        """
        Plot spectrogram showing time-frequency evolution.
        
        Parameters:
        -----------
        nperseg : int
            Length of each segment
        freq_range : tuple, optional
            (min_freq, max_freq) to display
        filename : str, optional
            Save plot to file
        """
        f, t, Sxx = self.compute_spectrogram(nperseg=nperseg)
        
        plt.figure(figsize=(12, 6))
        plt.pcolormesh(t, f, 10 * np.log10(Sxx + 1e-10), shading='gouraud', cmap='viridis')
        plt.ylabel('Frequency (Hz)')
        plt.xlabel('Time (s)')
        plt.title('Spectrogram - Time-Frequency Analysis')
        plt.colorbar(label='Power (dB)')
        
        if freq_range is not None:
            plt.ylim(freq_range)
            
        # Mark carrier if detected
        if self.carrier_frequency is not None:
            plt.axhline(self.carrier_frequency, color='r', linestyle='--', 
                       alpha=0.5, linewidth=2, label='Carrier')
            plt.legend()
            
        plt.tight_layout()
        
        if filename:
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"Spectrogram saved to: {filename}")
        else:
            plt.show()
            
    def plot_sideband_summary(self, filename: Optional[str] = None):
        """
        Create a comprehensive summary plot of sideband analysis.
        
        Parameters:
        -----------
        filename : str, optional
            Save plot to file
        """
        if len(self.sidebands) == 0:
            print("No sidebands detected to plot")
            return
            
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Plot 1: Spectrum with sidebands
        ax1 = axes[0, 0]
        ax1.semilogy(self.frequencies, self.fft_magnitude, 'b-', alpha=0.7, linewidth=1)
        ax1.axvline(self.carrier_frequency, color='r', linestyle='--', linewidth=2)
        for sb in self.sidebands:
            color = 'g' if sb['type'] == 'upper' else 'm'
            ax1.axvline(sb['frequency'], color=color, linestyle=':', alpha=0.6)
        ax1.set_xlabel('Frequency (Hz)')
        ax1.set_ylabel('Amplitude (log scale)')
        ax1.set_title('Full Spectrum')
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Zoomed spectrum around carrier
        ax2 = axes[0, 1]
        if len(self.sidebands) > 0:
            max_mod_freq = max([sb['modulation_frequency'] for sb in self.sidebands])
            zoom_range = (self.carrier_frequency - 2*max_mod_freq, 
                         self.carrier_frequency + 2*max_mod_freq)
            mask = (self.frequencies >= zoom_range[0]) & (self.frequencies <= zoom_range[1])
            ax2.plot(self.frequencies[mask], self.fft_magnitude[mask], 'b-', linewidth=1.5)
            ax2.axvline(self.carrier_frequency, color='r', linestyle='--', linewidth=2)
            for sb in self.sidebands:
                color = 'g' if sb['type'] == 'upper' else 'm'
                ax2.axvline(sb['frequency'], color=color, linestyle=':', linewidth=2)
        ax2.set_xlabel('Frequency (Hz)')
        ax2.set_ylabel('Amplitude')
        ax2.set_title('Zoomed View Around Carrier')
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Modulation frequency distribution
        ax3 = axes[1, 0]
        mod_freqs = [sb['modulation_frequency'] for sb in self.sidebands]
        mod_indices = [sb['modulation_index'] for sb in self.sidebands]
        colors = ['g' if sb['type'] == 'upper' else 'm' for sb in self.sidebands]
        ax3.bar(range(len(mod_freqs)), mod_indices, color=colors, alpha=0.7)
        ax3.set_xlabel('Sideband Index')
        ax3.set_ylabel('Modulation Index')
        ax3.set_title('Modulation Index Distribution')
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Sideband table
        ax4 = axes[1, 1]
        ax4.axis('tight')
        ax4.axis('off')
        
        table_data = [['Type', 'Freq (Hz)', 'Mod Freq', 'Index', 'Amp (dB)']]
        for sb in self.sidebands[:10]:  # Limit to first 10
            table_data.append([
                sb['type'][0].upper(),
                f"{sb['frequency']:.4f}",
                f"{sb['modulation_frequency']:.4f}",
                f"{sb['modulation_index']:.4f}",
                f"{sb['relative_amplitude_db']:.2f}"
            ])
            
        table = ax4.table(cellText=table_data, cellLoc='center', loc='center',
                         colWidths=[0.15, 0.2, 0.2, 0.2, 0.25])
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 1.5)
        
        # Color header row
        for i in range(5):
            table[(0, i)].set_facecolor('#4CAF50')
            table[(0, i)].set_text_props(weight='bold', color='white')
            
        plt.suptitle(f'FFT Sideband Analysis Summary\nCarrier: {self.carrier_frequency:.4f} Hz, '
                    f'Detected Sidebands: {len(self.sidebands)}', 
                    fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        
        if filename:
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"Summary plot saved to: {filename}")
        else:
            plt.show()
            
    def generate_report(self, filename: Optional[str] = None) -> Dict:
        """
        Generate a comprehensive analysis report.
        
        Parameters:
        -----------
        filename : str, optional
            Save report to JSON file
            
        Returns:
        --------
        Dict : Analysis report
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'analysis_parameters': {
                'sampling_rate': self.sampling_rate,
                'window_function': self.window,
                'data_length': len(self.timeseries) if self.timeseries is not None else 0,
                'frequency_resolution': self.frequencies[1] - self.frequencies[0] if self.frequencies is not None else None
            },
            'carrier_detection': {
                'frequency': self.carrier_frequency,
                'amplitude': float(self.fft_magnitude[np.argmin(np.abs(self.frequencies - self.carrier_frequency))]) if self.carrier_frequency else None
            },
            'sideband_summary': {
                'total_sidebands': len(self.sidebands),
                'upper_sidebands': len([sb for sb in self.sidebands if sb['type'] == 'upper']),
                'lower_sidebands': len([sb for sb in self.sidebands if sb['type'] == 'lower'])
            },
            'sidebands': []
        }
        
        # Add detailed sideband information
        for sb in self.sidebands:
            sb_dict = {k: float(v) if isinstance(v, (np.floating, np.integer)) else v 
                      for k, v in sb.items()}
            report['sidebands'].append(sb_dict)
            
        # Find sideband pairs
        pairs = self.find_sideband_pairs()
        report['sideband_pairs'] = []
        
        for pair in pairs:
            pair_dict = {
                'modulation_frequency': float(pair['modulation_frequency']),
                'avg_modulation_index': float(pair['avg_modulation_index']),
                'amplitude_asymmetry': float(pair['amplitude_asymmetry']),
                'lower_frequency': float(pair['lower_sideband']['frequency']),
                'upper_frequency': float(pair['upper_sideband']['frequency'])
            }
            report['sideband_pairs'].append(pair_dict)
            
        # Calculate statistics
        if len(self.sidebands) > 0:
            mod_freqs = [sb['modulation_frequency'] for sb in self.sidebands]
            mod_indices = [sb['modulation_index'] for sb in self.sidebands]
            
            report['statistics'] = {
                'mean_modulation_frequency': float(np.mean(mod_freqs)),
                'std_modulation_frequency': float(np.std(mod_freqs)),
                'min_modulation_frequency': float(np.min(mod_freqs)),
                'max_modulation_frequency': float(np.max(mod_freqs)),
                'mean_modulation_index': float(np.mean(mod_indices)),
                'max_modulation_index': float(np.max(mod_indices))
            }
            
        # Save to file if requested
        if filename:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"Report saved to: {filename}")
            
        return report
        
    def print_summary(self):
        """Print a text summary of the analysis results."""
        print("\n" + "="*70)
        print("FFT SIDEBAND DETECTION SUMMARY")
        print("="*70)
        
        if self.carrier_frequency is not None:
            print(f"\nCarrier Frequency: {self.carrier_frequency:.6f} Hz")
            carrier_idx = np.argmin(np.abs(self.frequencies - self.carrier_frequency))
            print(f"Carrier Amplitude: {self.fft_magnitude[carrier_idx]:.6e}")
            
        print(f"\nTotal Sidebands Detected: {len(self.sidebands)}")
        print(f"  - Upper Sidebands: {len([sb for sb in self.sidebands if sb['type'] == 'upper'])}")
        print(f"  - Lower Sidebands: {len([sb for sb in self.sidebands if sb['type'] == 'lower'])}")
        
        if len(self.sidebands) > 0:
            print("\nTop 5 Sidebands:")
            print("-" * 70)
            print(f"{'Type':<8} {'Freq (Hz)':<15} {'Mod Freq':<15} {'Index':<12} {'dB':<10}")
            print("-" * 70)
            
            sorted_sidebands = sorted(self.sidebands, 
                                     key=lambda x: x['modulation_index'], 
                                     reverse=True)
            
            for sb in sorted_sidebands[:5]:
                print(f"{sb['type']:<8} {sb['frequency']:<15.6f} "
                      f"{sb['modulation_frequency']:<15.6f} "
                      f"{sb['modulation_index']:<12.6f} "
                      f"{sb['relative_amplitude_db']:<10.2f}")
                      
            # Find and display pairs
            pairs = self.find_sideband_pairs()
            if len(pairs) > 0:
                print(f"\nMatched Sideband Pairs: {len(pairs)}")
                print("-" * 70)
                print(f"{'Mod Freq':<15} {'Avg Index':<15} {'Asymmetry':<15}")
                print("-" * 70)
                
                for pair in pairs[:5]:
                    print(f"{pair['modulation_frequency']:<15.6f} "
                          f"{pair['avg_modulation_index']:<15.6f} "
                          f"{pair['amplitude_asymmetry']:<15.4f}")
                          
        print("\n" + "="*70 + "\n")


def load_chi_timeseries(filename: str) -> Tuple[np.ndarray, Optional[np.ndarray]]:
    """
    Load χ-timeseries data from various file formats.
    
    Parameters:
    -----------
    filename : str
        Path to data file
        
    Returns:
    --------
    tuple : (data, time_array)
    """
    ext = os.path.splitext(filename)[1].lower()
    
    if ext == '.npy':
        data = np.load(filename)
        if data.ndim == 2 and data.shape[1] == 2:
            return data[:, 1], data[:, 0]
        else:
            return data, None
            
    elif ext in ['.txt', '.dat', '.csv']:
        data = np.loadtxt(filename)
        if data.ndim == 2 and data.shape[1] >= 2:
            return data[:, 1], data[:, 0]
        else:
            return data, None
            
    elif ext == '.json':
        with open(filename, 'r') as f:
            json_data = json.load(f)
        if isinstance(json_data, dict):
            data = np.array(json_data.get('data', json_data.get('chi', [])))
            time = np.array(json_data.get('time', [])) if 'time' in json_data else None
            return data, time
        else:
            return np.array(json_data), None
            
    else:
        raise ValueError(f"Unsupported file format: {ext}")


def main():
    """Main function for command-line interface."""
    parser = argparse.ArgumentParser(
        description='FFT Sideband Detector for χ-Timeseries Analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic analysis
  python fft_sideband_detector.py data.txt --sampling-rate 1000
  
  # With custom parameters
  python fft_sideband_detector.py data.npy -sr 500 --window hamming --threshold 0.03
  
  # Generate all outputs
  python fft_sideband_detector.py data.csv -sr 1000 --plot-all --save-report
        """
    )
    
    parser.add_argument('input', type=str,
                       help='Input χ-timeseries data file')
    parser.add_argument('-sr', '--sampling-rate', type=float, required=True,
                       help='Sampling rate in Hz')
    parser.add_argument('-w', '--window', type=str, default='hann',
                       choices=['hann', 'hamming', 'blackman', 'bartlett'],
                       help='Window function for FFT')
    parser.add_argument('-zp', '--zero-padding', type=int, default=0,
                       help='Zero padding factor')
    parser.add_argument('--carrier-range', type=float, nargs=2, metavar=('MIN', 'MAX'),
                       help='Frequency range for carrier detection')
    parser.add_argument('-t', '--threshold', type=float, default=0.05,
                       help='Sideband detection threshold (fraction of carrier)')
    parser.add_argument('--max-mod-freq', type=float,
                       help='Maximum modulation frequency to search')
    parser.add_argument('--freq-range', type=float, nargs=2, metavar=('MIN', 'MAX'),
                       help='Frequency range for plotting')
    parser.add_argument('--plot-spectrum', action='store_true',
                       help='Plot frequency spectrum')
    parser.add_argument('--plot-spectrogram', action='store_true',
                       help='Plot spectrogram')
    parser.add_argument('--plot-summary', action='store_true',
                       help='Plot comprehensive summary')
    parser.add_argument('--plot-all', action='store_true',
                       help='Generate all plots')
    parser.add_argument('--save-report', action='store_true',
                       help='Save JSON report')
    parser.add_argument('-o', '--output-dir', type=str, default='.',
                       help='Output directory for plots and reports')
    parser.add_argument('--no-show', action='store_true',
                       help='Don\'t display plots (only save)')
    
    args = parser.parse_args()
    
    # Create output directory if needed
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
        
    # Generate base filename for outputs
    base_name = os.path.splitext(os.path.basename(args.input))[0]
    
    print(f"\nLoading data from: {args.input}")
    data, time = load_chi_timeseries(args.input)
    print(f"Data loaded: {len(data)} samples")
    
    # Initialize detector
    detector = FFTSidebandDetector(sampling_rate=args.sampling_rate, 
                                   window=args.window)
    
    # Load data
    detector.load_data(data, time)
    
    # Compute FFT
    print(f"\nComputing FFT with {args.window} window...")
    detector.compute_fft(use_window=True, zero_padding=args.zero_padding)
    
    # Detect carrier
    print("Detecting carrier frequency...")
    carrier_range = tuple(args.carrier_range) if args.carrier_range else None
    detector.detect_carrier(freq_range=carrier_range)
    
    # Detect sidebands
    print("Detecting amplitude modulation sidebands...")
    detector.detect_sidebands(sideband_threshold=args.threshold,
                             max_modulation_freq=args.max_mod_freq)
    
    # Print summary
    detector.print_summary()
    
    # Generate plots
    freq_range = tuple(args.freq_range) if args.freq_range else None
    
    if args.plot_all or args.plot_spectrum:
        spectrum_file = os.path.join(args.output_dir, f'{base_name}_spectrum.png')
        detector.plot_spectrum(freq_range=freq_range, 
                              filename=spectrum_file if args.no_show else None)
        if not args.no_show:
            detector.plot_spectrum(freq_range=freq_range)
            
    if args.plot_all or args.plot_spectrogram:
        spectrogram_file = os.path.join(args.output_dir, f'{base_name}_spectrogram.png')
        detector.plot_spectrogram(freq_range=freq_range,
                                 filename=spectrogram_file if args.no_show else None)
        if not args.no_show:
            detector.plot_spectrogram(freq_range=freq_range)
            
    if args.plot_all or args.plot_summary:
        summary_file = os.path.join(args.output_dir, f'{base_name}_summary.png')
        detector.plot_sideband_summary(filename=summary_file if args.no_show else None)
        if not args.no_show:
            detector.plot_sideband_summary()
            
    # Generate report
    if args.save_report or args.plot_all:
        report_file = os.path.join(args.output_dir, f'{base_name}_report.json')
        detector.generate_report(filename=report_file)
        
    print("\nAnalysis complete!")


if __name__ == '__main__':
    main()
