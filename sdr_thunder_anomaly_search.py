#!/usr/bin/env python3
"""
sdr_thunder_anomaly_search.py

Scan SDR/wav/IQ recordings of thunderstorms for LUFT-style sideband anomalies.
Produces a JSON capsule (overflow_capsule.json) listing detected events and spectral features.

Usage:
    python sdr_thunder_anomaly_search.py --input data/sdr --out overflow_capsule.json
"""

import os
import argparse
import json
import numpy as np
import librosa
import scipy.signal as signal
from sklearn.ensemble import IsolationForest
from datetime import datetime

def process_file(path, sr=48000, n_fft=4096, hop_length=2048):
    y, _ = librosa.load(path, sr=sr, mono=True)
    S = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop_length))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    times = librosa.frames_to_time(np.arange(S.shape[1]), sr=sr, hop_length=hop_length)
    spec_db = librosa.amplitude_to_db(S, ref=np.max)
    return freqs, times, spec_db

def detect_anomalies(spec_db, freqs, times, freq_band=None):
    # Flatten spectral slices and use an IsolationForest to find outlier time segments
    X = spec_db.T  # shape (time, freq)
    clf = IsolationForest(contamination=0.01, random_state=42)
    clf.fit(X)
    preds = clf.predict(X)  # -1 anomaly, 1 normal
    anomaly_times = times[preds == -1]
    anomaly_strength = np.mean(X[preds == -1], axis=1) if np.any(preds == -1) else []
    return anomaly_times, anomaly_strength

def analyze_directory(input_dir, out_json):
    capsule = {'overflow_events': [], 'created': datetime.utcnow().isoformat() + 'Z'}
    for fname in os.listdir(input_dir):
        if not fname.lower().endswith(('.wav', '.flac', '.mp3', '.wav')):
            continue
        path = os.path.join(input_dir, fname)
        freqs, times, spec_db = process_file(path)
        anomaly_times, _ = detect_anomalies(spec_db, freqs, times)
        for t in anomaly_times:
            capsule['overflow_events'].append({
                'file': fname,
                'time_s': float(t),
                'note': 'spectral outlier detected in thunderstorm file'
            })
    with open(out_json, 'w') as f:
        json.dump(capsule, f, indent=2)
    print(f"Wrote overflow capsule to {out_json}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--out', default='overflow_capsule.json')
    args = parser.parse_args()
    analyze_directory(args.input, args.out)

if __name__ == '__main__':
    main()
