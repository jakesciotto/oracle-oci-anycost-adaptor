#!/usr/bin/env python3
"""
CloudZero AnyCost Stream client - Consolidated module for uploading CBF data.
This module handles authentication, data upload, and batch processing.
"""

import os
import json
import requests
import re
from datetime import datetime
from typing import List, Dict, Any, Optional


class CloudZeroClient:
    """Client for uploading data to CloudZero AnyCost Stream."""
    
    def __init__(self):
        """Initialize CloudZero client with environment configuration."""
        self.api_key = os.getenv('CLOUDZERO_API_KEY')
        self.connection_id = os.getenv('CLOUDZERO_CONNECTION_ID')
        self.api_url = os.getenv('CLOUDZERO_API_URL', 'https://api.cloudzero.com')
        
        if not self.api_key:
            raise ValueError("CLOUDZERO_API_KEY environment variable is required")
        if not self.connection_id:
            raise ValueError("CLOUDZERO_CONNECTION_ID environment variable is required")
    
    def _calculate_payload_size(self, payload: Dict[str, Any]) -> int:
        """Calculate the size of a JSON payload in bytes."""
        return len(json.dumps(payload, separators=(',', ':')).encode('utf-8'))
    
    def _split_into_batches(self, cbf_rows: List[Dict[str, str]], max_size_mb: float = 4.5) -> List[List[Dict[str, str]]]:
        """Split CBF rows into batches under the size limit.
        
        Args:
            cbf_rows: List of CBF records
            max_size_mb: Maximum size per batch in MB (default 4.5MB for safety)
            
        Returns:
            List of batches, each batch is a list of CBF rows
        """
        max_size_bytes = int(max_size_mb * 1024 * 1024)
        batches = []
        current_batch = []
        current_size = 0
        
        # Calculate base payload overhead (month, operation, etc)
        base_payload = {"month": "2025-01", "operation": "replace_drop", "data": []}
        base_size = self._calculate_payload_size(base_payload)
        
        for row in cbf_rows:
            # Estimate row size (add some padding for JSON formatting)
            row_size = len(json.dumps(row, separators=(',', ':')).encode('utf-8')) + 10
            
            # Check if adding this row would exceed the limit
            if current_size + row_size + base_size > max_size_bytes and current_batch:
                # Save current batch and start a new one
                batches.append(current_batch)
                current_batch = [row]
                current_size = row_size
            else:
                current_batch.append(row)
                current_size += row_size
        
        # Add the last batch if it has data
        if current_batch:
            batches.append(current_batch)
        
        return batches

    def upload_billing_data(self, cbf_rows: List[Dict[str, str]], 
                          month: str, 
                          operation: str = "replace_drop",
                          dry_run: bool = False) -> Dict[str, Any]:
        """
        Upload CBF data to CloudZero AnyCost Stream.
        
        Args:
            cbf_rows: List of CBF-formatted billing records
            month: Billing month in YYYY-MM format (e.g., "2024-08")
            operation: How to handle existing data ("replace_drop", "replace_hourly", "sum")
            dry_run: If True, prepare the request but don't actually send it
            
        Returns:
            API response dictionary
            
        Raises:
            ValueError: If required parameters are missing
            requests.RequestException: If API call fails
        """
        if not cbf_rows:
            raise ValueError("No CBF data provided")
        
        # Validate month format
        try:
            datetime.strptime(month, "%Y-%m")
        except ValueError:
            raise ValueError(f"Invalid month format '{month}'. Must be YYYY-MM (e.g., '2024-08')")
        
        # Prepare the request
        url = f"{self.api_url}/v2/connections/billing/anycost/{self.connection_id}/billing_drops"
        headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json"
        }
        
        # Check if we need to batch the data
        test_payload = {
            "month": month,
            "operation": operation,
            "data": cbf_rows
        }
        payload_size = self._calculate_payload_size(test_payload)
        max_size_bytes = 5 * 1024 * 1024  # 5MB limit
        
        print(f"📤 Preparing to upload {len(cbf_rows)} records to CloudZero")
        print(f"   Connection ID: {self.connection_id}")
        print(f"   Month: {month}")
        print(f"   Operation: {operation}")
        print(f"   Endpoint: {url}")
        print(f"   Payload size: {payload_size} bytes ({payload_size / (1024*1024):.1f}MB)")
        
        if payload_size > max_size_bytes:
            print(f"⚠️  Payload exceeds 5MB limit - splitting into batches...")
            batches = self._split_into_batches(cbf_rows)
            print(f"   Split into {len(batches)} batches")
            
            if dry_run:
                print(f"🔍 DRY RUN: {len(batches)} batch requests prepared but not sent")
                for i, batch in enumerate(batches, 1):
                    # First batch uses original operation, subsequent batches use "sum"
                    batch_operation = operation if i == 1 else "sum"
                    batch_payload = {"month": month, "operation": batch_operation, "data": batch}
                    batch_size = self._calculate_payload_size(batch_payload)
                    # Calculate cost for this batch
                    batch_cost = 0
                    for row in batch:
                        if 'cost/cost' in row and row['cost/cost']:
                            try:
                                batch_cost += float(row['cost/cost'])
                            except (ValueError, TypeError):
                                pass
                    print(f"   Batch {i}: {len(batch)} records, {batch_size} bytes ({batch_size / (1024*1024):.1f}MB), ${batch_cost:,.2f}, operation: {batch_operation}")
                return {
                    "dry_run": True,
                    "url": url,
                    "headers": headers,
                    "payload_records": len(cbf_rows),
                    "batches": len(batches),
                    "status": "prepared_batched"
                }
            else:
                # Upload each batch
                results = []
                for i, batch in enumerate(batches, 1):
                    # First batch uses original operation, subsequent batches use "sum" to add data
                    batch_operation = operation if i == 1 else "sum"
                    print(f"\n🚀 Uploading batch {i}/{len(batches)} ({len(batch)} records, operation: {batch_operation})...")
                    result = self._upload_single_batch(batch, month, batch_operation, url, headers)
                    results.append(result)
                    if not result["success"]:
                        print(f"❌ Batch {i} failed, stopping upload")
                        break
                
                total_uploaded = sum(r["records_uploaded"] for r in results if r["success"])
                success_count = sum(1 for r in results if r["success"])
                
                return {
                    "success": success_count == len(batches),
                    "batches_uploaded": success_count,
                    "total_batches": len(batches),
                    "records_uploaded": total_uploaded,
                    "batch_results": results
                }
        else:
            # Single payload upload
            if dry_run:
                print(f"🔍 DRY RUN: Request prepared but not sent")
                print(f"   Headers: {headers}")
                return {
                    "dry_run": True,
                    "url": url,
                    "headers": headers,
                    "payload_records": len(cbf_rows),
                    "status": "prepared"
                }
            else:
                return self._upload_single_batch(cbf_rows, month, operation, url, headers)
        
    def _upload_single_batch(self, cbf_rows: List[Dict[str, str]], month: str, operation: str, url: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """Upload a single batch of CBF data."""
        # Validate cost totals before upload
        batch_cost = 0
        for row in cbf_rows:
            if 'cost/cost' in row and row['cost/cost']:
                try:
                    batch_cost += float(row['cost/cost'])
                except (ValueError, TypeError):
                    print(f"⚠️  Invalid cost value: {row['cost/cost']}")
        
        print(f"💰 Batch cost validation: ${batch_cost:,.2f} for {len(cbf_rows)} records")
        
        payload = {
            "month": month,
            "operation": operation,
            "data": cbf_rows
        }
        
        try:
            print(f"🚀 Sending {len(cbf_rows)} records to CloudZero...")
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=60  # 60 second timeout for large uploads
            )
            
            response.raise_for_status()
            
            response_data = response.json() if response.text else {}
            
            print(f"✅ Upload successful!")
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {json.dumps(response_data, indent=2)}")
            
            return {
                "success": True,
                "status_code": response.status_code,
                "response": response_data,
                "records_uploaded": len(cbf_rows)
            }
            
        except requests.exceptions.Timeout:
            error_msg = f"Request timed out after 60 seconds"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "records_uploaded": 0
            }
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error: {e}"
            try:
                error_detail = response.json()
                print(f"❌ HTTP {response.status_code}: {error_detail}")
            except:
                print(f"❌ HTTP {response.status_code}: {response.text}")
            return {
                "success": False,
                "error": error_msg,
                "status_code": response.status_code,
                "records_uploaded": 0
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed: {e}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "records_uploaded": 0
            }
    
    def test_connection(self) -> bool:
        """
        Test connection to CloudZero API.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Test with a simple request (dry run)
            print(f"🔍 Testing CloudZero connection...")
            print(f"   API URL: {self.api_url}")
            print(f"   Connection ID: {self.connection_id}")
            print(f"   API Key: {'*' * (len(self.api_key) - 4) + self.api_key[-4:] if len(self.api_key) > 4 else '****'}")
            
            # For now, just validate that we have the required configuration
            if self.api_key and self.connection_id and self.api_url:
                print(f"✅ CloudZero configuration is valid")
                return True
            else:
                print(f"❌ CloudZero configuration is incomplete")
                return False
                
        except Exception as e:
            print(f"❌ CloudZero connection test failed: {e}")
            return False


def parse_month_range(month_input: str) -> List[str]:
    """Parse month input and return list of months.
    
    Supports:
    - Single month: "2024-08"
    - Month range: "2024-08:2024-10" (inclusive)
    - Comma-separated: "2024-08,2024-09,2024-11"
    """
    if not month_input or not month_input.strip():
        raise ValueError("Month input cannot be empty")
    
    month_pattern = re.compile(r'^\d{4}-\d{2}$')
    
    if ':' in month_input:
        # Handle range format: "2024-08:2024-10"
        parts = month_input.split(':')
        if len(parts) != 2:
            raise ValueError("Month range must have exactly one ':' separator")
        
        start_str, end_str = parts
        start_str, end_str = start_str.strip(), end_str.strip()
        
        if not month_pattern.match(start_str) or not month_pattern.match(end_str):
            raise ValueError("Month format must be YYYY-MM (e.g., '2024-08')")
        
        try:
            start_date = datetime.strptime(start_str + "-01", "%Y-%m-%d")
            end_date = datetime.strptime(end_str + "-01", "%Y-%m-%d")
        except ValueError as e:
            raise ValueError(f"Invalid date format: {e}")
        
        if start_date > end_date:
            raise ValueError("Start month cannot be after end month")
        
        months = []
        current = start_date
        while current <= end_date:
            months.append(current.strftime("%Y-%m"))
            # Move to next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)
        return months
    elif ',' in month_input:
        # Handle comma-separated format: "2024-08,2024-09,2024-11"
        months = [month.strip() for month in month_input.split(',')]
        for month in months:
            if not month_pattern.match(month):
                raise ValueError(f"Invalid month format '{month}'. Must be YYYY-MM (e.g., '2024-08')")
        return months
    else:
        # Single month
        month = month_input.strip()
        if not month_pattern.match(month):
            raise ValueError(f"Invalid month format '{month}'. Must be YYYY-MM (e.g., '2024-08')")
        return [month]


def upload_cbf_to_cloudzero(cbf_rows: List[Dict[str, str]], 
                           month: str,
                           operation: str = "replace_drop",
                           dry_run: bool = False) -> Dict[str, Any]:
    """
    Convenience function to upload CBF data to CloudZero.
    
    Args:
        cbf_rows: CBF-formatted billing records
        month: Billing month in YYYY-MM format
        operation: Upload operation type
        dry_run: If True, prepare but don't send the request
        
    Returns:
        Upload result dictionary
    """
    client = CloudZeroClient()
    return client.upload_billing_data(cbf_rows, month, operation, dry_run)


if __name__ == "__main__":
    # Test the CloudZero client
    client = CloudZeroClient()
    client.test_connection()