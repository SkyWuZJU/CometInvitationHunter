#!/usr/bin/env python3
"""
Direct test of Utools API to debug connection issues.
"""

import logging
import sys
import os

# Load environment configuration
def load_environment():
    """Load environment variables from config files"""
    dev_config = os.path.join(os.path.dirname(__file__), '..', 'config', 'development.env')
    if os.path.exists(dev_config):
        with open(dev_config, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

# Load environment before importing config
load_environment()

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from config import config
from utools_client import UtoolsClient, UtoolsError, RateLimitError, APIResponseError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_utools_configuration():
    """Test Utools configuration"""
    logger.info("Testing Utools configuration...")
    
    if not config.utools_api_key:
        logger.error("❌ UTOOLS_API_KEY not configured")
        return False
    
    if not config.utools_base_url:
        logger.error("❌ UTOOLS_BASE_URL not configured")
        return False
    
    logger.info(f"✓ Utools API key configured: {config.utools_api_key[:10]}...")
    logger.info(f"✓ Utools base URL configured: {config.utools_base_url}")
    
    return True

def test_utools_basic_request():
    """Test basic Utools API request"""
    logger.info("Testing basic Utools API request...")
    
    client = UtoolsClient(config.utools_api_key, config.utools_base_url)
    
    try:
        # Try a simple search request
        results, cursor = client.search_tweets("test", count=1)
        logger.info(f"✓ Basic search request successful: {len(results)} results")
        return True
        
    except RateLimitError as e:
        logger.warning(f"⚠️ Rate limit error (expected): {e}")
        return True  # Rate limits are expected, this means API is responding
        
    except APIResponseError as e:
        logger.error(f"❌ API response error: {e}")
        return False
        
    except UtoolsError as e:
        logger.error(f"❌ Utools API error: {e}")
        return False
        
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False

def test_utools_search_comet():
    """Test Utools API with Comet-specific search"""
    logger.info("Testing Utools API with Comet search...")
    
    client = UtoolsClient(config.utools_api_key, config.utools_base_url)
    
    try:
        # Try searching for Comet invitations
        results, cursor = client.search_tweets("perplexity.ai/browser/claim", count=5)
        logger.info(f"✓ Comet search successful: {len(results)} results")
        
        if results:
            logger.info("Sample results:")
            for i, result in enumerate(results[:2], 1):
                logger.info(f"  {i}. @{result.author_username}: {result.content[:100]}...")
        
        return True
        
    except RateLimitError as e:
        logger.warning(f"⚠️ Rate limit error: {e}")
        return True  # Rate limits are expected
        
    except APIResponseError as e:
        logger.error(f"❌ API response error: {e}")
        return False
        
    except UtoolsError as e:
        logger.error(f"❌ Utools API error: {e}")
        return False
        
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False

def test_utools_user_lookup():
    """Test Utools user lookup functionality"""
    logger.info("Testing Utools user lookup...")
    
    client = UtoolsClient(config.utools_api_key, config.utools_base_url)
    
    try:
        # Try looking up a known user
        user = client.get_user_by_screen_name("elonmusk")
        if user:
            logger.info(f"✓ User lookup successful: {user['legacy']['screen_name']} (ID: {user['rest_id']})")
        else:
            logger.warning("⚠️ User lookup returned None (user not found)")
        
        return True
        
    except RateLimitError as e:
        logger.warning(f"⚠️ Rate limit error: {e}")
        return True  # Rate limits are expected
        
    except APIResponseError as e:
        logger.error(f"❌ API response error: {e}")
        return False
        
    except UtoolsError as e:
        logger.error(f"❌ Utools API error: {e}")
        return False
        
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False

def main():
    """Run all Utools tests"""
    logger.info("Starting Utools API integration tests...")
    
    tests = [
        test_utools_configuration,
        test_utools_basic_request,
        test_utools_search_comet,
        test_utools_user_lookup
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"❌ Test {test.__name__} failed with exception: {e}")
            failed += 1
    
    logger.info(f"\n📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        logger.info("✅ All Utools integration tests passed!")
        return 0
    else:
        logger.error("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())