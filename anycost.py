#!/usr/bin/env python3
"""
Oracle OCI AnyCost Stream Adaptor - Unified Entry Point

This script provides a single entry point for all OCI to CloudZero operations:
- CSV processing and transformation
- Live OCI API data fetching
- Daily automation
- Testing and validation

Usage:
  python3 anycost.py csv --input input/data.csv              # Process CSV file
  python3 anycost.py oci --month 2025-09                     # Fetch from OCI API
  python3 anycost.py daily                                   # Run daily sync
  python3 anycost.py test                                    # Test connections
"""

import sys
import os
import argparse
import subprocess
from datetime import datetime, timedelta

# Add src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)


def cmd_csv(args):
    """Process CSV files to CBF format."""
    print("📁 CSV Processing Mode")
    
    from csv_to_cbf import main as csv_main
    
    # Set up arguments for csv_to_cbf module
    csv_args = []
    if args.input:
        csv_args.extend(["--input", args.input])
    if args.output:
        csv_args.extend(["--output", args.output])
    
    # Temporarily replace sys.argv for the csv_to_cbf module
    original_argv = sys.argv
    sys.argv = ["csv_to_cbf.py"] + csv_args
    
    try:
        csv_main()
    finally:
        sys.argv = original_argv


def cmd_oci(args):
    """Fetch data from OCI API and upload to CloudZero."""
    print("☁️  OCI API Mode")
    
    from oci_anycost_adaptor import main as oci_main
    
    # Set up arguments for oci_anycost_adaptor module
    oci_args = []
    if args.month:
        oci_args.extend(["--month", args.month])
    if args.months:
        oci_args.extend(["--months", args.months])
    if args.test_connection:
        oci_args.append("--test-connection")
    if args.dry_run:
        oci_args.append("--dry-run")
    
    # Temporarily replace sys.argv for the oci_anycost_adaptor module
    original_argv = sys.argv
    sys.argv = ["oci_anycost_adaptor.py"] + oci_args
    
    try:
        oci_main()
    finally:
        sys.argv = original_argv


def cmd_daily(args):
    """Run daily sync for yesterday's data."""
    print("📅 Daily Sync Mode")
    
    # Calculate yesterday's date
    yesterday = datetime.now() - timedelta(days=1)
    month = yesterday.strftime("%Y-%m")
    
    print(f"🚀 Starting daily OCI sync for {yesterday.strftime('%Y-%m-%d')}")
    print(f"📅 Processing month: {month}")
    
    # Check if we should use venv or current Python
    venv_python = "venv/bin/python"
    python_cmd = venv_python if os.path.exists(venv_python) else sys.executable
    
    try:
        # Run the OCI adaptor for the current month
        cmd = [python_cmd, __file__, "oci", "--month", month]
        
        if args.dry_run:
            cmd.append("--dry-run")
        
        print(f"🔄 Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        print("✅ Daily sync completed successfully!")
        print(result.stdout)
        
        # Show summary
        print(f"\n📊 Daily sync summary:")
        print(f"   Date processed: {yesterday.strftime('%Y-%m-%d')}")
        print(f"   Month: {month}")
        print(f"   Output: Check output/ directory for CBF files")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Daily sync failed: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


def cmd_test(args):
    """Test OCI and CloudZero connections."""
    print("🔍 Test Mode")
    
    try:
        # Test OCI connection
        print("\n1️⃣ Testing OCI connection...")
        from oci_usage import test_oci_connection
        if test_oci_connection():
            print("✅ OCI connection successful")
        else:
            print("❌ OCI connection failed")
            return False
        
        # Test CloudZero connection
        print("\n2️⃣ Testing CloudZero connection...")
        from cloudzero import CloudZeroClient
        client = CloudZeroClient()
        if client.test_connection():
            print("✅ CloudZero connection successful")
        else:
            print("❌ CloudZero connection failed")
            return False
        
        print("\n✅ All connection tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def main():
    """Main entry point with command routing."""
    parser = argparse.ArgumentParser(
        description="Oracle OCI AnyCost Stream Adaptor",
        epilog="""
Examples:
  %(prog)s csv --input input/data.csv --output output/cbf.csv
  %(prog)s oci --month 2025-09
  %(prog)s oci --months 2025-06,2025-07,2025-08
  %(prog)s daily
  %(prog)s daily --dry-run
  %(prog)s test
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # CSV command
    csv_parser = subparsers.add_parser('csv', help='Process CSV files to CBF format')
    csv_parser.add_argument('--input', required=True, help='Input CSV file path')
    csv_parser.add_argument('--output', help='Output CBF CSV file path')
    csv_parser.set_defaults(func=cmd_csv)
    
    # OCI command  
    oci_parser = subparsers.add_parser('oci', help='Fetch from OCI API and upload to CloudZero')
    oci_parser.add_argument('--month', help='Single month in YYYY-MM format')
    oci_parser.add_argument('--months', help='Multiple months (comma-separated or range)')
    oci_parser.add_argument('--test-connection', action='store_true', help='Test OCI connection only')
    oci_parser.add_argument('--dry-run', action='store_true', help='Prepare but do not upload')
    oci_parser.set_defaults(func=cmd_oci)
    
    # Daily command
    daily_parser = subparsers.add_parser('daily', help='Run daily sync for yesterday\'s data')
    daily_parser.add_argument('--dry-run', action='store_true', help='Test run without upload')
    daily_parser.set_defaults(func=cmd_daily)
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test OCI and CloudZero connections')
    test_parser.set_defaults(func=cmd_test)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    print("🔒 Oracle OCI AnyCost Stream Adaptor")
    print("="*50)
    
    # Route to appropriate command
    try:
        result = args.func(args)
        if result is False:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()