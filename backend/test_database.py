#!/usr/bin/env python3
"""
Simple test script to verify database functionality
"""
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
sys.path.append(str(Path(__file__).parent))

from database import (
    get_db, add_user, add_post, log_email_batch, 
    get_all_users, is_post_processed, health_check
)

def test_database_operations():
    """Test basic database operations"""
    print("Testing database operations...")
    
    # Test health check
    print("1. Testing health check...")
    if not health_check():
        print("❌ Health check failed")
        return False
    print("✅ Health check passed")
    
    # Get database session
    db = get_db()
    
    try:
        # Test adding a user
        print("2. Testing user creation...")
        user = add_user(db, "test@example.com")
        if user:
            print(f"✅ User created: {user.email}")
        else:
            print("❌ Failed to create user")
            return False
        
        # Test adding a post
        print("3. Testing post creation...")
        post = add_post(
            db=db,
            tweet_id="123456789",
            content="Check out this cool Comet invitation!",
            author_username="testuser",
            post_type="free",
            tweet_url="https://x.com/testuser/status/123456789",
            invitation_link="https://comet.com/invite/abc123"
        )
        if post:
            print(f"✅ Post created: {post.tweet_id}")
        else:
            print("❌ Failed to create post")
            return False
        
        # Test logging email batch
        print("4. Testing email log creation...")
        email_log = log_email_batch(
            db=db,
            batch_id="batch_001",
            recipient_count=1,
            posts_included=1,
            status="sent"
        )
        if email_log:
            print(f"✅ Email log created: {email_log.batch_id}")
        else:
            print("❌ Failed to create email log")
            return False
        
        # Test querying users
        print("5. Testing user query...")
        users = get_all_users(db)
        if users and len(users) > 0:
            print(f"✅ Found {len(users)} users")
        else:
            print("❌ No users found")
            return False
        
        # Test checking if post is processed
        print("6. Testing post processing check...")
        is_processed = is_post_processed(db, "123456789")
        if is_processed:
            print("✅ Post processing check works")
        else:
            print("❌ Post processing check failed")
            return False
        
        print("\n🎉 All database tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    
    finally:
        db.close()

if __name__ == "__main__":
    success = test_database_operations()
    sys.exit(0 if success else 1)