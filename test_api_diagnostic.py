#!/usr/bin/env python3
"""
Complete diagnostic for Utools API connectivity issues
"""

import sys
import os
sys.path.insert(0, 'backend')

import requests
import json
from utools_client import UtoolsClient

def test_api_connectivity():
    """Test API connectivity step by step"""
    
    print("=== UTOOLS API DIAGNOSTIC ===\n")
    
    # Test 1: Basic connectivity
    print("1. Testing basic API connectivity...")
    try:
        response = requests.get("https://twitter.good6.top/api/base/apitools", timeout=10)
        print(f"   ✓ Base URL accessible: HTTP {response.status_code}")
    except Exception as e:
        print(f"   ✗ Base URL failed: {e}")
        return False
    
    # Test 2: API key format
    api_key = "your_utools_api_key_here"
    print(f"\n2. API Key Analysis:")
    print(f"   Key: {api_key}")
    print(f"   Length: {len(api_key)}")
    print(f"   Format: {'Valid' if '|' in api_key else 'Invalid'}")
    
    # Test 3: Direct API call with detailed response
    print("\n3. Testing direct API call...")
    try:
        params = {
            'words': 'test',
            'product': 'Latest',
            'count': 1,
            'apiKey': api_key
        }
        
        response = requests.get("https://twitter.good6.top/api/base/apitools/search", params=params, timeout=10)
        print(f"   HTTP Status: {response.status_code}")
        print(f"   Response Headers: {dict(response.headers)}")
        print(f"   Response Text: {response.text}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   JSON Response: {json.dumps(data, indent=2)}")
                return True
            except:
                print(f"   Non-JSON Response: {response.text}")
        else:
            print(f"   Error Response: {response.text}")
            
    except Exception as e:
        print(f"   API call failed: {e}")
    
    # Test 4: URL encoding issue
    print("\n4. Testing URL encoding...")
    import urllib.parse
    encoded_key = urllib.parse.quote(api_key)
    print(f"   URL Encoded Key: {encoded_key}")
    
    try:
        params = {
            'words': 'test',
            'product': 'Latest',
            'count': 1,
            'apiKey': encoded_key
        }
        response = requests.get("https://twitter.good6.top/api/base/apitools/search", params=params, timeout=10)
        print(f"   Encoded HTTP Status: {response.status_code}")
        print(f"   Encoded Response: {response.text}")
    except Exception as e:
        print(f"   Encoded request failed: {e}")
    
    # Test 5: Alternative endpoint
    print("\n5. Testing different endpoint format...")
    try:
        # Try without URL encoding the key
        url = f"https://twitter.good6.top/api/base/apitools/search?words=test&product=Latest&count=1&apiKey={api_key}"
        response = requests.get(url, timeout=10)
        print(f"   Direct URL HTTP Status: {response.status_code}")
        print(f"   Direct URL Response: {response.text}")
    except Exception as e:
        print(f"   Direct URL failed: {e}")
    
    # Test 6: Check if key needs different format
    print("\n6. Key format suggestions:")
    print("   Current format: key|user_id-suffix")
    print("   Try regenerating key from: https://twitter.good6.top/personal")
    print("   Ensure key has proper permissions for search API")
    
    return False

if __name__ == "__main__":
    test_api_connectivity()