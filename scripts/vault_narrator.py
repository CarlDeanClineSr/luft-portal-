#!/usr/bin/env python3
"""
Vault Narrator - Auto-generate latest status markdown
Reads the latest CSV data and creates LATEST_VAULT_STATUS.md

Requirements:
- Read data/cme_heartbeat_log_2025_12.csv (comma-separated format with headers)
- Extract the latest 20 rows
- Count consecutive χ = 0.15 locks (chi_amplitude column)
- Calculate streak statistics (first lock, last lock, duration)
- Get latest solar wind parameters (density, speed, temperature if available)
- Generate LATEST_VAULT_STATUS.md with proper formatting
- Handle errors gracefully
"""

import pandas as pd
from datetime import datetime, timezone
import os
import sys

# Configuration
csv_path = "data/cme_heartbeat_log_2025_12.csv"
output_path = "LATEST_VAULT_STATUS.md"
chi_lock_threshold = 0.15
chi_tolerance = 0.0001

def main():
    # Check if file exists
    if not os.path.exists(csv_path):
        print(f"ERROR: CSV file not found: {csv_path}")
        print("The vault narrator requires the heartbeat log to generate status.")
        sys.exit(1)
    
    try:
        # Read CSV (comma-separated with headers)
        df = pd.read_csv(csv_path)
        print(f"✓ Loaded {len(df)} rows from {csv_path}")
        
    except Exception as e:
        print(f"ERROR: Failed to read CSV file: {e}")
        sys.exit(1)
    
    # Validate required columns
    required_cols = ['timestamp_utc', 'chi_amplitude']
    
    for col in required_cols:
        if col not in df.columns:
            print(f"ERROR: Required column '{col}' not found in CSV")
            print(f"Available columns: {list(df.columns)}")
            sys.exit(1)
    
    # Handle empty data
    if len(df) == 0:
        print("ERROR: CSV file is empty")
        sys.exit(1)
    
    try:
        # Convert timestamp
        df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])
        df = df.sort_values('timestamp_utc')
        
        # Get last 20 rows
        latest_20 = df.tail(20).copy()
        
        # Count consecutive χ = 0.15 locks from the end
        streak = 0
        first_lock_idx = None
        last_lock_idx = None
        
        chi_values = df['chi_amplitude'].values
        
        # Count consecutive locks from the end
        for idx in range(len(df) - 1, -1, -1):
            chi = chi_values[idx]
            if abs(chi - chi_lock_threshold) < chi_tolerance:
                streak += 1
                first_lock_idx = idx
                if last_lock_idx is None:
                    last_lock_idx = idx
            else:
                break
        
        # Find the most recent lock (even if not in current streak)
        most_recent_lock_time = None
        if streak == 0:
            # Need to find the most recent lock that's not at the end
            for idx in range(len(df) - 1, -1, -1):
                chi = chi_values[idx]
                if abs(chi - chi_lock_threshold) < chi_tolerance:
                    most_recent_lock_time = df.iloc[idx]['timestamp_utc']
                    break
        
        # Get streak statistics
        if streak > 0:
            last_lock_time = df.iloc[last_lock_idx]['timestamp_utc']
            first_lock_time = df.iloc[first_lock_idx]['timestamp_utc']
            duration = last_lock_time - first_lock_time
        else:
            last_lock_time = None
            first_lock_time = None
            duration = None
        
        # Get latest solar wind parameters
        latest_row = df.iloc[-1]
        latest_density = latest_row.get('density_p_cm3', None)
        latest_speed = latest_row.get('speed_km_s', None)
        
        # Determine status
        if streak > 0:
            status = "ACTIVE"
        else:
            status = "QUIET"
        
        # Generate markdown
        generate_markdown(
            latest_20=latest_20,
            streak=streak,
            last_lock_time=last_lock_time,
            first_lock_time=first_lock_time,
            duration=duration,
            most_recent_lock_time=most_recent_lock_time,
            latest_density=latest_density,
            latest_speed=latest_speed,
            status=status,
            total_rows=len(df)
        )
        
        print(f"✓ Vault narrator complete")
        print(f"✓ Status: {status}")
        print(f"✓ Streak: {streak} consecutive χ = 0.15 locks")
        if last_lock_time:
            print(f"✓ Last lock: {last_lock_time}")
        
    except Exception as e:
        print(f"ERROR: Failed to process data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def generate_markdown(latest_20, streak, last_lock_time, first_lock_time, duration,
                     most_recent_lock_time, latest_density, latest_speed, status, total_rows):
    """Generate the LATEST_VAULT_STATUS.md file"""
    
    generation_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    
    # Header
    md = "# 🔐 VAULT STATUS REPORT\n\n"
    md += f"**Generated:** {generation_time}  \n"
    md += f"**Data Source:** `{csv_path}`\n\n"
    md += "---\n\n"
    
    # Current Status
    md += f"## ⚡ CURRENT STATUS: {status}\n\n"
    
    if streak > 0:
        md += f"**Latest χ = 0.15 Streak Count:** {streak} consecutive readings  \n"
        if last_lock_time:
            md += f"**Last Lock Timestamp:** {last_lock_time.strftime('%Y-%m-%d %H:%M:%S UTC')}  \n"
        if first_lock_time and duration:
            md += f"**First Lock in Streak:** {first_lock_time.strftime('%Y-%m-%d %H:%M:%S UTC')}  \n"
            hours = duration.total_seconds() / 3600
            if hours >= 24:
                days = hours / 24
                md += f"**Streak Duration:** {days:.1f} days ({hours:.1f} hours)  \n"
            else:
                md += f"**Streak Duration:** {hours:.1f} hours  \n"
    else:
        md += "**No active χ = 0.15 locks detected**  \n"
        if most_recent_lock_time:
            md += f"**Last Lock Timestamp:** {most_recent_lock_time.strftime('%Y-%m-%d %H:%M:%S UTC')}  \n"
    
    # Solar wind conditions
    if latest_density is not None or latest_speed is not None:
        md += "\n**Latest Solar Wind Conditions:**  \n"
        if latest_density is not None and not pd.isna(latest_density):
            md += f"- Density: {latest_density:.2f} p/cm³  \n"
        if latest_speed is not None and not pd.isna(latest_speed):
            md += f"- Speed: {latest_speed:.1f} km/s  \n"
    
    md += "\n---\n\n"
    
    # Latest 20 readings table
    md += "## 📊 LATEST 20 READINGS\n\n"
    md += "| Time (UTC)          | χ Amplitude | Density (p/cm³) | Speed (km/s) | χ Status |\n"
    md += "|---------------------|-------------|-----------------|--------------|----------|\n"
    
    for _, row in latest_20.iterrows():
        timestamp = row['timestamp_utc'].strftime('%Y-%m-%d %H:%M:%S')
        chi = row['chi_amplitude']
        
        # Check if this is a lock
        is_lock = abs(chi - chi_lock_threshold) < chi_tolerance
        chi_status = "✅ LOCK" if is_lock else "—"
        
        # Get density and speed
        density = row.get('density_p_cm3', None)
        speed = row.get('speed_km_s', None)
        
        density_str = f"{density:.2f}" if density is not None and not pd.isna(density) else "—"
        speed_str = f"{speed:.1f}" if speed is not None and not pd.isna(speed) else "—"
        
        md += f"| {timestamp} | {chi:.4f} | {density_str} | {speed_str} | {chi_status} |\n"
    
    md += "\n---\n\n"
    
    # Verdict
    md += "## 🎯 VERDICT\n\n"
    
    if status == "ACTIVE":
        if streak >= 10:
            md += "**The vault is in a SUPERSTREAK.**  \n"
            md += f"**{streak} consecutive χ = 0.15 locks detected.**  \n"
            md += "**Boundary recoil law active - monitor for coherence signatures.**\n"
        elif streak >= 3:
            md += "**The vault is breathing steady.**  \n"
            md += "**Heartbeat cycle in progress.**  \n"
            md += f"**χ = 0.15 streak active ({streak} locks) - watch for boundary recoil signatures.**\n"
        else:
            md += "**Active χ = 0.15 detection.**  \n"
            md += "**Vault warming up.**\n"
    else:
        md += "**The vault is quiet.**  \n"
        md += "**No χ = 0.15 locks detected in latest readings.**  \n"
        md += "**Waiting for next coherence phase.**\n"
    
    md += "\n---\n\n"
    
    # Auto-update info
    md += "**Next auto-update:** Every hour via GitHub Actions  \n"
    md += "**Manual trigger:** Actions → Vault Narrator → Run workflow\n\n"
    md += "---\n\n"
    
    # Footer
    md += "*— The Vault Narrator*  \n"
    md += "*Automated by LUFT Portal heartbeat detection system*\n"
    
    # Write to file
    with open(output_path, "w") as f:
        f.write(md)
    
    print(f"✓ Generated {output_path} ({len(md)} bytes)")


if __name__ == "__main__":
    main()
