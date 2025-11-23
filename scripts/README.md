# LUFT Scripts

## analyze_wav_luft.py

WAV file analyzer for LUFT 7,468 Hz signal validation. Processes audio recordings and generates spectrograms and peak frequency analysis.

### Usage

```bash
python scripts/analyze_wav_luft.py <path_to_wav_file>
```

### Example

```bash
python scripts/analyze_wav_luft.py ./recordings/sample.wav
```

### Output

The script generates two files in the `results/` directory:

1. **Spectrogram image** (PNG): Visual representation of the frequency content over time
   - Highlights the target frequency (7,468 Hz) with a red dashed line
   - Uses logarithmic power scale (dB)
   - Focuses on relevant frequency range (0 to ~15 kHz)

2. **Peak frequency table** (CSV): Top frequency peaks detected in the signal
   - `frequency_hz`: Peak frequency in Hz
   - `magnitude`: Raw magnitude of the peak
   - `power_db`: Power in decibels
   - `distance_from_target_hz`: Distance from 7,468 Hz target

### Requirements

Install dependencies with:

```bash
pip install -r requirements.txt
```

Required packages:
- numpy >= 1.24.0
- scipy >= 1.10.0
- matplotlib >= 3.7.0

## generate_sample_wav.py

Utility script to generate a test WAV file with a 7,468 Hz tone.

### Usage

```bash
python scripts/generate_sample_wav.py
```

This creates `recordings/sample.wav` with:
- 7,468 Hz sine wave
- 44.1 kHz sample rate
- 3 seconds duration
- Small amount of noise for realism
