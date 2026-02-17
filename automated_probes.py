# =====================================================================
# IMPERIAL AUTOMATED SENTINEL: MULTI-SECTOR VACUUM AUDIT
# =====================================================================
# This script is executed automatically by GitHub Actions.
# It audits the Vacuum States and logs the Charge Bias (chi).

import os
import sys
import datetime
import subprocess

# 1. VERIFY ENGINE LIBRARIES
subprocess.check_call([sys.executable, "-m", "pip", "install", "uproot", "awkward", "numpy", "--quiet"])

import uproot
import numpy as np
import awkward as ak

# 2. SECTOR TARGET DEFINITIONS
# We target one primary node per sector for the daily automated run
sectors = {
    "ELECTRON_STATE": {
        "url": "root://eospublic.cern.ch//eos/opendata/cms/derived-data/NanoAODRun1/01-Jul-22/Run2012C_DoubleElectron/0024D189-4C26-496B-B33A-9F57E44D9E35.root",
        "p_branch": "Electron_pt",
        "q_branch": "Electron_charge",
        "type": "standard"
    },
    "MUON_STATE": {
        "url": "root://eospublic.cern.ch//eos/opendata/cms/derived-data/NanoAODRun1/01-Jul-22/Run2012C_DoubleMuParked/00185A4E-4626-496B-B33A-9F57E44D9E35.root",
        "p_branch": "Muon_pt",
        "q_branch": "Muon_charge",
        "type": "standard"
    },
    "HEAVY_ION_STATE": {
        "url": "root://eospublic.cern.ch//eos/opendata/cms/Run2010B/HIHighPt/AOD/25Apr2013-v1/00000/0034B803-0FB1-E211-89CD-003048D3FA18.root",
        "p_branch": "recoTracks_generalTracks__RECO.obj.pt_",
        "q_branch": "recoTracks_generalTracks__RECO.obj.charge_",
        "type": "standard"
    },
    "INTEGRITY_LEAK_STATE": {
        "url": "root://eospublic.cern.ch//eos/opendata/cms/derived-data/NanoAODRun1/01-Jul-22/Run2012C_DoubleElectron/01C603DD-8434-4AF5-B67E-FFED504757F7.root",
        "p_branch": "MET_pt",
        "q_branch": None,
        "type": "met" # Missing Transverse Energy has no charge, only tension
    }
}

# 3. INITIALIZE SECURE LOGGING
log_filename = f"imperial_vacuum_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.txt"

with open(log_filename, "w") as log:
    log.write("="*60 + "\n")
    log.write(f"IMPERIAL SENTINEL LOG: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC\n")
    log.write("="*60 + "\n\n")

    print(f">>> BOOTING AUTOMATED PROBES. LOGGING TO {log_filename}")

    # 4. EXECUTE SECTOR SWEEP
    for sector_name, details in sectors.items():
        local_file = f"temp_{sector_name}.root"
        print(f"\n>>> INITIATING TRANSFER: {sector_name}")
        
        # Pull data via XRootD Protocol
        ret = os.system(f"xrdcp -f -s {details['url']} {local_file}")
        
        if ret != 0 or not os.path.exists(local_file):
            error_msg = f"❌ [FAILURE] {sector_name}: Node connection refused by CERN servers.\n"
            print(error_msg)
            log.write(error_msg + "\n")
            continue
            
        try:
            with uproot.open(local_file) as f:
                tree = f["Events"]
                
                log.write(f"--- SECTOR: {sector_name} ---\n")
                
                if details["type"] == "standard":
                    # Standard Matter/Anti-Matter Audit
                    data = tree.arrays([details["p_branch"], details["q_branch"]], library="ak", entry_stop=500000)
                    p = ak.flatten(data[details["p_branch"]]).to_numpy()
                    q = ak.flatten(data[details["q_branch"]]).to_numpy()
                    
                    # Apply 0.5 GeV minimum tension threshold
                    mask = p > 0.5
                    pos = np.sum(q[mask] > 0)
                    neg = np.sum(q[mask] < 0)
                    
                    # Calculate Imperial Bias
                    total = pos + neg
                    chi = (pos - neg) / total if total > 0 else 0
                    max_yield = np.max(p)
                    
                    report = (
                        f"Fragments Audited:  {len(p):,}\n"
                        f"Positive State (+): {pos:,}\n"
                        f"Negative State (-): {neg:,}\n"
                        f"Charge Bias (χ):    {chi:+.6f}\n"
                        f"Max Vacuum Yield:   {max_yield:.2f} GeV\n"
                    )
                    
                elif details["type"] == "met":
                    # Energy Leak / Tension Break Audit
                    met_data = tree[details["p_branch"]].array(library="np")
                    max_leak = np.max(met_data)
                    avg_leak = np.mean(met_data)
                    
                    report = (
                        f"Events Audited:     {len(met_data):,}\n"
                        f"Max Energy Leak:    {max_leak:.2f} GeV\n"
                        f"Avg Vacuum Tension: {avg_leak:.2f} GeV\n"
                    )
                
                print(report)
                log.write(report + "\n")
                
        except Exception as e:
            error_msg = f"❌ [ERROR] {sector_name}: {str(e)}\n"
            print(error_msg)
            log.write(error_msg + "\n")
            
        finally:
            if os.path.exists(local_file):
                os.remove(local_file)

    log.write("="*60 + "\n")
    log.write("END OF DAILY AUDIT.\n")
    log.write("="*60 + "\n")

print(f"\n>>> AUDIT COMPLETE. DATA SECURED IN {log_filename}.")
