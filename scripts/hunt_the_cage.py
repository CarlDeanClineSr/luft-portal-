import os
import re

# TARGET: The specific patterns they use to define the "Cage"
# We look for "bins", "edges", "voxel", and the specific numbers from the PDF.
PATTERNS = {
    "GRID_DEFINITION": r"(?i)(binning|voxelization|grid|segmentation)\s*[:=]\s*\[",
    "HARDCODED_NUMBERS": r"(?i)(1680|382|0\.15|0\.025)",  # The tell-tale signs
    "R_BINS": r"(?i)(n_r|r_bins|radial_bins)\s*=\s*\d+",
    "ALPHA_BINS": r"(?i)(n_alpha|n_phi|angular_bins)\s*=\s*\d+"
}

def scan_file(filepath):
    """Scans a single file for evidence of the Cage."""
    evidence_found = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                line = line.strip()
                for key, pattern in PATTERNS.items():
                    if re.search(pattern, line):
                        evidence_found.append(f"  [Line {i+1}] {key}: {line}")
    except Exception as e:
        pass # Skip unreadable files
    return evidence_found

def hunt_the_cage(root_dir):
    """Recursively crawls the directory to find the definitions."""
    print(f"[*] IMPERIAL SCAN INITIATED ON: {root_dir}")
    print("[*] Hunting for Voxelization Hardcoding...")
    print("-" * 60)
    
    hits = 0
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(('.py', '.yaml', '.json', '.cpp', '.h', '.xml')):
                fullpath = os.path.join(root, file)
                evidence = scan_file(fullpath)
                if evidence:
                    print(f"\n[+] SUSPECT FILE LOCATED: {fullpath}")
                    for item in evidence:
                        print(item)
                    hits += 1

    print("-" * 60)
    if hits == 0:
        print("[!] No hardcoded cages found. They might be hiding it in binary.")
    else:
        print(f"[*] SCAN COMPLETE. {hits} FILES IDENTIFIED AS CONTAINING GRID DEFINITIONS.")
        print("[*] These are the lines where they delete the 0.15 steps.")

# To run this, save as hunt_the_cage.py and run in the folder where you cloned their code.
# Example usage:
# hunt_the_cage("./datasetshowcase")
