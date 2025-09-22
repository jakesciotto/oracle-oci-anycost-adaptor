#!/usr/bin/env python3
"""
Daily OCI to CloudZero sync script.
Runs automatically to fetch yesterday's usage data and upload to CloudZero.
"""

import os
import sys
import subprocess
from datetime import datetime, timedelta

def run_daily_sync():
    """Run daily sync for yesterday's data."""
    
    # Calculate yesterday's date
    yesterday = datetime.now() - timedelta(days=1)
    month = yesterday.strftime("%Y-%m")
    
    print(f"🚀 Starting daily OCI sync for {yesterday.strftime('%Y-%m-%d')}")
    print(f"📅 Processing month: {month}")
    
    # Activate virtual environment and run the adaptor
    venv_python = "venv/bin/python"
    if not os.path.exists(venv_python):
        print("❌ Virtual environment not found. Please run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt")
        sys.exit(1)
    
    try:
        # Run the OCI adaptor for the current month
        cmd = [venv_python, "run_oci_adaptor.py", "--month", month]
        
        print(f"🔄 Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        print("✅ Daily sync completed successfully!")
        print(result.stdout)
        
        # Show summary
        print(f"\n📊 Daily sync summary:")
        print(f"   Date processed: {yesterday.strftime('%Y-%m-%d')}")
        print(f"   Month: {month}")
        print(f"   Output: output/oci_cbf_output.csv")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Daily sync failed: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

def run_test_sync():
    """Run test sync (dry run) to verify configuration."""
    
    venv_python = "venv/bin/python"
    
    try:
        # Test connection first
        print("🔍 Testing OCI connection...")
        cmd = [venv_python, "run_oci_adaptor.py", "--test-connection"]
        subprocess.run(cmd, check=True)
        
        # Run dry run for current month
        month = datetime.now().strftime("%Y-%m")
        print(f"🧪 Running dry run for {month}...")
        cmd = [venv_python, "run_oci_adaptor.py", "--month", month, "--dry-run"]
        subprocess.run(cmd, check=True)
        
        print("✅ Test sync completed successfully!")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Test sync failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        run_test_sync()
    else:
        run_daily_sync()