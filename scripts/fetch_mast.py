import os
from astroquery.mast import Observations
import yaml

with open("config/constants.yaml", "r") as f:
    config = yaml.safe_load(f)

os.makedirs("data", exist_ok=True)
# Example file for WASP-39b - you can make this dynamic later
target_uri = "mast:JWST/product/jw01366004001_04101_00001-seg003_nrs1_uncal.fits"
local_path = "data/science_segment.fits"

print(f"Downloading {target_uri}...")
Observations.download_file(target_uri, local_path=local_path)
print("Download complete.")
