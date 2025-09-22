#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2016-2024, CloudZero, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""
Mock OCI data structures for testing Oracle OCI AnyCost Stream Adaptor without API keys.
This module provides realistic mock responses based on Oracle OCI Usage API documentation.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
import decimal


class MockOCIUsageItem:
    """Mock OCI Usage API response item"""
    
    def __init__(self, **kwargs):
        # Core fields based on OCI Usage API documentation
        self.service = kwargs.get('service', 'Compute')
        self.resource_id = kwargs.get('resource_id', 'ocid1.instance.oc1.us-ashburn-1.example123')
        self.compartment_name = kwargs.get('compartment_name', 'production')
        self.compartment_id = kwargs.get('compartment_id', 'ocid1.compartment.oc1..example456')
        self.region = kwargs.get('region', 'us-ashburn-1')
        self.availability_domain = kwargs.get('availability_domain', 'US-ASHBURN-AD-1')
        
        # Time fields
        self.time_usage_started = kwargs.get('time_usage_started', datetime.now() - timedelta(days=1))
        self.time_usage_ended = kwargs.get('time_usage_ended', datetime.now())
        
        # Cost fields
        self.computed_amount = kwargs.get('computed_amount', decimal.Decimal('15.50'))
        self.computed_quantity = kwargs.get('computed_quantity', decimal.Decimal('1.0'))
        self.currency = kwargs.get('currency', 'USD')
        
        # Resource details
        self.resource_name = kwargs.get('resource_name', 'vm-instance-prod-01')
        self.shape = kwargs.get('shape', 'VM.Standard2.1')
        self.unit = kwargs.get('unit', 'HOUR')
        
        # Tags (freeform and defined)
        self.freeform_tags = kwargs.get('freeform_tags', {'Environment': 'production', 'Team': 'engineering'})
        self.defined_tags = kwargs.get('defined_tags', {'Oracle-Tags': {'CreatedBy': 'user@company.com'}})


def create_mock_compute_usage() -> MockOCIUsageItem:
    """Create mock compute instance usage"""
    return MockOCIUsageItem(
        service='Compute',
        resource_id='ocid1.instance.oc1.us-ashburn-1.abcd1234567890',
        compartment_name='production-compute',
        region='us-ashburn-1',
        computed_amount=decimal.Decimal('24.80'),
        computed_quantity=decimal.Decimal('1.0'),
        shape='VM.Standard2.2',
        unit='HOUR',
        freeform_tags={'Environment': 'prod', 'Application': 'webapp'},
        resource_name='web-server-01'
    )


def get_mock_monthly_usage_data(month_year: str = "2024-01") -> List[MockOCIUsageItem]:
    """Generate comprehensive mock usage data for a month"""
    base_date = datetime.strptime(f"{month_year}-01", "%Y-%m-%d")
    
    usage_items = []
    
    # Daily usage entries for various services
    for day in range(1, 32):  # Full month
        try:
            current_date = base_date.replace(day=day)
        except ValueError:
            break  # Handle months with fewer than 31 days
            
        # Compute usage (daily)
        compute_item = create_mock_compute_usage()
        compute_item.time_usage_started = current_date
        compute_item.time_usage_ended = current_date + timedelta(hours=23, minutes=59)
        compute_item.computed_amount = decimal.Decimal('24.80') + decimal.Decimal(str(day * 0.1))  # Slight daily variation
        usage_items.append(compute_item)
    
    return usage_items