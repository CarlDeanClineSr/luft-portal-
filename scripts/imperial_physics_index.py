# ==============================================================================
#  IMPERIAL PHYSICS INDEX (MASTER DEFINITIONS)
#  Author: Carl Dean Cline Sr.
#  Status: LAW
# ==============================================================================

class VacuumConstants:
    """
    Immutable constants derived from the December 2025 - February 2026 data.
    """
    # The Universal Yield Point (Max Stress)
    CHI_MAX = 0.150
    
    # The Baseline Shift (Dec 11, 2025)
    BASELINE_PRE_DEC = 0.055
    BASELINE_POST_DEC = 0.115
    
    # The Expansion Cycle Periodicity (30 Days)
    CYCLE_PERIOD_DAYS = 30
    
    # Harmonic Modes
    MODE_STABLE = 2
    MODE_TRANSITION = 4

class FieldDefinitions:
    """
    Physical definitions for the medium.
    """
    MEDIUM_TYPE = "Continuous Vacuum Field"
    INTERACTION = "Preferred Matter State Dominance"
    
    @staticmethod
    def classify_state(chi_value):
        if chi_value <= 0.06:
            return "QUIET_STATE"
        elif 0.06 < chi_value <= 0.115:
            return "ELEVATED_TENSION"
        elif 0.115 < chi_value <= 0.150:
            return "SATURATION_LIMIT"
        else:
            return "TRANSIENT_SHOCK"
