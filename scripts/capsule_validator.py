import sys, json
from pathlib import Path

def validate_capsule(path):
    with open(path, 'r') as f:
        text = f.read()
    jblock = [b for b in text.split('```json') if b]
    if not jblock:
        print("No JSON block found.")
        sys.exit(1)
    try:
        data = json.loads(jblock[1].split('```')[0].strip())
    except Exception as e:
        print(f"JSON decode error: {e}")
        sys.exit(1)
    if not (0 <= data['particle']['proton_flux_pfu'] <= 1e6):
        print("Proton flux out of range!")
        sys.exit(2)
    if not (abs(data['magnetic']['bx_nT']) <= 1000 and abs(data['magnetic']['by_nT']) <= 1000 and abs(data['magnetic']['bz_nT']) <= 1000):
        print("Magnetic field out of range!")
        sys.exit(3)
    print("Capsule validated OK.")

if __name__ == "__main__":
    validate_capsule(sys.argv[1])
