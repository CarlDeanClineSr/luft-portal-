import numpy as np
import json
import os

# ============================================================================
# IMPERIAL CHI: VACUUM TO MASS CONVERSION DIAGNOSTIC
# ============================================================================
OUTPUT_DIR = "diagnostic_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 1. The Empirical Data from the Chi Bounding Report
BOUNDED_VACUUM_DENSITY = 1.2411e66  # J/m^3 (Calculated via Chi = 0.15 limit)
OBSERVED_LAMBDA_DENSITY = 5.36e-10  # J/m^3 (Actual empty space observation)
ENERGY_GAP_RATIO = BOUNDED_VACUUM_DENSITY / OBSERVED_LAMBDA_DENSITY

# 2. Standard Cosmological Constants
C = 299792458  # Speed of light (m/s)
PROTON_MASS = 1.67262192e-27  # kg
OBSERVABLE_UNIVERSE_VOLUME = 3.58e80  # m^3 (approximate)

def run_mass_conversion_audit():
    print("=" * 70)
    print("INITIATING IMPERIAL χ: VACUUM TO MASS CONVERSION AUDIT")
    print("=" * 70)

    # Step 1: Calculate the total "Missing" Energy in the universe volume
    total_missing_energy = BOUNDED_VACUUM_DENSITY * OBSERVABLE_UNIVERSE_VOLUME
    
    # Step 2: Convert that missing energy into physical mass (E = mc^2 -> m = E/c^2)
    total_converted_mass = total_missing_energy / (C**2)
    
    # Step 3: Calculate how many protons that mass equals
    total_protons_created = total_converted_mass / PROTON_MASS

    print(f"[*] Bounded Vacuum Density (χ=0.15): {BOUNDED_VACUUM_DENSITY:.4e} J/m³")
    print(f"[*] Observed Empty Space Density:    {OBSERVED_LAMBDA_DENSITY:.4e} J/m³")
    print(f"[*] The Energy Gap Ratio:            {ENERGY_GAP_RATIO:.4e}\n")

    print("[DIAGNOSTIC: WHERE IS THE ENERGY?]")
    print("-" * 50)
    print("If the vacuum is active, the 'missing' energy isn't missing.")
    print("It is folded into the resting mass of physical matter.\n")
    
    print(f">>> Total Converted Mass: {total_converted_mass:.4e} kg")
    print(f">>> Equivalent Protons Generated: {total_protons_created:.4e}")

    # The Eddington Number (estimated total protons in the observable universe) is ~10^80
    print("\n[CONCLUSION]")
    if 1e78 <= total_protons_created <= 1e82:
        print("✅ VERIFIED: The bounded vacuum energy perfectly accounts for the mass of the universe.")
        print("✅ The 0.15 limit acts as the threshold for mass generation.")
    else:
        print("❌ ANOMALY: The converted mass does not align with the Eddington number.")
        print("   Further refinement of the substrate boundaries is required.")

    # Save report
    report = {
        "bounded_density_J_m3": BOUNDED_VACUUM_DENSITY,
        "energy_gap_ratio": ENERGY_GAP_RATIO,
        "converted_mass_kg": total_converted_mass,
        "equivalent_protons": total_protons_created
    }
    
    report_path = os.path.join(OUTPUT_DIR, "mass_conversion_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=4)
    
    print("=" * 70)
    print(f"Report saved to {report_path}")

if __name__ == "__main__":
    run_mass_conversion_audit()
