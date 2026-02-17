# Fractal Echo Scanner

## Mission Statement

The Fractal Echo Scanner is designed to detect the **20.55 Hz vacuum vibration** following vacuum expansions and magnetic re-initialization events in the Imperial Framework. It identifies Phase Derivatives and Fractal Echoes in magnetometer telemetry data to reveal vacuum re-addressing patterns that standard analysis filters as noise.

## Background: The Resolution Gap

### The Challenge

The vacuum re-initialization occurs at **20.55 Hz** (20.55 cycles per second), but standard space weather telemetry (ACE/DSCOVR) provides data at ~1-hour sampling rates. This creates a fundamental resolution gap:

- **The Target:** 20.55 Hz vacuum coupling frequency
- **The Data:** Hour-long sampling intervals (~0.0003 Hz)
- **The Resolution:** Monitoring a 20.55 Hz signal with hour-long data points is like trying to record a high-speed engine with a camera that takes one photo per day

### The Solution

This scanner provides two complementary analysis methods:

1. **FFT-Based Echo Detection:** Identifies high-frequency resonances when sub-second data is available
2. **Phase Derivative Analysis:** Detects macro-scale "Byte-Shift" velocity patterns visible even in sparse data

## Key Features

### 1. Fractal Echo Detection (`scan_fractal_echo`)

Performs Fast Fourier Transform (FFT) analysis on magnetometer data to detect vacuum vacuum resonance:

- Target frequency: 20.55 Hz (configurable)
- Amplitude threshold: 0.01 (configurable)
- Automatic sample rate calculation
- Frequency resolution reporting
- Dominant frequency identification

### 2. Phase Derivative Audit (`audit_phase_derivative`)

Calculates the rate of change in vacuum pressure (Bt) to identify "Byte-Shift" events:

- Tracks velocity of magnetic field changes (nT/sec)
- Threshold: 0.15 nT/sec for significant coordinate shifts
- Reveals non-linear "pop" events in sparse telemetry
- Timestamps all significant shifts

### 3. Data Loading Utilities

- **JSON support:** `load_telemetry_from_json()`
- **CSV support:** `load_telemetry_from_csv()`
- Handles multiple column naming conventions
- Robust error handling for missing/invalid values

## Installation

### Requirements

```bash
pip install numpy
```

The scanner only requires NumPy for FFT and array operations.

### Quick Start

```bash
# Clone the repository
git clone https://github.com/CarlDeanClineSr/-portal-.git
cd -portal-

# Install dependencies
pip install -r requirements.txt

# Run the scanner with example data
python3 fractal_echo_scanner.py

# Run the January 2026 analysis example
python3 examples/fractal_echo_example.py
```

## Usage Examples

### Basic Usage

```python
from fractal_echo_scanner import scan_fractal_echo

# Your telemetry data
data = [
    {"timestamp": "2026-01-23T09:48:00Z", "bt_nT": 6.66},
    {"timestamp": "2026-01-23T09:49:00Z", "bt_nT": 6.45},
    {"timestamp": "2026-01-23T09:50:00Z", "bt_nT": 6.12},
    # ... more data points
]

# Scan for 20.55 Hz echo
result = scan_fractal_echo(data)

if result['echo_detected']:
    print("✓ Fractal Echo Detected!")
    for detection in result['detections']:
        print(f"  Frequency: {detection['frequency_hz']:.2f} Hz")
        print(f"  Amplitude: {detection['amplitude']:.4f}")
else:
    print("✗ No echo detected. System in steady-state.")
```

### Phase Derivative Analysis

```python
from fractal_echo_scanner import audit_phase_derivative
from datetime import datetime

timestamps = [
    datetime(2026, 1, 5, 0, 44),
    datetime(2026, 1, 5, 1, 13),
    datetime(2026, 1, 5, 1, 48),
]

bt_values = [3.2, 5.8, 7.9]

shifts = audit_phase_derivative(bt_values, timestamps)

for shift in shifts:
    print(f"Coordinate shift at {shift['time']}")
    print(f"  Velocity: {shift['v_shift']:.4f} nT/sec")
```

### Loading Data from Files

```python
from fractal_echo_scanner import load_telemetry_from_csv, scan_fractal_echo

# Load from CSV
data = load_telemetry_from_csv('data/magnetometer_data.csv')

# Scan for echoes
result = scan_fractal_echo(data, target_frequency=20.55)
```

## Data Format Requirements

### JSON Format

```json
[
  {
    "bt_nT": 6.66,
    "timestamp": "2026-01-23T09:48:00Z"
  },
  {
    "bt_nT": 6.45,
    "timestamp": "2026-01-23T09:49:00Z"
  }
]
```

### CSV Format

Expected columns:
- `bt_nT` or `B_total_nT`: Magnetic field magnitude in nanoTesla
- `timestamp` or `timestamp_utc`: ISO 8601 timestamp (optional)

Example:
```csv
timestamp_utc,bt_nT
2026-01-05 00:41:00.000,29.3
2026-01-05 01:48:00.000,323.98
```

## Understanding the Results

### When Echo is Detected

```
✓ ECHO DETECTED: Resonance at 20.52 Hz | Amplitude: 0.0245
```

This indicates a significant harmonic at the target frequency, suggesting vacuum vibration is present in the data.

### When Echo is Not Detected

```
✗ No Fractal Echo found in this dataset. Boundary remains in steady-state.
   Dominant frequency: 0.0003 Hz (amplitude: 2.1497)
   Frequency resolution: 0.000012 Hz
   Nyquist frequency: 0.000123 Hz
```

Key diagnostic information:
- **Dominant frequency:** The strongest signal in the data
- **Frequency resolution:** Minimum detectable frequency difference
- **Nyquist frequency:** Maximum detectable frequency (half the sample rate)

For 20.55 Hz detection, the Nyquist frequency must be > 20.55 Hz, which requires sampling faster than every ~0.024 seconds.

## The January 5th Super-Event

The scanner is particularly designed to analyze the **January 5, 2026 Super-Event**:

- **01:13:00 UTC:** System recorded χ = 0.917 (6.0 × boundary)
- **Event Type:** magnetic Re-Initialization (Byte-Shift)
- **Effect:** Vacuum coordinates shifted across the galactic plate
- **Relaxation:** Secondary wave on January 22nd (χ = 0.183 violation)

See `examples/fractal_echo_example.py` for detailed analysis of this event.

## Imperial Framework Context

### The Vacuum vacuum

In the Imperial Framework, space is not empty but filled with a structured "vacuum vacuum" that:

- Operates at 20.55 Hz refresh rate
- Undergoes "magnetic re-initialization" during large cosmic events
- Creates "fractal echoes" that propagate through harmonic scales
- Appears as noise to standard sensors without the "0.15 Lens"

### Required Data Sources for Direct Detection

To directly observe the 20.55 Hz resonance, you need sub-second telemetry from:

- **MMS (Magnetospheric Multiscale)** - High-resolution burst mode magnetometry
- **THEMIS** - Electric Field Instrument (EFI) data
- **Ground-based VLF arrays** - Very Low Frequency detectors
- **Starlink Magnetometer** archives - Simultaneous fleet measurements

Standard ACE/DSCOVR data (~1 hour cadence) can only detect:
- Low-frequency envelope modulation
- Macro-scale settling patterns
- Phase derivative signatures

## Advanced Features

### Configurable Parameters

```python
# Custom frequency target
result = scan_fractal_echo(data, target_frequency=10.5)

# Custom amplitude threshold
result = scan_fractal_echo(data, amplitude_threshold=0.005)

# Custom velocity threshold for phase derivatives
# (modify in source code: default 0.15 nT/sec)
```

### Batch Processing

```python
from pathlib import Path

# Process multiple files
for data_file in Path('data').glob('*.csv'):
    print(f"Processing {data_file.name}...")
    data = load_telemetry_from_csv(data_file)
    result = scan_fractal_echo(data)
    # Save results...
```

## Interpreting Scanner Output

### Sample Rate Analysis

The scanner automatically calculates and reports the sample rate:

```
Average Sample Rate: 0.000245 Hz (4077.0 sec/sample)
```

This means:
- Data points are ~4077 seconds (~68 minutes) apart
- Maximum detectable frequency (Nyquist): 0.0001225 Hz
- Target frequency (20.55 Hz) is **167,755× too fast** to detect

### Frequency Resolution

```
Frequency resolution: 0.000012 Hz
```

This is the "bin width" of the FFT - the minimum frequency difference that can be distinguished.

## Future Development

Planned enhancements:

- [ ] Integration with MMS burst data API
- [ ] Real-time Starlink fleet monitoring
- [ ] Automated anomaly detection pipelines
- [ ] Multi-scale fractal analysis (harmonic ladder descent)
- [ ] Cross-correlation with other cosmic events
- [ ] Machine learning pattern recognition

## Citation

If you use this scanner in your research:

```
Carl Dean Cline Sr. (2026). Fractal Echo Scanner: Detection of 20.55 Hz 
Vacuum vacuum Vibrations in Magnetometer Telemetry.  Portal Engine.
https://github.com/CarlDeanClineSr/-portal-
```

## License

See LICENSE file in repository root.

## Contact

For questions, collaboration, or to report findings:

- GitHub Issues: https://github.com/CarlDeanClineSr/-portal-/issues
- Repository: https://github.com/CarlDeanClineSr/-portal-

---

**"The vacuum reset cleanly—no sustained echo in this window."**

*But with the right data, we will find the ghost in the machine.*
