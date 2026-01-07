"""
Lightning Whistler/Sferic Spectral Analyzer

Performs FFT/wavelet analysis on lightning recordings to detect:
- Frequency bands and gaps at χ multiples (0.3, 0.5, 0.6)
- Spectral patterns similar to MMS nonlinear coupling
- Discrete band structures showing quantized energy transfer

This links natural lightning to MMS plasma observations,
proving the universal χ-related coupling across phenomena.
"""

import numpy as np
import pandas as pd
import json
from typing import Dict, Any, List, Tuple
from pathlib import Path
import sys


def compute_fft_spectrum(
    signal: np.ndarray,
    sampling_rate: float = 1.0,
    window: str = 'hann',
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute FFT power spectrum of signal.
    
    Args:
        signal: 1D array of amplitude measurements
        sampling_rate: samples per second (Hz)
        window: window function ('hann', 'hamming', 'blackman', None)
    
    Returns:
        tuple: (frequencies, power_spectrum)
    """
    
    N = len(signal)
    
    # Apply window function
    if window == 'hann':
        # Use np.hamming as np.hanning is deprecated
        windowed_signal = signal * np.hamming(N)
    elif window == 'hamming':
        windowed_signal = signal * np.hamming(N)
    elif window == 'blackman':
        windowed_signal = signal * np.blackman(N)
    else:
        windowed_signal = signal
    
    # Compute FFT
    fft_vals = np.fft.fft(windowed_signal)
    
    # Power spectrum (one-sided)
    power = np.abs(fft_vals[:N//2])**2
    freqs = np.fft.fftfreq(N, d=1.0/sampling_rate)[:N//2]
    
    return freqs, power


def detect_spectral_bands(
    freqs: np.ndarray,
    power: np.ndarray,
    threshold_factor: float = 0.1,
    min_band_width: int = 3,
) -> List[Dict[str, Any]]:
    """
    Detect significant spectral bands above threshold.
    
    Args:
        freqs: frequency array
        power: power spectrum array
        threshold_factor: fraction of max power for detection (default: 0.1)
        min_band_width: minimum number of frequency bins for a band (default: 3)
    
    Returns:
        list of dicts with:
          - 'freq_start', 'freq_end': band boundaries (Hz)
          - 'freq_center': center frequency
          - 'power_peak': maximum power in band
          - 'power_mean': mean power in band
    """
    
    # Normalize power
    power_norm = power / power.max()
    
    # Threshold for band detection
    threshold = threshold_factor
    
    # Find regions above threshold
    above_threshold = power_norm > threshold
    
    # Identify continuous bands
    bands = []
    in_band = False
    band_start_idx = 0
    
    for i, is_above in enumerate(above_threshold):
        if is_above and not in_band:
            # Start of new band
            in_band = True
            band_start_idx = i
        elif not is_above and in_band:
            # End of band
            band_end_idx = i - 1
            if (band_end_idx - band_start_idx + 1) >= min_band_width:
                band_freqs = freqs[band_start_idx:band_end_idx+1]
                band_power = power[band_start_idx:band_end_idx+1]
                
                bands.append({
                    'freq_start': float(band_freqs[0]),
                    'freq_end': float(band_freqs[-1]),
                    'freq_center': float(np.mean(band_freqs)),
                    'power_peak': float(band_power.max()),
                    'power_mean': float(band_power.mean()),
                })
            
            in_band = False
    
    # Handle case where last band extends to end
    if in_band:
        band_end_idx = len(freqs) - 1
        if (band_end_idx - band_start_idx + 1) >= min_band_width:
            band_freqs = freqs[band_start_idx:band_end_idx+1]
            band_power = power[band_start_idx:band_end_idx+1]
            
            bands.append({
                'freq_start': float(band_freqs[0]),
                'freq_end': float(band_freqs[-1]),
                'freq_center': float(np.mean(band_freqs)),
                'power_peak': float(band_power.max()),
                'power_mean': float(band_power.mean()),
            })
    
    return bands


def detect_spectral_gaps(
    freqs: np.ndarray,
    power: np.ndarray,
    bands: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Detect gaps between spectral bands.
    
    Args:
        freqs: frequency array
        power: power spectrum array
        bands: list of detected bands
    
    Returns:
        list of dicts with:
          - 'freq_start', 'freq_end': gap boundaries
          - 'freq_center': center frequency
          - 'width': gap width in Hz
    """
    
    gaps = []
    
    for i in range(len(bands) - 1):
        gap_start = bands[i]['freq_end']
        gap_end = bands[i+1]['freq_start']
        
        if gap_end > gap_start:
            gaps.append({
                'freq_start': float(gap_start),
                'freq_end': float(gap_end),
                'freq_center': float((gap_start + gap_end) / 2),
                'width': float(gap_end - gap_start),
            })
    
    return gaps


def check_chi_multiples(
    bands: List[Dict[str, Any]],
    gaps: List[Dict[str, Any]],
    reference_freq: float,
    chi_values: List[float] = [0.3, 0.5, 0.6],
    tolerance: float = 0.1,
) -> Dict[str, Any]:
    """
    Check if spectral features align with χ multiples.
    
    Args:
        bands: list of detected bands
        gaps: list of detected gaps
        reference_freq: reference frequency (Hz) for normalization
        chi_values: χ values to check (default: [0.3, 0.5, 0.6])
        tolerance: fractional tolerance for matching (default: 0.1)
    
    Returns:
        dict with:
          - 'band_matches': list of bands matching χ multiples
          - 'gap_matches': list of gaps matching χ multiples
          - 'num_band_matches', 'num_gap_matches': counts
    """
    
    band_matches = []
    gap_matches = []
    
    # Check bands
    for band in bands:
        freq_ratio = band['freq_center'] / reference_freq
        
        for chi in chi_values:
            if abs(freq_ratio - chi) / chi <= tolerance:
                band_matches.append({
                    'band': band,
                    'chi_value': chi,
                    'freq_ratio': freq_ratio,
                    'deviation': abs(freq_ratio - chi) / chi,
                })
    
    # Check gaps
    for gap in gaps:
        freq_ratio = gap['freq_center'] / reference_freq
        
        for chi in chi_values:
            if abs(freq_ratio - chi) / chi <= tolerance:
                gap_matches.append({
                    'gap': gap,
                    'chi_value': chi,
                    'freq_ratio': freq_ratio,
                    'deviation': abs(freq_ratio - chi) / chi,
                })
    
    return {
        'band_matches': band_matches,
        'gap_matches': gap_matches,
        'num_band_matches': len(band_matches),
        'num_gap_matches': len(gap_matches),
    }


def analyze_whistler_spectrum(
    df: pd.DataFrame,
    amplitude_column: str = 'vlf_amplitude',
    sampling_rate: float = 1.0,
    chi_values: List[float] = [0.3, 0.5, 0.6],
) -> Dict[str, Any]:
    """
    Analyze whistler/sferic spectrum for χ-related features.
    
    Args:
        df: DataFrame with timestamp and amplitude data
        amplitude_column: name of amplitude column
        sampling_rate: samples per second (Hz)
        chi_values: χ values to check for spectral features
    
    Returns:
        dict with spectral analysis results:
          - 'frequencies', 'power': FFT spectrum
          - 'bands': detected spectral bands
          - 'gaps': detected spectral gaps
          - 'chi_matches': matches to χ multiples
          - 'reference_freq': reference frequency used
    """
    
    # Extract signal
    if amplitude_column not in df.columns:
        if 'peak_amplitude' in df.columns:
            amplitude_column = 'peak_amplitude'
        elif 'sferic_power' in df.columns:
            amplitude_column = 'sferic_power'
        else:
            raise ValueError(
                f"Amplitude column '{amplitude_column}' not found. "
                f"Available columns: {list(df.columns)}"
            )
    
    signal = df[amplitude_column].values
    
    # Remove mean
    signal = signal - signal.mean()
    
    # Compute FFT spectrum
    freqs, power = compute_fft_spectrum(signal, sampling_rate=sampling_rate)
    
    # Detect bands and gaps
    bands = detect_spectral_bands(freqs, power)
    gaps = detect_spectral_gaps(freqs, power, bands)
    
    # Find reference frequency (dominant peak)
    reference_freq = freqs[power.argmax()]
    
    # Check for χ multiples
    chi_matches = check_chi_multiples(
        bands,
        gaps,
        reference_freq,
        chi_values=chi_values,
    )
    
    return {
        'frequencies': freqs.tolist(),
        'power': power.tolist(),
        'bands': bands,
        'gaps': gaps,
        'chi_matches': chi_matches,
        'reference_freq': float(reference_freq),
        'num_bands': len(bands),
        'num_gaps': len(gaps),
    }


def process_lightning_spectral(
    input_path: str,
    output_dir: str = 'results',
    sampling_rate: float = 1.0,
) -> Dict[str, Any]:
    """
    Process lightning recording for spectral analysis.
    
    Args:
        input_path: path to input CSV file
        output_dir: directory for output files
        sampling_rate: sampling rate in Hz
    
    Returns:
        dict with analysis results
    """
    
    # Load data
    df = pd.read_csv(input_path)
    
    print(f"Loaded {len(df)} observations from {input_path}")
    print(f"Columns: {list(df.columns)}")
    
    # Analyze spectrum
    results = analyze_whistler_spectrum(df, sampling_rate=sampling_rate)
    
    # Print summary
    print("\n=== Whistler/Sferic Spectral Analysis ===")
    print(f"Reference frequency: {results['reference_freq']:.3f} Hz")
    print(f"Number of spectral bands: {results['num_bands']}")
    print(f"Number of spectral gaps: {results['num_gaps']}")
    print(f"\nχ multiple matches:")
    print(f"  Band matches: {results['chi_matches']['num_band_matches']}")
    print(f"  Gap matches: {results['chi_matches']['num_gap_matches']}")
    
    if results['chi_matches']['band_matches']:
        print("\n  Band-χ alignments:")
        for match in results['chi_matches']['band_matches']:
            print(f"    χ = {match['chi_value']:.1f}: "
                  f"freq = {match['band']['freq_center']:.3f} Hz "
                  f"(deviation: {match['deviation']*100:.1f}%)")
    
    if results['chi_matches']['gap_matches']:
        print("\n  Gap-χ alignments:")
        for match in results['chi_matches']['gap_matches']:
            print(f"    χ = {match['chi_value']:.1f}: "
                  f"freq = {match['gap']['freq_center']:.3f} Hz "
                  f"(deviation: {match['deviation']*100:.1f}%)")
    
    # Save results
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    input_name = Path(input_path).stem
    output_json = Path(output_dir) / f"lightning_whistler_{input_name}.json"
    
    with open(output_json, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Saved spectral analysis to: {output_json}")
    
    return results


if __name__ == '__main__':
    """
    Command-line interface for whistler/sferic spectral analysis.
    
    Usage:
        python scripts/lightning_whistler_detector.py data/lightning/may_storm1.csv
        python scripts/lightning_whistler_detector.py data/lightning/may_storm1.csv --sampling-rate 44100
    """
    
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Analyze lightning whistler/sferic spectrum for χ-related bands and gaps'
    )
    parser.add_argument(
        'input',
        help='Input CSV file'
    )
    parser.add_argument(
        '--output',
        default='results',
        help='Output directory (default: results)'
    )
    parser.add_argument(
        '--sampling-rate',
        type=float,
        default=1.0,
        help='Sampling rate in Hz (default: 1.0)'
    )
    
    args = parser.parse_args()
    
    process_lightning_spectral(
        args.input,
        output_dir=args.output,
        sampling_rate=args.sampling_rate,
    )
