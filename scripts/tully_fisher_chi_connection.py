import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
from scipy import constants as const


def main():
    # Electron/proton mass ratio (SI units)
    m_e = const.m_e  # kg
    m_p = const.m_p  # kg
    chi = (m_e / m_p) ** 0.25
    print(f"chi = (m_e / m_p)^(1/4) = {chi:.4f}")

    # Tully-Fisher 1/4 power scaling
    alpha_tf = 0.25
    print(f"Tully-Fisher exponent = {alpha_tf}")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Left: chi scaling across mass ratios
    m_ratio = np.logspace(-4, 0, 100)
    chi_scaled = m_ratio ** 0.25
    ax1.loglog(m_ratio, chi_scaled, label="χ = (m_e/m_p)^(1/4)")
    ax1.axhline(chi, color="red", linestyle="--", label=f"Observed χ = {chi:.4f}")
    ax1.set_xlabel("Mass Ratio (m_e / m_p)")
    ax1.set_ylabel("χ")
    ax1.set_title("Chi Scaling (Micro → Macro)")
    ax1.legend()
    ax1.grid(True)

    # Right: Tully–Fisher scaling across luminosity ratios
    L_ratio = np.logspace(0, 12, 100)
    V_tf = L_ratio ** 0.25
    ax2.loglog(L_ratio, V_tf, label="V_rot ∝ L^(1/4) (Tully-Fisher)")
    ax2.set_xlabel("Luminosity (L / L_sun)")
    ax2.set_ylabel("Rotation Speed (normalized)")
    ax2.set_title("Tully-Fisher Law (Macro Scale)")
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout()

    output_path = Path("figures") / "chi_tully_fisher_connection.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300)

    print(f"\n✅ Figure saved: {output_path}")
    print("   Same 1/4-power scaling at micro (chi) and macro (Tully-Fisher) scales!")


if __name__ == "__main__":
    main()
