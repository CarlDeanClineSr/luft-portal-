import os
from astroquery.mast import Observations

# Define root path
ROOT_DIR = os.getcwd()
DATA_DIR = os.path.join(ROOT_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Define file path
target_uri = "mast:JWST/product/jw01366004001_04101_00001-seg003_nrs1_uncal.fits"
file_path = os.path.join(DATA_DIR, "science_segment.fits")

print(f"Downloading to: {file_path}")
Observations.download_file(target_uri, local_path=file_path)

if os.path.exists(file_path):
    print(f"Download verified. File size: {os.path.getsize(file_path)} bytes.")
else:
    print("Download failed.")
    exit(1)
