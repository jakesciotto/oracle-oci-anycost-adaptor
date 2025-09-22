#!/usr/bin/env python3
"""
Convert Oracle OCI CSV data to Common Bill Format (CBF) and upload to CloudZero.
This script processes CSV files from the input/ directory.
"""

import csv
import os
import sys
import argparse
from datetime import datetime
from typing import List, Dict, Any
import json

def read_oci_csv(file_path: str) -> List[Dict[str, str]]:
    """
    Read OCI CSV file and return list of records.
    
    Args:
        file_path: Path to the OCI CSV file
        
    Returns:
        List of dictionaries representing OCI usage records
    """
    print(f"Reading OCI CSV file: {file_path}")
    
    with open(file_path, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        records = list(reader)
    
    print(f"✓ Read {len(records)} records from CSV")
    return records


def transform_csv_to_cbf(oci_records: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Transform OCI CSV records to Common Bill Format (CBF).
    
    Args:
        oci_records: List of OCI usage records from CSV
        
    Returns:
        List of CBF-formatted rows
    """
    print(f"Transforming {len(oci_records)} OCI records to CBF format...")
    
    cbf_rows = []
    
    for record in oci_records:
        # Skip empty rows or header metadata rows
        if not record.get('computed_amount') or record.get('computed_amount') == '':
            continue
            
        # Handle computed_amount - ensure it's a valid number
        try:
            cost_value = float(record.get('computed_amount', 0))
        except (ValueError, TypeError):
            cost_value = 0.0
        
        cost = str(cost_value)
        
        # Determine line item type based on service and cost
        lineitem_type = determine_lineitem_type_from_csv(record, cost_value)
        
        # Handle discounted cost (same as cost for most cases)
        if cost_value < 0:
            discounted_cost = cost  # Keep negative for discounts
        else:
            discounted_cost = cost
        
        # Build resource ID from available identifiers
        resource_id = build_resource_id_from_csv(record)
        
        # Format usage start time
        usage_start = format_csv_usage_time(record.get('time_usage_started'))
        
        cbf_row = {
            "lineitem/type": lineitem_type,
            "resource/service": record.get('service', 'Unknown'),
            "resource/id": resource_id,
            "time/usage_start": usage_start,
            "cost/cost": cost,
            "cost/discounted_cost": discounted_cost,
        }
        
        # Add optional CBF fields if data is available
        if record.get('region'):
            cbf_row["resource/region"] = record['region']
            
        if record.get('compartment_name'):
            cbf_row["resource/compartment"] = record['compartment_name']
            
        if record.get('shape'):
            cbf_row["resource/shape"] = record['shape']
            
        if record.get('unit'):
            cbf_row["billing/unit"] = record['unit']
            
        if record.get('computed_quantity'):
            try:
                quantity = str(float(record['computed_quantity']))
                cbf_row["billing/quantity"] = quantity
            except (ValueError, TypeError):
                pass
        
        # Parse and add tags if available
        if record.get('tags'):
            try:
                # The tags field contains JSON-like data
                tags_str = record['tags']
                if tags_str and tags_str != 'null' and not tags_str.startswith('[{'):
                    # Simple key-value tags
                    cbf_row["tag/source"] = "oci-csv"
                elif tags_str.startswith('[{'):
                    # Complex JSON tags - extract meaningful info
                    cbf_row["tag/source"] = "oci-csv"
            except:
                pass  # Skip malformed tags
        
        cbf_rows.append(cbf_row)
    
    # Calculate summary
    total_cost = sum(float(row['cost/cost']) for row in cbf_rows if row['cost/cost'])
    usage_count = len([row for row in cbf_rows if row['lineitem/type'] == 'Usage'])
    discount_count = len([row for row in cbf_rows if row['lineitem/type'] == 'Discount'])
    
    print(f"✓ Transformed to {len(cbf_rows)} CBF rows")
    print(f"  - Usage items: {usage_count}")
    print(f"  - Discounts/Credits: {discount_count}")
    print(f"  - Total cost: ${total_cost:.2f}")
    
    return cbf_rows


def determine_lineitem_type_from_csv(record: Dict[str, str], cost_value: float) -> str:
    """
    Determine the CBF line item type based on CSV record data.
    
    Args:
        record: CSV record dictionary
        cost_value: Computed cost as float
        
    Returns:
        CBF line item type
    """
    service = record.get('service', '').lower()
    
    # Handle negative amounts (credits/discounts)
    if cost_value < 0:
        return "Discount"
    
    # Handle specific service types
    if 'support' in service:
        return "Support"
    elif 'reserved' in service or 'commitment' in service:
        return "CommittedUsePurchase"
    elif 'credit' in service:
        return "Discount"
    else:
        return "Usage"


def build_resource_id_from_csv(record: Dict[str, str]) -> str:
    """
    Build a resource ID from CSV record.
    
    Args:
        record: CSV record dictionary
        
    Returns:
        Resource identifier string
    """
    # Try to use the actual resource ID if available
    if record.get('resource_id') and record['resource_id'].strip():
        return record['resource_id']
    
    # Fall back to resource name
    if record.get('resource_name') and record['resource_name'].strip():
        return record['resource_name']
    
    # Build from service and other identifiers
    service = record.get('service', 'unknown')
    region = record.get('region', 'unknown-region')
    compartment = record.get('compartment_name', 'unknown-compartment')
    
    return f"{service.lower()}-{region}-{compartment}".replace(' ', '-')


def format_csv_usage_time(time_str: str) -> str:
    """
    Format time string from CSV to ISO 8601 for CBF.
    
    Args:
        time_str: Time string from CSV
        
    Returns:
        ISO 8601 formatted string
    """
    if not time_str or time_str.strip() == '':
        return datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    
    try:
        # Try to parse the time string and format consistently
        if 'T' in time_str:
            return time_str  # Already in ISO format
        else:
            # Handle other formats if needed
            return time_str + "T00:00:00.000000Z"
    except:
        return datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def write_cbf_csv(cbf_rows: List[Dict[str, str]], output_file: str):
    """
    Write CBF rows to CSV file with dynamic fieldnames.
    
    Args:
        cbf_rows: CBF-formatted rows
        output_file: Output file path
    """
    print(f"Writing {len(cbf_rows)} CBF records to: {output_file}")
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Get all unique field names from all rows
    all_fieldnames = set()
    for row in cbf_rows:
        all_fieldnames.update(row.keys())
    fieldnames = sorted(list(all_fieldnames))
    
    # Write CSV with dynamic fieldnames
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cbf_rows)
    
    print(f"✓ CBF data written to: {output_file}")
    print(f"  Total records: {len(cbf_rows)}")
    print(f"  Fields: {len(fieldnames)}")


def main():
    """Main function for CSV to CBF conversion and upload."""
    parser = argparse.ArgumentParser(
        description="Convert Oracle OCI CSV data to CBF format and upload to CloudZero",
        epilog="""
Examples:
  # Convert CSV to CBF
  python csv_to_cbf.py --input input/oci_raw_data_2025_09.csv
  
  # Convert and upload to CloudZero
  python csv_to_cbf.py --input input/oci_raw_data_2025_09.csv --upload
  
  # Specify custom output file
  python csv_to_cbf.py --input input/oci_raw_data_2025_09.csv --output output/my_cbf.csv
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--input",
        required=True,
        help="Path to input OCI CSV file (e.g., input/oci_raw_data_2025_09.csv)"
    )
    parser.add_argument(
        "--output",
        default="output/cbf_from_csv.csv",
        help="Path to output CBF CSV file (default: output/cbf_from_csv.csv)"
    )
# Note: CloudZero upload functionality will be added once connection details are configured
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.exists(args.input):
        print(f"✗ Error: Input file not found: {args.input}")
        sys.exit(1)
    
    try:
        # Read OCI CSV data
        oci_records = read_oci_csv(args.input)
        
        if not oci_records:
            print("No data found in CSV file. Exiting.")
            sys.exit(0)
        
        # Transform to CBF format
        cbf_rows = transform_csv_to_cbf(oci_records)
        
        if not cbf_rows:
            print("No valid records to process. Exiting.")
            sys.exit(0)
        
        # Write CBF data to file
        write_cbf_csv(cbf_rows, args.output)
        
        print(f"\n✓ CBF conversion completed successfully!")
        print(f"📁 Input: {args.input} ({len(oci_records)} OCI records)")
        print(f"📄 Output: {args.output} ({len(cbf_rows)} CBF records)")
        print(f"💰 Total cost: ${sum(float(row['cost/cost']) for row in cbf_rows if row['cost/cost']):.2f}")
        print(f"\nNext steps:")
        print(f"1. Review the CBF file: {args.output}")
        print(f"2. Configure CloudZero connection details to enable upload functionality")
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()