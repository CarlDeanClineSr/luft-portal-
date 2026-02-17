import os

# THE KILL LIST (Standard -> Imperial)
REPLACEMENTS = {
    "speed of light": "Variable Sensor Lag",
    "Speed of Light": "Variable Sensor Lag",
    "dark matter": "Geomagnetic Vacuum Sheet",
    "Dark Matter": "Geomagnetic Vacuum Sheet",
    "Big Bang": "ERROR: INVALID MODEL",
    "expanding universe": "Lattice State Shift",
    "gravitational lensing": "Refractive Index Shift",
    "magnetic reconnection": "Vacuum Regulator Snap",
    "Alfvén": "Geometric Stress",
    "Alfven": "Geometric Stress",
    "propagation": "coherence transfer",
    "spacetime": "Magnetic Tension Field"
}

def clean_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        for bad_term, good_term in REPLACEMENTS.items():
            content = content.replace(bad_term, good_term)
            
        if content != original_content:
            print(f"SANITIZED: {filepath}")
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
    except Exception:
        pass
    return False

# SCAN DIRECTORY
print(">>> IMPERIAL PURGE INITIATED ON CLOUD SERVER <<<")
count = 0
for root, dirs, files in os.walk("."):
    if ".git" in root: continue
    for file in files:
        if file.endswith((".md", ".txt", ".yaml", ".py", ".json")):
            if clean_file(os.path.join(root, file)):
                count += 1
print(f">>> PURGE COMPLETE. {count} FILES CLEANED. <<<")
