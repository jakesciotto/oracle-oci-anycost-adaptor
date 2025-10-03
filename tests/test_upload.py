#!/usr/bin/env python3
"""
Test CloudZero upload with a small sample of data.
"""

import sys
import os

# Add src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

# Set test environment variables
os.environ['CLOUDZERO_API_KEY'] = 'test_api_key_placeholder'
os.environ['CLOUDZERO_CONNECTION_ID'] = 'acedd206-ad47-468a-b731-b326d0695bde'
os.environ['CLOUDZERO_API_URL'] = 'https://api.cloudzero.com'

from cloudzero import upload_cbf_to_cloudzero

# Create a small sample of CBF data (just a day's worth)
sample_cbf_data = [
    {
        "lineitem/type": "Usage",
        "resource/service": "Virtual Cloud Network",
        "resource/id": "ocid1.vnic.oc1.iad.abuwcljslxvdxaqd32l6aahne2jxzgjfcn7a455qgecpx3xxooljzup4nnfq",
        "time/usage_start": "2025-09-22T00:00:00.000000Z",
        "cost/cost": "0.029342138515",
        "cost/discounted_cost": "0.029342138515",
        "resource/region": "us-ashburn-1",
        "resource/compartment": "shutterstock",
        "billing/quantity": "3.452016295864",
        "tag/source": "oci-api"
    },
    {
        "lineitem/type": "Usage", 
        "resource/service": "Compute",
        "resource/id": "ocid1.instance.oc1.us-ashburn-1.example123",
        "time/usage_start": "2025-09-22T00:00:00.000000Z",
        "cost/cost": "24.80",
        "cost/discounted_cost": "24.80",
        "resource/region": "us-ashburn-1",
        "resource/compartment": "shutterstock",
        "billing/quantity": "1.0",
        "billing/unit": "HOUR",
        "resource/shape": "VM.Standard2.2",
        "tag/source": "oci-api"
    }
]

if __name__ == "__main__":
    print("🧪 Testing CloudZero upload with sample data...")
    print(f"   Sample records: {len(sample_cbf_data)}")
    print(f"   Connection ID: {os.environ['CLOUDZERO_CONNECTION_ID']}")
    
    try:
        # Test with dry run (won't actually send the request)
        result = upload_cbf_to_cloudzero(
            cbf_rows=sample_cbf_data,
            month="2025-09", 
            operation="replace_drop",
            dry_run=True  # This is the key - dry run only
        )
        
        print(f"\n✅ Dry run test completed successfully!")
        print(f"   Status: {result.get('status')}")
        print(f"   Records prepared: {result.get('payload_records')}")
        print(f"   Endpoint: {result.get('url')}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")