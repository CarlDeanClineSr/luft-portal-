#!/usr/bin/env python3
"""
create_gif_luft.py
Stitches chart_cycle_*.png files into an animated GIF (luft_relay.gif).

Usage:
    python3 scripts/create_gif_luft.py

Requirements:
    - imageio Python package
    - PNG files in charts/ directory matching pattern chart_cycle_*.png

Output:
    charts/luft_relay.gif (animated GIF)
"""
import re
from pathlib import Path

try:
    import imageio
except ImportError:
    print("ERROR: imageio package not found.")
    print("Please install it with: pip install imageio")
    raise SystemExit(1)

CHARTS_DIR = Path('charts')
OUTPUT_GIF = CHARTS_DIR / 'luft_relay.gif'

# Duration per frame in seconds (adjust for desired animation speed)
FRAME_DURATION = 0.5


def natural_sort_key(s):
    """
    Generate a sort key for natural sorting (1, 2, 10 instead of 1, 10, 2).
    """
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', str(s))]


def main():
    """Main GIF creation pipeline."""
    print("Starting GIF creation from cycle charts...")
    
    if not CHARTS_DIR.exists():
        print(f"ERROR: Charts directory {CHARTS_DIR} does not exist.")
        raise SystemExit(1)
    
    # Find all chart_cycle_*.png files
    cycle_charts = sorted(
        CHARTS_DIR.glob('chart_cycle_*.png'),
        key=natural_sort_key
    )
    
    if not cycle_charts:
        print(f"ERROR: No chart_cycle_*.png files found in {CHARTS_DIR}")
        print("\nPlease run save_cycle_charts.py first to generate cycle charts:")
        print("  python3 scripts/save_cycle_charts.py --cycle 1")
        print("  python3 scripts/save_cycle_charts.py --cycle 2")
        print("  etc.")
        raise SystemExit(1)
    
    print(f"\nFound {len(cycle_charts)} cycle chart(s):")
    for chart in cycle_charts:
        print(f"  - {chart.name}")
    
    # Read images
    images = []
    for chart in cycle_charts:
        try:
            img = imageio.imread(chart)
            images.append(img)
        except Exception as e:
            print(f"Warning: Could not read {chart.name}: {e}")
            continue
    
    if not images:
        print("ERROR: No valid images could be loaded.")
        raise SystemExit(1)
    
    # Create animated GIF
    print(f"\nCreating animated GIF: {OUTPUT_GIF}")
    print(f"Frame duration: {FRAME_DURATION}s per frame")
    
    try:
        imageio.mimsave(
            OUTPUT_GIF,
            images,
            duration=FRAME_DURATION,
            loop=0  # 0 means infinite loop
        )
        print(f"\n✓ Successfully created {OUTPUT_GIF}")
        print(f"  Total frames: {len(images)}")
        print(f"  Animation loops: infinite")
    except Exception as e:
        print(f"ERROR: Failed to create GIF: {e}")
        raise SystemExit(1)


if __name__ == '__main__':
    main()
