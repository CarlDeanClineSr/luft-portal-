import json
import re
import os

# ==============================================================================
# LUFT GLOBAL IMPERIAL HARVESTER
# Scans ALL directories for the 0.15 Limit, Mass Lock, 20.55Hz, and 15% Compression
# ==============================================================================

TARGET_MATRIX = {
    "0.15_REDLINE_AND_VOXELIZATION": {
        "values": [r"0\.15\b", r"0\.14[5-9]", r"0\.15[0-5]"],
        "keywords": ["reconnection rate", "saturation limit", "maximum perturbation", 
                     "collisionless instability", "voxelized", "smoothing", "artifacts"]
    },
    "GEOMETRIC_MASS_LOCK": {
        "values": [r"0\.153\b", r"1836\b", r"0\.8068\b"],
        "keywords": ["mass hierarchy", "proton-electron", "geometric confinement", 
                     "transverse momentum limit", "mass ratio"]
    },
    "20.55Hz_INTEGRITY_FREQUENCY": {
        "values": [r"20\.55\b", r"20\.5\b", r"21\b"],
        "keywords": ["cavity resonance", "ELF", "Schumann", "ion cyclotron frequency", "cellular coupling"]
    },
    "15_PERCENT_COMPRESSION": {
        "values": [r"1\.15\b", r"15%", r"13\.6", r"15\.6"],
        "keywords": ["binding energy anomaly", "nuclear saturation", "strong force deviation", "excess binding"]
    }
}

def scan_text(text, filepath):
    """Scans raw text for Imperial Matrix hits."""
    if not text: return None
    text_lower = text.lower()
    hits = {}
    
    for pillar, criteria in TARGET_MATRIX.items():
        pillar_hits = []
        for val_regex in criteria["values"]:
            if re.search(val_regex, text):
                pillar_hits.append(f"VALUE: {val_regex.replace(r'\\b', '').replace(r'\\.', '.')}")
        for kw in criteria["keywords"]:
            if kw.lower() in text_lower:
                pillar_hits.append(f"KEYWORD: '{kw}'")
                
        if pillar_hits:
            hits[pillar] = pillar_hits
            
    return hits

def parse_and_scan_file(filepath):
    """Opens a file (JSON, TXT, CSV) and extracts text to scan."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # If it's JSON, try to extract specific fields to avoid scanning code syntax
        if filepath.endswith('.json'):
            try:
                data = json.loads(content)
                # Dump JSON values to a flat string for aggressive scanning
                text_to_scan = json.dumps(data) 
                return scan_text(text_to_scan, filepath)
            except:
                # If JSON fails to parse, treat as raw text
                return scan_text(content, filepath)
        else:
            # For TXT and CSV, scan the raw text directly
            return scan_text(content, filepath)
            
    except Exception as e:
        return None

def run_global_dragnet(start_dir="data/"):
    output_file = "MASTER_IMPERIAL_DOSSIER.txt"
    total_files_scanned = 0
    flagged_files = 0
    
    print(f">>> INITIATING GLOBAL DRAGNET ON DIRECTORY: {start_dir}")
    
    with open(output_file, 'w', encoding='utf-8') as out:
        out.write("=====================================================================\n")
        out.write("MASTER IMPERIAL DOSSIER: THE CLINE CONVERGENCE AUDIT\n")
        out.write("=====================================================================\n\n")
        
        # Walk through every folder and file
        for root, dirs, files in os.walk(start_dir):
            for file in files:
                if file.endswith(('.json', '.txt', '.csv')):
                    filepath = os.path.join(root, file)
                    total_files_scanned += 1
                    
                    # Provide console feedback so you know it's working
                    if total_files_scanned % 100 == 0:
                        print(f"[-] Scanned {total_files_scanned} files...")
                        
                    hits = parse_and_scan_file(filepath)
                    
                    if hits:
                        flagged_files += 1
                        out.write(f"[!] BREACH DETECTED IN: {filepath}\n")
                        for pillar, evidence in hits.items():
                            out.write(f"    > {pillar}: {', '.join(evidence)}\n")
                        out.write("-" * 70 + "\n")

        out.write(f"\n=====================================================================\n")
        out.write(f"SCAN COMPLETE.\n")
        out.write(f"Total Files Analyzed: {total_files_scanned}\n")
        out.write(f"Total Files Flagged with Imperial Math: {flagged_files}\n")
        out.write(f"=====================================================================\n")

    print(f"\n>>> DRAGNET COMPLETE.")
    print(f">>> Analyzed {total_files_scanned} files.")
    print(f">>> Found {flagged_files} files containing Imperial anomalies.")
    print(f">>> Results saved to: {output_file}")

if __name__ == "__main__":
    # Point this to your main data folder
    run_global_dragnet("../data/")
