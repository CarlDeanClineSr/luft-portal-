#!/usr/bin/env python3
"""
Imperial Physics Observatory: NASA Daily Data Harvest
Downloads yesterday's magnetometer data from all NASA missions
"""

import pyspedas
from pytplot import get_data
import pandas as pd
import numpy as np
import argparse
from datetime import datetime, timedelta
from pathlib import Path

MISSIONS = {
    'ace': {
        'function': pyspedas.ace.mag,
        'datatype': 'h0',
        'vars': ['Bx_gse', 'By_gse', 'Bz_gse', 'Bt']
    },
    'dscovr': {
        'function': pyspedas.dscovr.mag,
        'datatype': None,
        'vars': ['b_gse_x', 'b_gse_y', 'b_gse_z']
    },
    'voyager1': {
        'function': lambda **kwargs: pyspedas.voyager.mag(probe='1', **kwargs),
        'datatype': None,
        'vars': ['vg1_mag_br', 'vg1_mag_bt', 'vg1_mag_bn']
    },
    'voyager2': {
        'function': lambda **kwargs: pyspedas.voyager.mag(probe='2', **kwargs),
        'datatype': None,
        'vars': ['vg2_mag_br', 'vg2_mag_bt', 'vg2_mag_bn']
    },
    'maven': {
        'function': pyspedas.maven.mag,
        'datatype': None,
        'vars': ['OB_B']
    },
    'wind': {
        'function': pyspedas.wind.mfi,
        'datatype': 'h0',
        'vars': ['BGSE']
    },
    'stereoa': {
        'function': lambda **kwargs: pyspedas.stereo.mag(probe='a', **kwargs),
        'datatype': None,
        'vars': ['BFIELD']
    },
    'psp': {
        'function': pyspedas.psp.fields,
        'datatype': 'mag_rtn',
        'vars': ['psp_fld_l2_mag_RTN']
    }
}

def download_mission_data(mission, date_str):
    """
    Download magnetometer data for a specific mission and date
    
    Args:
        mission: Mission name (ace, dscovr, voyager1, etc.)
        date_str: Date string (YYYY-MM-DD)
        
    Returns:
        DataFrame with magnetometer data
    """
    print(f"\n[{mission.upper()}] Downloading data for {date_str}")
    
    if mission not in MISSIONS:
        print(f"  ERROR: Unknown mission '{mission}'")
        return pd.DataFrame()
    
    config = MISSIONS[mission]
    
    # Calculate time range (full day)
    start_time = f"{date_str} 00:00:00"
    end_time = f"{date_str} 23:59:59"
    
    try:
        # Download data
        kwargs = {'trange': [start_time, end_time], 'time_clip': True}
        if config['datatype']:
            kwargs['datatype'] = config['datatype']
        
        vars_loaded = config['function'](**kwargs)
        
        if not vars_loaded:
            print(f"  No data available for {date_str}")
            return pd.DataFrame()
        
        # Extract variables
        data_dict = {'timestamp': None}
        
        for var in config['vars']:
            try:
                times, values = get_data(var)
                if data_dict['timestamp'] is None:
                    data_dict['timestamp'] = pd.to_datetime(times, unit='s')
                data_dict[var] = values
            except:
                print(f"  WARNING: Could not load variable '{var}'")
        
        if data_dict['timestamp'] is None:
            print(f"  ERROR: No valid data extracted")
            return pd.DataFrame()
        
        df = pd.DataFrame(data_dict)
        
        # Calculate total field magnitude if components available
        if mission in ['ace', 'dscovr']:
            if all(col in df.columns for col in ['Bx_gse', 'By_gse', 'Bz_gse']):
                df['Bt'] = np.sqrt(df['Bx_gse']**2 + df['By_gse']**2 + df['Bz_gse']**2)
        
        df['mission'] = mission.upper()
        df['date'] = date_str
        
        print(f"  SUCCESS: Downloaded {len(df)} records")
        return df
        
    except Exception as e:
        print(f"  ERROR: {str(e)}")
        return pd.DataFrame()

def main():
    parser = argparse.ArgumentParser(description='NASA Daily Data Harvest')
    parser.add_argument('--mission', required=True, help='Mission name')
    parser.add_argument('--date', required=True, help='Date (YYYY-MM-DD)')
    parser.add_argument('--output', required=True, help='Output directory')
    
    args = parser.parse_args()
    
    # Download data
    df = download_mission_data(args.mission, args.date)
    
    if len(df) > 0:
        # Create output directory
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save to CSV
        output_file = output_dir / f"{args.mission}_{args.date}.csv"
        df.to_csv(output_file, index=False)
        print(f"\n  Saved to: {output_file}")
    else:
        print(f"\n  No data saved for {args.mission} on {args.date}")

if __name__ == '__main__':
    main()
