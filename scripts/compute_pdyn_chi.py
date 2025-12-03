#!/usr/bin/env python3
"""
compute_pdyn_chi.py
Compute solar wind dynamic pressure (P_dyn) in nPa and χ from the
normalized ACE plasma audit JSON. Appends p_dyn_nPa and chi_from_pdyn
fields to each record and writes the file back.

Usage:
    python3 scripts/compute_pdyn_chi.py

Outputs:
    data/ace_plasma_audit_normalized.json (updated in place)
    data/ace_plasma_audit_normalized_with_chi.json (written as safety copy)
"""
import json
from pathlib import Path

K_PDYN = 1.6726e-6  # conversion constant for n(cm^-3)*v(km/s)^2 -> nPa
CHI_A = 0.0032
CHI_B = 0.054

DATA = Path('data')
IN_FILE = DATA / 'ace_plasma_audit_normalized.json'
OUT_FILE = DATA / 'ace_plasma_audit_normalized_with_chi.json'

def load_json(p):
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(p, obj):
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

if not IN_FILE.exists():
    print(f"Missing input file: {IN_FILE}")
    raise SystemExit(1)

records = load_json(IN_FILE)
for rec in records:
    n = rec.get('density_p_cm3') or 0.0
    v = rec.get('speed_km_s') or 0.0
    try:
        p_dyn = K_PDYN * float(n) * (float(v) ** 2)
    except Exception:
        p_dyn = None
    if p_dyn is not None:
        chi = CHI_A * p_dyn + CHI_B
        rec['p_dyn_nPa'] = round(p_dyn, 4)
        rec['chi_from_pdyn'] = round(chi, 6)
    else:
        rec['p_dyn_nPa'] = None
        rec['chi_from_pdyn'] = None

# write safety copy
save_json(OUT_FILE, records)
# overwrite original normalized file as well
save_json(IN_FILE, records)
print(f"Wrote {len(records)} records with p_dyn_nPa and chi_from_pdyn to {OUT_FILE} and updated {IN_FILE}")
