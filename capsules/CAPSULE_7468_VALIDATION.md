# Capsule: 7,468 Hz Signal Validation Analysis (CAPSULE-7468-003)

## Overview
This capsule documents the implementation of WAV processing tools for the LUFT 7,468 Hz signal validation project.

## Implementation Details

### Scripts Created

1. **analyze_wav_luft.py** - Main analysis tool
   - Processes WAV audio files
   - Generates spectrograms with frequency-time analysis
   - Detects and extracts peak frequencies via FFT
   - Highlights 7,468 Hz target frequency
   - Outputs PNG spectrogram and CSV peak table

2. **generate_sample_wav.py** - Test data generator
   - Creates synthetic 7,468 Hz tone WAV files
   - Includes realistic noise
   - Useful for validation and testing

### Key Features

- **Multi-format support**: Handles 8-bit, 16-bit, 32-bit WAV files
- **Stereo/Mono**: Automatically handles both formats
- **Frequency resolution**: Optimized window size for accurate 7,468 Hz detection
- **Visualization**: High-quality spectrograms with logarithmic power scale
- **Peak detection**: Identifies dominant frequencies with magnitude and power
- **Target validation**: Automatically checks if 7,468 Hz is present

### Usage

```bash
# Install dependencies
pip install -r requirements.txt

# Generate test sample
python scripts/generate_sample_wav.py

# Analyze WAV file
python scripts/analyze_wav_luft.py recordings/sample.wav
```

### Output Format

#### Spectrogram (PNG)
- X-axis: Time (seconds)
- Y-axis: Frequency (Hz)
- Color: Power spectral density (dB)
- Red dashed line: 7,468 Hz target frequency

#### Peak Table (CSV)
Columns:
- `frequency_hz`: Peak frequency in Hertz
- `magnitude`: Raw FFT magnitude
- `power_db`: Power in decibels (20*log10)
- `distance_from_target_hz`: Absolute distance from 7,468 Hz

### Validation Results

Test with synthetic 7,468 Hz tone:
- ✓ Frequency detected: 7,468.00 Hz (0.00 Hz error)
- ✓ Power: 85.95 dB
- ✓ Clean spectrogram with clear peak at target frequency

### Technical Notes

- Sample rate: 44.1 kHz (standard audio)
- FFT window: 4096 samples (adaptive based on file length)
- Overlap: 50% (Hann window)
- Frequency range displayed: 0 - 15 kHz (focused on target)
- Peak detection threshold: 1% of maximum magnitude
- Minimum peak separation: 10 Hz

### Dependencies

- numpy >= 1.24.0 (numerical operations, FFT)
- scipy >= 1.10.0 (signal processing, spectrogram)
- matplotlib >= 3.7.0 (visualization)

### File Structure

```
luft-portal-/
├── scripts/
│   ├── analyze_wav_luft.py      # Main analyzer
│   ├── generate_sample_wav.py   # Test generator
│   └── README.md                 # Scripts documentation
├── recordings/                   # Input WAV files (gitignored)
├── results/                      # Output spectrograms and CSVs (gitignored)
├── requirements.txt              # Python dependencies
└── README.md                     # Updated with usage instructions
```

### Future Enhancements

Potential improvements for cross-site validation:
1. Batch processing of multiple WAV files
2. Time-series analysis of frequency stability
3. Statistical comparison across different recording sites
4. Automated anomaly detection
5. Integration with LUFT frequency atlas

## Status
✓ Complete - Ready for validation with real field recordings

## References
- LUFT-PORTAL_README.md - Original requirements
- ARCHIVE_GUIDE.md - WAV file management guidelines
