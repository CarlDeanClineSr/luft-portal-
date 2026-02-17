#!/usr/bin/env python3
"""
NSVS 2354429 Pulse Visualization

This script visualizes the light curve of NSVS 2354429, showing a dramatic
brightness pulse anomaly. The star normally sits at Magnitude 12.5 but showed
a brief excursion to Magnitude 10.317 - representing a 7.7× increase in brightness.

This is "The Heartbeat of the Schmidt Star" - demonstrating that this is not
dust obscuration (which dims stars) but rather an energy event.
"""

import matplotlib.pyplot as plt
import pandas as pd
import os

# Data constants
PULSE_MAGNITUDE_THRESHOLD = 11.0  # Magnitude threshold to separate pulse from quiet state

# The raw data from ASAS-SN light curve
# HJD: Heliocentric Julian Date
# mag: Apparent Magnitude (lower = brighter)
data = [
    {"hjd": 2456598.014, "mag": 12.509}, {"hjd": 2456625.870, "mag": 12.564},
    {"hjd": 2456884.126, "mag": 12.561}, {"hjd": 2456932.071, "mag": 12.555},
    {"hjd": 2456988.979, "mag": 12.550}, {"hjd": 2456991.891, "mag": 12.547},
    # THE ANOMALY - Massive brightness increase
    {"hjd": 2456999.929, "mag": 10.317}, 
    # Recovery back to baseline
    {"hjd": 2457005.066, "mag": 12.542}, {"hjd": 2457007.091, "mag": 12.538},
    {"hjd": 2457032.902, "mag": 12.510}, {"hjd": 2457084.824, "mag": 12.512}
]

df = pd.DataFrame(data)

# Setup the Plot
plt.figure(figsize=(12, 7))

# Plot the "Quiet" points (normal state)
quiet = df[df['mag'] > PULSE_MAGNITUDE_THRESHOLD]
plt.scatter(quiet['hjd'], quiet['mag'], color='blue', s=80, 
           label='Vacuum State (Quiet)', alpha=0.7, edgecolors='darkblue', linewidths=1)

# Calculate statistics for labeling
pulse = df[df['mag'] < PULSE_MAGNITUDE_THRESHOLD]

# Validate that pulse data exists (it should for NSVS 2354429)
if len(pulse) == 0:
    raise ValueError("No pulse event found in data. Check magnitude threshold.")

pulse_mag = pulse['mag'].values[0]

# Plot the "Pulse" point (anomaly)
plt.scatter(pulse['hjd'], pulse['mag'], color='red', s=300, 
           label=f'High Energy Pulse (Mag {pulse_mag:.2f})', marker='*', 
           edgecolors='darkred', linewidths=2, zorder=5)

# Calculate additional statistics for annotations
baseline_mag = quiet['mag'].mean()
pulse_hjd = pulse['hjd'].values[0]
# Convert magnitude difference to brightness ratio using Pogson's equation
# Brightness ratio = 10^(Δmag/2.5), where Δmag is the magnitude difference
delta_mag = baseline_mag - pulse_mag
brightness_increase = 10**(delta_mag / 2.5)

# Add a horizontal line showing the baseline
plt.axhline(y=baseline_mag, color='gray', linestyle='--', linewidth=1, 
           alpha=0.5, label=f'Baseline (Mag {baseline_mag:.2f})')

# Formatting (Astronomy standard: Invert Y axis so brighter is up)
plt.gca().invert_yaxis()
plt.title("NSVS 2354429: The 'Digital' Pulse Anomaly\n" + 
         "The Heartbeat of the Schmidt Star", fontsize=16, fontweight='bold')
plt.xlabel("Time (HJD - Heliocentric Julian Date)", fontsize=13)
plt.ylabel("Magnitude (Brightness →)", fontsize=13)
plt.grid(True, which='both', linestyle='--', alpha=0.3)
plt.legend(fontsize=11, loc='best')

# Add annotation for the pulse (data is guaranteed to exist at this point)
plt.annotate(f'Δmag = {delta_mag:.2f}\n~{brightness_increase:.1f}× brighter',
            xy=(pulse_hjd, pulse_mag), xytext=(pulse_hjd + 30, pulse_mag + 0.8),
            fontsize=10, ha='left',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7),
            arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.3',
                          color='red', linewidth=2))

# Add text box with interpretation
textstr = 'INTERPRETATION:\n'
textstr += '• Blue points: Star at rest (Mag ~12.5)\n'
textstr += f'• Red star: Energy pulse event (Mag {pulse_mag:.2f})\n'
textstr += '• This is NOT dust (dust dims stars)\n'
textstr += f'• This IS an energy event ({brightness_increase:.1f}× brightness increase)'

props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
plt.text(0.02, 0.98, textstr, transform=plt.gca().transAxes, fontsize=10,
        verticalalignment='top', bbox=props)

# Tighten layout
plt.tight_layout()

# Ensure output directory exists
os.makedirs('figures', exist_ok=True)

# Save the figure
output_file = 'figures/nsvs_2354429_pulse_visualization.png'
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"Visualization saved to: {output_file}")

# Show the graph
plt.show()

# Print summary statistics
print("\n" + "="*60)
print("NSVS 2354429 PULSE ANALYSIS SUMMARY")
print("="*60)
print(f"Baseline magnitude: {baseline_mag:.3f}")
print(f"Pulse magnitude: {pulse_mag:.3f}")
print(f"Magnitude change: {delta_mag:.3f} mag")
print(f"Brightness increase: {brightness_increase:.2f}×")
print(f"Duration: Single observation at HJD {pulse_hjd:.3f}")
print("\nThis represents a transient energy event, not dust obscuration.")
print("="*60)
