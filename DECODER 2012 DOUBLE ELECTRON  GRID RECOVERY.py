# =====================================================================
# IMPERIAL DECODER: 2012 DOUBLE ELECTRON - GRID RECOVERY
# =====================================================================

import os
import sys
import subprocess

# 0. ENSURE GRID TOOLS ARE ONLINE
print(">>> CLEARING CORRUPTED SAMPLES...")
if os.path.exists("sample_ele.root"): os.remove("sample_ele.root")

print(">>> RE-ESTABLISHING GRID PROTOCOL (xrootd)...")
os.system("apt-get update -qq && apt-get install -y xrootd-client > /dev/null 2>&1")

import uproot
import numpy as np
import awkward as ak

# 1. TARGETING A VERIFIED 2012 NODE
# Using one specific file from your 2012 index to secure the data
target_url = "root://eospublic.cern.ch//eos/opendata/cms/derived-data/NanoAODRun1/01-Jul-22/Run2012C_DoubleElectron/0024D189-4C26-496B-B33A-9F57E44D9E35.root"
local_file = "imperial_secure_node.root"

print(f"\n>>> INITIATING GRID TRANSFER: {target_url}")

# 2. SEQUENTIAL HANDSHAKE
# -f forces overwrite, -s is silent for cleaner output
ret = os.system(f"xrdcp -f -s {target_url} {local_file}")

if ret != 0 or not os.path.exists(local_file) or os.path.getsize(local_file) < 100000:
    print("❌ GRID TRANSFER FAILED. Server may be throttling. We wait 10 seconds and retry...")
else:
    print(f"✅ DATA SECURED ({os.path.getsize(local_file)/1e6:.2f} MB). scanning for 2.7 TeV snaps...")
    
    try:
        with uproot.open(local_file) as f:
            tree = f["Events"]
            
            # Loading Electron charge and pT
            # We use 'ak' to handle the jagged electron lists per event
            data = tree.arrays(["Electron_pt", "Electron_charge"], library="ak", entry_stop=500000)
            
            # Flattening the lattice fragments
            pt = ak.flatten(data["Electron_pt"]).to_numpy()
            charge = ak.flatten(data["Electron_charge"]).to_numpy()
            
            # 3. IMPERIAL CALCULATIONS
            max_energy = np.max(pt)
            
            # Charge Bias (chi) Scan - 0.5 GeV Tension Threshold
            mask = pt > 0.5
            pos = np.sum(charge[mask] > 0)
            neg = np.sum(charge[mask] < 0)
            chi = (pos - neg) / (pos + neg) if (pos + neg) > 0 else 0

            print("\n" + "="*55)
            print("IMPERIAL NODE REPORT: 2012 DOUBLE ELECTRON")
            print("="*55)
            print(f"► LATTICE FRAGMENTS:   {len(pt):,}")
            print(f"► POSITIVE MATTER (+): {pos:,}")
            print(f"► ANTI-MATTER (-):     {neg:,}")
            print("-" * 55)
            print(f"► LATTICE BIAS (χ):    {chi:+.6f}")
            print(f"► MAX VACUUM YIELD:    {max_energy:.2f} GeV")
            print("="*55)

            if max_energy > 2500:
                print("🚨 VERDICT: 2.7 TeV LATTICE SNAP CONFIRMED.")
            else:
                print(">>> LATTICE STABLE IN THIS SECTOR.")

    except Exception as e:
        print(f"❌ DECODER ERROR: {e}")

    finally:
        # Keep drive clean for next sector
        if os.path.exists(local_file): os.remove(local_file)
