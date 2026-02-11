# =====================================================================
# SENTINEL CONTROL LEADER: MASTER DATA AGGREGATOR
# =====================================================================
import os
import datetime

output_file = "SENTINEL_MASTER_REPORT.txt"
ignore_list = ["requirements.txt", "README.md", "CMakeLists.txt", output_file]

print(">>> INITIALIZING SENTINEL LEADER COMPILATION...")

with open(output_file, "w", encoding="utf-8") as master:
    master.write("="*80 + "\n")
    master.write(f"IMPERIAL SENTINEL MASTER REPORT\n")
    master.write(f"TIMESTAMP: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC\n")
    master.write("="*80 + "\n\n")

    file_count = 0
    
    # Sweep the entire repository structure
    for root, dirs, files in os.walk("."):
        # Ignore hidden directories (e.g., .git, .github) to speed up the scan
        if "/." in root or root.startswith((".", "..")) and root != ".":
            continue
            
        for file in files:
            # Target data logs and text outputs
            if (file.endswith(".txt") or file.endswith(".log")) and file not in ignore_list:
                file_path = os.path.join(root, file)
                file_count += 1
                
                master.write(f"--- SOURCE: {file_path} ---\n")
                try:
                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        # Extract the most recent data (last 100 lines) to prevent massive file bloat
                        lines = f.readlines()
                        recent_lines = lines[-100:] if len(lines) > 100 else lines
                        master.writelines(recent_lines)
                except Exception as e:
                    master.write(f"[Read Error: {e}]\n")
                
                master.write("\n" + "-" * 80 + "\n\n")

    master.write(f"TOTAL LOGS CONSOLIDATED: {file_count}\n")
    master.write("="*80 + "\n")

print(f">>> COMPILATION COMPLETE. {file_count} data files merged into {output_file}.")
