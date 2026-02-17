import argparse
import os
import sys
import pandas as pd
from datetime import datetime

try:
    import pyspedas
    import pytplot
except ImportError:
    print("Error: pyspedas not installed. Run: pip install pyspedas")
    sys.exit(1)

def download_encounter(encounter_id, start_date, end_date, output_dir):
    print(f"Downloading Encounter {encounter_id}: {start_date} to {end_date}")
    
    try:
        # Load MAG data (RTN coordinates)
        pyspedas.psp.fields(
            trange=[start_date, end_date],
            datatype='mag_rtn', 
            level='l2',
            time_clip=True,
            varnames=['psp_fld_l2_mag_RTN'],
            display=False,
            downloadonly=False
        )
        
        # Extract from Tplot
        data = pytplot.get_data('psp_fld_l2_mag_RTN')
        if data is None:
            print(f"Error: No data found for Encounter {encounter_id}")
            return

        # Format DataFrame
        df = pd.DataFrame(data.y, columns=['B_R', 'B_T', 'B_N'])
        df['timestamp'] = [datetime.utcfromtimestamp(t).isoformat() for t in data.times]
        
        # Save CSV
        filename = f"psp_encounter{encounter_id}_mag.csv"
        filepath = os.path.join(output_dir, filename)
        df.to_csv(filepath, index=False)
        print(f"Saved: {filepath} ({len(df)} rows)")

    except Exception as e:
        print(f"Critical Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--encounter", required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--output", default="data/psp")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    download_encounter(args.encounter, args.start, args.end, args.output)
