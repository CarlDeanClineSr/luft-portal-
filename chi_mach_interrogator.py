import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import glob

# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================
OUTPUT_DIR = "diagnostic_outputs"
CHI_MAX = 0.15
os.makedirs(OUTPUT_DIR, exist_ok=True)

def find_target_csv():
    """Scans the repository for any CSV containing the required telemetry."""
    print("🔍 SCANNING REPOSITORY FOR TELEMETRY FILES...")
    for file in glob.glob("**/*.csv", recursive=True):
        try:
            # Read just the header row to save memory
            headers = pd.read_csv(file, nrows=0).columns
            if 'mach' in headers and 'R' in headers:
                print(f"   [LOCKED ON] Found valid telemetry target: {file}")
                return file
        except Exception:
            continue
    return None

def interrogate_mach_boundary():
    print("=" * 70)
    print("INITIATING IMPERIAL χ vs. MACH NUMBER INTERROGATION")
    print("=" * 70)

    target_file = find_target_csv()
    
    if not target_file:
        print("❌ ERROR: No CSV files containing 'mach' and 'R' columns were found in the repository.")
        print("   Please ensure your data file is uploaded and contains those exact headers.")
        return

    try:
        # Load data and force numeric conversion to handle missing/empty values (,,)
        df = pd.read_csv(target_file)
        df['R'] = pd.to_numeric(df['R'], errors='coerce')
        df['mach'] = pd.to_numeric(df['mach'], errors='coerce')
        
        # Drop rows where we don't have both R (tension) and Mach (speed)
        clean_df = df.dropna(subset=['R', 'mach']).copy()
        
        if len(clean_df) == 0:
            print("❌ ERROR: File found, but no valid Mach/R pairs exist. Check for telemetry gaps.")
            return

        print(f"✅ Secured {len(clean_df)} solid plasma observations.")
        
        clean_df['chi_proxy'] = clean_df['R']

        # ---------------------------------------------------------
        # THE MATH: SUBSTRATE DECELERATION
        # ---------------------------------------------------------
        high_tension = clean_df[clean_df['chi_proxy'] > (CHI_MAX * 0.5)]
        low_tension = clean_df[clean_df['chi_proxy'] <= (CHI_MAX * 0.5)]

        avg_mach_low = low_tension['mach'].mean()
        avg_mach_high = high_tension['mach'].mean() if len(high_tension) > 0 else 0

        print("\n[MATHEMATICAL DIAGNOSTIC: THE BRAKING EFFECT]")
        print("-" * 50)
        print("Fundamental Premise: As χ → 0.15, the lattice hardens, acting as a physical brake.")
        print(f"Average Mach (Relaxed Lattice, χ < 0.075):  {avg_mach_low:.3f}")
        print(f"Average Mach (Stressed Lattice, χ > 0.075): {avg_mach_high:.3f}")
        
        if avg_mach_high < avg_mach_low:
            print(">>> VERIFIED: Plasma decelerates as substrate tension increases.")
            print(">>> The vacuum is actively resisting the flow.")
        else:
            print(">>> ANOMALY: Plasma maintains or increases speed under stress.")

        # ---------------------------------------------------------
        # GENERATE VISUAL EVIDENCE
        # ---------------------------------------------------------
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(10, 6))

        ax.scatter(clean_df['chi_proxy'], clean_df['mach'], color='cyan', alpha=0.6, s=15, label="Observed Plasma States")
        
        ax.axvline(CHI_MAX, color='red', linestyle='--', linewidth=2.5, label='Universal χ Boundary (0.15)')
        ax.axvspan(0.13, 0.17, color='red', alpha=0.2, label='Attractor Zone')

        ax.set_title("Substrate Braking Effect: Mach Number vs. Lattice Tension (χ)", color='white', fontsize=14)
        ax.set_xlabel(r"Lattice Tension Proxy ($\chi$)", color='white', fontsize=12)
        ax.set_ylabel("Plasma Speed (Mach Number)", color='white', fontsize=12)
        ax.grid(True, alpha=0.2)
        ax.legend()

        plot_path = os.path.join(OUTPUT_DIR, "mach_vs_chi_boundary.png")
        plt.savefig(plot_path, dpi=300)
        print(f"\n✅ Visual diagnostic saved to: {plot_path}")
        print("=" * 70)

    except Exception as e:
        print(f"❌ Execution Failed: {e}")

if __name__ == "__main__":
    interrogate_mach_boundary()
