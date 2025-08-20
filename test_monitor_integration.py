#!/usr/bin/env python3
"""
Integration test for the monitoring service.
Tests the service startup and basic functionality without making real API calls.
"""

import asyncio
import logging
import sys
import os
from unittest.mock import Mock, patch, AsyncMock

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_environment():
    """Load test environment variables"""
    os.environ['DATABASE_URL'] = 'sqlite:///./test_comet_hunter.db'
    os.environ['UTOOLS_API_KEY'] = 'test_key'
    os.environ['MONITORING_INTERVAL'] = '10'  # Short interval for testing
    os.environ['RESEND_API_KEY'] = 'test_resend_key'
    os.environ['FROM_EMAIL'] = 'test@example.com'

async def test_monitor_startup():
    """Test that the monitor can start up without errors"""
    logger.info("Testing monitor startup...")
    
    # Load environment
    load_environment()
    
    # Import monitor after setting environment
    sys.path.append('monitor')
    from main import CometMonitor
    
    # Create monitor instance
    monitor = CometMonitor()
    
    # Mock the Utools client to avoid real API calls
    with patch.object(monitor.utools_client, 'search_tweets_paginated') as mock_search:
        mock_search.return_value = []  # Return empty results
        
        # Mock the email notifier to avoid real email sending
        with patch.object(monitor.notifier, 'send_batch_notification') as mock_email:
            mock_email.return_value = True
            
            # Run one monitoring cycle
            try:
                await monitor._monitoring_cycle()
                logger.info("✓ Monitoring cycle completed successfully")
            except Exception as e:
                logger.error(f"❌ Monitoring cycle failed: {e}")
                raise
    
    logger.info("✓ Monitor startup test passed")

async def test_monitor_with_mock_data():
    """Test monitor with mock search results"""
    logger.info("Testing monitor with mock data...")
    
    # Load environment
    load_environment()
    
    # Import required modules
    sys.path.append('backend')
    sys.path.append('monitor')
    from main import CometMonitor
    from utools_client import SearchResult
    from database import init_database
    
    # Initialize test database
    init_database()
    
    # Create monitor instance
    monitor = CometMonitor()
    
    # Create mock search results
    mock_results = [
        SearchResult(
            tweet_id="test123",
            content="Check out this Comet invitation! https://www.perplexity.ai/browser/claim/TEST123",
            author_username="testuser",
            author_id="123456",
            created_at="2024-01-01T12:00:00Z",
            tweet_url="https://x.com/testuser/status/test123"
        ),
        SearchResult(
            tweet_id="test456",
            content="I have Comet invites! DM me if you want one.",
            author_username="testuser2",
            author_id="789012",
            created_at="2024-01-01T12:00:00Z",
            tweet_url="https://x.com/testuser2/status/test456"
        )
    ]
    
    # Mock the search method to return our test data
    with patch.object(monitor, '_search_all_keywords') as mock_search:
        mock_search.return_value = mock_results
        
        # Mock email sending
        with patch.object(monitor.notifier, 'send_batch_notification') as mock_email:
            mock_email.return_value = True
            
            # Run monitoring cycle
            try:
                await monitor._monitoring_cycle()
                logger.info("✓ Monitoring cycle with mock data completed")
                
                # Verify email was called if posts were found
                if mock_email.called:
                    logger.info("✓ Email notification was triggered")
                else:
                    logger.info("ℹ No email notification (no new posts or no users)")
                    
            except Exception as e:
                logger.error(f"❌ Monitoring cycle with mock data failed: {e}")
                raise
    
    logger.info("✓ Monitor with mock data test passed")

async def main():
    """Run integration tests"""
    logger.info("Starting monitoring service integration tests...")
    
    try:
        await test_monitor_startup()
        await test_monitor_with_mock_data()
        
        logger.info("✅ All integration tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Clean up test database
    try:
        if os.path.exists('test_comet_hunter.db'):
            os.remove('test_comet_hunter.db')
            logger.info("✓ Test database cleaned up")
    except Exception as e:
        logger.warning(f"Failed to clean up test database: {e}")

if __name__ == "__main__":
    asyncio.run(main())