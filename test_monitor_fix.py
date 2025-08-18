#!/usr/bin/env python3
"""
Test script to identify monitor system issues
"""

import sys
import os
sys.path.insert(0, 'backend')
sys.path.insert(0, 'monitor')

import logging
from utools_client import UtoolsClient
from config import config

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_monitor_keywords():
    """Test all monitor keywords individually"""
    
    client = UtoolsClient(
        api_key=config.utools_api_key,
        base_url=config.utools_base_url
    )
    
    # Monitor keywords from search_config.py
    keywords = [
        "perplexity.ai/browser/claim",
        "comet invitation",
        "comet invite", 
        "comet browser invite",
        "comet access",
        "perplexity browser invite",
        "ai browser invite"
    ]
    
    print("=== Testing Monitor Keywords ===")
    
    failed_keywords = []
    for keyword in keywords:
        try:
            print(f"Testing: '{keyword}'")
            results = client.search_recent_tweets_paginated(
                keyword, 
                max_results=50,
                monitoring_interval_seconds=1800
            )
            print(f"  ✓ Success: {len(results)} results")
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            failed_keywords.append((keyword, str(e)))
    
    return failed_keywords

def test_monitor_configuration():
    """Test monitor configuration"""
    
    print("\n=== Monitor Configuration ===")
    print(f"API Key: {config.utools_api_key[:20]}...")
    print(f"Base URL: {config.utools_base_url}")
    
    # Test client creation
    try:
        client = UtoolsClient(
            api_key=config.utools_api_key,
            base_url=config.utools_base_url
        )
        print("  ✓ Client created successfully")
        
        # Test with a simple keyword
        results = client.search_tweets('comet browser invite', count=1)
        print(f"  ✓ Basic search working: {len(results[0])} results")
        
    except Exception as e:
        print(f"  ✗ Configuration error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Monitor System Diagnostic")
    print("=" * 40)
    
    # Test configuration
    config_ok = test_monitor_configuration()
    
    # Test keywords
    failed = test_monitor_keywords()
    
    print(f"\n=== Summary ===")
    print(f"Configuration: {'OK' if config_ok else 'FAILED'}")
    print(f"Failed keywords: {len(failed)}")
    
    if failed:
        print("Failed keywords:")
        for keyword, error in failed:
            print(f"  - '{keyword}': {error}")