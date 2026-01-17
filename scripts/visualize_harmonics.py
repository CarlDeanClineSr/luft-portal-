#!/usr/bin/env python3
"""
visualize_harmonics.py
======================
Visualize harmonic mode transitions from PSP encounter data.

Creates a timeline showing when the vacuum lattice shifted between
Mode 1 (Fundamental), Mode 2 (First Harmonic), and Mode 3 (Second Harmonic).

Author: Carl Dean Cline Sr. + Copilot Agent Task
Date: January 17, 2026
"""

import json
import argparse
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np

# Color scheme for modes
MODE_COLORS = {
    1: '#00ff00',  # Green - Fundamental (calm)
    2: '#ffaa00',  # Orange - First Harmonic (energized)
    3: '#ff0000',  # Red - Second Harmonic (extreme)
    4: '#ff00ff'   # Magenta - Violation (critical)
}

MODE_LABELS = {
    1: 'Mode 1: Fundamental (χ≤0.15)',
    2: 'Mode 2: First Harmonic (χ≤0.30)',
    3: 'Mode 3: Second Harmonic (χ≤0.45)',
    4: 'VIOLATION (χ>0.45)'
}


def load_harmonic_data(json_path):
    """Load harmonic analysis JSON file."""
    with open(json_path, 'r') as f:
        return json.load(f)


def plot_encounter_harmonics(json_path, output_path):
    """Create a timeline plot of harmonic mode transitions for a single encounter."""
    
    data = load_harmonic_data(json_path)
    transitions = data['mode_transitions']
    
    if not transitions:
        print(f"⚠️  No transitions found in {json_path}")
        return
    
    # Extract encounter number from filename
    encounter = Path(json_path).stem.replace('encounter', '').replace('_harmonics', '')
    
    # Prepare data for plotting
    timestamps = []
    modes = []
    
    for trans in transitions:
        try:
            ts = datetime.fromisoformat(trans['timestamp'].replace('Z', '+00:00'))
            timestamps.append(ts)
            modes.append(trans['to_mode'])
        except Exception as e:
            print(f"Warning: Could not parse timestamp: {trans['timestamp']}")
            continue
    
    if not timestamps:
        print(f"⚠️  No valid timestamps in {json_path}")
        return
    
    # Create figure
    fig, ax = plt.subplots(figsize=(14, 6))
    
    # Plot transitions as vertical colored bars
    for i in range(len(timestamps) - 1):
        start_time = timestamps[i]
        end_time = timestamps[i + 1]
        mode = modes[i]
        
        # Determine if we should add a label (first occurrence of each mode)
        should_label = (i == 0 or modes[i] != modes[i-1])
        label = MODE_LABELS.get(mode, f'Mode {mode}') if should_label else ''
        
        ax.axvspan(start_time, end_time, 
                   alpha=0.5, 
                   color=MODE_COLORS.get(mode, '#888888'),
                   label=label)
    
    # Handle the final mode (extend to a reasonable end time)
    if len(timestamps) > 0:
        final_start = timestamps[-1]
        # Extend final mode by the average time delta
        if len(timestamps) > 1:
            avg_delta = (timestamps[-1] - timestamps[0]) / (len(timestamps) - 1)
            final_end = timestamps[-1] + avg_delta
        else:
            # Single timestamp - extend by 1 hour
            final_end = timestamps[-1] + timedelta(hours=1)
        
        final_mode = modes[-1]
        # Check if we should label (avoid IndexError for single mode)
        should_label = len(modes) == 1 or modes[-1] != modes[-2]
        label = MODE_LABELS.get(final_mode, f'Mode {final_mode}') if should_label else ''
        
        ax.axvspan(final_start, final_end, 
                   alpha=0.5, 
                   color=MODE_COLORS.get(final_mode, '#888888'),
                   label=label)
    
    # Plot transition points
    ax.scatter(timestamps, modes, c=[MODE_COLORS.get(m, '#888888') for m in modes], 
               s=100, zorder=5, edgecolors='black', linewidths=1.5)
    
    # Formatting
    ax.set_xlabel('Time', fontsize=12, fontweight='bold')
    ax.set_ylabel('Harmonic Mode', fontsize=12, fontweight='bold')
    ax.set_title(f'PSP Encounter {encounter}: Vacuum Lattice Harmonic Transitions\n' + 
                 f'Carl Dean Cline Sr.\'s Discovery: χ Resonates in Modes (0.15, 0.30, 0.45)',
                 fontsize=14, fontweight='bold', pad=20)
    
    # Y-axis
    ax.set_ylim(0.5, 4.5)
    ax.set_yticks([1, 2, 3, 4])
    ax.set_yticklabels(['Mode 1\n(χ≤0.15)', 'Mode 2\n(χ≤0.30)', 'Mode 3\n(χ≤0.45)', 'VIOLATION\n(χ>0.45)'])
    
    # X-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    plt.xticks(rotation=45, ha='right')
    
    # Grid
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_facecolor('#f0f0f0')
    
    # Legend (remove duplicates)
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), 
              loc='upper left', framealpha=0.9, fontsize=10)
    
    # Statistics box
    profile = data['resonance_profile']
    stats_text = (f"Mode 1: {profile['mode_1_fundamental_pct']}%\n"
                  f"Mode 2: {profile['mode_2_harmonic_pct']}%\n"
                  f"Mode 3: {profile['mode_3_harmonic_pct']}%\n"
                  f"Violations: {profile['violations_pct']}%")
    
    ax.text(0.98, 0.97, stats_text, 
            transform=ax.transAxes, 
            verticalalignment='top', 
            horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
            fontsize=10, fontfamily='monospace')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Saved: {output_path}")


def plot_multi_encounter_summary(harmonics_dir, output_path):
    """Create a summary plot comparing harmonic profiles across all encounters."""
    
    # Find all harmonic JSON files
    json_files = sorted(Path(harmonics_dir).glob('encounter*_harmonics.json'))
    
    if not json_files:
        print(f"⚠️  No harmonic JSON files found in {harmonics_dir}")
        return
    
    encounters = []
    mode1_pcts = []
    mode2_pcts = []
    mode3_pcts = []
    viol_pcts = []
    
    for json_file in json_files:
        data = load_harmonic_data(json_file)
        encounter = json_file.stem.replace('encounter', '').replace('_harmonics', '')
        
        encounters.append(f"E{encounter}")
        profile = data['resonance_profile']
        mode1_pcts.append(profile['mode_1_fundamental_pct'])
        mode2_pcts.append(profile['mode_2_harmonic_pct'])
        mode3_pcts.append(profile['mode_3_harmonic_pct'])
        viol_pcts.append(profile['violations_pct'])
    
    # Create stacked bar chart
    fig, ax = plt.subplots(figsize=(12, 7))
    
    x = np.arange(len(encounters))
    width = 0.6
    
    p1 = ax.bar(x, mode1_pcts, width, label='Mode 1 (χ≤0.15)', color=MODE_COLORS[1])
    p2 = ax.bar(x, mode2_pcts, width, bottom=mode1_pcts, label='Mode 2 (χ≤0.30)', color=MODE_COLORS[2])
    
    mode12_sum = [m1 + m2 for m1, m2 in zip(mode1_pcts, mode2_pcts)]
    p3 = ax.bar(x, mode3_pcts, width, bottom=mode12_sum, label='Mode 3 (χ≤0.45)', color=MODE_COLORS[3])
    
    mode123_sum = [m12 + m3 for m12, m3 in zip(mode12_sum, mode3_pcts)]
    p4 = ax.bar(x, viol_pcts, width, bottom=mode123_sum, label='Violations (χ>0.45)', color=MODE_COLORS[4])
    
    # Formatting
    ax.set_xlabel('PSP Encounter', fontsize=12, fontweight='bold')
    ax.set_ylabel('Percentage of Observations (%)', fontsize=12, fontweight='bold')
    ax.set_title('PSP Multi-Encounter Harmonic Mode Distribution\n' +
                 'Carl Dean Cline Sr.\'s Discovery: Vacuum Lattice Resonance Structure',
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(encounters)
    ax.legend(loc='upper right', framealpha=0.9)
    ax.set_ylim(0, 100)
    ax.grid(True, alpha=0.3, axis='y', linestyle='--')
    ax.set_facecolor('#f0f0f0')
    
    # Add percentage labels on bars
    for i in x:
        y_offset = 0
        for pct in [mode1_pcts[i], mode2_pcts[i], mode3_pcts[i], viol_pcts[i]]:
            if pct > 2:  # Only label if segment is visible
                ax.text(i, y_offset + pct/2, f'{pct:.1f}%', 
                        ha='center', va='center', fontsize=9, fontweight='bold')
            y_offset += pct
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Saved: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Visualize PSP harmonic mode transitions",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--dir', type=str, required=True,
                        help='Directory containing harmonic JSON files')
    parser.add_argument('--output-dir', type=str, default='figures/harmonics',
                        help='Output directory for plots (default: figures/harmonics)')
    
    args = parser.parse_args()
    
    harmonics_dir = Path(args.dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║  PSP HARMONIC MODE VISUALIZATION                                   ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print()
    
    # Find all harmonic JSON files
    json_files = sorted(harmonics_dir.glob('encounter*_harmonics.json'))
    
    if not json_files:
        print(f"❌ No harmonic JSON files found in {harmonics_dir}")
        print("Run batch_harmonic_scan.sh first.")
        return 1
    
    print(f"Found {len(json_files)} encounter(s) to visualize")
    print()
    
    # Plot individual encounters
    for json_file in json_files:
        encounter = json_file.stem.replace('encounter', '').replace('_harmonics', '')
        output_path = output_dir / f'encounter{encounter}_harmonic_timeline.png'
        
        print(f"Plotting Encounter {encounter}...")
        plot_encounter_harmonics(json_file, output_path)
    
    # Plot multi-encounter summary
    print("\nGenerating multi-encounter summary...")
    summary_path = output_dir / 'multi_encounter_harmonic_summary.png'
    plot_multi_encounter_summary(harmonics_dir, summary_path)
    
    print()
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║  VISUALIZATION COMPLETE                                             ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print()
    print(f"📁 Output directory: {output_dir}")
    print()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
