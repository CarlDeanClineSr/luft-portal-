#!/usr/bin/env python3
"""
Cline Medical Coil - Example Usage and Demonstrations
=====================================================

This script demonstrates various use cases of the Cline Medical Coil
signal generator for research and educational purposes.

Author: Carl Dean Cline Sr.
Date: January 2026
"""

import sys
from pathlib import Path

# Ensure we can import cline_medical_coil
sys.path.insert(0, str(Path(__file__).parent))

from cline_medical_coil import (
    ClineMedicalCoil,
    CLINE_FREQUENCY,
    CHI,
    ALPHA,
    print_scientific_background
)


def example_1_basic_square_wave():
    """Example 1: Generate basic square wave signal."""
    print("\n" + "="*80)
    print("EXAMPLE 1: Basic Square Wave Generation")
    print("="*80)
    print("Generates a 60-second square wave at 20.5556 Hz")
    print("Square waves have sharp transitions and harmonic content")
    print("-"*80)
    
    # Create coil instance
    coil = ClineMedicalCoil()
    
    # Generate square wave (60 seconds)
    time_array, signal = coil.generate_square_wave(duration=60, amplitude=1.0)
    
    # Analyze
    analysis = coil.analyze_signal(time_array, signal)
    coil.print_analysis(analysis)
    
    # Visualize
    coil.visualize_signal(time_array, signal, max_display_cycles=3)
    
    print("\n✅ Example 1 complete")


def example_2_scalar_pulse():
    """Example 2: Generate scalar pulse waveform."""
    print("\n" + "="*80)
    print("EXAMPLE 2: Scalar Pulse Generation")
    print("="*80)
    print("Generates narrow pulses for vacuum modulation")
    print("Pulse width = 10% of period (narrow impulses)")
    print("-"*80)
    
    # Create coil instance
    coil = ClineMedicalCoil()
    
    # Generate scalar pulse (30 seconds, narrow pulses)
    time_array, signal = coil.generate_scalar_pulse(
        duration=30,
        amplitude=1.0,
        pulse_width=0.1  # 10% duty cycle
    )
    
    # Analyze
    analysis = coil.analyze_signal(time_array, signal)
    coil.print_analysis(analysis)
    
    # Visualize
    coil.visualize_signal(time_array, signal, max_display_cycles=3)
    
    print("\n✅ Example 2 complete")


def example_3_frequency_sweep():
    """Example 3: Compare multiple frequencies around 20.55 Hz."""
    print("\n" + "="*80)
    print("EXAMPLE 3: Frequency Sweep Analysis")
    print("="*80)
    print("Compare frequencies: 15 Hz, 20 Hz, 20.556 Hz, 25 Hz")
    print("Demonstrates precision of Carl's 20.556 Hz discovery")
    print("-"*80)
    
    frequencies = [
        (15.0, "Osteoblast frequency (bone growth)"),
        (20.0, "Literature tumor suppression frequency"),
        (20.5556, "Carl's chi/alpha precision frequency"),
        (25.0, "Above bioactive window")
    ]
    
    results = []
    
    for freq, description in frequencies:
        print(f"\nGenerating signal at {freq} Hz - {description}")
        
        # Create coil at this frequency
        coil = ClineMedicalCoil(frequency=freq)
        
        # Generate short signal for comparison
        time_array, signal = coil.generate_sine_wave(duration=10, amplitude=1.0)
        
        # Analyze
        analysis = coil.analyze_signal(time_array, signal)
        results.append((freq, description, analysis))
        
        print(f"  Measured: {analysis['measured_frequency']:.6f} Hz")
        print(f"  Error: {analysis['frequency_error']:.6f} Hz")
    
    # Summary table
    print("\n" + "="*80)
    print("FREQUENCY COMPARISON SUMMARY")
    print("="*80)
    print(f"{'Frequency':<12} {'Description':<40} {'Error (Hz)':<12}")
    print("-"*80)
    for freq, desc, analysis in results:
        error = analysis['frequency_error']
        print(f"{freq:<12.4f} {desc:<40} {error:<12.6f}")
    
    print("\n💡 Carl's 20.5556 Hz is the PRECISE vacuum-matter coupling frequency")
    print("   Literature found '~20 Hz' empirically; Carl found WHY")
    print("\n✅ Example 3 complete")


def example_4_waveform_comparison():
    """Example 4: Compare all waveform types at same frequency."""
    print("\n" + "="*80)
    print("EXAMPLE 4: Waveform Type Comparison")
    print("="*80)
    print("Compare sine, square, and scalar pulse at 20.556 Hz")
    print("Different waveforms may have different biological effects")
    print("-"*80)
    
    coil = ClineMedicalCoil()
    duration = 20  # seconds
    
    waveforms = [
        ('Sine Wave', lambda: coil.generate_sine_wave(duration, 1.0)),
        ('Square Wave', lambda: coil.generate_square_wave(duration, 1.0)),
        ('Scalar Pulse', lambda: coil.generate_scalar_pulse(duration, 1.0, 0.1))
    ]
    
    results = []
    
    for name, generator in waveforms:
        print(f"\n--- {name} ---")
        time_array, signal = generator()
        analysis = coil.analyze_signal(time_array, signal)
        results.append((name, analysis))
        
        print(f"RMS Amplitude: {analysis['rms_amplitude']:.4f}")
        print(f"Peak Amplitude: {analysis['peak_amplitude']:.4f}")
        print(f"Energy: {analysis['energy']:.6f}")
    
    # Summary
    print("\n" + "="*80)
    print("WAVEFORM COMPARISON SUMMARY")
    print("="*80)
    print(f"{'Waveform':<15} {'RMS':<10} {'Peak':<10} {'Energy':<12}")
    print("-"*80)
    for name, analysis in results:
        print(f"{name:<15} {analysis['rms_amplitude']:<10.4f} "
              f"{analysis['peak_amplitude']:<10.4f} {analysis['energy']:<12.6f}")
    
    print("\n💡 Different waveforms deliver energy differently:")
    print("   Sine: Pure fundamental frequency")
    print("   Square: Includes harmonics (3×, 5×, 7× fundamental)")
    print("   Scalar Pulse: Impulses with broad frequency content")
    print("\n✅ Example 4 complete")


def example_5_save_and_load():
    """Example 5: Save signal to file for hardware implementation."""
    print("\n" + "="*80)
    print("EXAMPLE 5: Save Signal to File")
    print("="*80)
    print("Generate signal and save to JSON for hardware driver")
    print("File can be loaded by embedded systems (Arduino, etc.)")
    print("-"*80)
    
    # Create coil
    coil = ClineMedicalCoil()
    
    # Generate square wave
    time_array, signal = coil.generate_square_wave(duration=5, amplitude=1.0)
    
    # Analyze
    analysis = coil.analyze_signal(time_array, signal)
    coil.print_analysis(analysis)
    
    # Save to file (cross-platform compatible path)
    from pathlib import Path
    import tempfile
    temp_dir = tempfile.gettempdir()
    output_file = str(Path(temp_dir) / "cline_medical_coil_signal.json")
    metadata = {
        'mode': 'square',
        'purpose': 'Medical coil hardware driver',
        'warning': 'Research use only - NOT FDA approved'
    }
    coil.save_signal(time_array, signal, output_file, metadata)
    
    print(f"\n✅ Signal saved to: {output_file}")
    print(f"   This file can be loaded by hardware controllers")
    print(f"   Use with precision DAC for accurate waveform reproduction")
    print("\n✅ Example 5 complete")


def example_6_chi_alpha_calculation():
    """Example 6: Show chi/alpha coupling ratio calculation."""
    print("\n" + "="*80)
    print("EXAMPLE 6: Chi/Alpha Coupling Ratio")
    print("="*80)
    print("Demonstrates the physics behind 20.556 Hz")
    print("-"*80)
    
    print(f"\n📐 FUNDAMENTAL CONSTANTS:")
    print(f"   Chi (χ):   {CHI:.6f}  (Vacuum stability limit - Carl's discovery)")
    print(f"   Alpha (α): {ALPHA:.8f}  (Fine structure constant)")
    
    print(f"\n🔬 COUPLING RATIO:")
    print(f"   χ/α = {CHI} / {ALPHA:.8f}")
    print(f"       = {CHI/ALPHA:.6f} Hz")
    print(f"       = {CLINE_FREQUENCY:.6f} Hz")
    
    print(f"\n💡 PHYSICAL INTERPRETATION:")
    print(f"   Chi (χ): Vacuum tensile strength limit")
    print(f"   Alpha (α): Electromagnetic coupling strength")
    print(f"   χ/α: 'Gear ratio' between vacuum and matter")
    print(f"        = Resonance frequency of vacuum-matter interface")
    
    print(f"\n📚 COMPARISON TO LITERATURE:")
    print(f"   Literature: '~20 Hz' affects cells (empirical)")
    print(f"   Carl:        20.5556 Hz (theoretical derivation)")
    print(f"   Difference:  ~2.8% (within experimental error)")
    
    print(f"\n🎯 PRECISION REQUIREMENT:")
    print(f"   Target:    20.5556 Hz")
    print(f"   Tolerance: ±0.001 Hz (< 0.005%)")
    print(f"   Reason:    Sharp resonance, requires precision")
    
    print("\n✅ Example 6 complete")


def run_all_examples():
    """Run all examples in sequence."""
    print("\n" + "="*80)
    print("CLINE MEDICAL COIL - COMPLETE DEMONSTRATION SUITE")
    print("="*80)
    print("Running all examples...")
    print("="*80)
    
    examples = [
        ("Basic Square Wave", example_1_basic_square_wave),
        ("Scalar Pulse", example_2_scalar_pulse),
        ("Frequency Sweep", example_3_frequency_sweep),
        ("Waveform Comparison", example_4_waveform_comparison),
        ("Save to File", example_5_save_and_load),
        ("Chi/Alpha Physics", example_6_chi_alpha_calculation)
    ]
    
    for i, (name, func) in enumerate(examples, 1):
        print(f"\n{'='*80}")
        print(f"Running Example {i}/{len(examples)}: {name}")
        print(f"{'='*80}")
        
        try:
            func()
            print(f"\n✅ Example {i} completed successfully")
        except Exception as e:
            print(f"\n❌ Example {i} failed: {e}")
        
        if i < len(examples):
            print("\n" + "-"*80)
            input("Press Enter to continue to next example...")
    
    print("\n" + "="*80)
    print("ALL EXAMPLES COMPLETE")
    print("="*80)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Cline Medical Coil - Example Usage Demonstrations",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--example', type=int, choices=range(1, 7),
                        help='Run specific example (1-6)')
    parser.add_argument('--all', action='store_true',
                        help='Run all examples in sequence')
    parser.add_argument('--info', action='store_true',
                        help='Display scientific background')
    
    args = parser.parse_args()
    
    # Display header
    print("\n" + "="*80)
    print("Cline Medical Coil - Example Demonstrations")
    print("Carl Dean Cline Sr.'s 20.556 Hz Discovery")
    print("="*80)
    
    if args.info:
        print_scientific_background()
        return
    
    if args.all:
        run_all_examples()
        return
    
    if args.example:
        examples_map = {
            1: example_1_basic_square_wave,
            2: example_2_scalar_pulse,
            3: example_3_frequency_sweep,
            4: example_4_waveform_comparison,
            5: example_5_save_and_load,
            6: example_6_chi_alpha_calculation
        }
        examples_map[args.example]()
        return
    
    # No arguments - show menu
    print("\nAvailable Examples:")
    print("  1. Basic square wave generation")
    print("  2. Scalar pulse generation")
    print("  3. Frequency sweep analysis")
    print("  4. Waveform comparison")
    print("  5. Save signal to file")
    print("  6. Chi/alpha coupling calculation")
    print("\nUsage:")
    print("  python examples_medical_coil.py --example 1")
    print("  python examples_medical_coil.py --all")
    print("  python examples_medical_coil.py --info")
    print("\nOr run individual examples:")
    print("  python cline_medical_coil.py --mode square --duration 60")


if __name__ == "__main__":
    main()
