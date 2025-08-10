#!/usr/bin/env python3
"""
End-to-end test for the email notification system with Resend.
"""

import asyncio
import logging
import sys
import os
from unittest.mock import Mock, patch

# Load environment configuration
def load_environment():
    """Load environment variables from config files"""
    dev_config = os.path.join(os.path.dirname(__file__), 'config', 'development.env')
    if os.path.exists(dev_config):
        with open(dev_config, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

# Load environment before imports
load_environment()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add paths
sys.path.append('backend')

from database import init_database, get_db_with_retry, add_user
import resend

# Import monitor components
monitor_file = os.path.join(os.path.dirname(__file__), 'monitor', 'main.py')
import importlib.util
spec = importlib.util.spec_from_file_location("monitor_main", monitor_file)
monitor_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor_main)

CometMonitor = monitor_main.CometMonitor
ClassifiedPost = monitor_main.ClassifiedPost

async def test_complete_email_workflow():
    """Test the complete email workflow with mock data"""
    logger.info("Testing complete email notification workflow...")
    
    # Initialize test database
    init_database()
    
    # Add test users to database
    db = get_db_with_retry()
    if db:
        try:
            add_user(db, "test1@example.com")
            add_user(db, "test2@example.com")
            logger.info("✓ Added test users to database")
        finally:
            db.close()
    
    # Create test posts
    test_posts = [
        ClassifiedPost(
            tweet_id="real_test_123",
            content="🚀 Comet browser invitation available! https://www.perplexity.ai/browser/claim/REALTEST123",
            author_username="comet_sharer",
            post_type="free",
            invitation_link="https://www.perplexity.ai/browser/claim/REALTEST123",
            tweet_url="https://x.com/comet_sharer/status/real_test_123",
            conditions=None,
            created_at="2024-01-01T12:00:00Z"
        ),
        ClassifiedPost(
            tweet_id="real_test_456",
            content="I have 5 Comet invites to share! Follow me and DM for one. First come first serve! 🎯",
            author_username="invite_giver",
            post_type="conditional",
            invitation_link=None,
            tweet_url="https://x.com/invite_giver/status/real_test_456",
            conditions="Follow the author, Send DM to author",
            created_at="2024-01-01T12:00:00Z"
        )
    ]
    
    # Create monitor instance
    monitor = CometMonitor()
    
    # Mock Resend API to capture the email data without sending
    captured_emails = []
    
    def mock_resend_send(email_data):
        logger.info("📧 Captured email data for analysis:")
        logger.info(f"  From: {email_data['from']}")
        logger.info(f"  To: {email_data['to']}")
        logger.info(f"  Subject: {email_data['subject']}")
        logger.info(f"  HTML length: {len(email_data['html'])} chars")
        logger.info(f"  Text length: {len(email_data['text'])} chars")
        logger.info(f"  Headers: {email_data.get('headers', {})}")
        logger.info(f"  Tags: {email_data.get('tags', [])}")
        
        # Store for verification
        captured_emails.append(email_data)
        
        # Return mock response
        mock_response = Mock()
        mock_response.id = f"test_email_{len(captured_emails)}"
        return mock_response
    
    # Apply mock
    original_send = resend.Emails.send
    resend.Emails.send = mock_resend_send
    
    try:
        # Send notifications
        await monitor._send_notifications(test_posts)
        
        # Verify email was captured
        if not captured_emails:
            logger.error("❌ No emails were sent")
            return False
        
        email_data = captured_emails[0]
        
        # Verify email structure
        if not email_data.get('from'):
            logger.error("❌ Missing 'from' field")
            return False
        
        if not email_data.get('to'):
            logger.error("❌ Missing 'to' field")
            return False
        
        if len(email_data['to']) != 2:
            logger.error(f"❌ Expected 2 recipients, got {len(email_data['to'])}")
            return False
        
        if "test1@example.com" not in email_data['to'] or "test2@example.com" not in email_data['to']:
            logger.error("❌ Missing expected recipients")
            return False
        
        # Verify subject
        if "New Comet Invitations Found" not in email_data['subject']:
            logger.error("❌ Incorrect email subject")
            return False
        
        # Verify HTML content
        html_content = email_data['html']
        if "Free Invitations" not in html_content:
            logger.error("❌ HTML missing free invitations section")
            return False
        
        if "Conditional Invitations" not in html_content:
            logger.error("❌ HTML missing conditional invitations section")
            return False
        
        if "comet_sharer" not in html_content:
            logger.error("❌ HTML missing free post author")
            return False
        
        if "invite_giver" not in html_content:
            logger.error("❌ HTML missing conditional post author")
            return False
        
        if "https://www.perplexity.ai/browser/claim/REALTEST123" not in html_content:
            logger.error("❌ HTML missing invitation link")
            return False
        
        if "Follow the author, Send DM to author" not in html_content:
            logger.error("❌ HTML missing conditions")
            return False
        
        if "Unsubscribe" not in html_content:
            logger.error("❌ HTML missing unsubscribe link")
            return False
        
        # Verify text content
        text_content = email_data['text']
        if "FREE INVITATIONS" not in text_content:
            logger.error("❌ Text missing free invitations section")
            return False
        
        if "CONDITIONAL INVITATIONS" not in text_content:
            logger.error("❌ Text missing conditional invitations section")
            return False
        
        # Verify headers
        headers = email_data.get('headers', {})
        if 'List-Unsubscribe' not in headers:
            logger.error("❌ Missing List-Unsubscribe header")
            return False
        
        # Verify tags
        tags = email_data.get('tags', [])
        tag_names = [tag['name'] for tag in tags]
        if 'category' not in tag_names or 'batch_id' not in tag_names:
            logger.error("❌ Missing required tags")
            return False
        
        logger.info("✅ All email verification checks passed!")
        return True
        
    finally:
        # Restore original function
        resend.Emails.send = original_send

async def main():
    """Run the complete email system test"""
    logger.info("🧪 Starting complete email system test...")
    
    try:
        success = await test_complete_email_workflow()
        
        if success:
            logger.info("🎉 Complete email system test PASSED!")
            logger.info("📧 Resend integration is working correctly")
            logger.info("✉️ Email templates are properly formatted")
            logger.info("🔗 Unsubscribe functionality is included")
            logger.info("🏷️ Email headers and tags are set correctly")
            return 0
        else:
            logger.error("❌ Complete email system test FAILED!")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        # Clean up test database
        try:
            if os.path.exists('comet_hunter_dev.db'):
                os.remove('comet_hunter_dev.db')
                logger.info("🧹 Test database cleaned up")
        except Exception as e:
            logger.warning(f"Failed to clean up test database: {e}")

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)