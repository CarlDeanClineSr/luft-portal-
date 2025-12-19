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
from pathlib import Path

# Configuration
csv_path = "data/cme_heartbeat_log_2025_12.csv"
output_path = "LATEST_VAULT_STATUS.md"
chi_lock_threshold = 0.15
chi_tolerance = 0.0001

# Streak flag thresholds (in hours) - can be overridden via environment variables
LONG_STREAK_HOURS = float(os.environ.get("VAULT_LONG_STREAK_HOURS", "48"))
SUPERSTREAK_HOURS = float(os.environ.get("VAULT_SUPERSTREAK_HOURS", "72"))

# NOAA summary paths
NOAA_SRS_PATH = Path("reports/latest_srs.md")
NOAA_F107_PATH = Path("reports/latest_f107.md")

# Charts output directory
CHARTS_DIR = Path("reports/charts")
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

def get_streak_flag(duration_hours):
    """Determine streak flag based on duration thresholds"""
    if duration_hours >= SUPERSTREAK_HOURS:
        return f"Superstreak {duration_hours:.0f}h"
    elif duration_hours >= LONG_STREAK_HOURS:
        return f"Long streak {duration_hours:.0f}h"
    else:
        return None


def check_noaa_summaries():
    """Check for NOAA summary files and return their info"""
    summaries = {}
    
    for name, path in [("SRS", NOAA_SRS_PATH), ("F10.7", NOAA_F107_PATH)]:
        if path.exists():
            try:
                # Get file modification time
                mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
                summaries[name] = {
                    "path": path,
                    "available": True,
                    "timestamp": mtime
                }
            except Exception as e:
                print(f"Warning: Could not get timestamp for {path}: {e}")
                summaries[name] = {
                    "path": path,
                    "available": True,
                    "timestamp": None
                }
        else:
            summaries[name] = {
                "path": path,
                "available": False,
                "timestamp": None
            }
    
    return summaries


def generate_charts(df, streak_count, charts_dir):
    """Generate mini charts for the report"""
    try:
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend for CI
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
    except ImportError:
        print("Warning: matplotlib not available, skipping chart generation")
        return None, None
    
    # Filter to last ~72 hours of data
    if len(df) == 0:
        print("Warning: No data available for charts")
        return None, None
    
    latest_time = df['timestamp_utc'].iloc[-1]
    cutoff_time = latest_time - pd.Timedelta(hours=72)
    df_window = df[df['timestamp_utc'] >= cutoff_time].copy()
    
    if len(df_window) == 0:
        print("Warning: No data in 72-hour window for charts")
        return None, None
    
    # Chart 1: χ amplitude and streak sparkline
    chi_chart_path = charts_dir / "chi_amplitude_sparkline.png"
    try:
        fig, ax = plt.subplots(figsize=(8, 2), dpi=100)
        
        # Plot χ amplitude
        ax.plot(df_window['timestamp_utc'], df_window['chi_amplitude'], 
                color='#2E86AB', linewidth=1.5, marker='o', markersize=3)
        
        # Add horizontal line at χ = 0.15
        ax.axhline(y=chi_lock_threshold, color='#A23B72', linestyle='--', 
                   linewidth=1, alpha=0.7, label='χ = 0.15 lock')
        
        # Highlight lock periods
        is_lock = (df_window['chi_amplitude'] - chi_lock_threshold).abs() < chi_tolerance
        lock_periods = df_window[is_lock]
        if len(lock_periods) > 0:
            ax.scatter(lock_periods['timestamp_utc'], lock_periods['chi_amplitude'],
                      color='#F18F01', s=30, zorder=5, label='Lock', alpha=0.8)
        
        ax.set_xlabel('Time (UTC)', fontsize=8)
        ax.set_ylabel('χ Amplitude', fontsize=8)
        ax.set_title(f'χ Amplitude (last 72h) — Current streak: {streak_count} locks', 
                    fontsize=9, pad=5)
        ax.tick_params(labelsize=7)
        ax.grid(True, alpha=0.3, linewidth=0.5)
        ax.legend(fontsize=7, loc='upper right')
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        plt.savefig(chi_chart_path, bbox_inches='tight', dpi=100)
        plt.close()
        print(f"✓ Generated χ amplitude chart: {chi_chart_path}")
    except Exception as e:
        print(f"Warning: Failed to generate χ amplitude chart: {e}")
        chi_chart_path = None
    
    # Chart 2: Solar wind speed/density mini-plot
    sw_chart_path = charts_dir / "solar_wind_miniplot.png"
    try:
        # Check if we have solar wind data
        has_speed = 'speed_km_s' in df_window.columns and df_window['speed_km_s'].notna().any()
        has_density = 'density_p_cm3' in df_window.columns and df_window['density_p_cm3'].notna().any()
        
        if not (has_speed or has_density):
            print("Warning: No solar wind data available for chart")
            sw_chart_path = None
        else:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 3), dpi=100, sharex=True)
            
            # Plot speed
            if has_speed:
                valid_speed = df_window[df_window['speed_km_s'].notna()]
                ax1.plot(valid_speed['timestamp_utc'], valid_speed['speed_km_s'],
                        color='#06A77D', linewidth=1.5, marker='o', markersize=2)
                ax1.set_ylabel('Speed (km/s)', fontsize=8)
                ax1.tick_params(labelsize=7)
                ax1.grid(True, alpha=0.3, linewidth=0.5)
            else:
                ax1.text(0.5, 0.5, 'No speed data', ha='center', va='center',
                        transform=ax1.transAxes, fontsize=8)
                ax1.set_ylabel('Speed (km/s)', fontsize=8)
            
            # Plot density
            if has_density:
                valid_density = df_window[df_window['density_p_cm3'].notna()]
                ax2.plot(valid_density['timestamp_utc'], valid_density['density_p_cm3'],
                        color='#D62246', linewidth=1.5, marker='o', markersize=2)
                ax2.set_ylabel('Density (p/cm³)', fontsize=8)
                ax2.tick_params(labelsize=7)
                ax2.grid(True, alpha=0.3, linewidth=0.5)
            else:
                ax2.text(0.5, 0.5, 'No density data', ha='center', va='center',
                        transform=ax2.transAxes, fontsize=8)
                ax2.set_ylabel('Density (p/cm³)', fontsize=8)
            
            ax2.set_xlabel('Time (UTC)', fontsize=8)
            
            # Format x-axis
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
            plt.xticks(rotation=45, ha='right')
            
            fig.suptitle('Solar Wind Parameters (last 72h)', fontsize=9, y=0.98)
            plt.tight_layout()
            plt.savefig(sw_chart_path, bbox_inches='tight', dpi=100)
            plt.close()
            print(f"✓ Generated solar wind chart: {sw_chart_path}")
    except Exception as e:
        print(f"Warning: Failed to generate solar wind chart: {e}")
        sw_chart_path = None
    
    return chi_chart_path, sw_chart_path


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
        
        # Calculate streak duration in hours
        duration_hours = None
        if duration is not None:
            duration_hours = duration.total_seconds() / 3600
        
        # Determine status
        if streak > 0:
            status = "ACTIVE"
        else:
            status = "QUIET"
        
        # Check NOAA summaries
        noaa_summaries = check_noaa_summaries()
        
        # Generate charts
        chi_chart_path, sw_chart_path = generate_charts(df, streak, CHARTS_DIR)
        
        # Generate markdown
        generate_markdown(
            latest_20=latest_20,
            streak=streak,
            last_lock_time=last_lock_time,
            first_lock_time=first_lock_time,
            duration=duration,
            duration_hours=duration_hours,
            most_recent_lock_time=most_recent_lock_time,
            latest_density=latest_density,
            latest_speed=latest_speed,
            status=status,
            total_rows=len(df),
            noaa_summaries=noaa_summaries,
            chi_chart_path=chi_chart_path,
            sw_chart_path=sw_chart_path
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
                     duration_hours, most_recent_lock_time, latest_density, latest_speed, 
                     status, total_rows, noaa_summaries, chi_chart_path, sw_chart_path):
    """Generate the LATEST_VAULT_STATUS.md file"""
    
    generation_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    
    # Header
    md = "# 🔐 VAULT STATUS REPORT\n\n"
    md += f"**Generated:** {generation_time}  \n"
    md += f"**Data Source:** `{csv_path}`\n\n"
    md += "---\n\n"
    
    # Current Status with streak flag
    status_line = f"## ⚡ CURRENT STATUS: {status}"
    
    # Add streak flag if applicable
    if streak > 0 and duration_hours is not None:
        streak_flag = get_streak_flag(duration_hours)
        if streak_flag:
            status_line += f" — {streak_flag} @ χ=0.15"
    
    md += status_line + "\n\n"
    
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
    
    # NOAA Summaries section
    md += "## 🌞 NOAA SPACE WEATHER SUMMARIES\n\n"
    
    for name, info in noaa_summaries.items():
        if info["available"]:
            relative_path = str(info["path"])
            if info["timestamp"]:
                time_str = info["timestamp"].strftime('%Y-%m-%d %H:%M UTC')
                md += f"- [{name} Report]({relative_path}) (fetched: {time_str})  \n"
            else:
                md += f"- [{name} Report]({relative_path})  \n"
        else:
            md += f"- {name} Report: *not available*  \n"
    
    md += "\n---\n\n"
    
    # Mini charts section
    if chi_chart_path or sw_chart_path:
        md += "## 📈 MINI CHARTS\n\n"
        
        if chi_chart_path:
            # Use relative path from repository root
            chart_rel_path = str(chi_chart_path).replace("\\", "/")
            md += f"### χ Amplitude & Streak (72h window)\n\n"
            md += f"![χ Amplitude Sparkline]({chart_rel_path})\n\n"
        
        if sw_chart_path:
            chart_rel_path = str(sw_chart_path).replace("\\", "/")
            md += f"### Solar Wind Parameters (72h window)\n\n"
            md += f"![Solar Wind Mini-plot]({chart_rel_path})\n\n"
        
        md += "---\n\n"
    
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
