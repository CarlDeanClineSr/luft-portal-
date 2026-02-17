#!/usr/bin/env python3
"""
Universal ASAS-SN Query Script

This script queries ASAS-SN Sky Patrol using the skypatrol library for fully automated
light curve retrieval. It can query ANY star by coordinates or name.

Usage:
    # Query specific NSVS targets (default)
    python3 nsvs_direct_query.py
    
    # Query custom targets from command line
    python3 nsvs_direct_query.py --target "My Star" --ra 240.256 --dec 27.611
    
    # Query multiple targets from JSON file
    python3 nsvs_direct_query.py --config custom_targets.json
    
    # Query by star name (uses SIMBAD lookup)
    python3 nsvs_direct_query.py --name "Betelgeuse"

Uses skypatrol (the modern, maintained version of pyasassn) for direct API access.
"""

import json
import os
import sys
import argparse
from datetime import datetime, timezone

try:
    from pyasassn.client import SkyPatrolClient
    SKYPATROL_AVAILABLE = True
except ImportError:
    SKYPATROL_AVAILABLE = False
    print("ERROR: skypatrol not available.")
    print("Install with: pip install skypatrol")
    print("Note: The package is called 'skypatrol' but the module is 'pyasassn'")
    print("This is the newest maintained version of the ASAS-SN API client.")
    if __name__ == "__main__":
        exit(1)

try:
    from astroquery.vizier import Vizier
    from astroquery.simbad import Simbad
    from astropy.coordinates import SkyCoord
    import astropy.units as u
    ASTROQUERY_AVAILABLE = True
except ImportError:
    ASTROQUERY_AVAILABLE = False
    print("WARNING: astroquery not available. Star name resolution will not work.")
    print("Install with: pip install astroquery")

def query_asassn_vizier(ra, dec, radius=2.5):
    """
    Query ASAS-SN data via VizieR mirror using astroquery.
    
    Args:
        ra: Right Ascension (degrees)
        dec: Declination (degrees)
        radius: Search radius (arcminutes, default 2.5)
    
    Returns:
        dict: Dictionary with keys 'source', 'num_sources', 'data' containing catalog
              metadata, or None if query fails or no sources found
    """
    try:
        print(f"    Querying VizieR for ASAS-SN data: RA={ra:.5f}, Dec={dec:.5f}, radius={radius}'")
        
        # Create coordinate object
        coord = SkyCoord(ra=ra*u.deg, dec=dec*u.deg, frame='icrs')
        
        # Query VizieR for ASAS-SN catalog (II/366 is ASAS-SN Variable Stars Database)
        # Use reasonable limit since cone searches should return few results
        v = Vizier(columns=['all'], row_limit=100)
        result = v.query_region(coord, radius=radius*u.arcmin, catalog='II/366')
        
        if result and len(result) > 0:
            # Convert astropy table to dict for JSON serialization
            table = result[0]
            print(f"    ✓ Found {len(table)} sources in VizieR")
            
            # Convert table to list of dicts
            data = []
            for row in table:
                row_dict = {}
                for col in table.colnames:
                    val = row[col]
                    # Convert masked values and numpy types to Python types
                    if hasattr(val, 'mask') and val.mask:
                        row_dict[col] = None
                    elif hasattr(val, 'item'):
                        row_dict[col] = val.item()
                    else:
                        row_dict[col] = val
                data.append(row_dict)
            
            return {
                'source': 'VizieR II/366 (ASAS-SN Variable Stars)',
                'num_sources': len(table),
                'data': data
            }
        else:
            print(f"    ✗ No sources found in VizieR")
            return None
            
    except Exception as e:
        print(f"    ✗ VizieR Query Error: {e}")
        return None


def convert_deg_to_hms_dms(ra_deg, dec_deg):
    """
    Convert decimal degree coordinates to HMS/DMS format.
    
    Args:
        ra_deg: Right Ascension in decimal degrees
        dec_deg: Declination in decimal degrees
    
    Returns:
        tuple: (ra_h, ra_m, ra_s, dec_sign, dec_d, dec_m, dec_s)
    """
    # Convert RA to HMS
    ra_h = int(ra_deg / 15)
    ra_m = int((ra_deg / 15 - ra_h) * 60)
    ra_s = ((ra_deg / 15 - ra_h) * 60 - ra_m) * 60
    
    # Convert Dec to DMS
    dec_sign = '+' if dec_deg >= 0 else '-'
    dec_d = int(abs(dec_deg))
    dec_m = int((abs(dec_deg) - dec_d) * 60)
    dec_s = ((abs(dec_deg) - dec_d) * 60 - dec_m) * 60
    
    return ra_h, ra_m, ra_s, dec_sign, dec_d, dec_m, dec_s


def query_asassn_lightcurve(client, ra, dec, radius=10):
    """
    Query ASAS-SN Sky Patrol for full light curve data using skypatrol.
    
    Args:
        client: SkyPatrolClient instance
        ra: Right Ascension (degrees)
        dec: Declination (degrees)
        radius: Search radius (arcseconds, default 10)
    
    Returns:
        dict: Light curve data with HJD, magnitudes, errors, or None if query fails
    """
    try:
        print(f"    Querying ASAS-SN Sky Patrol: RA={ra:.5f}, Dec={dec:.5f}, radius={radius}\"")
        
        # Cone search to find sources
        results = client.cone_search(
            ra_deg=ra,
            dec_deg=dec,
            radius=radius,
            catalog='master_list',
            download=False
        )
        
        if results is None or len(results) == 0:
            print(f"    ✗ No sources found in ASAS-SN catalog")
            return None
        
        # Get the closest match
        source = results.iloc[0]
        # Convert to Python int (handles numpy int64, int32, or regular int)
        asassn_id = int(source['asas_sn_id']) if hasattr(source['asas_sn_id'], 'item') else source['asas_sn_id']
        print(f"    ✓ Found source: ASAS-SN ID {asassn_id}")
        
        # Download full light curve
        print(f"    Downloading light curve data...")
        lc_collection = client.query_list(
            [asassn_id],
            catalog='master_list',
            download=True
        )
        
        if not lc_collection or len(lc_collection) == 0:
            print(f"    ✗ No light curve data available")
            return None
        
        # Extract light curve
        lc = lc_collection[asassn_id]
        
        # Convert to simple format - lc.data is a DataFrame
        data_points = []
        for idx in range(len(lc.data)):
            row = lc.data.iloc[idx]
            data_points.append({
                'hjd': float(row['jd']),  # Julian Date
                'mag': float(row['mag']),
                'mag_err': float(row['mag_err']),
                'filter': row['phot_filter'],
                'quality': row['quality']
            })
        
        print(f"    ✓ Downloaded {len(data_points)} observations")
        
        return {
            'asassn_id': asassn_id,
            'num_observations': len(data_points),
            'data': data_points
        }
        
    except Exception as e:
        print(f"    ✗ Query Error: {e}")
        import traceback
        traceback.print_exc()
        return None

# Default NSVS target list (Schmidt "Dipper" Stars)
NSVS_TARGETS = {
    "NSVS 2354429": {
        "ra": 240.25563,
        "dec": 27.61100,
        "name": "NSVS 2354429",
        "note": "The 'Smoker' - Confirmed pulse Mag 10.317"
    },
    "NSVS 2913753": {
        "ra": 307.87533,
        "dec": 41.21147,
        "name": "NSVS 2913753",
        "note": "Schmidt Dipper - Cygnus/Lyra region"
    },
    "NSVS 3037513": {
        "ra": 308.37521,
        "dec": 41.32047,
        "name": "NSVS 3037513",
        "note": "Schmidt Dipper - Cygnus/Lyra region"
    },
    "NSVS 6804071": {
        "ra": 304.87933,
        "dec": 41.54903,
        "name": "NSVS 6804071",
        "note": "Schmidt Dipper - Cygnus/Lyra region"
    },
    "NSVS 6814519": {
        "ra": 305.00079,
        "dec": 41.71017,
        "name": "NSVS 6814519",
        "note": "Schmidt Dipper - Cygnus/Lyra region"
    },
    "NSVS 7255468": {
        "ra": 306.44008,
        "dec": 41.66428,
        "name": "NSVS 7255468",
        "note": "Schmidt Dipper - Cygnus/Lyra region"
    },
    "NSVS 7575062": {
        "ra": 307.88392,
        "dec": 41.80644,
        "name": "NSVS 7575062",
        "note": "Schmidt Dipper - Cygnus/Lyra region"
    },
    "NSVS 7642696": {
        "ra": 308.23404,
        "dec": 41.65069,
        "name": "NSVS 7642696",
        "note": "Schmidt Dipper - Cygnus/Lyra region"
    },
}


def resolve_star_name(star_name):
    """
    Resolve star name to RA/Dec coordinates using SIMBAD.
    
    Args:
        star_name: Name of the star (e.g., "Betelgeuse", "Alpha Ori", "HD 39801")
    
    Returns:
        dict: {'ra': degrees, 'dec': degrees, 'name': resolved_name} or None if not found
    """
    if not ASTROQUERY_AVAILABLE:
        print(f"  ✗ Cannot resolve star name - astroquery not available")
        return None
    
    try:
        print(f"  Resolving star name '{star_name}' via SIMBAD...")
        simbad = Simbad()
        simbad.add_votable_fields('ra(d)', 'dec(d)')
        result = simbad.query_object(star_name)
        
        if result and len(result) > 0:
            ra = float(result['RA_d'][0])
            dec = float(result['DEC_d'][0])
            resolved_name = result['MAIN_ID'][0]
            print(f"  ✓ Resolved to: {resolved_name} (RA={ra:.5f}, Dec={dec:.5f})")
            return {
                'ra': ra,
                'dec': dec,
                'name': resolved_name,
                'note': f'Resolved from {star_name}'
            }
        else:
            print(f"  ✗ Star not found in SIMBAD")
            return None
            
    except Exception as e:
        print(f"  ✗ SIMBAD lookup error: {e}")
        return None


def load_targets_from_file(filename):
    """
    Load target list from JSON configuration file.
    
    Expected format:
    {
        "Star Name 1": {"ra": 123.456, "dec": 45.678, "note": "optional note"},
        "Star Name 2": {"ra": 234.567, "dec": -12.345}
    }
    
    Or by star names to resolve:
    {
        "targets": ["Betelgeuse", "Rigel", "Sirius"]
    }
    
    Args:
        filename: Path to JSON configuration file
    
    Returns:
        dict: Target dictionary in same format as NSVS_TARGETS
    """
    try:
        with open(filename, 'r') as f:
            config = json.load(f)
        
        # Check if it's a list of names to resolve
        if 'targets' in config and isinstance(config['targets'], list):
            print(f"Resolving {len(config['targets'])} star names from config...")
            targets = {}
            for star_name in config['targets']:
                resolved = resolve_star_name(star_name)
                if resolved:
                    targets[resolved['name']] = resolved
            return targets
        else:
            # Direct coordinate list
            return config
            
    except Exception as e:
        print(f"Error loading config file: {e}")
        return None

def main():
    """Execute fully automated ASAS-SN light curve queries for any star targets"""
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Query ASAS-SN light curves for any stars',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Query default NSVS targets
  python3 nsvs_direct_query.py
  
  # Query a single star by coordinates
  python3 nsvs_direct_query.py --target "HD 189733" --ra 300.179 --dec 22.709
  
  # Query a star by name (SIMBAD lookup)
  python3 nsvs_direct_query.py --name "Betelgeuse"
  python3 nsvs_direct_query.py --name "Alpha Orionis"
  
  # Query multiple stars from JSON config file
  python3 nsvs_direct_query.py --config my_targets.json
  
  # Combine: default + custom star
  python3 nsvs_direct_query.py --name "Sirius" --include-defaults
        """
    )
    parser.add_argument('--target', type=str, help='Name for custom target')
    parser.add_argument('--ra', type=float, help='Right Ascension (degrees)')
    parser.add_argument('--dec', type=float, help='Declination (degrees)')
    parser.add_argument('--name', type=str, help='Star name to resolve via SIMBAD')
    parser.add_argument('--config', type=str, help='JSON file with target list')
    parser.add_argument('--include-defaults', action='store_true', 
                       help='Include default NSVS targets with custom targets')
    parser.add_argument('--radius', type=float, default=10.0,
                       help='Search radius in arcseconds (default: 10)')
    
    args = parser.parse_args()
    
    # Determine target list
    targets = {}
    
    # Load from config file
    if args.config:
        print(f"Loading targets from config file: {args.config}")
        loaded_targets = load_targets_from_file(args.config)
        if loaded_targets:
            targets.update(loaded_targets)
            print(f"✓ Loaded {len(loaded_targets)} targets from config")
        else:
            print("✗ Failed to load config file")
            exit(1)
    
    # Add single target by coordinates
    if args.target and args.ra is not None and args.dec is not None:
        targets[args.target] = {
            'ra': args.ra,
            'dec': args.dec,
            'name': args.target,
            'note': 'Custom target from command line'
        }
        print(f"✓ Added custom target: {args.target}")
    
    # Add single target by name
    if args.name:
        resolved = resolve_star_name(args.name)
        if resolved:
            targets[resolved['name']] = resolved
        else:
            print(f"✗ Could not resolve star name: {args.name}")
            if not targets and not args.include_defaults:
                exit(1)
    
    # Include defaults if requested or if no custom targets specified
    if args.include_defaults or len(targets) == 0:
        print(f"Including default NSVS targets ({len(NSVS_TARGETS)} stars)")
        targets.update(NSVS_TARGETS)
    
    # Validate we have targets
    if len(targets) == 0:
        print("ERROR: No targets specified!")
        print("Use --help for usage examples")
        exit(1)
    
    print("="*70)
    print("UNIVERSAL ASAS-SN QUERY MISSION (via skypatrol)")
    print("="*70)
    print(f"Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"Total Targets: {len(targets)}")
    print(f"Search Radius: {args.radius}\" (arcseconds)")
    print(f"Method: ASAS-SN Sky Patrol via skypatrol library")
    print(f"skypatrol available: {SKYPATROL_AVAILABLE}")
    print("="*70)
    print()
    
    # Initialize Sky Patrol client
    if not SKYPATROL_AVAILABLE:
        print("ERROR: skypatrol library not available!")
        print("Install with: pip install skypatrol")
        exit(1)
    
    try:
        print("Initializing ASAS-SN Sky Patrol client...")
        client = SkyPatrolClient()
        print("✓ Client initialized successfully")
        print()
    except Exception as e:
        print(f"✗ Failed to initialize client: {e}")
        exit(1)
    
    # Run automated queries
    results = {}
    successful_queries = 0
    failed_queries = 0
    
    for name, coords in targets.items():
        print(f"TARGET: {name}")
        if 'note' in coords:
            print(f"  Note: {coords['note']}")
        print(f"  Coordinates: RA={coords['ra']:.5f}°, Dec={coords['dec']:.5f}°")
        
        # Query for full light curve
        lc_data = query_asassn_lightcurve(client, coords['ra'], coords['dec'], radius=args.radius)
        
        if lc_data:
            results[name] = {
                'coordinates': coords,
                'light_curve': lc_data,
                'query_time': datetime.now(timezone.utc).isoformat(),
                'status': 'SUCCESS'
            }
            print(f"  ✓ Light curve data retrieved ({lc_data['num_observations']} points)")
            successful_queries += 1
        else:
            results[name] = {
                'coordinates': coords,
                'light_curve': None,
                'error': 'Query failed or no data',
                'query_time': datetime.now(timezone.utc).isoformat(),
                'status': 'FAILED'
            }
            print(f"  ✗ No light curve data available")
            failed_queries += 1
        
        print()
    
    # Summary
    print("="*70)
    print("AUTOMATED QUERY MISSION COMPLETE")
    print("="*70)
    print(f"Successful: {successful_queries}/{len(targets)}")
    print(f"Failed: {failed_queries}/{len(targets)}")
    print()
    
    # Save results
    output_dir = "data/beacon_scan"
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    
    # Save full light curve data
    lightcurve_file = f'{output_dir}/asassn_lightcurves_{timestamp}.json'
    with open(lightcurve_file, 'w') as f:
        json.dump({
            'query_time': datetime.now(timezone.utc).isoformat(),
            'method': 'ASAS-SN Sky Patrol via skypatrol (fully automated)',
            'search_radius_arcsec': args.radius,
            'note': 'This contains complete time-series light curve data for any queried stars.',
            'targets_queried': len(targets),
            'successful_queries': successful_queries,
            'failed_queries': failed_queries,
            'results': results
        }, f, indent=2)
    
    print(f"Full light curve data saved to: {lightcurve_file}")
    
    # Generate summary for easy analysis
    summary = []
    for name, result in results.items():
        if result['status'] == 'SUCCESS' and result['light_curve']:
            lc = result['light_curve']['data']
            mags = [p['mag'] for p in lc]
            summary.append({
                'name': name,
                'asassn_id': result['light_curve']['asassn_id'],
                'num_observations': len(lc),
                'min_mag': min(mags),
                'max_mag': max(mags),
                'median_mag': sorted(mags)[len(mags)//2],
                'flux_ratio': 10**((sorted(mags)[len(mags)//2] - min(mags)) / 2.5)
            })
    
    summary_file = f'{output_dir}/lightcurve_summary_{timestamp}.json'
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"Summary statistics saved to: {summary_file}")
    print()
    
    # Print beacon analysis summary
    if len(summary) > 0:
        print("="*70)
        print("BRIGHTNESS VARIATION ANALYSIS")
        print("="*70)
        print()
        
        for item in summary:
            print(f"{item['name']} ({item['asassn_id']}):")
            print(f"  Observations: {item['num_observations']}")
            print(f"  Min Mag: {item['min_mag']:.2f} (brightest)")
            print(f"  Max Mag: {item['max_mag']:.2f} (dimmest)")
            print(f"  Median Mag: {item['median_mag']:.2f}")
            print(f"  Flux Ratio: {item['flux_ratio']:.1f}×")
            
            # Check beacon criteria
            is_beacon = (item['min_mag'] < 11.0 and item['flux_ratio'] > 5.0)
            if is_beacon:
                print(f"  ★★★ BEACON SIGNATURE DETECTED ★★★")
            else:
                is_variable = item['flux_ratio'] > 2.0
                if is_variable:
                    print(f"  Variable star (flux ratio > 2×)")
                else:
                    print(f"  Relatively stable")
            print()
    
    print("="*70)
    print("DATA READY FOR ANALYSIS")
    print("="*70)
    print(f"  Light curves: {lightcurve_file}")
    print(f"  Statistics: {summary_file}")
    print("="*70)
    
    return results

if __name__ == "__main__":
    main()
