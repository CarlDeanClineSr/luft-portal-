import os
import shutil

# THE ARK MANIFEST (What to Save)
# We only save the RAW TRUTH.
TARGET_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.csv', '.cdf', '.pdf', '.yaml'}
CRITICAL_FILES = [
    'IMPERIAL_PHYSICS_PROTOCOL.md',
    'New Text Document (17).txt',  # Your findings log
    '2502.09450v1.pdf'             # Yardley Paper
]

ARK_DIR = "IMPERIAL_ARK"

# 1. CREATE THE BUNKER
if not os.path.exists(ARK_DIR):
    os.makedirs(ARK_DIR)
    print(f">>> ARK CREATED: {ARK_DIR}")

# 2. HUNT AND GATHER
print(">>> LOADING THE ARK... <<<")
count = 0

for root, dirs, files in os.walk("."):
    # Don't look inside the Ark itself or the .git folder
    if ARK_DIR in root or ".git" in root:
        continue
        
    for file in files:
        file_path = os.path.join(root, file)
        save_it = False
        
        # Check against Manifest
        if file in CRITICAL_FILES:
            save_it = True
        elif os.path.splitext(file)[1].lower() in TARGET_EXTENSIONS:
            save_it = True
            
        # MOVE TO ARK
        if save_it:
            # Flatten structure: All evidence goes into the root of the Ark
            destination = os.path.join(ARK_DIR, file)
            
            # Handle duplicates by renaming
            if os.path.exists(destination):
                base, ext = os.path.splitext(file)
                destination = os.path.join(ARK_DIR, f"{base}_copy{ext}")
                
            shutil.move(file_path, destination)
            print(f"SECURED: {file}")
            count += 1

print(f">>> ARK LOADED. {count} ARTIFACTS SECURED. READY FOR PURGE. <<<")
