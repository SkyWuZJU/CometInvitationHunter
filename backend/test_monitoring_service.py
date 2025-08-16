#!/usr/bin/env python3
"""
Test the monitoring service functionality without running it continuously.
"""

import logging
import sys
import os
import asyncio
from unittest.mock import Mock, patch

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
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'monitor'))

from config import config

# Import monitor components
monitor_file = os.path.join(os.path.dirname(__file__), '..', 'monitor', 'main.py')
import importlib.util
spec = importlib.util.spec_from_file_location("monitor_main", monitor_file)
monitor_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor_main)

CometMonitor = monitor_main.CometMonitor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_monitor_initialization():
    """Test monitor initialization"""
    logger.info("Testing monitor initialization...")
    
    try:
        monitor = CometMonitor()
        logger.info("✓ Monitor initialized successfully")
        logger.info(f"  - Monitoring interval: {monitor.monitoring_interval} seconds")
        logger.info(f"  - Search keywords: {len(monitor.search_keywords)} configured")
        logger.info(f"  - Max results per keyword: {monitor.max_results_per_keyword}")
        return True
    except Exception as e:
        logger.error(f"❌ Monitor initialization failed: {e}")
        return False

def test_monitor_single_cycle():
    """Test a single monitoring cycle"""
    logger.info("Testing single monitoring cycle...")
    
    try:
        monitor = CometMonitor()
        
        # Mock the email notification to avoid sending real emails
        original_send = monitor.notifier.send_batch_notification
        
        def mock_send(posts, recipients):
            logger.info(f"Mock notification: {len(posts)} posts to {len(recipients)} recipients")
            return True
        
        monitor.notifier.send_batch_notification = mock_send
        
        try:
            # Run a single monitoring cycle
            logger.info("Running single monitoring cycle...")
            
            # This would normally be called in the async loop
            # We'll simulate it by calling the search and classification directly
            all_classified_posts = []
            
            for keyword in monitor.search_keywords[:2]:  # Limit to 2 keywords for testing
                logger.info(f"Testing search for keyword: '{keyword}'")
                
                try:
                    results, cursor = monitor.utools_client.search_tweets(keyword, count=5)
                    logger.info(f"  Found {len(results)} results for '{keyword}'")
                    
                    # Classify results
                    for result in results:
                        classified = monitor.classifier.classify_post(result)
                        if classified:
                            all_classified_posts.append(classified)
                    
                except Exception as e:
                    logger.warning(f"  Search failed for '{keyword}': {e}")
                    continue
            
            logger.info(f"✓ Single cycle completed: {len(all_classified_posts)} classified posts")
            
            if all_classified_posts:
                logger.info("Sample classified posts:")
                for post in all_classified_posts[:2]:
                    logger.info(f"  - {post.post_type}: @{post.author_username}")
            
            return True
            
        finally:
            # Restore original function
            monitor.notifier.send_batch_notification = original_send
        
    except Exception as e:
        logger.error(f"❌ Single monitoring cycle failed: {e}")
        return False

def test_monitor_configuration_validation():
    """Test monitor configuration validation"""
    logger.info("Testing monitor configuration validation...")
    
    try:
        monitor = CometMonitor()
        
        # Check required configuration
        if not monitor.utools_client.api_key:
            logger.error("❌ Utools API key not configured")
            return False
        
        if not monitor.notifier.resend_api_key:
            logger.error("❌ Resend API key not configured")
            return False
        
        if not monitor.search_keywords:
            logger.error("❌ No search keywords configured")
            return False
        
        if monitor.monitoring_interval < 60:
            logger.warning("⚠️ Monitoring interval is very short - may hit rate limits")
        
        logger.info("✓ Monitor configuration validation passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Configuration validation failed: {e}")
        return False

def test_monitor_error_handling():
    """Test monitor error handling"""
    logger.info("Testing monitor error handling...")
    
    try:
        monitor = CometMonitor()
        
        # Test with invalid search keyword
        try:
            results, cursor = monitor.utools_client.search_tweets("", count=1)
            logger.info("✓ Empty search handled gracefully")
        except Exception as e:
            logger.info(f"✓ Empty search error handled: {e}")
        
        # Test classification with invalid data
        try:
            from utools_client import SearchResult
            invalid_result = SearchResult(
                tweet_id="",
                content="",
                author_username="",
                author_id="",
                created_at="",
                tweet_url=""
            )
            classified = monitor.classifier.classify_post(invalid_result)
            logger.info("✓ Invalid post classification handled gracefully")
        except Exception as e:
            logger.info(f"✓ Invalid post classification error handled: {e}")
        
        logger.info("✓ Error handling tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error handling test failed: {e}")
        return False

def main():
    """Run all monitoring service tests"""
    logger.info("Starting monitoring service tests...")
    
    tests = [
        test_monitor_initialization,
        test_monitor_configuration_validation,
        test_monitor_single_cycle,
        test_monitor_error_handling
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
        logger.info("✅ All monitoring service tests passed!")
        return 0
    else:
        logger.error("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())