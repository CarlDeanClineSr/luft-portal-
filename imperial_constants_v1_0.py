#!/usr/bin/env python3
"""
LUFT Imperial Constants
Version: 1.0
Updated: 2026-01-23
Author: Carl Dean Cline Sr.
License: CC BY 4.0

This module defines the authoritative constants for LUFT (Lattice Unified Field Theory)
data transcription and analysis. All LUFT scripts should import constants from this module
to ensure consistency and precision across the entire codebase.

Usage:
    from imperial_constants_v1_0 import CHI_LIMIT, COUPLING_FREQ_HZ, validate_chi

References:
    - LUFT_DATA_TRANSCRIPTION_MASTER_REFERENCE.md
    - The Cline Convergence: Empirical Validation of χ = 0.15
"""

import numpy as np
from datetime import datetime
from typing import Dict, Optional

# ============================================================================
# === FUNDAMENTAL CONSTANTS ===
# ============================================================================

# Universal Boundary Condition
CHI_LIMIT = 0.15                    # Universal vacuum boundary (dimensionless)
CHI_TOLERANCE = 0.005               # Measurement precision (±0.5%)

# Physical Constants (CODATA 2018)
ALPHA_FS = 1 / 137.035999           # Fine-structure constant
PHI_GOLDEN = (1 + np.sqrt(5)) / 2  # Golden ratio (1.618033988749895)
G_MANTISSA = 6.6743e-11             # Gravitational constant (SI units)

# Particle Masses
ELECTRON_MASS = 9.10938356e-31      # kg
PROTON_MASS = 1.672621898e-27       # kg
MASS_RATIO = ELECTRON_MASS / PROTON_MASS  # m_e/m_p ≈ 5.446e-4

# ============================================================================
# === DERIVED QUANTITIES ===
# ============================================================================

# Coupling Frequency (χ/α)
COUPLING_FREQ_HZ = CHI_LIMIT / ALPHA_FS     # 20.55 Hz (biological resonance)

# Gravity Relation (1/χ)
GRAVITY_INVERSE = 1 / CHI_LIMIT             # 6.6667 (matches G × 10^11)

# Mass Ratio Root
MASS_RATIO_ROOT = 0.1528                    # (m_e/m_p)^(1/4)
MASS_RATIO_ROOT_PRECISE = MASS_RATIO ** 0.25  # Computed value

# Harmonic Modes
CHI_SECOND_HARMONIC = 2 * CHI_LIMIT         # 0.30 (transient limit)
CHI_HARMONICS = [CHI_LIMIT * n for n in [1, 2, 4, 8, 16, 32]]  # Binary ladder

# Attractor State Bounds
ATTRACTOR_MIN = 0.145                       # Lower bound of clustering region
ATTRACTOR_MAX = 0.155                       # Upper bound of clustering region

# ============================================================================
# === STATUS CODES ===
# ============================================================================

STATUS_COMPLIANT = "BELOW_LIMIT"      # χ < 0.145
STATUS_BOUNDARY = "AT_BOUNDARY"       # 0.145 ≤ χ ≤ 0.155
STATUS_TRANSIENT = "TRANSIENT"        # 0.155 < χ < 0.30
STATUS_HARMONIC = "SECOND_HARMONIC"   # χ ≈ 0.30
STATUS_VIOLATION = "CAUSALITY_RISK"   # χ > 0.43 (A_IC limit)
STATUS_RECOVERY = "RECOVERY"          # Returning to baseline after excursion

# ============================================================================
# === VALIDATION FUNCTIONS ===
# ============================================================================

def validate_chi(chi_observed: float, timestamp: str) -> Dict:
    """
    Validates χ measurement against universal boundary.
    
    Parameters:
    -----------
    chi_observed : float
        Measured χ value (dimensionless)
    timestamp : str
        UTC timestamp in ISO 8601 format (YYYY-MM-DDTHH:MM:SS.fffZ)
    
    Returns:
    --------
    dict
        {
            'timestamp': str,
            'chi_observed': float,
            'chi_limit': float,
            'excess': float,
            'status': str,
            'compliant': bool,
            'harmonic_mode': int or None
        }
    
    Example:
    --------
    >>> result = validate_chi(0.1498, "2026-01-05T00:45:00.000Z")
    >>> print(result['status'])
    'AT_BOUNDARY'
    """
    excess = chi_observed - CHI_LIMIT
    
    # Determine status
    if chi_observed < CHI_LIMIT - CHI_TOLERANCE:
        status = STATUS_COMPLIANT
        compliant = True
        harmonic = None
    elif abs(chi_observed - CHI_LIMIT) <= CHI_TOLERANCE:
        status = STATUS_BOUNDARY
        compliant = True
        harmonic = 1
    elif abs(chi_observed - CHI_SECOND_HARMONIC) <= CHI_TOLERANCE:
        status = STATUS_HARMONIC
        compliant = True  # Transient, but allowed
        harmonic = 2
    elif chi_observed > 0.43:
        status = STATUS_VIOLATION
        compliant = False
        harmonic = None
    else:
        status = STATUS_TRANSIENT
        compliant = True
        harmonic = None
    
    return {
        'timestamp': timestamp,
        'chi_observed': chi_observed,
        'chi_limit': CHI_LIMIT,
        'excess': excess,
        'status': status,
        'compliant': compliant,
        'harmonic_mode': harmonic
    }


def get_fundamental_unifications() -> Dict:
    """
    Returns the fundamental unifications derived from χ = 0.15.
    
    Returns:
    --------
    dict
        Dictionary containing gravity synthesis, mass ratio, coupling frequency,
        and their error margins relative to measured values.
    """
    # Gravity Synthesis: G ∝ 1/χ
    G_derived = (1.0 / CHI_LIMIT) * 1e-11
    G_error = abs(G_derived - G_MANTISSA) / G_MANTISSA * 100
    
    # Mass Ratio Geometric Limit: χ ≈ (m_e/m_p)^(1/4)
    chi_from_mass = MASS_RATIO_ROOT_PRECISE
    mass_error = abs(chi_from_mass - CHI_LIMIT) / CHI_LIMIT * 100
    
    return {
        'chi_universal': CHI_LIMIT,
        'gravity': {
            'derived_G': G_derived,
            'codata_G': G_MANTISSA,
            'error_percent': G_error,
            'formula': 'G = (1/χ) × 10^-11'
        },
        'mass_ratio': {
            'chi_from_mass': chi_from_mass,
            'electron_mass': ELECTRON_MASS,
            'proton_mass': PROTON_MASS,
            'mass_ratio': MASS_RATIO,
            'error_percent': mass_error,
            'formula': 'χ ≈ (m_e/m_p)^(1/4)'
        },
        'coupling': {
            'frequency_hz': COUPLING_FREQ_HZ,
            'alpha': ALPHA_FS,
            'formula': 'f = χ/α',
            'application': 'Cline Medical Coil (biological resonance)'
        }
    }


def format_timestamp_iso8601(dt: datetime) -> str:
    """
    Format datetime to ISO 8601 with millisecond precision.
    
    Parameters:
    -----------
    dt : datetime
        Python datetime object
    
    Returns:
    --------
    str
        ISO 8601 formatted string with .000 precision
        Example: "2026-01-05T00:45:00.000Z"
    """
    return dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')


def classify_chi_status(chi_val: float) -> str:
    """
    Classify χ value into status category.
    
    Parameters:
    -----------
    chi_val : float
        Measured χ value
    
    Returns:
    --------
    str
        Status code (STATUS_COMPLIANT, STATUS_BOUNDARY, etc.)
    """
    if np.isnan(chi_val):
        return 'UNKNOWN'
    elif chi_val > ATTRACTOR_MAX:
        if chi_val > 0.43:
            return STATUS_VIOLATION
        elif abs(chi_val - CHI_SECOND_HARMONIC) <= CHI_TOLERANCE:
            return STATUS_HARMONIC
        else:
            return STATUS_TRANSIENT
    elif chi_val >= ATTRACTOR_MIN:
        return STATUS_BOUNDARY
    else:
        return STATUS_COMPLIANT


# ============================================================================
# === MODULE METADATA ===
# ============================================================================

__version__ = "1.0"
__author__ = "Carl Dean Cline Sr."
__date__ = "2026-01-23"
__all__ = [
    # Constants
    'CHI_LIMIT', 'CHI_TOLERANCE', 'ALPHA_FS', 'PHI_GOLDEN', 'G_MANTISSA',
    'ELECTRON_MASS', 'PROTON_MASS', 'MASS_RATIO',
    'COUPLING_FREQ_HZ', 'GRAVITY_INVERSE', 'MASS_RATIO_ROOT',
    'CHI_SECOND_HARMONIC', 'CHI_HARMONICS',
    'ATTRACTOR_MIN', 'ATTRACTOR_MAX',
    # Status Codes
    'STATUS_COMPLIANT', 'STATUS_BOUNDARY', 'STATUS_TRANSIENT',
    'STATUS_HARMONIC', 'STATUS_VIOLATION', 'STATUS_RECOVERY',
    # Functions
    'validate_chi', 'get_fundamental_unifications',
    'format_timestamp_iso8601', 'classify_chi_status'
]


# ============================================================================
# === DEMONSTRATION ===
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("LUFT Imperial Constants - Version 1.0")
    print("=" * 70)
    
    print("\n🔬 FUNDAMENTAL CONSTANTS:")
    print(f"   χ (Chi Limit)           = {CHI_LIMIT}")
    print(f"   χ Tolerance             = ±{CHI_TOLERANCE}")
    print(f"   α (Fine Structure)      = {ALPHA_FS:.10f}")
    print(f"   φ (Golden Ratio)        = {PHI_GOLDEN:.10f}")
    print(f"   G (Gravitational)       = {G_MANTISSA:.5e} m³/(kg·s²)")
    
    print("\n📐 DERIVED QUANTITIES:")
    print(f"   Coupling Frequency      = {COUPLING_FREQ_HZ:.4f} Hz")
    print(f"   Gravity Inverse (1/χ)   = {GRAVITY_INVERSE:.4f}")
    print(f"   Mass Ratio Root         = {MASS_RATIO_ROOT}")
    print(f"   Second Harmonic (2χ)    = {CHI_SECOND_HARMONIC}")
    
    print("\n🌌 FUNDAMENTAL UNIFICATIONS:")
    unif = get_fundamental_unifications()
    print(f"   Gravity Error:          {unif['gravity']['error_percent']:.3f}%")
    print(f"   Mass Ratio Error:       {unif['mass_ratio']['error_percent']:.3f}%")
    
    print("\n✅ EXAMPLE VALIDATION:")
    test_events = [
        ("2026-01-05T00:41:00.000Z", 0.1284),
        ("2026-01-05T00:45:00.000Z", 0.1498),
        ("2026-01-05T01:00:00.000Z", 0.1389),
        ("2026-01-05T01:13:00.000Z", 0.0917),
    ]
    
    for timestamp, chi in test_events:
        result = validate_chi(chi, timestamp)
        print(f"   {timestamp}: χ={chi:.4f} → {result['status']}")
    
    print("=" * 70)
