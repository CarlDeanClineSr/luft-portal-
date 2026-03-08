import yaml
import subprocess
import datetime
import os

with open("luft_queries_automated.yml", "r") as f:
    config = yaml.safe_load(f)

global_cfg = config["global"]
queries = config["queries"]

os.makedirs(global_cfg["output_dir"], exist_ok=True)
os.makedirs(global_cfg["scripts_dir"], exist_ok=True)

log_path = global_cfg["log_file"]
with open(log_path, "a") as log:
    log.write(f"\n=== LUFT Engine Run @ {datetime.datetime.utcnow()} ===\n")

for q in queries:
    if not q.get("auto_run", False):
        continue

    print(f"Running: {q['title']} (ID: {q['id']})")
    script_path = os.path.join(global_cfg["scripts_dir"], q["script"])

    # Build command (example: python chi_validator.py --data dscovr.json --window 24)
    cmd = ["python", script_path]
    for k, v in q["params"].items():
        cmd.extend([f"--{k}", str(v)])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        with open(log_path, "a") as log:
            log.write(f"[SUCCESS] {q['id']} - {result.stdout}\n")
        print("Success!")
    except Exception as e:
        with open(log_path, "a") as log:
            log.write(f"[ERROR] {q['id']} - {str(e)}\n")
        print("Failed:", e)
