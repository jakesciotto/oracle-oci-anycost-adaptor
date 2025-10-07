#!/usr/bin/env python3
"""
OCI Usage API integration for fetching cost and usage data.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import time
import oci
from oci.usage_api import models as usage_models
from oci_config import get_usage_client, get_identity_client


def get_tenancy_info() -> Dict[str, str]:
    """
    Get tenancy information including name and ID.
    
    Returns:
        Dictionary with tenancy details
    """
    from oci_config import OCIConfig
    
    config = OCIConfig()
    tenancy_id = config.get_config()['tenancy']
    identity_client = get_identity_client()
    
    try:
        tenancy = identity_client.get_tenancy(tenancy_id).data
        return {
            'id': tenancy_id,
            'name': tenancy.name,
            'description': tenancy.description
        }
    except Exception as e:
        print(f"Warning: Could not fetch tenancy details: {e}")
        return {
            'id': tenancy_id,
            'name': 'Unknown',
            'description': 'Could not retrieve tenancy information'
        }


def fetch_oci_usage_data(start_date: datetime, end_date: datetime, 
                        granularity: str = 'DAILY') -> List[Dict[str, Any]]:
    """
    Fetch usage data from OCI Usage API.
    
    Args:
        start_date: Start date for usage data
        end_date: End date for usage data  
        granularity: Data granularity ('DAILY' or 'MONTHLY')
        
    Returns:
        List of usage data items
    """
    usage_client = get_usage_client()
    tenancy_info = get_tenancy_info()
    
    # Create request for summarized usage data
    request = usage_models.RequestSummarizedUsagesDetails(
        tenant_id=tenancy_info['id'],
        time_usage_started=start_date,
        time_usage_ended=end_date,
        granularity=granularity,
        is_aggregate_by_time=False,
        compartment_depth=2,  # Required when using compartmentName in groupBy
        group_by=[
            'service',
            'resourceId', 
            'compartmentName',
            'region'
        ]
    )
    
    try:
        # DEBUG: Log API request parameters
        print(f"📝 OCI API Request Parameters:")
        print(f"   Date range: {start_date} to {end_date}")
        print(f"   Granularity: {granularity}")
        print(f"   Group by: {request.group_by}")
        print(f"   Compartment depth: {request.compartment_depth}")
        
        all_items = []
        page_num = 1
        page_token = None
        
        while True:
            print(f"🔄 Fetching page {page_num}...")
            
            # Add retry logic for rate limits
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Make API call with pagination
                    response = usage_client.request_summarized_usages(
                        request, 
                        page=page_token,
                        limit=1000  # Max items per page
                    )
                    break  # Success, exit retry loop
                    
                except oci.exceptions.ServiceError as e:
                    if e.status == 429:  # Rate limit exceeded
                        if attempt < max_retries - 1:
                            wait_time = (2 ** attempt) * 5  # Exponential backoff: 5s, 10s, 20s
                            print(f"⏸️  Rate limit hit (429). Waiting {wait_time}s before retry {attempt + 2}/{max_retries}...")
                            time.sleep(wait_time)
                            continue
                        else:
                            print(f"❌ Rate limit exceeded after {max_retries} retries")
                            raise
                    elif e.status == 500:  # Server error
                        if attempt < max_retries - 1:
                            wait_time = 5
                            print(f"⏸️  Server error (500). Waiting {wait_time}s before retry {attempt + 2}/{max_retries}...")
                            time.sleep(wait_time)
                            continue
                        else:
                            raise
                    else:
                        # Other service errors - don't retry
                        raise
            
            page_items = response.data.items
            all_items.extend(page_items)
            
            print(f"   Page {page_num}: {len(page_items)} records")
            
            # Add small delay between pages to be respectful to API
            if page_num > 1:
                time.sleep(1)
            
            # Check if there are more pages
            if hasattr(response, 'opc_next_page') and response.opc_next_page:
                page_token = response.opc_next_page
                page_num += 1
            else:
                break
        
        print(f"✅ Total records retrieved: {len(all_items)}")
        
        # DEBUG: Calculate total cost for verification
        total_cost = 0
        for item in all_items:
            if hasattr(item, 'computed_amount') and item.computed_amount:
                total_cost += float(item.computed_amount)
        
        print(f"💰 Total cost: ${total_cost:,.2f}")
        
        return all_items
        
    except oci.exceptions.ServiceError as e:
        print(f"OCI API Error: {e.code} - {e.message}")
        raise
    except Exception as e:
        print(f"Unexpected error fetching usage data: {e}")
        raise


def fetch_oci_monthly_usage(year: int, month: int) -> List[Dict[str, Any]]:
    """
    Fetch usage data for a specific month.
    
    Args:
        year: Year (e.g., 2024)
        month: Month (1-12)
        
    Returns:
        List of usage data items for the month
    """
    # OCI requires dates with hour=0, minute=0, second=0, microsecond=0
    start_date = datetime(year, month, 1, 0, 0, 0, 0)
    
    # Calculate end of month with proper precision
    if month == 12:
        end_date = datetime(year + 1, 1, 1, 0, 0, 0, 0) - timedelta(days=1)
    else:
        end_date = datetime(year, month + 1, 1, 0, 0, 0, 0) - timedelta(days=1)
    
    return fetch_oci_usage_data(start_date, end_date, granularity='DAILY')


def test_oci_connection() -> bool:
    """
    Test OCI connection and credentials.
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        tenancy_info = get_tenancy_info()
        print(f"✓ Connected to OCI tenancy: {tenancy_info['name']} ({tenancy_info['id']})")
        
        # Try a simple usage API call for the last 7 days  
        # OCI requires date precision with hours, minutes, seconds as 0
        end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = end_date - timedelta(days=7)
        
        usage_data = fetch_oci_usage_data(start_date, end_date)
        print(f"✓ Retrieved {len(usage_data)} usage records from the last 7 days")
        
        return True
    except Exception as e:
        print(f"✗ OCI connection failed: {e}")
        return False


if __name__ == "__main__":
    print("Testing OCI Usage API connection...")
    test_oci_connection()