# =====================================================================
# DATA-DRIVEN TERMINOLOGY SCRUBBER 
# Replaces old-world math/theory lingo with grounded magnetic terminology
# =====================================================================
import os
import re

# The exact file types we want to clean
TARGET_EXTENSIONS = [".txt", ".md", ".csv", ".yaml", ".yml", ".html"]

# The dictionary of words to scrub. 
# (?i) makes it case-insensitive so it catches LATTICE, Lattice, and lattice.
# \b ensures it only catches whole words so it doesn't break code.
# You can change the right side of the colon to whatever fits the data best.

SCRUB_DICT = {
    r'(?i)\blattice\b': 'vacuum',
    r'(?i)\bgrid\b': 'vacuum',
    r'(?i)\bfluidic\b': 'magnetic',
    r'(?i)\bgeometric\b': 'magnetic',
    r'(?i)\bnode\b': 'focal point',
    r'(?i)\btheory\b': '',             # Leaves a blank
    r'(?i)\bluft\b': '',               # Leaves a blank
    r'(?i)\btheoretical\b': 'measured' # Grounding the lingo
}

print(">>> INITIALIZING TERMINOLOGY SCRUBBER...")

files_modified = 0
replacements_made = 0

# Sweep the repository
for root, dirs, files in os.walk("."):
    # Ignore hidden folders like .git
    if "/." in root or root.startswith((".", "..")) and root != ".":
        continue
        
    for file in files:
        ext = os.path.splitext(file)[1].lower()
        
        if ext in TARGET_EXTENSIONS:
            file_path = os.path.join(root, file)
            
            try:
                # Read the file
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                
                original_content = content
                
                # Apply all replacements
                for old_word, new_word in SCRUB_DICT.items():
                    content, count = re.subn(old_word, new_word, content)
                    replacements_made += count
                
                # If changes were made, write them back to the file
                if content != original_content:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    files_modified += 1
                    print(f"Cleaned: {file_path}")
                    
            except Exception as e:
                print(f"[Error reading {file_path}: {e}]")

print("="*80)
print(f">>> SCRUB COMPLETE. Modified {files_modified} files with {replacements_made} term replacements.")
print("="*80)
