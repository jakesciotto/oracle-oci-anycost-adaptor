#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2016-2024, CloudZero, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""
Oracle Cloud Infrastructure (OCI) AnyCost Stream Adaptor

This adaptor performs the following steps:
  1. Fetch cost data from Oracle Cloud Infrastructure Usage API for a billing month
  2. Transform that OCI data into Common Billing Format (CBF)
  3. Send that CBF data into the CloudZero platform through an AnyCost Stream connection

When uploading to AnyCost Stream:
- A billing month (or multiple months) must be specified in ISO 8601 format (e.g., "2024-08")
- Supports batch processing for multiple months with range or comma-separated formats
- An operation type can be specified to control how data is handled:
  - replace_drop: Replace all existing data for the month (default)
  - replace_hourly: Replace data with overlapping hours
  - sum: Append data to existing records
"""

import csv
import getpass
import json
import sys
import argparse
from datetime import datetime
from typing import List, Dict, Any

import requests

from oci_usage import fetch_oci_monthly_usage, test_oci_connection
from oci_transform import process_oci_usage_data
from anycost_example import upload_to_anycost, parse_month_range
import csv

# Check for Python version 3.9 or newer
if sys.version_info < (3, 9):
    sys.exit("This script requires Python 3.9 or newer.")


def fetch_and_process_oci_data(year: int, month: int) -> List[Dict[str, str]]:
    """
    Fetch OCI usage data for a month and transform to CBF format.
    
    Args:
        year: Year (e.g., 2024)
        month: Month (1-12)
        
    Returns:
        CBF-formatted rows
    """
    print(f"Fetching OCI usage data for {year}-{month:02d}...")
    
    try:
        # Fetch raw OCI usage data
        oci_usage_items = fetch_oci_monthly_usage(year, month)
        
        if not oci_usage_items:
            print(f"No usage data found for {year}-{month:02d}")
            return []
        
        # Transform to CBF format
        cbf_rows = process_oci_usage_data(oci_usage_items)
        
        return cbf_rows
        
    except Exception as e:
        print(f"Error fetching OCI data for {year}-{month:02d}: {e}")
        raise


def process_multiple_months(months: List[str]) -> List[Dict[str, str]]:
    """
    Process multiple months of OCI data.
    
    Args:
        months: List of month strings in YYYY-MM format
        
    Returns:
        Combined CBF rows from all months
    """
    all_cbf_rows = []
    
    for month_str in months:
        year, month = map(int, month_str.split('-'))
        
        try:
            cbf_rows = fetch_and_process_oci_data(year, month)
            all_cbf_rows.extend(cbf_rows)
            print(f"✓ Processed {len(cbf_rows)} records for {month_str}")
        except Exception as e:
            print(f"✗ Failed to process {month_str}: {e}")
            continue
    
    return all_cbf_rows


def main():
    """Main function for OCI AnyCost Stream Adaptor."""
    parser = argparse.ArgumentParser(
        description="Oracle Cloud Infrastructure AnyCost Stream Adaptor",
        epilog="""
Examples:
  # Process single month
  python oci_anycost_adaptor.py --month 2024-08
  
  # Process multiple months
  python oci_anycost_adaptor.py --months 2024-06,2024-07,2024-08
  
  # Process month range
  python oci_anycost_adaptor.py --months 2024-06:2024-08
  
  # Test OCI connection only
  python oci_anycost_adaptor.py --test-connection
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Add argument groups for better organization
    data_group = parser.add_mutually_exclusive_group(required=True)
    data_group.add_argument(
        "--month", 
        help="Single month to process (YYYY-MM format, e.g., 2024-08)"
    )
    data_group.add_argument(
        "--months",
        help="Multiple months: comma-separated (2024-06,2024-07) or range (2024-06:2024-08)"
    )
    data_group.add_argument(
        "--test-connection",
        action="store_true", 
        help="Test OCI connection and exit"
    )
    
    parser.add_argument(
        "--output", 
        default="oci_cbf_output.csv",
        help="Path to output CBF CSV file (default: oci_cbf_output.csv)"
    )
    parser.add_argument(
        "--no-upload",
        action="store_true",
        help="Skip AnyCost Stream upload prompt"
    )
    
    args = parser.parse_args()
    
    # Test connection if requested
    if args.test_connection:
        print("Testing OCI connection...")
        if test_oci_connection():
            print("✓ OCI connection successful")
            sys.exit(0)
        else:
            print("✗ OCI connection failed")
            sys.exit(1)
    
    # Test OCI connection before processing
    print("Verifying OCI connection...")
    if not test_oci_connection():
        print("✗ Cannot connect to OCI. Please check your configuration.")
        print("Make sure you have:")
        print("  1. Created .env file with OCI credentials")
        print("  2. Installed dependencies: pip install -r requirements.txt")
        print("  3. Valid OCI API key and permissions")
        sys.exit(1)
    
    # Determine months to process
    if args.month:
        months = [args.month]
    else:
        months = parse_month_range(args.months)
    
    print(f"\nProcessing {len(months)} month(s): {', '.join(months)}")
    
    # Process the data
    try:
        cbf_rows = process_multiple_months(months)
        
        if not cbf_rows:
            print("No data to process. Exiting.")
            sys.exit(0)
        
        # Write CBF data to file with dynamic fieldnames
        print(f"\n✓ Writing {len(cbf_rows)} CBF records to: {args.output}")
        
        # Get all unique field names from all rows
        all_fieldnames = set()
        for row in cbf_rows:
            all_fieldnames.update(row.keys())
        fieldnames = sorted(list(all_fieldnames))
        
        # Write CSV with dynamic fieldnames
        with open(args.output, "w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(cbf_rows)
        
        print(f"✓ CBF data written to: {args.output}")
        print(f"  Total records: {len(cbf_rows)}")
        print(f"  Fields: {len(fieldnames)}")
        
        # Upload to AnyCost Stream if requested
        if not args.no_upload:
            should_upload = input("\nWould you like to upload the CBF data to an AnyCost Stream connection? (y/n): ")
            if should_upload.lower() == "y":
                upload_to_anycost(cbf_rows)
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()