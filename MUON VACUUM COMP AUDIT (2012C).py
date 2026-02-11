# =====================================================================
# MULTI-NODE VACUUM AUDIT (HTTP/CURL BYPASS)
# =====================================================================
# INSTRUCTIONS: Change TARGET_SECTOR to 'Electron', 'Muon', or 'HeavyIon'

TARGET_SECTOR = 'Electron' 

import os
import sys
import subprocess

# 0. ENGINE STARTUP
print(f">>> BOOTING PROBE: {TARGET_SECTOR} SECTOR")
subprocess.check_call([sys.executable, "-m", "pip", "install", "uproot", "awkward", "numpy", "--quiet"])

import uproot
import numpy as np
import awkward as ak

# 1. SECTOR COORDINATES (Switched to HTTP)
if TARGET_SECTOR == 'Electron':
    base = "http://opendata.cern.ch/eos/opendata/cms/derived-data/NanoAODRun1/01-Jul-22/Run2012C_DoubleElectron/"
    uuids = ["0024D189-4C26-496B-B33A-9F57E44D9E35.root", "01C603DD-8434-4AF5-B67E-FFED504757F7.root", "2BE4C972-142D-4125-8480-3E621A27C6CB.root"]
    branch_p, branch_q = "Electron_pt", "Electron_charge"
elif TARGET_SECTOR == 'Muon':
    base = "http://opendata.cern.ch/eos/opendata/cms/derived-data/NanoAODRun1/01-Jul-22/Run2012C_DoubleMuParked/"
    uuids = ["00185A4E-4626-4D2A-937B-7369B70C92F8.root", "002C1F03-5E26-4B1F-A61A-28B36868B44F.root"]
    branch_p, branch_q = "Muon_pt", "Muon_charge"
else: # HeavyIon Fallback
    base = "http://opendata.cern.ch/eos/opendata/cms/Run2010B/HIHighPt/AOD/25Apr2013-v1/00000/"
    uuids = ["0034B803-0FB1-E211-89CD-003048D3FA18.root", "0046E565-A6B1-E211-850C-003048D2BF40.root"]
    branch_p, branch_q = "recoTracks_generalTracks__RECO.obj.pt_", "recoTracks_generalTracks__RECO.obj.charge_"

# 2. THE SCAN LOOP
print(f">>> COMMENCING SEQUENTIAL AUDIT OF {len(uuids)} NODES...")

for i, uuid in enumerate(uuids):
    local_file = "temp_sector.root"
    url = base + uuid
    
    try:
        print(f"\n[{i+1}/{len(uuids)}] DOWNLOADING NODE: {uuid[:8]}")
        
        # Using curl with a 10-minute maximum time limit (-m 600)
        # -L follows redirects, -o specifies output
        subprocess.run(["curl", "-L", "-m", "600", "-o", local_file, url], check=True)
        
        # Verify file exists and has significant size (>1MB) to prevent uproot crash
        if os.path.exists(local_file) and os.path.getsize(local_file) > 1000000:
            print(f"✅ Download complete ({(os.path.getsize(local_file)/1e6):.2f} MB). Analyzing...")
            with uproot.open(local_file) as f:
                tree = f["Events"]
                data = tree.arrays([branch_p, branch_q], library="ak", entry_stop=500000)
                
                p = ak.flatten(data[branch_p]).to_numpy()
                q = ak.flatten(data[branch_q]).to_numpy()
                
                # --- CALCULATION ---
                mask = p > 0.5 
                pos, neg = np.sum(q[mask] > 0), np.sum(q[mask] < 0)
                chi = (pos - neg) / (pos + neg) if (pos + neg) > 0 else 0
                yield_max = np.max(p)
                
                print(f"► BIAS (χ): {chi:+.6f} | MAX YIELD: {yield_max:.2f} GeV")
        else:
            print("❌ NODE ERROR: Downloaded file is empty, corrupted, or blocked by firewall.")
            
    except subprocess.TimeoutExpired:
        print("❌ NODE ERROR: Transfer timed out after 10 minutes. Moving to next node.")
    except subprocess.CalledProcessError as e:
        print(f"❌ NODE ERROR: curl failed with code {e.returncode}.")
    except Exception as e:
        print(f"❌ DATA ERROR: {e}")
    finally:
        if os.path.exists(local_file): 
            os.remove(local_file)

print("\n>>> SECTOR SCAN COMPLETE.")
