import pandas as pd
import json

# Load plasma data
with open('data/ace_plasma_latest.json', 'r') as f:
    plasma = pd.read_json(f)
print("Plasma sample:", plasma.tail())

# Load mag data
with open('data/ace_mag_latest.json', 'r') as f:
    mag = pd.read_json(f)
print("Magnetometer sample:", mag.tail())

# Optionally run LUFT modulation fit...
# e.g., fit Omega/chi model, check for snap events
