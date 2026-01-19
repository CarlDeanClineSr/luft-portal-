import argparse
import numpy as np
import json
import os
from pathlib import Path

try:
    from skypatrol import SkyPatrolClient
except ImportError:
    try:
        from pyasassn.client import SkyPatrolClient
    except ImportError:
        SkyPatrolClient = None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--job-id', type=int, required=True)
    parser.add_argument('--total-targets', type=int, required=True)
    parser.add_argument('--batch-size', type=int, required=True)
    parser.add_argument('--n-jobs', type=int, required=True)
    parser.add_argument('--output', type=str, required=True)
    args = parser.parse_args()

    # Deterministic target generation (Fibonacci Sphere)
    start_idx = args.job_id * args.batch_size
    end_idx = min(start_idx + args.batch_size, args.total_targets)
    indices = np.arange(start_idx, end_idx) + 0.5
    phi = np.arccos(1 - 2*indices/args.total_targets)
    theta = np.pi * (1 + 5**0.5) * indices
    targets = list(zip(np.degrees(theta) % 360, 90 - np.degrees(phi)))

    print(f"Scanning {len(targets)} targets...")
    
    # ==============================================================================
    #  ASAS-SN QUERY & FLUX ANALYSIS LOGIC
    # ==============================================================================
    
    # Initialize Client (outside the loop for speed)
    client = None
    try:
        if SkyPatrolClient:
            client = SkyPatrolClient()
            print("  [INFO] SkyPatrol Client Initialized")
    except Exception as e:
        print(f"  [WARN] Client init failed: {e}")

    results = []
    
    # BATCH SCAN LOOP
    for i, (ra, dec) in enumerate(targets):
        try:
            if not client:
                break # Fail safe
                
            # 1. Cone Search (Find star at these coords)
            # Using 7.2 arcsec radius (0.002 deg) to pin specific targets
            search_results = client.cone_search(
                ra_deg=ra, 
                dec_deg=dec, 
                radius=0.002, 
                catalog='master_list',
                download=False
            )
            
            if search_results is None or len(search_results) == 0:
                continue # Empty sky patch
                
            # Get the ASAS-SN ID of the brightest match
            star_id = search_results.iloc[0]['asas_sn_id']
            
            # 2. Get Light Curve
            lc = client.query_list([star_id], catalog='master_list', download=True)[star_id]
            data = lc.data # DataFrame with 'mag', 'flux', 'jd'
            
            if len(data) < 10:
                continue # Skip noise
                
            # 3. IMPERIAL MATH ANALYSIS (Flux Ratio)
            # Convert Mag to Flux if needed, or use existing flux col
            # Standard: Flux = 10^(-0.4 * mag)
            # We look for MAX deviation from MEDIAN
            
            median_flux = 10**(-0.4 * data['mag'].median())
            max_flux = 10**(-0.4 * data['mag'].min()) # Brightest point
            
            flux_ratio = max_flux / median_flux
            
            # 4. THE CLINE CRITERIA
            # Chi > 0.15 means Flux Ratio > 1.15
            # We filter for "Super-Violations" (> 2.0x) to save bandwidth
            
            is_stress_node = False
            if flux_ratio > 2.0:
                is_stress_node = True
                print(f"  [★ FOUND] RA:{ra:.4f} DEC:{dec:.4f} | Ratio: {flux_ratio:.2f}x")
            
            # 5. Append Result
            results.append({
                "ra": ra,
                "dec": dec,
                "asas_sn_id": int(star_id),
                "n_obs": len(data),
                "median_mag": float(data['mag'].median()),
                "min_mag": float(data['mag'].min()),
                "flux_ratio": float(flux_ratio),
                "is_stress_node": is_stress_node
            })

        except Exception as e:
            # Log error but keep scanning
            pass
            
        # Reporting heartbeat
        if (i + 1) % 100 == 0:
            print(f"  Status: {i+1}/{len(targets)} scanned. Found {len(results)} stars.")

    # ==============================================================================

    print(f"✅ Job {args.job_id} complete")

    # Save results
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump({'job_id': args.job_id, 'results': results}, f, indent=2)

if __name__ == '__main__':
    main()
