#!/usr/bin/env python3
"""
Test script for the monitoring service components.
"""

import asyncio
import logging
import sys
import os
from unittest.mock import Mock, patch

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from database import get_db_with_retry, init_database
from utools_client import SearchResult
from config import config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import monitor components by loading the file directly
monitor_file = os.path.join(os.path.dirname(__file__), '..', 'monitor', 'main.py')
import importlib.util
spec = importlib.util.spec_from_file_location("monitor_main", monitor_file)
monitor_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor_main)

PostClassifier = monitor_main.PostClassifier
EmailNotifier = monitor_main.EmailNotifier
CometMonitor = monitor_main.CometMonitor

def test_post_classifier():
    """Test the post classification logic"""
    logger.info("Testing PostClassifier...")
    
    classifier = PostClassifier()
    
    # Test free sharing post
    free_post = SearchResult(
        tweet_id="123456789",
        content="Check out this Comet invitation! https://www.perplexity.ai/browser/claim/ABC123XYZ",
        author_username="testuser",
        author_id="987654321",
        created_at="2024-01-01T12:00:00Z",
        tweet_url="https://x.com/testuser/status/123456789"
    )
    
    classified = classifier.classify_post(free_post)
    if classified is None:
        logger.error(f"Free post was not classified: {free_post.content}")
        return
    logger.info(f"Free post classified as: {classified.post_type}")
    assert classified is not None
    assert classified.post_type == 'free'
    assert classified.invitation_link is not None
    logger.info("✓ Free sharing post classification works")
    
    # Test conditional sharing post
    conditional_post = SearchResult(
        tweet_id="987654321",
        content="I have Comet browser invites! DM me if you want one. Must follow first.",
        author_username="testuser2",
        author_id="123456789",
        created_at="2024-01-01T12:00:00Z",
        tweet_url="https://x.com/testuser2/status/987654321"
    )
    
    classified = classifier.classify_post(conditional_post)
    if classified is None:
        logger.error("Conditional post was not classified")
        return
    logger.info(f"Classified as: {classified.post_type}")
    assert classified is not None
    assert classified.post_type == 'conditional'
    assert classified.conditions is not None
    logger.info("✓ Conditional sharing post classification works")
    
    # Test non-invitation post
    normal_post = SearchResult(
        tweet_id="555666777",
        content="Just had a great day at the beach!",
        author_username="testuser3",
        author_id="111222333",
        created_at="2024-01-01T12:00:00Z",
        tweet_url="https://x.com/testuser3/status/555666777"
    )
    
    classified = classifier.classify_post(normal_post)
    assert classified is None
    logger.info("✓ Non-invitation post correctly ignored")

def test_email_notifier():
    """Test email notification creation (without actually sending)"""
    logger.info("Testing EmailNotifier...")
    
    notifier = EmailNotifier()
    
    # Create test posts
    ClassifiedPost = monitor_main.ClassifiedPost
    
    test_posts = [
        ClassifiedPost(
            tweet_id="123",
            content="Free Comet invite: https://www.perplexity.ai/browser/claim/TEST123",
            author_username="freeuser",
            post_type="free",
            invitation_link="https://www.perplexity.ai/browser/claim/TEST123",
            tweet_url="https://x.com/freeuser/status/123",
            conditions=None,
            created_at="2024-01-01T12:00:00Z"
        ),
        ClassifiedPost(
            tweet_id="456",
            content="Comet invites available! DM me to get one.",
            author_username="conditionaluser",
            post_type="conditional",
            invitation_link=None,
            tweet_url="https://x.com/conditionaluser/status/456",
            conditions="Send DM to author",
            created_at="2024-01-01T12:00:00Z"
        )
    ]
    
    # Test email content creation
    html_content = notifier._create_email_html(test_posts, "test123")
    text_content = notifier._create_email_text(test_posts, "test123")
    
    assert "Free Invitations" in html_content
    assert "Conditional Invitations" in html_content
    assert "freeuser" in html_content
    assert "conditionaluser" in html_content
    
    assert "FREE INVITATIONS" in text_content
    assert "CONDITIONAL INVITATIONS" in text_content
    
    logger.info("✓ Email content creation works")

async def test_monitor_components():
    """Test monitor components without making real API calls"""
    logger.info("Testing CometMonitor components...")
    
    # Initialize database for testing
    init_database()
    
    monitor = CometMonitor()
    
    # Test deduplication
    test_results = [
        SearchResult("123", "content1", "user1", "id1", "time1", "url1"),
        SearchResult("456", "content2", "user2", "id2", "time2", "url2"),
        SearchResult("123", "content1", "user1", "id1", "time1", "url1"),  # Duplicate
    ]
    
    unique_results = monitor._deduplicate_results(test_results)
    assert len(unique_results) == 2
    logger.info("✓ Deduplication works")
    
    logger.info("✓ Monitor components test completed")

def main():
    """Run all tests"""
    logger.info("Starting monitoring service tests...")
    
    try:
        # Test individual components
        test_post_classifier()
        test_email_notifier()
        
        # Test async components
        asyncio.run(test_monitor_components())
        
        logger.info("✅ All tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()