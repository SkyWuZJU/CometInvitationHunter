#!/usr/bin/env python3
"""
Test script for FastAPI backend endpoints.
"""

import sys
import json
import requests
import time
from typing import Dict, Any

def test_endpoint(url: str, method: str = "GET", data: Dict[Any, Any] = None) -> Dict[str, Any]:
    """Test an API endpoint and return results"""
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            return {"success": False, "error": f"Unsupported method: {method}"}
        
        return {
            "success": True,
            "status_code": response.status_code,
            "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
        }
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"JSON decode error: {e}"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {e}"}

def main():
    """Run API tests"""
    base_url = "http://localhost:8000"
    
    print("🚀 Starting FastAPI Backend Tests")
    print("=" * 50)
    
    # Test 1: Root endpoint
    print("\n1. Testing root endpoint...")
    result = test_endpoint(f"{base_url}/")
    if result["success"]:
        print(f"✓ Status: {result['status_code']}")
        print(f"✓ Response: {json.dumps(result['response'], indent=2)}")
    else:
        print(f"✗ Error: {result['error']}")
    
    # Test 2: Health endpoint
    print("\n2. Testing health endpoint...")
    result = test_endpoint(f"{base_url}/api/health")
    if result["success"]:
        print(f"✓ Status: {result['status_code']}")
        print(f"✓ Response: {json.dumps(result['response'], indent=2)}")
    else:
        print(f"✗ Error: {result['error']}")
    
    # Test 3: User verification endpoint (invalid data)
    print("\n3. Testing user verification endpoint with invalid data...")
    invalid_data = {"email": "invalid-email", "x_handle": ""}
    result = test_endpoint(f"{base_url}/api/users/verify", "POST", invalid_data)
    if result["success"]:
        print(f"✓ Status: {result['status_code']}")
        print(f"✓ Response: {json.dumps(result['response'], indent=2)}")
    else:
        print(f"✗ Error: {result['error']}")
    
    # Test 4: User verification endpoint (valid format, but won't verify)
    print("\n4. Testing user verification endpoint with valid format...")
    valid_data = {"email": "test@example.com", "x_handle": "testuser"}
    result = test_endpoint(f"{base_url}/api/users/verify", "POST", valid_data)
    if result["success"]:
        print(f"✓ Status: {result['status_code']}")
        print(f"✓ Response: {json.dumps(result['response'], indent=2)}")
    else:
        print(f"✗ Error: {result['error']}")
    
    print("\n" + "=" * 50)
    print("🎉 API Tests Completed!")

if __name__ == "__main__":
    main()