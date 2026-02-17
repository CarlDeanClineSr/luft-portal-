# quick_jj_check.py
import numpy as np
import math

# Constants
hbar = 1.054571817e-34
e = 1.602176634e-19
kB = 1.380649e-23

# Device params (example: measurement-like)
Ic = 5.315e-6    # A
C = 1.988e-12    # F
gamma = 0.95     # normalized bias I/Ic
f_test = -0.05   # sample FOAM modulation (ΔEJ/EJ), try -0.1 .. 0.1

# Derived
EJ = hbar * Ic / (2*e)                    # Josephson energy (J)
omega_p0 = math.sqrt(2*e*Ic/(hbar*C))    # plasma freq (rad/s)
omega_p = omega_p0 * (1 - gamma**2)**0.25

def deltaU(EJ, gamma):
    return 2*EJ*(math.sqrt(1-gamma**2) - gamma*math.acos(gamma))

DeltaU = deltaU(EJ, gamma)
B0 = (36.0/5.0) * (DeltaU / (hbar * omega_p))
S0 = B0/2.0  # leading-order sensitivity d ln Γ/df approx -B0/2

print("Device params:")
print(f" Ic = {Ic:.3e} A, C = {C:.3e} F, gamma = {gamma}")
print()
print("Derived quantities:")
print(f" EJ = {EJ:.3e} J")
print(f" omega_p0/(2π) = {omega_p0/(2*math.pi):.3e} Hz")
print(f" T* = ħ ωp/(2π kB) = { (hbar*omega_p)/(2*math.pi*kB):.3e} K")
print()
print("Barrier and WKB:")
print(f" ΔU = {DeltaU:.3e} J")
print(f" B0 = {B0:.3f}")
print(f" Sensitivity (approx) S0 = B0/2 = {S0:.3f}")
print()
# effect of f_test
dlnGamma = -S0 * f_test
print(f"For f = {f_test:+.3f}, ln(Γ/Γ0) ≈ {dlnGamma:+.3f} -> Γ change ≈ exp({dlnGamma:.3f}) = {math.exp(dlnGamma):.3f}")
