#!/usr/bin/env python3
"""
create_gif_luft.py
==================
Create an animated GIF from cycle chart PNG files.

This script reads all chart_cycle_*.png files from the charts/ directory
and combines them into an animated GIF (luft_relay.gif).

Usage:
    python3 scripts/create_gif_luft.py
    python3 scripts/create_gif_luft.py --duration 1.0  # Custom frame duration

Requirements:
    - imageio (install with: pip install imageio)
    - Pillow (install with: pip install Pillow)

Author: Carl Dean Cline Sr.
Repository: https://github.com/CarlDeanClineSr/luft-portal-
"""

import argparse
import sys
from pathlib import Path
from typing import List

try:
    import imageio
except ImportError:
    print("ERROR: imageio package not found.")
    print("Install with: pip install imageio")
    sys.exit(1)


def find_cycle_charts(charts_dir: Path) -> List[Path]:
    """
    Find all chart_cycle_*.png files in the charts directory.
    
    Args:
        charts_dir: Path to charts directory
    
    Returns:
        Sorted list of chart PNG file paths
    """
    # Find all cycle chart PNGs
    cycle_charts = sorted(charts_dir.glob('chart_cycle_*.png'))
    
    if not cycle_charts:
        print(f"WARNING: No chart_cycle_*.png files found in {charts_dir}")
        # Also check for any PNG files
        any_pngs = sorted(charts_dir.glob('*.png'))
        if any_pngs:
            print(f"Found {len(any_pngs)} other PNG file(s), using them instead:")
            for png in any_pngs:
                print(f"  - {png.name}")
            return any_pngs
        else:
            print("No PNG files found at all.")
            return []
    
    return cycle_charts


def create_gif(image_paths: List[Path], output_path: Path, duration: float = 0.5) -> None:
    """
    Create an animated GIF from a list of image files.
    
    Args:
        image_paths: List of paths to image files
        output_path: Path where the GIF should be saved
        duration: Duration of each frame in seconds (default: 0.5)
    """
    if not image_paths:
        print("ERROR: No images to create GIF from")
        sys.exit(1)
    
    print(f"Creating GIF from {len(image_paths)} frame(s):")
    for img_path in image_paths:
        print(f"  - {img_path.name}")
    
    # Read all images
    images = []
    for img_path in image_paths:
        try:
            img = imageio.imread(img_path)
            images.append(img)
        except Exception as e:
            print(f"WARNING: Could not read {img_path}: {e}")
            continue
    
    if not images:
        print("ERROR: Failed to read any images")
        sys.exit(1)
    
    # Write GIF
    try:
        imageio.mimsave(
            output_path,
            images,
            duration=duration,
            loop=0  # Infinite loop
        )
        print(f"\nSuccessfully created {output_path}")
        print(f"  Frames: {len(images)}")
        print(f"  Duration per frame: {duration}s")
        print(f"  Total duration: {len(images) * duration}s")
    except Exception as e:
        print(f"ERROR: Failed to create GIF: {e}")
        sys.exit(1)


def main():
    """Main entry point for GIF creation script."""
    parser = argparse.ArgumentParser(
        description='Create animated GIF from cycle chart PNGs'
    )
    parser.add_argument(
        '--duration',
        '-d',
        type=float,
        default=0.5,
        help='Duration of each frame in seconds (default: 0.5)'
    )
    parser.add_argument(
        '--output',
        '-o',
        type=str,
        default='charts/luft_relay.gif',
        help='Output GIF path (default: charts/luft_relay.gif)'
    )
    
    args = parser.parse_args()
    
    # Setup paths
    charts_dir = Path('charts')
    output_path = Path(args.output)
    
    # Ensure charts directory exists
    if not charts_dir.exists():
        print(f"ERROR: Charts directory not found: {charts_dir}")
        sys.exit(1)
    
    # Find cycle chart images
    image_paths = find_cycle_charts(charts_dir)
    
    if not image_paths:
        print("\nNo images found to create GIF.")
        print("Run these scripts first:")
        print("  python3 scripts/save_cycle_charts.py --cycle 1")
        print("  python3 scripts/save_cycle_charts.py --cycle 2")
        print("  (etc.)")
        sys.exit(1)
    
    # Create the GIF
    create_gif(image_paths, output_path, duration=args.duration)


if __name__ == '__main__':
    main()
