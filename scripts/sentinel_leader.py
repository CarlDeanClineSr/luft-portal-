# =====================================================================
# SENTINEL CONTROL LEADER v2.1: OMNI-DATA AGGREGATOR (PATCHED)
# =====================================================================
import os
import datetime

output_file = "SENTINEL_MASTER_REPORT.txt"

# Explicitly blacklisting the massive star data files and generic dependencies
ignore_list = [
    "requirements.txt", 
    "README.md", 
    "CMakeLists.txt", 
    "Star_data.md",                  # <--- Added to prevent data flood
    "Repository Knowledge Index.md", # <--- Added to prevent index flood
    output_file
]

target_extensions = [".txt", ".log", ".csv", ".md"]

print(">>> INITIALIZING SENTINEL OMNI-SCANNER v2.1...")

with open(output_file, "w", encoding="utf-8") as master:
    master.write("="*80 + "\n")
    master.write(f"IMPERIAL SENTINEL MASTER REPORT (v2.1)\n")
    master.write(f"TIMESTAMP: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC\n")
    master.write("="*80 + "\n\n")

    file_count = 0
    
    # Sweep the entire repository structure
    for root, dirs, files in os.walk("."):
        # Ignore hidden directories to speed up the scan
        if "/." in root or root.startswith((".", "..")) and root != ".":
            continue
            
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            
            # Target Logs, Time-Stamped Rows (CSV), and Reports/Papers (MD)
            if ext in target_extensions and file not in ignore_list:
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        lines = f.readlines()
                        if not lines:
                            continue
                            
                        file_count += 1
                        master.write(f"--- SOURCE: {file_path} ---\n")
                        
                        # FORMAT 1: Time-Stamped Data (CSVs)
                        if ext == ".csv":
                            master.write(lines[0]) # Always grab the header
                            if len(lines) > 6:
                                master.write("... [DATA TRUNCATED] ...\n")
                            master.writelines(lines[-5:]) # Grab the 5 most recent rows
                            
                        # FORMAT 2: Papers, Capsules, and Markdown Reports
                        elif ext == ".md":
                            master.writelines(lines[:10]) # Grab the Title and Summary
                            if len(lines) > 15:
                                master.write("\n... [CONTENT TRUNCATED] ...\n\n")
                                master.writelines(lines[-5:]) # Grab the conclusion
                                
                        # FORMAT 3: Standard Logs and Text Files
                        else:
                            master.writelines(lines[-20:]) # Grab the latest 20 lines
                            
                except Exception as e:
                    master.write(f"[Read Error: {e}]\n")
                
                master.write("\n" + "-" * 80 + "\n\n")

    master.write(f"TOTAL FILES CONSOLIDATED: {file_count}\n")
    master.write("="*80 + "\n")

print(f">>> OMNI-SCAN COMPLETE. {file_count} files merged. Flooding prevented.")
