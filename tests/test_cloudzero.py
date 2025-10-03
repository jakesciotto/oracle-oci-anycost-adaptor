#!/usr/bin/env python3
"""
Test CloudZero connection and configuration.
"""

import sys
import os

# Add src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

from cloudzero import CloudZeroClient

if __name__ == "__main__":
    print("🔍 Testing CloudZero AnyCost Stream connection...")
    
    try:
        client = CloudZeroClient()
        success = client.test_connection()
        
        if success:
            print(f"\n✅ CloudZero configuration is ready!")
            print(f"   Next steps:")
            print(f"   1. Add your CloudZero API key to env/.env")
            print(f"   2. Test with dry run: python run_oci_adaptor.py --month 2025-09 --dry-run")
            print(f"   3. Perform actual upload: python run_oci_adaptor.py --month 2025-09")
        else:
            print(f"\n❌ CloudZero configuration needs attention")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"\nPlease check your env/.env file configuration")