import os
import json
import glob
import numpy as np
import pandas as pd
from datetime import datetime

# --- IMPERIAL CONVERGENCE CONSTANTS ---
CHI_LIMIT = 0.15
INTEGRITY_FREQ = 20.55  # Hz
H_PLANCK = 6.62607015e-34  # J/Hz
OBSERVED_LAMBDA_DENSITY = 5.36e-10  # J/m^3

# Derived Energy of a single ring-mode structural quantum
E_RING = H_PLANCK * INTEGRITY_FREQ

def scan_telemetry_for_mass_conversion(data_dir="data"):
    """
    Scans the LUFT telemetry data directory to calculate mass conversion 
    metrics based on the Chi = 0.15 boundary and Route 3b Baryonic Coupling.
    """
    report = {
        "report_generated_utc": datetime.utcnow().isoformat(),
        "engine_constants": {
            "chi_limit": CHI_LIMIT,
            "integrity_frequency_hz": INTEGRITY_FREQ,
            "e_ring_joules": E_RING,
            "target_lambda_density_j_m3": OBSERVED_LAMBDA_DENSITY
        },
        "scanned_files": 0,
        "total_data_points": 0,
        "mode_8_fractures": 0,
        "mass_conversion_metrics": {}
    }

    # Find all CSV telemetry files in the data directory
    search_pattern = os.path.join(data_dir, "**", "*.csv")
    csv_files = glob.glob(search_pattern, recursive=True)
    report["scanned_files"] = len(csv_files)

    total_points = 0
    fracture_events = 0
    
    # Trackers for density (assuming standard CME telemetry headers: density_cm3)
    max_density_cm3 = 0.0
    mean_density_cm3 = 0.0

    for file_path in csv_files:
        try:
            df = pd.read_csv(file_path)
            
            # Accommodate variation in column headers ('density' or 'density_cm3')
            density_col = 'density_cm3' if 'density_cm3' in df.columns else 'density' if 'density' in df.columns else None
            chi_col = 'chi_amplitude' if 'chi_amplitude' in df.columns else None

            if density_col:
                points = len(df)
                total_points += points
                
                # Update max density
                local_max = df[density_col].max()
                if local_max > max_density_cm3:
                    max_density_cm3 = local_max
                
                # Check for Mode 8 Fractures using actual tension (Chi), not just arbitrary density
                if chi_col:
                    fractures = df[df[chi_col] >= CHI_LIMIT]
                    fracture_events += len(fractures)
                else:
                    # Fallback proxy: If density spikes 5x above standard baseline (0.25)
                    fractures = df[df[density_col] > 1.25]
                    fracture_events += len(fractures)

        except Exception as e:
            print(f"[!] Error reading {file_path}: {e}")

    report["total_data_points"] = total_points
    report["mode_8_fractures"] = fracture_events
    
    # --- ROUTE 3b: BARYONIC COUPLING MATH ---
    # Convert density from cm^-3 to m^-3 for standard SI calculation
    max_proton_density_m3 = max_density_cm3 * 1e6 
    
    if max_proton_density_m3 > 0:
        # Ring energy × peak universe proton number density
        rho_ring_baryonic = E_RING * max_proton_density_m3
        gap_baryonic = np.log10(rho_ring_baryonic / OBSERVED_LAMBDA_DENSITY)
    else:
        rho_ring_baryonic = 0
        gap_baryonic = 0

    report["mass_conversion_metrics"] = {
        "max_recorded_density_cm3": max_density_cm3,
        "max_recorded_density_m3": max_proton_density_m3,
        "rho_ring_baryonic_j_m3": rho_ring_baryonic,
        "gap_to_lambda_log10": gap_baryonic,
        "status": "BOUNDED" if (fracture_events / max(total_points, 1) < 0.05) else "FRACTURED"
    }

    return report

def main():
    print("[⚙️] Initializing LUFT Portal Mass Conversion Scanner...")
    # Point this to wherever your raw telemetry CSVs are stored.
    report_data = scan_telemetry_for_mass_conversion(data_dir=".")
    
    output_file = "mass_conversion_report.json"
    with open(output_file, 'w') as f:
        json.dump(report_data, f, indent=4)
        
    print(f"[SUCCESS] Scanned {report_data['total_data_points']} telemetry points.")
    if report_data['total_data_points'] > 0:
        print(f"[SUCCESS] Log10 Gap to Lambda: {report_data['mass_conversion_metrics']['gap_to_lambda_log10']:.4f}")
    print(f"[SUCCESS] Wrote {output_file}")

if __name__ == "__main__":
    main()
