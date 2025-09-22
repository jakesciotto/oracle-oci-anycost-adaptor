#!/usr/bin/env python3
"""
Entry point script for Oracle OCI AnyCost Stream Adaptor.
This script can be run from the project root directory.
"""

import sys
import os

# Add src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

# Import and run the main adaptor
from oci_anycost_adaptor import main

if __name__ == "__main__":
    main()