#!/usr/bin/env python3
"""
End-to-end test of the email notification system.
"""

import logging
import sys
import os
from unittest.mock import Mock

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
from utools_client import UtoolsClient, SearchResult
from database import get_db_with_retry, get_all_users

# Import monitor components
monitor_file = os.path.join(os.path.dirname(__file__), '..', 'monitor', 'main.py')
import importlib.util
spec = importlib.util.spec_from_file_location("monitor_main", monitor_file)
monitor_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor_main)

PostClassifier = monitor_main.PostClassifier
EmailNotifier = monitor_main.EmailNotifier
ClassifiedPost = monitor_main.ClassifiedPost

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_connection():
    """Test database connection and user retrieval"""
    logger.info("Testing database connection...")
    
    try:
        db = get_db_with_retry()
        if not db:
            logger.error("❌ Failed to connect to database")
            return False
        
        users = get_all_users(db)
        logger.info(f"✓ Database connection successful: {len(users)} users found")
        
        if users:
            logger.info("Sample users:")
            for user in users[:3]:
                logger.info(f"  - {user.email} (verified at: {user.verified_at})")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

def test_post_classification():
    """Test post classification system"""
    logger.info("Testing post classification...")
    
    classifier = PostClassifier()
    
    # Test free invitation post
    free_result = SearchResult(
        tweet_id="test123",
        content="Check out this Comet invitation! https://www.perplexity.ai/browser/claim/ABC123",
        author_username="testuser",
        author_id="123456",
        created_at="2024-01-01T12:00:00Z",
        tweet_url="https://x.com/testuser/status/test123"
    )
    
    classified_free = classifier.classify_post(free_result)
    if not classified_free or classified_free.post_type != 'free':
        logger.error("❌ Free invitation classification failed")
        return False
    
    logger.info("✓ Free invitation classified correctly")
    
    # Test conditional invitation post
    conditional_result = SearchResult(
        tweet_id="test456",
        content="I have Comet invites! DM me if you want one.",
        author_username="testuser2",
        author_id="789012",
        created_at="2024-01-01T12:00:00Z",
        tweet_url="https://x.com/testuser2/status/test456"
    )
    
    classified_conditional = classifier.classify_post(conditional_result)
    if not classified_conditional or classified_conditional.post_type != 'conditional':
        logger.error("❌ Conditional invitation classification failed")
        return False
    
    logger.info("✓ Conditional invitation classified correctly")
    
    return True

def test_email_notification_with_mock():
    """Test email notification system with mock Resend API"""
    logger.info("Testing email notification system...")
    
    notifier = EmailNotifier()
    
    # Create test posts
    test_posts = [
        ClassifiedPost(
            tweet_id="test123",
            content="Check out this Comet invitation! https://www.perplexity.ai/browser/claim/ABC123",
            author_username="testuser",
            post_type="free",
            invitation_link="https://www.perplexity.ai/browser/claim/ABC123",
            tweet_url="https://x.com/testuser/status/test123",
            conditions=None,
            created_at="2024-01-01T12:00:00Z"
        ),
        ClassifiedPost(
            tweet_id="test456",
            content="I have Comet invites! DM me if you want one.",
            author_username="testuser2",
            post_type="conditional",
            invitation_link=None,
            tweet_url="https://x.com/testuser2/status/test456",
            conditions="Send DM to author",
            created_at="2024-01-01T12:00:00Z"
        )
    ]
    
    test_recipients = ["test@example.com", "user@test.com"]
    
    # Mock the Resend API
    import resend
    original_send = resend.Emails.send
    
    def mock_send(email_data):
        logger.info(f"Mock Resend API call with {len(email_data['to'])} recipients")
        mock_response = Mock()
        mock_response.id = "mock_email_id_456"
        return mock_response
    
    resend.Emails.send = mock_send
    
    try:
        success = notifier.send_batch_notification(test_posts, test_recipients)
        
        if success:
            logger.info("✓ Email notification system working correctly")
            return True
        else:
            logger.error("❌ Email notification failed")
            return False
    
    finally:
        resend.Emails.send = original_send

def test_utools_api_integration():
    """Test Utools API integration for finding real posts"""
    logger.info("Testing Utools API integration...")
    
    client = UtoolsClient(config.utools_api_key, config.utools_base_url)
    classifier = PostClassifier()
    
    try:
        # Search for recent Comet invitations
        results, cursor = client.search_tweets("perplexity.ai/browser/claim", count=10)
        logger.info(f"✓ Found {len(results)} posts from Utools API")
        
        # Classify the results
        classified_posts = []
        for result in results:
            classified = classifier.classify_post(result)
            if classified:
                classified_posts.append(classified)
        
        logger.info(f"✓ Classified {len(classified_posts)} invitation posts")
        
        if classified_posts:
            free_count = len([p for p in classified_posts if p.post_type == 'free'])
            conditional_count = len([p for p in classified_posts if p.post_type == 'conditional'])
            logger.info(f"  - Free invitations: {free_count}")
            logger.info(f"  - Conditional invitations: {conditional_count}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Utools API integration failed: {e}")
        return False

def test_end_to_end_workflow():
    """Test the complete end-to-end workflow"""
    logger.info("Testing end-to-end workflow...")
    
    try:
        # 1. Get users from database
        db = get_db_with_retry()
        if not db:
            logger.error("❌ Database connection failed")
            return False
        
        users = get_all_users(db)
        # All users in the database are considered verified (they have verified_at timestamp)
        verified_users = [user for user in users if user.verified_at is not None]
        db.close()
        
        if not verified_users:
            logger.warning("⚠️ No verified users found - using test email")
            test_emails = ["test@example.com"]
        else:
            test_emails = [user.email for user in verified_users[:2]]  # Limit to 2 for testing
        
        logger.info(f"✓ Found {len(test_emails)} recipient emails")
        
        # 2. Search for posts
        client = UtoolsClient(config.utools_api_key, config.utools_base_url)
        results, cursor = client.search_tweets("comet invitation", count=5)
        logger.info(f"✓ Found {len(results)} posts from search")
        
        # 3. Classify posts
        classifier = PostClassifier()
        classified_posts = []
        for result in results:
            classified = classifier.classify_post(result)
            if classified:
                classified_posts.append(classified)
        
        logger.info(f"✓ Classified {len(classified_posts)} invitation posts")
        
        if not classified_posts:
            logger.warning("⚠️ No classified posts found - creating test posts")
            classified_posts = [
                ClassifiedPost(
                    tweet_id="test789",
                    content="Test Comet invitation for end-to-end testing",
                    author_username="testuser",
                    post_type="free",
                    invitation_link="https://www.perplexity.ai/browser/claim/TEST789",
                    tweet_url="https://x.com/testuser/status/test789",
                    conditions=None,
                    created_at="2024-01-01T12:00:00Z"
                )
            ]
        
        # 4. Send notifications (with mock)
        notifier = EmailNotifier()
        
        import resend
        original_send = resend.Emails.send
        
        def mock_send(email_data):
            logger.info(f"Mock email sent to {len(email_data['to'])} recipients")
            mock_response = Mock()
            mock_response.id = "mock_end_to_end_123"
            return mock_response
        
        resend.Emails.send = mock_send
        
        try:
            success = notifier.send_batch_notification(classified_posts, test_emails)
            
            if success:
                logger.info("✅ End-to-end workflow completed successfully!")
                return True
            else:
                logger.error("❌ End-to-end workflow failed at notification step")
                return False
        
        finally:
            resend.Emails.send = original_send
        
    except Exception as e:
        logger.error(f"❌ End-to-end workflow failed: {e}")
        return False

def main():
    """Run all integration tests"""
    logger.info("Starting email notification system integration tests...")
    
    tests = [
        test_database_connection,
        test_post_classification,
        test_email_notification_with_mock,
        test_utools_api_integration,
        test_end_to_end_workflow
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
        logger.info("✅ All email notification system tests passed!")
        return 0
    else:
        logger.error("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())