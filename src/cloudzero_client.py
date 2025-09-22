#!/usr/bin/env python3
"""
CloudZero AnyCost Stream client for uploading CBF data.
This module handles authentication and data upload to CloudZero.
"""

import os
import json
import requests
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
    
    def upload_billing_data(self, cbf_rows: List[Dict[str, str]], 
                          month: str, 
                          operation: str = "replace_drop",
                          dry_run: bool = True) -> Dict[str, Any]:
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
        
        payload = {
            "month": month,
            "operation": operation,
            "data": cbf_rows
        }
        
        print(f"📤 Preparing to upload {len(cbf_rows)} records to CloudZero")
        print(f"   Connection ID: {self.connection_id}")
        print(f"   Month: {month}")
        print(f"   Operation: {operation}")
        print(f"   Endpoint: {url}")
        
        if dry_run:
            print(f"🔍 DRY RUN: Request prepared but not sent")
            print(f"   Headers: {headers}")
            print(f"   Payload size: {len(json.dumps(payload))} bytes")
            return {
                "dry_run": True,
                "url": url,
                "headers": headers,
                "payload_records": len(cbf_rows),
                "status": "prepared"
            }
        
        try:
            print(f"🚀 Sending request to CloudZero...")
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
            raise requests.RequestException(error_msg)
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error: {e}"
            try:
                error_detail = response.json()
                print(f"❌ HTTP {response.status_code}: {error_detail}")
            except:
                print(f"❌ HTTP {response.status_code}: {response.text}")
            raise
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed: {e}"
            print(f"❌ {error_msg}")
            raise
    
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


def upload_cbf_to_cloudzero(cbf_rows: List[Dict[str, str]], 
                           month: str,
                           operation: str = "replace_drop",
                           dry_run: bool = True) -> Dict[str, Any]:
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