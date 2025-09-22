#!/usr/bin/env python3
"""
Test the OCI adaptor with mock data to verify the transformation pipeline works.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from oci_mock_data import get_mock_monthly_usage_data
from oci_transform import process_oci_usage_data
import csv

def test_mock_data_transformation():
    """Test the full pipeline with mock OCI data."""
    print("Testing OCI AnyCost adaptor with mock data...")
    
    # Generate mock data for January 2024
    print("1. Generating mock OCI usage data...")
    mock_usage_items = get_mock_monthly_usage_data("2024-01")
    print(f"   Generated {len(mock_usage_items)} mock usage records")
    
    # Transform to CBF format
    print("2. Transforming to Common Bill Format (CBF)...")
    cbf_rows = process_oci_usage_data(mock_usage_items)
    
    # Write to CSV file
    output_file = "tests/test_oci_cbf_output.csv"
    print(f"3. Writing CBF data to {output_file}...")
    
    # Get all unique field names from all rows
    all_fieldnames = set()
    for row in cbf_rows:
        all_fieldnames.update(row.keys())
    fieldnames = sorted(list(all_fieldnames))
    
    # Write CSV with dynamic fieldnames
    with open(output_file, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cbf_rows)
    
    # Show sample of the output
    print(f"\n✓ Test completed successfully!")
    print(f"   - Input: {len(mock_usage_items)} OCI usage items")
    print(f"   - Output: {len(cbf_rows)} CBF records")
    print(f"   - File: {output_file}")
    
    if cbf_rows:
        print(f"\nSample CBF record:")
        sample = cbf_rows[0]
        for key, value in sample.items():
            print(f"   {key}: {value}")
    
    return True

if __name__ == "__main__":
    test_mock_data_transformation()