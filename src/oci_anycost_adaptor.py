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
import os
import sys
import argparse
from datetime import datetime
from typing import List, Dict, Any

import requests

from oci_usage import fetch_oci_monthly_usage, test_oci_connection
from oci_transform import process_oci_usage_data
from cloudzero import parse_month_range, upload_cbf_to_cloudzero
import csv

# Check for Python version 3.9 or newer
if sys.version_info < (3, 9):
    sys.exit("This script requires Python 3.9 or newer.")


def fetch_and_process_oci_data(year: int, month: int, save_raw_data: bool = True) -> List[Dict[str, str]]:
    """
    Fetch OCI usage data for a month and transform to CBF format.
    
    Args:
        year: Year (e.g., 2024)
        month: Month (1-12)
        save_raw_data: Whether to save raw OCI data to input/ folder
        
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
        
        # Save raw OCI data to input folder if requested
        if save_raw_data:
            save_raw_oci_data(oci_usage_items, year, month)
        
        # Transform to CBF format
        cbf_rows = process_oci_usage_data(oci_usage_items)
        
        return cbf_rows
        
    except Exception as e:
        print(f"Error fetching OCI data for {year}-{month:02d}: {e}")
        raise


def save_raw_oci_data(oci_usage_items: List[Any], year: int, month: int):
    """
    Save raw OCI usage data to input folder as CSV.
    
    Args:
        oci_usage_items: Raw OCI usage API response items
        year: Year (e.g., 2024)
        month: Month (1-12)
    """
    import os
    
    # Create input directory if it doesn't exist
    input_dir = "input"
    if not os.path.exists(input_dir):
        os.makedirs(input_dir)
    
    # Generate filename with timestamp
    filename = f"oci_raw_data_{year}_{month:02d}.csv"
    filepath = os.path.join(input_dir, filename)
    
    print(f"Saving raw OCI data to {filepath}...")
    
    # Extract fields from first item to determine CSV structure
    if not oci_usage_items:
        return
        
    # Get all possible fields from the first few items
    all_fields = set()
    for item in oci_usage_items[:10]:  # Sample first 10 items for field discovery
        for attr in dir(item):
            if not attr.startswith('_') and not callable(getattr(item, attr, None)):
                all_fields.add(attr)
    
    fieldnames = sorted(list(all_fields))
    
    # Write CSV with raw OCI data
    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for item in oci_usage_items:
            row = {}
            for field in fieldnames:
                value = getattr(item, field, None)
                # Extract actual values instead of converting objects to strings
                if value is not None:
                    if hasattr(value, 'strftime'):  # datetime objects
                        row[field] = value.strftime('%Y-%m-%dT%H:%M:%SZ')
                    elif isinstance(value, (int, float)):  # numeric values
                        row[field] = str(value)
                    elif isinstance(value, str):  # string values
                        row[field] = value
                    elif isinstance(value, (dict, list)):
                        # Skip complex objects that cause CSV corruption
                        row[field] = ''
                    else:
                        # For other object types, try to get the actual value
                        try:
                            # If it's a simple value, convert to string
                            if hasattr(value, '__str__') and not hasattr(value, '__dict__'):
                                row[field] = str(value)
                            else:
                                # Skip complex objects
                                row[field] = ''
                        except:
                            row[field] = ''
                else:
                    row[field] = ''
            writer.writerow(row)
    
    print(f"✓ Saved {len(oci_usage_items)} raw records to {filepath}")


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
        default="output/oci_cbf_output.csv",
        help="Path to output CBF CSV file (default: output/oci_cbf_output.csv)"
    )
    parser.add_argument(
        "--no-upload",
        action="store_true",
        help="Skip AnyCost Stream upload"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Prepare upload request but don't actually send it (for testing)"
    )
    parser.add_argument(
        "--operation",
        choices=["replace_drop", "replace_hourly", "sum"],
        default="replace_drop",
        help="Upload operation type (default: replace_drop)"
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
        
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
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
        
        # Upload to CloudZero AnyCost Stream if requested
        if not args.no_upload:
            try:
                # Determine the billing month from the processed months
                billing_month = months[0] if len(months) == 1 else months[0]  # Use first month for multi-month
                
                print(f"\n🚀 Uploading to CloudZero AnyCost Stream...")
                upload_result = upload_cbf_to_cloudzero(
                    cbf_rows=cbf_rows,
                    month=billing_month,
                    operation=args.operation,
                    dry_run=args.dry_run
                )
                
                if upload_result.get('dry_run'):
                    print(f"✅ Dry run completed - upload request prepared but not sent")
                    print(f"   To perform actual upload, run without --dry-run flag")
                elif upload_result.get('success'):
                    print(f"✅ Successfully uploaded {upload_result['records_uploaded']} records to CloudZero")
                else:
                    print(f"❌ Upload failed")
                    
            except Exception as e:
                print(f"❌ Upload error: {e}")
                print(f"   Data saved to {args.output} - you can retry upload later")
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()