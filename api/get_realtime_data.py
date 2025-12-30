#!/usr/bin/env python3
"""
Real-time Space Weather Data API
Fetches live data from DSCOVR satellite and calculates chi amplitude
Returns JSON for instrument panel gauges
"""

import json
import sys
import os
from datetime import datetime, timezone
import requests

def fetch_dscovr_data():
    """Fetch latest DSCOVR data from NOAA"""
    try:
        # NOAA DSCOVR real-time data endpoint
        url = "https://services.swpc.noaa.gov/products/solar-wind/mag-7-day.json"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Field indices for magnetic data
        IDX_TIME = 0
        IDX_BX = 1
        IDX_BY = 2
        IDX_BZ = 3
        IDX_BT = 6
        
        # Get latest non-null entry
        for row in reversed(data[1:]):  # Skip header
            if row[IDX_BX] and row[IDX_BY] and row[IDX_BZ]:  # All components present
                return {
                    'time_tag': row[IDX_TIME],
                    'bx': float(row[IDX_BX]),
                    'by': float(row[IDX_BY]),
                    'bz': float(row[IDX_BZ]),
                    'bt': float(row[IDX_BT]) if row[IDX_BT] else None,
                }
        return None
    except Exception as e:
        print(f"Error fetching magnetic data: {e}", file=sys.stderr)
        return None

def fetch_plasma_data():
    """Fetch latest plasma data from NOAA"""
    try:
        url = "https://services.swpc.noaa.gov/products/solar-wind/plasma-7-day.json"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Field indices for plasma data
        IDX_TIME = 0
        IDX_DENSITY = 1
        IDX_SPEED = 2
        IDX_TEMPERATURE = 3
        
        # Get latest non-null entry
        for row in reversed(data[1:]):  # Skip header
            if row[IDX_DENSITY] and row[IDX_SPEED]:  # Density and speed present
                return {
                    'time_tag': row[IDX_TIME],
                    'density': float(row[IDX_DENSITY]),
                    'speed': float(row[IDX_SPEED]),
                    'temperature': float(row[IDX_TEMPERATURE]) if row[IDX_TEMPERATURE] else None,
                }
        return None
    except Exception as e:
        print(f"Error fetching plasma data: {e}", file=sys.stderr)
        return None

def calculate_chi(bz, density, speed):
    """
    Calculate chi amplitude using LUFT formula
    χ = (|Bz| * sqrt(density) * speed) / normalization_factor
    """
    if bz is None or density is None or speed is None:
        return None
    
    # Normalization factor calibrated to 0.15 boundary
    normalization = 50000.0
    
    chi = (abs(bz) * (density ** 0.5) * speed) / normalization
    return chi

def determine_storm_phase(chi, bz):
    """Determine storm phase based on chi and Bz"""
    if chi is None:
        return "UNKNOWN"
    
    if chi > 0.15:
        return "PEAK"
    elif chi >= 0.13:
        if bz and bz < -5:
            return "PRE"
        else:
            return "POST-STORM"
    else:
        return "QUIET"

def get_realtime_data():
    """Main function to fetch and process real-time data"""
    mag_data = fetch_dscovr_data()
    plasma_data = fetch_plasma_data()
    
    if not mag_data or not plasma_data:
        # Return error status
        return {
            'status': 'error',
            'message': 'Unable to fetch DSCOVR data',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    # Calculate chi
    chi = calculate_chi(mag_data['bz'], plasma_data['density'], plasma_data['speed'])
    storm_phase = determine_storm_phase(chi, mag_data['bz'])
    
    # Compile response
    result = {
        'status': 'ok',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'data_timestamp': mag_data['time_tag'],
        'chi': chi,
        'storm_phase': storm_phase,
        'bz': mag_data['bz'],
        'bt': mag_data['bt'],
        'bx': mag_data['bx'],
        'by': mag_data['by'],
        'density': plasma_data['density'],
        'speed': plasma_data['speed'],
        'temperature': plasma_data['temperature'],
        'source': 'DSCOVR/NOAA',
        'warnings': {
            'chi_boundary': chi >= 0.15 if chi else False,
            'chi_violation': chi > 0.15 if chi else False,
            'bz_southward': mag_data['bz'] < 0 if mag_data['bz'] else False,
            'bz_critical': mag_data['bz'] < -8 if mag_data['bz'] else False,
            'high_speed': plasma_data['speed'] >= 600,
            'high_density': plasma_data['density'] >= 8
        }
    }
    
    return result

if __name__ == '__main__':
    # Output JSON
    data = get_realtime_data()
    print(json.dumps(data, indent=2))
