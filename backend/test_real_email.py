#!/usr/bin/env python3
"""
Test real email sending with Resend API (to verified users only).
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
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'monitor'))

from config import config
from database import get_db_with_retry, get_all_users

# Import monitor components
monitor_file = os.path.join(os.path.dirname(__file__), '..', 'monitor', 'main.py')
import importlib.util
spec = importlib.util.spec_from_file_location("monitor_main", monitor_file)
monitor_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor_main)

EmailNotifier = monitor_main.EmailNotifier
ClassifiedPost = monitor_main.ClassifiedPost

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_real_email_to_verified_users():
    """Test sending real email to verified users"""
    logger.info("Testing real email delivery to verified users...")
    
    # Get verified users from database
    db = get_db_with_retry()
    if not db:
        logger.error("❌ Failed to connect to database")
        return False
    
    users = get_all_users(db)
    verified_users = [user for user in users if user.verified_at is not None]
    db.close()
    
    if not verified_users:
        logger.warning("⚠️ No verified users found - cannot test real email")
        return False
    
    logger.info(f"Found {len(verified_users)} verified users")
    
    # Create test posts
    test_posts = [
        ClassifiedPost(
            tweet_id="test_real_123",
            content="🚀 TEST EMAIL: This is a test of the Comet Invitation Hunter notification system! https://www.perplexity.ai/browser/claim/TEST123",
            author_username="test_system",
            post_type="free",
            invitation_link="https://www.perplexity.ai/browser/claim/TEST123",
            tweet_url="https://x.com/test_system/status/test_real_123",
            conditions=None,
            created_at="2024-01-01T12:00:00Z"
        ),
        ClassifiedPost(
            tweet_id="test_real_456",
            content="📧 TEST EMAIL: I have test Comet invites! This is a system test - please ignore.",
            author_username="test_system2",
            post_type="conditional",
            invitation_link=None,
            tweet_url="https://x.com/test_system2/status/test_real_456",
            conditions="This is a test email - no action required",
            created_at="2024-01-01T12:00:00Z"
        )
    ]
    
    # Get recipient emails (limit to first user for testing)
    test_emails = [verified_users[0].email]  # Only send to first user for testing
    logger.info(f"Sending test email to: {test_emails[0]}")
    
    # Send real email
    notifier = EmailNotifier()
    
    try:
        success = notifier.send_batch_notification(test_posts, test_emails)
        
        if success:
            logger.info("✅ Real email sent successfully!")
            logger.info("Please check the recipient's inbox for the test email.")
            return True
        else:
            logger.error("❌ Real email sending failed")
            return False
    
    except Exception as e:
        logger.error(f"❌ Real email test failed with exception: {e}")
        return False

def main():
    """Run real email test"""
    logger.info("Starting real email delivery test...")
    
    # Confirm with user before sending real email
    print("\n⚠️  WARNING: This will send a REAL EMAIL to verified users!")
    print("This test will send a test notification email to the first verified user in the database.")
    response = input("Do you want to continue? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y']:
        logger.info("Test cancelled by user")
        return 0
    
    if test_real_email_to_verified_users():
        logger.info("✅ Real email test completed successfully!")
        return 0
    else:
        logger.error("❌ Real email test failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())