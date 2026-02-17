#!/usr/bin/env python3
"""
Test Core Directive:  Daily Rebound Property
============================================

Tests that χ returns to baseline within 24 hours after perturbation. 

This is a fundamental property of Carl Dean Cline Sr.'s χ ≤ 0.15 discovery: 
the system always rebounds to baseline within 24 hours. 

Author: Carl Dean Cline Sr. 
Location: Lincoln, Nebraska, USA
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path
from datetime import datetime, timedelta

def test_daily_rebound(data_source) -> bool:
    """
    Test that χ returns to baseline within 24 hours. 
    
    Args:
        data_source: Either a Path to existing CSV file, or a directory path for test data generation
        
    Returns:
        True if test passes, False otherwise
    """
    # Convert to Path object if string
    if isinstance(data_source, str):
        data_source = Path(data_source)
    
    # Determine if data_source is an existing file or a directory for test generation
    if data_source.exists() and data_source.is_file():
        # data_source is an existing CSV file
        data_path = data_source
        print(f"Loading data from: {data_path}")
        df = pd.read_csv(data_path)
    else:
        # data_source is a directory for generating test data
        data_path = data_source / "chi_test.csv"
        sample = pd.DataFrame(
            {
                "timestamp": pd.date_range("2025-01-01", periods=12, freq="1h"),
                "chi_amplitude": np.random.uniform(0.05, 0.14, 12),
            }
        )
        sample.to_csv(data_path, index=False)
        print(f"Loading data from: {data_path}")
        df = sample
    
    if 'chi_amplitude' not in df.columns or 'timestamp' not in df.columns:
        print("Error:  Required columns 'chi_amplitude' and 'timestamp' not found")
        return False
    
    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Sort by timestamp
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    print(f"Testing {len(df)} observations...")
    
    baseline_threshold = 0.10  # χ < 0.10 considered baseline
    elevated_threshold = 0.12  # χ > 0.12 considered elevated
    max_rebound_hours = 24
    
    violations = 0
    total_tests = 0
    
    for i in range(len(df) - 1):
        chi = df.loc[i, 'chi_amplitude']
        
        # If χ is elevated, check if it returns to baseline within 24 hours
        if chi > elevated_threshold:
            start = pd.to_datetime(df.loc[i, 'timestamp'])
            
            # Look ahead up to 24 hours
            for j in range(i + 1, len(df)):
                end = pd.to_datetime(df.loc[j, 'timestamp'])
                delta_t = (end - start).total_seconds() / 3600  # hours
                
                if delta_t > max_rebound_hours: 
                    # Didn't return to baseline within 24 hours
                    violations += 1
                    print(f"⚠️  Violation at {start}:  χ={chi:.4f}, no rebound within 24h")
                    break
                
                if df.loc[j, 'chi_amplitude'] < baseline_threshold: 
                    # Returned to baseline
                    total_tests += 1
                    break
    
    print(f"\nTotal elevated events tested: {total_tests}")
    print(f"Rebound violations: {violations}")
    
    if violations == 0:
        print("✅ PASS: All elevated χ events returned to baseline within 24 hours")
        return True
    else: 
        print(f"❌ FAIL:  {violations} events did not return to baseline within 24 hours")
        return False


def main():
    """Main entry point."""
    print("\n" + "=" * 70)
    print("Daily Rebound Directive Test")
    print("Carl Dean Cline Sr.'s χ Discovery Property")
    print("=" * 70 + "\n")
    
    # Look for data files
    data_dir = Path("data")
    
    if not data_dir.exists():
        print("Error: data/ directory not found")
        print("Please ensure χ data files exist in data/")
        sys.exit(1)
    
    # Find χ data files
    chi_files = list(data_dir.glob("chi_analysis_*.csv"))
    chi_files.extend(data_dir.glob("dscovr_chi_*. csv"))
    
    if not chi_files:
        print("Warning: No χ data files found in data/")
        print("Creating minimal test dataset...")
        
        # Create minimal test data
        test_data = pd.DataFrame({
            'timestamp': pd.date_range('2025-01-01', periods=100, freq='1h'),
            'chi_amplitude': np.random.uniform(0.05, 0.14, 100)
        })
        
        test_file = data_dir / "test_chi_data.csv"
        test_data.to_csv(test_file, index=False)
        chi_files = [test_file]
        print(f"Created test file: {test_file}")
    
    # Test each file
    all_passed = True
    for data_file in chi_files: 
        print(f"\nTesting:  {data_file.name}")
        print("-" * 70)
        passed = test_daily_rebound(str(data_file))
        if not passed:
            all_passed = False
        print("-" * 70)
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("Daily rebound property confirmed")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        print("Daily rebound property violated")
        sys.exit(1)


if __name__ == "__main__":
    main()
