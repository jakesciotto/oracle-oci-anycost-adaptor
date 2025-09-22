#!/usr/bin/env python3
"""
Oracle Cloud Infrastructure (OCI) Configuration Module

This module provides secure configuration for OCI API connections using
environment variables for sensitive data.
"""

import os
import oci
from typing import Dict, Optional

# Load environment variables from .env file
def load_env_file():
    """Load environment variables from .env file if it exists."""
    env_file = 'env/.env'
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if value and not os.getenv(key):
                        os.environ[key] = value

# Load .env on import
load_env_file()


class OCIConfig:
    """
    Secure OCI configuration using environment variables for sensitive data.
    """
    
    def __init__(self):
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, str]:
        """
        Load OCI configuration from environment variables.
        
        Returns:
            Dict containing OCI configuration
            
        Raises:
            ValueError: If required environment variables are missing
        """
        required_vars = [
            'OCI_USER_OCID',
            'OCI_TENANCY_OCID', 
            'OCI_FINGERPRINT',
            'OCI_PRIVATE_KEY_PATH',
            'OCI_REGION'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")
        
        return {
            'user': os.getenv('OCI_USER_OCID'),
            'tenancy': os.getenv('OCI_TENANCY_OCID'),
            'fingerprint': os.getenv('OCI_FINGERPRINT'),
            'key_file': os.getenv('OCI_PRIVATE_KEY_PATH'),
            'region': os.getenv('OCI_REGION'),
            'pass_phrase': os.getenv('OCI_PRIVATE_KEY_PASSPHRASE')  # Optional
        }
    
    def get_config(self) -> Dict[str, str]:
        """
        Get the OCI configuration dictionary.
        
        Returns:
            OCI configuration suitable for oci.config
        """
        return self.config
    
    def validate_config(self) -> bool:
        """
        Validate that the configuration can connect to OCI.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            oci.config.validate_config(self.config)
            return True
        except Exception as e:
            print(f"Configuration validation failed: {e}")
            return False


def get_usage_client() -> oci.usage_api.UsageapiClient:
    """
    Create and return an OCI Usage API client.
    
    Returns:
        Configured UsageapiClient instance
        
    Raises:
        ValueError: If configuration is invalid
    """
    config = OCIConfig()
    
    if not config.validate_config():
        raise ValueError("Invalid OCI configuration")
    
    return oci.usage_api.UsageapiClient(config.get_config())


def get_identity_client() -> oci.identity.IdentityClient:
    """
    Create and return an OCI Identity client for tenancy information.
    
    Returns:
        Configured IdentityClient instance
    """
    config = OCIConfig()
    return oci.identity.IdentityClient(config.get_config())