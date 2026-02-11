# =====================================================================
# MET / CAUSALITY LEAK SCAN (HTTP BYPASS)
# =====================================================================
import os, sys, subprocess
print(">>> INITIALIZING MET SCAN...")
subprocess.check_call([sys.executable, "-m", "pip", "install", "uproot", "awkward", "numpy", "--quiet"])
import uproot, numpy as np

# Target: 2012C Missing Energy Sector HTTP Node
url = "http://opendata.cern.ch/eos/opendata/cms/derived-data/NanoAODRun1/01-Jul-22/Run2012C_DoubleElectron/01C603DD-8434-4AF5-B67E-FFED504757F7.root"
local = "integrity_leak.root"

print(f">>> DOWNLOADING MET DATA: {url.split('/')[-1]}")
try:
    subprocess.run(["curl", "-L", "-m", "600", "-o", local, url], check=True)

    if os.path.exists(local) and os.path.getsize(local) > 1000000:
        print(f"✅ Download complete. Analyzing Transverse Energy...")
        with uproot.open(local) as f:
            met = f["Events"]["MET_pt"].array(library="np")
            max_leak = np.max(met)
            avg_leak = np.mean(met)

            print("\n" + "="*60)
            print("MET REPORT: CAUSALITY BOUND INTEGRITY")
            print("="*60)
            print(f"► EVENTS AUDITED: {len(met):,}")
            print(f"► MAX ENERGY LEAK: {max_leak:.2f} GeV")
            print(f"► AVG VACUUM TENSION: {avg_leak:.2f} GeV")
            print("="*60)
    else:
        print("❌ ERROR: Downloaded file is empty or missing.")
except Exception as e:
    print(f"❌ PROCESS FAILED: {e}")
finally:
    if os.path.exists(local): os.remove(local)
