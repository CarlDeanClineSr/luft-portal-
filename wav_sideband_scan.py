#!/usr/bin/env python3
"""
wav_sideband_scan.py
====================
Scan LUFT HDSDR .wav files for the 20.55 Hz integrity frequency sideband.

Target: ±20.55 Hz sidebands around the carrier in each file.
If symmetric sidebands are present with error < 5%, the oscillating
lens hypothesis has instrumental support.

Usage:
    python wav_sideband_scan.py --file data/sdr/HDSDR_20250806_135410Z_7468kHz_RF.wav
    python wav_sideband_scan.py --all   # scan all HDSDR files in data/sdr/
"""

import numpy as np
import struct
import json
import glob
import argparse
from pathlib import Path

# LUFT constants
F_RING       = 20.55     # Hz — integrity frequency
CHI_LIMIT    = 0.15      # Universal boundary
SIDEBAND_TOL = 2.0       # Hz — search window around expected sideband
SYM_ERR_MAX  = 0.05      # 5% symmetry error threshold for confirmation

def read_wav_samples(filepath):
    """
    Read raw samples from a WAV file without scipy dependency.
    Returns (samples_array, sample_rate).
    """
    with open(filepath, 'rb') as f:
        # Read RIFF header
        riff = f.read(4)
        if riff != b'RIFF':
            raise ValueError(f"Not a WAV file: {filepath}")
        f.read(4)  # chunk size
        f.read(4)  # WAVE
        f.read(4)  # fmt
        fmt_size = struct.unpack('<I', f.read(4))[0]
        fmt_data = f.read(fmt_size)
        
        audio_fmt  = struct.unpack('<H', fmt_data[0:2])[0]
        n_channels = struct.unpack('<H', fmt_data[2:4])[0]
        sample_rate = struct.unpack('<I', fmt_data[4:8])[0]
        bits        = struct.unpack('<H', fmt_data[14:16])[0]
        
        # Find data chunk
        while True:
            chunk_id = f.read(4)
            if not chunk_id:
                raise ValueError("No data chunk found")
            chunk_size = struct.unpack('<I', f.read(4))[0]
            if chunk_id == b'data':
                raw = f.read(chunk_size)
                break
            f.seek(chunk_size, 1)
        
    # Decode samples
    if bits == 16:
        samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
    elif bits == 8:
        samples = (np.frombuffer(raw, dtype=np.uint8).astype(np.float32) - 128)
    elif bits == 32:
        samples = np.frombuffer(raw, dtype=np.int32).astype(np.float32)
    else:
        raise ValueError(f"Unsupported bit depth: {bits}")
    
    # If stereo, take left channel
    if n_channels == 2:
        samples = samples[::2]
    
    return samples, sample_rate

def compute_envelope(samples, sample_rate, block_size=None):
    """
    Compute amplitude envelope via RMS in sliding blocks.
    This isolates the low-frequency modulation of the RF signal.
    """
    if block_size is None:
        block_size = max(1, int(sample_rate * 0.025))  # 25ms blocks
    
    n_blocks = len(samples) // block_size
    envelope = np.array([
        np.sqrt(np.mean(samples[i*block_size:(i+1)*block_size]**2))
        for i in range(n_blocks)
    ])
    envelope_rate = sample_rate / block_size
    return envelope, envelope_rate

def scan_for_sideband(filepath):
    """
    Full pipeline: load WAV → envelope → FFT → search for 20.55 Hz sideband.
    """
    result = {
        "file": str(filepath),
        "f_ring_target": F_RING,
        "sideband_detected": False,
        "carrier_freq_hz": None,
        "upper_sideband_hz": None,
        "lower_sideband_hz": None,
        "upper_amplitude": None,
        "lower_amplitude": None,
        "symmetry_error": None,
        "confirmed": False,
        "note": ""
    }
    
    try:
        samples, fs = read_wav_samples(filepath)
        result["sample_rate_hz"] = fs
        result["duration_seconds"] = len(samples) / fs
        
        # Get amplitude envelope
        envelope, env_rate = compute_envelope(samples, fs)
        result["envelope_sample_rate"] = env_rate
        
        # Nyquist check
        nyquist = env_rate / 2
        if nyquist < F_RING * 1.5:
            result["note"] = f"Nyquist ({nyquist:.1f} Hz) too low for {F_RING} Hz detection"
            return result
        
        # FFT of envelope
        n = len(envelope)
        fft_mag = np.abs(np.fft.rfft(envelope - np.mean(envelope)))
        freqs   = np.fft.rfftfreq(n, d=1.0/env_rate)
        
        # Find dominant carrier in envelope (below 5 Hz)
        carrier_mask = (freqs > 0.01) & (freqs < 5.0)
        if np.any(carrier_mask):
            carrier_idx = np.where(carrier_mask)[0][np.argmax(fft_mag[carrier_mask])]
            carrier_freq = freqs[carrier_idx]
            carrier_amp  = fft_mag[carrier_idx]
            result["carrier_freq_hz"] = float(carrier_freq)
            result["carrier_amplitude"] = float(carrier_amp)
        
        # Check for sidebands AT carrier ± 20.55 Hz
        if result["carrier_freq_hz"]:
            f_c = result["carrier_freq_hz"]
            
            up_target = f_c + F_RING
            up_mask   = (freqs > up_target - SIDEBAND_TOL) & (freqs < up_target + SIDEBAND_TOL)
            
            lo_target = f_c - F_RING
            lo_mask   = (freqs > max(0.01, lo_target - SIDEBAND_TOL)) & (freqs < lo_target + SIDEBAND_TOL) & (freqs > 0)
            
            if np.any(up_mask) and np.any(lo_mask):
                up_amp = float(fft_mag[np.where(up_mask)[0][np.argmax(fft_mag[up_mask])]])
                lo_amp = float(fft_mag[np.where(lo_mask)[0][np.argmax(fft_mag[lo_mask])]])
                
                sym_err = abs(up_amp - lo_amp) / max(up_amp, lo_amp)
                
                result["upper_sideband_hz"]  = float(up_target)
                result["lower_sideband_hz"]  = float(lo_target)
                result["upper_amplitude"]    = up_amp
                result["lower_amplitude"]    = lo_amp
                result["symmetry_error"]     = float(sym_err)
                result["sideband_detected"]  = True
                result["confirmed"]          = sym_err < SYM_ERR_MAX
                
                if result["confirmed"]:
                    result["note"] = f"CONFIRMED: Symmetric sidebands at f_c ± {F_RING} Hz (symmetry error {sym_err*100:.2f}% < 5%)"
                else:
                    result["note"] = f"Sidebands present but asymmetric (symmetry error {sym_err*100:.2f}% > 5%)"
        
    except Exception as e:
        result["note"] = f"Error: {str(e)}"
    
    return result

def main():
    parser = argparse.ArgumentParser(description="Scan HDSDR WAV files for 20.55 Hz LUFT sideband")
    parser.add_argument('--file', type=str, help='Single WAV file to scan')
    parser.add_argument('--all',  action='store_true', help='Scan all HDSDR_*.wav files in data/sdr/')
    parser.add_argument('--output', type=str, default='diagnostic_outputs/wav_sideband_scan_results.json')
    args = parser.parse_args()
    
    files = []
    if args.all:
        files = sorted(glob.glob('data/sdr/HDSDR_*.wav'))
        if not files:
            print("No HDSDR_*.wav files found in data/sdr/.")
            return
    elif args.file:
        files = [args.file]
    else:
        parser.print_help()
        return
    
    Path("diagnostic_outputs").mkdir(exist_ok=True)
    
    print("="*70)
    print(f"LUFT WAV SIDEBAND SCANNER")
    print(f"Target: {F_RING} Hz integrity frequency")
    print("="*70)
    
    all_results = []
    confirmed_count = 0
    
    for fpath in files:
        print(f"\nScanning: {Path(fpath).name}")
        r = scan_for_sideband(fpath)
        all_results.append(r)
        
        status = "✅ CONFIRMED" if r["confirmed"] else ("⚡ DETECTED"  if r["sideband_detected"] else "— not detected")
        sym_str = f"  sym_err: {r['symmetry_error']*100:.1f}%" if r.get('symmetry_error') is not None else ""
        
        print(f"  {status}{sym_str}")
        if r["note"]:
            print(f"  → {r['note']}")
        
        if r["confirmed"]:
            confirmed_count += 1
    
    print("\n" + "="*70)
    print(f"SCAN COMPLETE: {len(files)} files")
    print(f"Confirmed signatures: {confirmed_count} / {len(files)}")
    if confirmed_count > 0:
        print(f"✅ 20.55 Hz oscillating lens signature present in data")
    print("="*70)
    
    with open(args.output, 'w') as f:
        json.dump(all_results, f, indent=2)

if __name__ == "__main__":
    main()
