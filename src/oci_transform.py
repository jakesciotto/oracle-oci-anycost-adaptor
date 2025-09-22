#!/usr/bin/env python3
"""
Transform OCI Usage API data to Common Bill Format (CBF).
"""

from typing import List, Dict, Any
from datetime import datetime
import decimal


def transform_oci_to_cbf(oci_usage_items: List[Any]) -> List[Dict[str, str]]:
    """
    Transform OCI usage data to Common Bill Format (CBF).
    
    Args:
        oci_usage_items: List of OCI usage API response items
        
    Returns:
        List of CBF-formatted rows
    """
    cbf_rows = []
    
    for item in oci_usage_items:
        # Determine line item type based on service and usage
        lineitem_type = determine_lineitem_type(item)
        
        # Handle different cost scenarios - ensure we have a valid number
        cost_value = item.computed_amount if item.computed_amount is not None else 0.0
        cost = str(cost_value)
        
        # For credits and discounts, ensure negative values are handled correctly
        if float(cost) < 0:
            lineitem_type = "Discount"
            discounted_cost = cost  # Keep negative for discounts
        else:
            discounted_cost = cost  # Same as cost for regular usage
        
        # Build resource ID from available identifiers
        resource_id = build_resource_id(item)
        
        # Format usage start time
        usage_start = format_usage_time(item.time_usage_started)
        
        cbf_row = {
            "lineitem/type": lineitem_type,
            "resource/service": item.service or "Unknown",
            "resource/id": resource_id,
            "time/usage_start": usage_start,
            "cost/cost": cost,
            "cost/discounted_cost": discounted_cost,
        }
        
        # Add optional CBF fields if data is available
        if hasattr(item, 'region') and item.region:
            cbf_row["resource/region"] = item.region
            
        if hasattr(item, 'compartment_name') and item.compartment_name:
            cbf_row["resource/compartment"] = item.compartment_name
            
        if hasattr(item, 'shape') and item.shape:
            cbf_row["resource/shape"] = item.shape
            
        if hasattr(item, 'unit') and item.unit:
            cbf_row["billing/unit"] = item.unit
            
        if hasattr(item, 'computed_quantity') and item.computed_quantity:
            cbf_row["usage/amount"] = str(item.computed_quantity)
            
        # Add tags as metadata
        if hasattr(item, 'freeform_tags') and item.freeform_tags:
            for key, value in item.freeform_tags.items():
                cbf_row[f"tag/{key.lower()}"] = str(value)
        
        cbf_rows.append(cbf_row)
    
    return cbf_rows


def determine_lineitem_type(item: Any) -> str:
    """
    Determine the CBF line item type based on OCI usage data.
    
    Args:
        item: OCI usage item
        
    Returns:
        CBF line item type
    """
    service = getattr(item, 'service', '').lower()
    amount = getattr(item, 'computed_amount', 0)
    
    # Handle None amounts
    if amount is None:
        amount = 0
    
    # Handle negative amounts (credits/discounts)
    if float(amount) < 0:
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


def build_resource_id(item: Any) -> str:
    """
    Build a resource ID from available OCI identifiers.
    
    Args:
        item: OCI usage item
        
    Returns:
        Resource identifier string
    """
    # Try to use the actual resource ID if available
    if hasattr(item, 'resource_id') and item.resource_id:
        return item.resource_id
    
    # Fall back to resource name
    if hasattr(item, 'resource_name') and item.resource_name:
        return item.resource_name
    
    # Build from service and other identifiers
    service = getattr(item, 'service', 'unknown')
    region = getattr(item, 'region', 'unknown-region')
    compartment = getattr(item, 'compartment_name', 'unknown-compartment')
    
    return f"{service.lower()}-{region}-{compartment}".replace(' ', '-')


def format_usage_time(usage_time: datetime) -> str:
    """
    Format datetime to ISO 8601 string for CBF.
    
    Args:
        usage_time: DateTime object
        
    Returns:
        ISO 8601 formatted string
    """
    if isinstance(usage_time, datetime):
        return usage_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    elif isinstance(usage_time, str):
        return usage_time
    else:
        return datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def process_oci_usage_data(oci_usage_items: List[Any]) -> List[Dict[str, str]]:
    """
    Main function to process OCI usage data to CBF format.
    
    Args:
        oci_usage_items: Raw OCI usage API response items
        
    Returns:
        CBF-formatted rows ready for CloudZero upload
    """
    print(f"Processing {len(oci_usage_items)} OCI usage items...")
    
    cbf_rows = transform_oci_to_cbf(oci_usage_items)
    
    # Calculate totals for summary  
    total_cost = sum(float(row['cost/cost']) for row in cbf_rows if row['cost/cost'])
    usage_count = len([row for row in cbf_rows if row['lineitem/type'] == 'Usage'])
    discount_count = len([row for row in cbf_rows if row['lineitem/type'] == 'Discount'])
    
    print(f"✓ Transformed to {len(cbf_rows)} CBF rows")
    print(f"  - Usage items: {usage_count}")
    print(f"  - Discounts/Credits: {discount_count}")
    print(f"  - Total cost: ${total_cost:.2f}")
    
    return cbf_rows