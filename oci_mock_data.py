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


class MockOCIUsageResponse:
    """Mock OCI Usage API response container"""
    
    def __init__(self, items: List[MockOCIUsageItem]):
        self.items = items


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


def create_mock_storage_usage() -> MockOCIUsageItem:
    """Create mock block storage usage"""
    return MockOCIUsageItem(
        service='Block Storage',
        resource_id='ocid1.volume.oc1.us-ashburn-1.efgh5678901234',
        compartment_name='production-storage',
        region='us-ashburn-1',
        computed_amount=decimal.Decimal('8.64'),
        computed_quantity=decimal.Decimal('100.0'),
        unit='GB-MONTH',
        freeform_tags={'Environment': 'prod', 'BackupPolicy': 'daily'},
        resource_name='web-server-01-boot-volume'
    )


def create_mock_database_usage() -> MockOCIUsageItem:
    """Create mock database usage"""
    return MockOCIUsageItem(
        service='Database',
        resource_id='ocid1.database.oc1.us-ashburn-1.ijkl9012345678',
        compartment_name='production-database',
        region='us-ashburn-1',
        computed_amount=decimal.Decimal('156.00'),
        computed_quantity=decimal.Decimal('2.0'),
        shape='VM.Standard2.4',
        unit='OCPU-HOUR',
        freeform_tags={'Environment': 'prod', 'DatabaseType': 'primary'},
        resource_name='prod-db-cluster'
    )


def create_mock_network_usage() -> MockOCIUsageItem:
    """Create mock networking/data transfer usage"""
    return MockOCIUsageItem(
        service='Networking',
        resource_id='ocid1.vcn.oc1.us-ashburn-1.mnop3456789012',
        compartment_name='production-network',
        region='us-ashburn-1',
        computed_amount=decimal.Decimal('12.45'),
        computed_quantity=decimal.Decimal('124.5'),
        unit='GB',
        freeform_tags={'Environment': 'prod', 'TrafficType': 'outbound'},
        resource_name='prod-vcn-outbound-data'
    )


def create_mock_support_usage() -> MockOCIUsageItem:
    """Create mock Oracle support cost"""
    return MockOCIUsageItem(
        service='Support',
        resource_id=None,  # Support costs might not have specific resource IDs
        compartment_name='root-compartment',
        region='us-ashburn-1',
        computed_amount=decimal.Decimal('500.00'),
        computed_quantity=decimal.Decimal('1.0'),
        unit='MONTH',
        freeform_tags={'SupportLevel': 'premium'},
        resource_name='Oracle Premier Support'
    )


def create_mock_credit_usage() -> MockOCIUsageItem:
    """Create mock promotional credit usage"""
    return MockOCIUsageItem(
        service='Credit',
        resource_id=None,
        compartment_name='root-compartment', 
        region='us-ashburn-1',
        computed_amount=decimal.Decimal('-100.00'),  # Credits are negative
        computed_quantity=decimal.Decimal('1.0'),
        unit='USD',
        freeform_tags={'CreditType': 'promotional'},
        resource_name='Oracle Cloud Free Tier Credit'
    )


def create_mock_reserved_capacity() -> MockOCIUsageItem:
    """Create mock reserved capacity purchase"""
    return MockOCIUsageItem(
        service='Reserved Capacity',
        resource_id='ocid1.capacity.oc1.us-ashburn-1.qrst6789012345',
        compartment_name='production-reserved',
        region='us-ashburn-1',
        computed_amount=decimal.Decimal('1200.00'),
        computed_quantity=decimal.Decimal('10.0'),
        shape='VM.Standard2.2',
        unit='MONTH',
        freeform_tags={'ReservationType': 'one-year', 'Commitment': 'standard'},
        resource_name='compute-reserved-capacity-1yr'
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
        
        # Storage usage (daily)
        storage_item = create_mock_storage_usage()
        storage_item.time_usage_started = current_date
        storage_item.time_usage_ended = current_date + timedelta(hours=23, minutes=59)
        usage_items.append(storage_item)
        
        # Database usage (daily)
        db_item = create_mock_database_usage()
        db_item.time_usage_started = current_date
        db_item.time_usage_ended = current_date + timedelta(hours=23, minutes=59)
        usage_items.append(db_item)
        
        # Network usage (varies by day)
        if day % 3 == 0:  # Every third day has significant network usage
            network_item = create_mock_network_usage()
            network_item.time_usage_started = current_date
            network_item.time_usage_ended = current_date + timedelta(hours=23, minutes=59)
            network_item.computed_amount = decimal.Decimal('12.45') * decimal.Decimal(str(day / 10))
            usage_items.append(network_item)
    
    # Monthly charges (once per month)
    support_item = create_mock_support_usage()
    support_item.time_usage_started = base_date
    support_item.time_usage_ended = base_date.replace(day=28)  # End of month
    usage_items.append(support_item)
    
    # Credits (applied monthly)
    credit_item = create_mock_credit_usage()
    credit_item.time_usage_started = base_date
    credit_item.time_usage_ended = base_date.replace(day=28)
    usage_items.append(credit_item)
    
    # Reserved capacity (if applicable)
    reserved_item = create_mock_reserved_capacity()
    reserved_item.time_usage_started = base_date
    reserved_item.time_usage_ended = base_date.replace(day=28)
    usage_items.append(reserved_item)
    
    return usage_items


def get_mock_usage_response(tenant_id: str, start_date: datetime, end_date: datetime) -> MockOCIUsageResponse:
    """Generate mock OCI Usage API response for date range"""
    # For simplicity, return one month's worth of data
    month_year = start_date.strftime("%Y-%m")
    usage_items = get_mock_monthly_usage_data(month_year)
    
    # Filter items to match the requested date range
    filtered_items = []
    for item in usage_items:
        if start_date <= item.time_usage_started <= end_date:
            filtered_items.append(item)
    
    return MockOCIUsageResponse(filtered_items)


# Sample OCI configuration for testing
MOCK_OCI_CONFIG = {
    'user': 'ocid1.user.oc1..mockuser123456789',
    'key_file': '~/.oci/mock_oci_api_key.pem',
    'fingerprint': 'ab:cd:ef:12:34:56:78:90:ab:cd:ef:12:34:56:78:90',
    'tenancy': 'ocid1.tenancy.oc1..mocktenancy123456789',
    'region': 'us-ashburn-1'
}


# Mock error scenarios for testing
class MockOCIServiceError(Exception):
    """Mock OCI service error"""
    
    def __init__(self, status_code: int, message: str):
        self.status = status_code
        self.message = message
        super().__init__(f"HTTP {status_code}: {message}")


def simulate_rate_limit_error():
    """Simulate OCI API rate limiting"""
    raise MockOCIServiceError(429, "Too Many Requests - Rate limit exceeded")


def simulate_auth_error():
    """Simulate OCI authentication error"""
    raise MockOCIServiceError(401, "Unauthorized - Invalid credentials")


def simulate_permission_error():
    """Simulate OCI permission error"""
    raise MockOCIServiceError(403, "Forbidden - Insufficient permissions to access usage data")