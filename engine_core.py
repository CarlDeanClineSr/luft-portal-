# LUFT ENGINE CORE DIRECTIVE LOADER
# Loads the YAML engine_core_directive.yaml as the LAW for all code, exposing its parameters to Python scripts.

import yaml

def load_engine_directive(filepath="configs/engine_core_directive.yaml"):
    """
    Load the LUFT engine core directive from a YAML file.
    This file contains shared χ ceiling/floor, watch variables, and gold feeds.
    """
    with open(filepath, "r") as f:
        return yaml.safe_load(f)

if __name__ == "__main__":
    directive = load_engine_directive()
    print("# == LUFT ENGINE CORE DIRECTIVE (SHARED LAW FOR ALL CODE) ==")
    print(f"χ ceiling: {directive['chi_ceiling']}")
    print(f"χ floor:   {directive['chi_floor']}")
    print("Watch variables:", directive['watch_variables'])
    print("Gold feeds:", directive['gold_feeds'])
    print("Description:")
    print(directive.get('description', '').strip())
