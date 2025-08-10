#!/usr/bin/env python3
"""
Test script for Resend email integration.
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

from config import config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import monitor components
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'monitor'))
monitor_file = os.path.join(os.path.dirname(__file__), '..', 'monitor', 'main.py')
import importlib.util
spec = importlib.util.spec_from_file_location("monitor_main", monitor_file)
monitor_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor_main)

EmailNotifier = monitor_main.EmailNotifier
ClassifiedPost = monitor_main.ClassifiedPost

def test_resend_configuration():
    """Test Resend configuration"""
    logger.info("Testing Resend configuration...")
    
    notifier = EmailNotifier()
    
    if not notifier.resend_api_key:
        logger.error("❌ RESEND_API_KEY not configured")
        return False
    
    if not notifier.from_email:
        logger.error("❌ FROM_EMAIL not configured")
        return False
    
    logger.info(f"✓ Resend API key configured: {notifier.resend_api_key[:10]}...")
    logger.info(f"✓ From email configured: {notifier.from_email}")
    
    return True

def test_email_template_creation():
    """Test email template creation"""
    logger.info("Testing email template creation...")
    
    notifier = EmailNotifier()
    
    # Create test posts
    test_posts = [
        ClassifiedPost(
            tweet_id="test123",
            content="Check out this Comet invitation! https://www.perplexity.ai/browser/claim/TEST123",
            author_username="testuser",
            post_type="free",
            invitation_link="https://www.perplexity.ai/browser/claim/TEST123",
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
    
    # Test HTML template
    html_content = notifier._create_email_html(test_posts, "test123")
    if not html_content or len(html_content) < 100:
        logger.error("❌ HTML template creation failed")
        return False
    
    # Test text template
    text_content = notifier._create_email_text(test_posts, "test123")
    if not text_content or len(text_content) < 100:
        logger.error("❌ Text template creation failed")
        return False
    
    logger.info("✓ Email templates created successfully")
    logger.info(f"  HTML length: {len(html_content)} characters")
    logger.info(f"  Text length: {len(text_content)} characters")
    
    # Check for key content
    if "Free Invitations" not in html_content:
        logger.error("❌ HTML template missing free invitations section")
        return False
    
    if "Conditional Invitations" not in html_content:
        logger.error("❌ HTML template missing conditional invitations section")
        return False
    
    if "testuser" not in html_content:
        logger.error("❌ HTML template missing test user")
        return False
    
    if "Unsubscribe" not in html_content:
        logger.error("❌ HTML template missing unsubscribe link")
        return False
    
    logger.info("✓ Email templates contain expected content")
    return True

def test_resend_api_mock():
    """Test Resend API integration with mock"""
    logger.info("Testing Resend API integration (mock)...")
    
    notifier = EmailNotifier()
    
    if not notifier.resend_api_key:
        logger.warning("⚠️ Skipping API test - no API key configured")
        return True
    
    # Create test posts
    test_posts = [
        ClassifiedPost(
            tweet_id="test123",
            content="Test Comet invitation post",
            author_username="testuser",
            post_type="free",
            invitation_link="https://www.perplexity.ai/browser/claim/TEST123",
            tweet_url="https://x.com/testuser/status/test123",
            conditions=None,
            created_at="2024-01-01T12:00:00Z"
        )
    ]
    
    test_recipients = ["test@example.com"]
    
    # Mock the Resend API to avoid actually sending emails during testing
    import resend
    original_send = resend.Emails.send
    
    def mock_send(email_data):
        logger.info(f"Mock Resend API call with data: {email_data.keys()}")
        # Return a mock response object
        mock_response = Mock()
        mock_response.id = "mock_email_id_123"
        return mock_response
    
    resend.Emails.send = mock_send
    
    try:
        # Test sending
        success = notifier.send_batch_notification(test_posts, test_recipients)
        
        if success:
            logger.info("✓ Mock Resend API integration successful")
            return True
        else:
            logger.error("❌ Mock Resend API integration failed")
            return False
    
    finally:
        # Restore original function
        resend.Emails.send = original_send

def main():
    """Run all Resend tests"""
    logger.info("Starting Resend email integration tests...")
    
    tests = [
        test_resend_configuration,
        test_email_template_creation,
        test_resend_api_mock
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
        logger.info("✅ All Resend integration tests passed!")
        return 0
    else:
        logger.error("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())