"""
Example usage of the Utools API client.
This script demonstrates how to use the client for searching tweets and verifying followers.
"""

import asyncio
import logging
from utools_client import UtoolsClient, UtoolsError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API configuration from design document
API_KEY = "your_utools_api_key_here"
TARGET_USER_ID = "1260183271930904577"  # @0xSky99


async def main():
    """Example usage of Utools API client"""
    
    # Initialize client
    client = UtoolsClient(API_KEY)
    
    try:
        # Example 1: Search for Comet invitation tweets
        print("=== Searching for Comet invitation tweets ===")
        keywords = "perplexity.ai/browser/claim"
        results = client.search_tweets(keywords, count=10)
        
        print(f"Found {len(results)} tweets for '{keywords}':")
        for i, tweet in enumerate(results[:3], 1):  # Show first 3 results
            print(f"\n{i}. Tweet ID: {tweet.tweet_id}")
            print(f"   Author: @{tweet.author_username}")
            print(f"   Content: {tweet.content[:100]}...")
            print(f"   URL: {tweet.tweet_url}")
        
        # Example 2: Verify if a user follows @0xSky99
        print("\n=== Verifying follower status ===")
        test_username = "elonmusk"  # Example username
        
        try:
            is_following = client.verify_user_follows(test_username, TARGET_USER_ID)
            print(f"@{test_username} {'follows' if is_following else 'does not follow'} @0xSky99")
        except UtoolsError as e:
            print(f"Could not verify @{test_username}: {e}")
        
        # Example 3: Get user information
        print("\n=== Getting user information ===")
        user_info = client.get_user_by_screen_name("0xSky99")
        if user_info:
            print(f"User @0xSky99:")
            print(f"  ID: {user_info['rest_id']}")
            print(f"  Name: {user_info['legacy'].get('name', 'N/A')}")
        else:
            print("User @0xSky99 not found")
        
        # Example 4: Get followers (limited sample)
        print("\n=== Getting followers sample ===")
        followers = client.get_followers(TARGET_USER_ID, count=5)
        print(f"@0xSky99 has followers (showing first 5 IDs): {followers[:5]}")
        
    except UtoolsError as e:
        logger.error(f"API error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    # Note: This example uses the real API key and will make actual API calls
    # Uncomment the line below to run the example (be mindful of rate limits)
    # asyncio.run(main())
    
    print("Example script ready. Uncomment the asyncio.run(main()) line to execute.")
    print("Note: This will make real API calls to Utools API.")