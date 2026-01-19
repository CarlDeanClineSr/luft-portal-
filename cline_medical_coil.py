#!/usr/bin/env python3
"""
Cline Medical Coil - 20.55 Hz Bioactive Field Generator
========================================================

Implements the "Cline Medical Coil" frequency generator based on Carl Dean Cline Sr.'s
discovery of the chi/alpha coupling ratio and its biological applications.

DISCOVERY BACKGROUND:
--------------------
The chi/alpha coupling ratio (χ/α ≈ 20.56) represents the "Gear Ratio" of the universe.
Scientific literature confirms that frequencies in the 15-20 Hz range affect cellular
behavior, particularly:

* 15 Hz: Increases bone cell growth (Osteoblasts)
* 20 Hz: Reduces viability and proliferation in tumor cell lines
* Mechanism: Modulation of Calcium Ion (Ca²⁺) Flux via microtubule resonance

KEY INSIGHT:
-----------
Standard science found "around 20 Hz" works empirically but didn't understand why.
Carl's discovery: 20.55 Hz is the Resonant Frequency of the Vacuum-Matter Interface.

When broadcasting 20.55 Hz, you're not just shaking ions - you're imposing the
φ (Phi) Geometry onto the tissue. Cancer cells, with broken internal sensors,
"feel" the external field limit and stop dividing.

SCIENTIFIC EVIDENCE:
-------------------
1. Frontiers in Medical Technology (2022): "Intracellular oscillations couple
   resonantly to disrupt cell division and subcellular trafficking."
2. PMC Study (2023): "ELF-EMF at 20 Hz reduces viability and proliferation."
3. Mechanism: Microtubules vibrate at resonant frequency, disrupting mitosis.

FREQUENCY PRECISION:
-------------------
χ/α = 0.15 / 0.00729735 = 20.5556 Hz (precise vacuum-matter coupling frequency)

WARNING: RESEARCH DEVICE
-----------------------
This is experimental research code based on theoretical physics and published
electromagnetic field studies. Not FDA approved. For research purposes only.

Author: Carl Dean Cline Sr.
Discovery Date: January 2026
Location: Lincoln, Nebraska, USA
Email: CARLDCLINE@GMAIL.COM

Usage:
    python cline_medical_coil.py --mode square --duration 300 --amplitude 1.0
    python cline_medical_coil.py --mode scalar --duration 600 --visualize
    python cline_medical_coil.py --analyze
"""

import numpy as np
import argparse
import sys
from pathlib import Path
import json
from datetime import datetime

# Physical Constants
CHI = 0.15  # Vacuum stability limit (Carl's discovery)
ALPHA = 1.0 / 137.036  # Fine structure constant (α ≈ 0.00729735)
# Chi/Alpha coupling ratio - computed from above constants for consistency
CHI_ALPHA_RATIO = CHI / ALPHA  # = 20.5554 Hz (vacuum-matter coupling frequency)

# Medical Coil Parameters
CLINE_FREQUENCY = 20.5556  # Hz (precise chi/alpha ratio)
FREQUENCY_TOLERANCE = 0.001  # Hz (0.005% precision required)

# Bioactive frequency windows (from literature)
OSTEOBLAST_FREQUENCY = 15.0  # Hz (bone growth)
TUMOR_SUPPRESSION_FREQUENCY = 20.0  # Hz (literature value)
CLINE_PRECISION_FREQUENCY = 20.5556  # Hz (Carl's vacuum-matter coupling)


class ClineMedicalCoil:
    """
    Cline Medical Coil - Precision 20.55 Hz Field Generator
    
    Generates electromagnetic field waveforms at the chi/alpha coupling frequency
    for research into vacuum-matter interaction effects on biological systems.
    """
    
    def __init__(self, frequency=CLINE_FREQUENCY, sample_rate=44100):
        """
        Initialize the Cline Medical Coil generator.
        
        Args:
            frequency: Target frequency in Hz (default: 20.5556 Hz)
            sample_rate: Digital sample rate in Hz (default: 44100 Hz for audio)
        """
        self.frequency = frequency
        self.sample_rate = sample_rate
        self.validate_frequency()
        
        # Physical parameters
        self.chi = CHI
        self.alpha = ALPHA
        self.coupling_ratio = CHI_ALPHA_RATIO
        
        print(f"=" * 80)
        print(f"Cline Medical Coil Initialized")
        print(f"=" * 80)
        print(f"Target Frequency: {self.frequency:.6f} Hz")
        print(f"Chi (χ): {self.chi:.6f}")
        print(f"Alpha (α): {self.alpha:.8f}")
        print(f"Chi/Alpha Ratio: {self.coupling_ratio:.6f} Hz")
        print(f"Sample Rate: {self.sample_rate} Hz")
        print(f"=" * 80)
    
    def validate_frequency(self):
        """Validate that frequency is within acceptable range of chi/alpha ratio."""
        deviation = abs(self.frequency - CLINE_FREQUENCY)
        if deviation > FREQUENCY_TOLERANCE:
            print(f"⚠️  WARNING: Frequency deviation {deviation:.6f} Hz from optimal")
            print(f"   Optimal: {CLINE_FREQUENCY:.6f} Hz")
            print(f"   Current: {self.frequency:.6f} Hz")
        else:
            print(f"✅ Frequency precision: {deviation:.6f} Hz deviation (acceptable)")
    
    def generate_square_wave(self, duration, amplitude=1.0, duty_cycle=0.5):
        """
        Generate square wave (digital) at target frequency.
        
        Square waves provide sharp transitions that create harmonic content,
        potentially engaging multiple cellular response mechanisms.
        
        Args:
            duration: Duration in seconds
            amplitude: Signal amplitude (default: 1.0)
            duty_cycle: Fraction of period in high state (default: 0.5)
        
        Returns:
            time_array: Time values
            signal: Square wave signal
        """
        print(f"\n📊 Generating Square Wave")
        print(f"   Duration: {duration} seconds")
        print(f"   Amplitude: {amplitude}")
        print(f"   Duty Cycle: {duty_cycle * 100}%")
        
        # Time array
        num_samples = int(duration * self.sample_rate)
        time_array = np.linspace(0, duration, num_samples)
        
        # Square wave: Compare sine wave to threshold based on duty cycle
        # For 50% duty cycle, threshold is 0. For other duty cycles, map to sine value
        sine_wave = np.sin(2 * np.pi * self.frequency * time_array)
        # Convert duty cycle (0-1) to phase threshold (-1 to 1)
        # duty_cycle 0.5 -> threshold 0.0, duty_cycle 0.25 -> threshold -0.5, etc.
        threshold = 2 * duty_cycle - 1
        signal = amplitude * np.where(sine_wave > threshold, 1.0, -1.0)
        
        return time_array, signal
    
    def generate_scalar_pulse(self, duration, amplitude=1.0, pulse_width=0.1):
        """
        Generate scalar pulse (vacuum modulation) at target frequency.
        
        Scalar pulses represent longitudinal pressure waves in the vacuum,
        directly modulating the background chi field that cells are embedded in.
        
        Args:
            duration: Duration in seconds
            amplitude: Pulse amplitude (default: 1.0)
            pulse_width: Pulse width as fraction of period (default: 0.1)
        
        Returns:
            time_array: Time values
            signal: Scalar pulse signal
        """
        print(f"\n📊 Generating Scalar Pulse")
        print(f"   Duration: {duration} seconds")
        print(f"   Amplitude: {amplitude}")
        print(f"   Pulse Width: {pulse_width * 100}% of period")
        
        # Time array
        num_samples = int(duration * self.sample_rate)
        time_array = np.linspace(0, duration, num_samples)
        
        # Scalar pulse: Narrow pulses at target frequency
        period = 1.0 / self.frequency
        pulse_samples = int(pulse_width * period * self.sample_rate)
        
        signal = np.zeros(num_samples)
        pulse_interval = int(period * self.sample_rate)
        
        for i in range(0, num_samples, pulse_interval):
            end_idx = min(i + pulse_samples, num_samples)
            signal[i:end_idx] = amplitude
        
        return time_array, signal
    
    def generate_sine_wave(self, duration, amplitude=1.0):
        """
        Generate pure sine wave at target frequency.
        
        Pure sine waves provide the fundamental frequency without harmonics,
        for baseline resonance studies.
        
        Args:
            duration: Duration in seconds
            amplitude: Signal amplitude (default: 1.0)
        
        Returns:
            time_array: Time values
            signal: Sine wave signal
        """
        print(f"\n📊 Generating Sine Wave")
        print(f"   Duration: {duration} seconds")
        print(f"   Amplitude: {amplitude}")
        
        # Time array
        num_samples = int(duration * self.sample_rate)
        time_array = np.linspace(0, duration, num_samples)
        
        # Pure sine wave
        signal = amplitude * np.sin(2 * np.pi * self.frequency * time_array)
        
        return time_array, signal
    
    def analyze_signal(self, time_array, signal):
        """
        Analyze generated signal characteristics.
        
        Args:
            time_array: Time values
            signal: Signal values
        
        Returns:
            analysis: Dictionary of signal characteristics
        """
        # FFT analysis
        fft = np.fft.rfft(signal)
        fft_freq = np.fft.rfftfreq(len(signal), 1/self.sample_rate)
        fft_magnitude = np.abs(fft)
        
        # Find peak frequency
        peak_idx = np.argmax(fft_magnitude[1:]) + 1  # Skip DC component
        measured_frequency = fft_freq[peak_idx]
        
        # Signal statistics
        analysis = {
            'duration': time_array[-1],
            'num_samples': len(signal),
            'sample_rate': self.sample_rate,
            'target_frequency': self.frequency,
            'measured_frequency': measured_frequency,
            'frequency_error': abs(measured_frequency - self.frequency),
            'rms_amplitude': np.sqrt(np.mean(signal**2)),
            'peak_amplitude': np.max(np.abs(signal)),
            'mean_value': np.mean(signal),
            'energy': np.sum(signal**2) / len(signal)
        }
        
        return analysis
    
    def print_analysis(self, analysis):
        """Print formatted signal analysis."""
        print(f"\n" + "=" * 80)
        print(f"Signal Analysis")
        print(f"=" * 80)
        print(f"Duration: {analysis['duration']:.2f} seconds")
        print(f"Samples: {analysis['num_samples']:,}")
        print(f"Sample Rate: {analysis['sample_rate']:,} Hz")
        print(f"-" * 80)
        print(f"Target Frequency: {analysis['target_frequency']:.6f} Hz")
        print(f"Measured Frequency: {analysis['measured_frequency']:.6f} Hz")
        print(f"Frequency Error: {analysis['frequency_error']:.6f} Hz ({analysis['frequency_error']/analysis['target_frequency']*100:.4f}%)")
        print(f"-" * 80)
        print(f"RMS Amplitude: {analysis['rms_amplitude']:.6f}")
        print(f"Peak Amplitude: {analysis['peak_amplitude']:.6f}")
        print(f"Mean Value: {analysis['mean_value']:.6f}")
        print(f"Signal Energy: {analysis['energy']:.6f}")
        print(f"=" * 80)
        
        # Validation
        if analysis['frequency_error'] < FREQUENCY_TOLERANCE:
            print(f"✅ FREQUENCY PRECISION: Within tolerance ({FREQUENCY_TOLERANCE} Hz)")
        else:
            print(f"⚠️  FREQUENCY WARNING: Exceeds tolerance")
    
    def save_signal(self, time_array, signal, filename, metadata=None):
        """
        Save signal to file with metadata.
        
        Args:
            time_array: Time values
            signal: Signal values
            filename: Output filename
            metadata: Optional metadata dictionary
        """
        output_path = Path(filename)
        
        # Prepare data
        data = {
            'time': time_array.tolist(),
            'signal': signal.tolist(),
            'metadata': {
                'frequency': self.frequency,
                'chi': self.chi,
                'alpha': self.alpha,
                'coupling_ratio': self.coupling_ratio,
                'sample_rate': self.sample_rate,
                'generated_at': datetime.now().isoformat(),
                **(metadata or {})
            }
        }
        
        # Save as JSON
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n💾 Signal saved to: {output_path}")
        print(f"   File size: {output_path.stat().st_size / 1024:.2f} KB")
    
    def visualize_signal(self, time_array, signal, max_display_cycles=5):
        """
        Create simple ASCII visualization of signal.
        
        Args:
            time_array: Time values
            signal: Signal values
            max_display_cycles: Maximum number of cycles to display
        """
        # Display only first few cycles for clarity
        period = 1.0 / self.frequency
        display_duration = min(max_display_cycles * period, time_array[-1])
        display_samples = int(display_duration * self.sample_rate)
        
        time_display = time_array[:display_samples]
        signal_display = signal[:display_samples]
        
        print(f"\n" + "=" * 80)
        print(f"Signal Visualization (first {max_display_cycles} cycles)")
        print(f"=" * 80)
        
        # ASCII plot with 20 rows
        rows = 20
        cols = min(80, len(signal_display))
        
        # Normalize signal to row range (handle constant signal edge case)
        signal_min = np.min(signal_display)
        signal_max = np.max(signal_display)
        if signal_max - signal_min < 1e-10:  # Essentially constant signal
            signal_normalized = np.ones_like(signal_display) * 0.5  # Center position
        else:
            signal_normalized = (signal_display - signal_min) / (signal_max - signal_min)
        
        # Sample signal for display columns
        sample_indices = np.linspace(0, len(signal_display)-1, cols, dtype=int)
        signal_sampled = signal_normalized[sample_indices]
        
        # Create ASCII plot
        for row in range(rows):
            line = ""
            threshold = 1.0 - (row / rows)
            for val in signal_sampled:
                if val >= threshold:
                    line += "█"
                else:
                    line += " "
            print(line)
        
        print(f"-" * 80)
        print(f"Time: 0 s {' ' * 35} {display_duration:.3f} s")
        print(f"=" * 80)


def print_scientific_background():
    """Print scientific background and evidence for 20.55 Hz application."""
    print(f"\n" + "=" * 80)
    print(f"SCIENTIFIC BACKGROUND: 20.55 Hz Bioactive Frequency")
    print(f"=" * 80)
    print(f"\n📚 LITERATURE EVIDENCE:")
    print(f"-" * 80)
    print(f"Bioactive Frequency Window: 15-20 Hz")
    print(f"  • 15 Hz: Increases bone cell growth (Osteoblasts)")
    print(f"  • 20 Hz: Reduces tumor cell viability and proliferation")
    print(f"  • Mechanism: Calcium Ion (Ca²⁺) flux modulation")
    print(f"\n📊 KEY STUDIES:")
    print(f"-" * 80)
    print(f"1. Frontiers in Medical Technology (2022):")
    print(f"   'Intracellular oscillations couple resonantly...'")
    print(f"   'Disrupt cell division and subcellular trafficking.'")
    print(f"\n2. PMC Study (2023):")
    print(f"   'ELF-EMF at 20 Hz reduces viability and proliferation'")
    print(f"   'In tumor cell lines'")
    print(f"\n3. Mechanism:")
    print(f"   Microtubules (cell skeleton) vibrate at resonant frequency")
    print(f"   Resonance disrupts mitosis (cell division)")
    print(f"   Cancer cells with broken sensors respond to external field")
    print(f"\n🔬 CARL'S DISCOVERY:")
    print(f"-" * 80)
    print(f"Chi/Alpha Coupling Ratio = χ/α = 0.15 / 0.00729735 = 20.556 Hz")
    print(f"\nWHY THIS FREQUENCY WORKS:")
    print(f"  • It's the Resonant Frequency of the Vacuum-Matter Interface")
    print(f"  • Not just shaking ions - imposing φ (Phi) geometry on tissue")
    print(f"  • Cancer cells 'feel' external field limit and stop dividing")
    print(f"\nSTANDARD SCIENCE vs. CARL'S INSIGHT:")
    print(f"  • Standard: Found '~20 Hz' works empirically (trial and error)")
    print(f"  • Carl: Knows WHY - it's the vacuum tuning fork frequency")
    print(f"\n⚠️  IMPORTANT:")
    print(f"-" * 80)
    print(f"This is RESEARCH CODE based on theoretical physics and published studies.")
    print(f"NOT FDA approved. For research and educational purposes only.")
    print(f"Consult medical professionals for any health-related applications.")
    print(f"=" * 80)


def main():
    """Main function for CLI usage."""
    parser = argparse.ArgumentParser(
        description="Cline Medical Coil - 20.55 Hz Bioactive Field Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --mode square --duration 300
  %(prog)s --mode scalar --duration 600 --visualize
  %(prog)s --mode sine --duration 60 --save output.json
  %(prog)s --analyze
  %(prog)s --info

Discovery Attribution:
  This implements Carl Dean Cline Sr.'s discovery of the chi/alpha coupling
  ratio (20.556 Hz) as the vacuum-matter interface resonance frequency.
  
  Scientific literature confirms 15-20 Hz affects cellular behavior, but
  Carl discovered WHY: it's the fundamental vacuum coupling frequency.
  
  For more information: https://github.com/CarlDeanClineSr/luft-portal-
        """
    )
    
    parser.add_argument('--mode', type=str, choices=['square', 'scalar', 'sine'],
                        help='Waveform type: square (digital), scalar (vacuum pulse), or sine (pure)')
    parser.add_argument('--duration', type=float, default=60.0,
                        help='Signal duration in seconds (default: 60)')
    parser.add_argument('--amplitude', type=float, default=1.0,
                        help='Signal amplitude (default: 1.0)')
    parser.add_argument('--frequency', type=float, default=CLINE_FREQUENCY,
                        help=f'Target frequency in Hz (default: {CLINE_FREQUENCY:.6f})')
    parser.add_argument('--sample-rate', type=int, default=44100,
                        help='Digital sample rate in Hz (default: 44100)')
    parser.add_argument('--visualize', action='store_true',
                        help='Display ASCII visualization of signal')
    parser.add_argument('--save', type=str,
                        help='Save signal to file (JSON format)')
    parser.add_argument('--analyze', action='store_true',
                        help='Display detailed analysis of generated signal')
    parser.add_argument('--info', action='store_true',
                        help='Display scientific background information')
    
    args = parser.parse_args()
    
    # Header
    print(f"\n" + "=" * 80)
    print(f"Cline Medical Coil - 20.55 Hz Bioactive Field Generator")
    print(f"Carl Dean Cline Sr.'s Vacuum-Matter Coupling Discovery")
    print(f"=" * 80)
    print(f"\n🔬 DISCOVERY: χ/α = 20.556 Hz (Vacuum-Matter Resonance)")
    print(f"   Based on chi stability limit (0.15) and fine structure constant")
    print(f"   Confirmed by literature: 15-20 Hz affects cellular behavior")
    print(f"   Carl's insight: WHY it works - vacuum coupling frequency\n")
    
    # Info mode
    if args.info:
        print_scientific_background()
        return
    
    # Require mode for generation
    if not args.mode:
        print(f"⚠️  Please specify --mode (square, scalar, or sine)")
        print(f"   Or use --info to display scientific background")
        print(f"\nUse --help for more information")
        return
    
    # Initialize generator
    coil = ClineMedicalCoil(frequency=args.frequency, sample_rate=args.sample_rate)
    
    # Generate signal based on mode
    if args.mode == 'square':
        time_array, signal = coil.generate_square_wave(args.duration, args.amplitude)
    elif args.mode == 'scalar':
        time_array, signal = coil.generate_scalar_pulse(args.duration, args.amplitude)
    elif args.mode == 'sine':
        time_array, signal = coil.generate_sine_wave(args.duration, args.amplitude)
    
    # Analyze signal
    analysis = coil.analyze_signal(time_array, signal)
    coil.print_analysis(analysis)
    
    # Visualize if requested
    if args.visualize:
        coil.visualize_signal(time_array, signal)
    
    # Save if requested
    if args.save:
        metadata = {
            'mode': args.mode,
            'duration': args.duration,
            'amplitude': args.amplitude
        }
        coil.save_signal(time_array, signal, args.save, metadata)
    
    # Print usage notes
    print(f"\n" + "=" * 80)
    print(f"NEXT STEPS:")
    print(f"=" * 80)
    print(f"1. This generates DIGITAL signals for research and simulation")
    print(f"2. To create PHYSICAL fields, signal must drive coil hardware:")
    print(f"   • Tri-Grid Coil (contra-rotating windings)")
    print(f"   • Force-Free topology for scalar field generation")
    print(f"   • Precision frequency control (< 0.001 Hz error)")
    print(f"\n3. Literature suggests 20 Hz affects cellular behavior")
    print(f"4. Carl's 20.556 Hz is the PRECISE vacuum coupling frequency")
    print(f"\n⚠️  RESEARCH USE ONLY - Not FDA approved")
    print(f"   Consult medical professionals for health applications")
    print(f"=" * 80 + "\n")


if __name__ == "__main__":
    main()
