#!/usr/bin/env python3
"""
Example script demonstrating the post classification and processing system.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from post_processor import PostClassifier, PostProcessor, process_posts
from utools_client import SearchResult
from database import init_database


def main():
    """Demonstrate post processing functionality"""
    print("=== Comet Invitation Hunter - Post Processing Demo ===\n")
    
    # Initialize database
    print("Initializing database...")
    init_database()
    print("Database initialized.\n")
    
    # Create sample search results
    sample_results = [
        SearchResult(
            tweet_id="1001",
            content="🎉 Comet browser invitation available! https://www.perplexity.ai/browser/claim/ABC123XYZ Get AI-powered browsing now!",
            author_username="techuser1",
            author_id="1001",
            created_at="2024-01-01T10:00:00Z",
            tweet_url="https://x.com/techuser1/status/1001"
        ),
        SearchResult(
            tweet_id="1002",
            content="I have 5 Comet browser invites! DM me if you want access to the AI browser. First come, first served!",
            author_username="aiexplorer",
            author_id="1002",
            created_at="2024-01-01T10:15:00Z",
            tweet_url="https://x.com/aiexplorer/status/1002"
        ),
        SearchResult(
            tweet_id="1003",
            content="Just tried the new Comet browser - it's incredible for AI research! The interface is so smooth.",
            author_username="researcher",
            author_id="1003",
            created_at="2024-01-01T10:30:00Z",
            tweet_url="https://x.com/researcher/status/1003"
        ),
        SearchResult(
            tweet_id="1004",
            content="🔥 Comet browser invite giveaway! Follow me and comment below with your favorite AI tool. Must be following @0xSky99 too!",
            author_username="aiinfluencer",
            author_id="1004",
            created_at="2024-01-01T10:45:00Z",
            tweet_url="https://x.com/aiinfluencer/status/1004"
        ),
        SearchResult(
            tweet_id="1005",
            content="Check this out: perplexity.ai/browser/claim/XYZ789ABC - Comet browser access link!",
            author_username="sharebot",
            author_id="1005",
            created_at="2024-01-01T11:00:00Z",
            tweet_url="https://x.com/sharebot/status/1005"
        ),
        SearchResult(
            tweet_id="1006",
            content="Like and retweet for Comet browser invite! Will DM the lucky winners 🚀",
            author_username="giveawayhost",
            author_id="1006",
            created_at="2024-01-01T11:15:00Z",
            tweet_url="https://x.com/giveawayhost/status/1006"
        )
    ]
    
    # Simulate search results from multiple keywords
    search_results_by_keyword = {
        "comet invitation": sample_results[:3],
        "perplexity browser": sample_results[2:5],
        "comet invite": sample_results[3:]
    }
    
    print("Sample search results:")
    total_results = sum(len(results) for results in search_results_by_keyword.values())
    print(f"- Total results across all keywords: {total_results}")
    for keyword, results in search_results_by_keyword.items():
        print(f"- '{keyword}': {len(results)} results")
    print()
    
    # Process the search results
    print("Processing search results...")
    processed_posts = process_posts(search_results_by_keyword)
    
    print(f"Found {len(processed_posts)} invitation posts after processing:\n")
    
    # Display results
    for i, post in enumerate(processed_posts, 1):
        print(f"--- Post {i} ---")
        print(f"Tweet ID: {post.tweet_id}")
        print(f"Author: @{post.author_username}")
        print(f"Type: {post.post_type.value.upper()}")
        print(f"URL: {post.tweet_url}")
        print(f"Content: {post.content[:100]}{'...' if len(post.content) > 100 else ''}")
        
        if post.post_type.value == "free":
            print(f"Invitation Link: {post.invitation_link}")
        else:
            print(f"Conditions: {post.conditions}")
        
        print()
    
    # Demonstrate individual classification
    print("=== Individual Classification Demo ===\n")
    
    classifier = PostClassifier()
    
    test_posts = [
        "Get your Comet browser invite here: https://www.perplexity.ai/browser/claim/TEST123",
        "DM me for Comet browser access! Limited invites available.",
        "Just browsing with AI - the future is here!",
        "Follow and RT for a chance to win Comet browser invite! 🎯"
    ]
    
    for i, content in enumerate(test_posts, 1):
        print(f"Test Post {i}: {content}")
        
        test_result = SearchResult(
            tweet_id=f"test{i}",
            content=content,
            author_username="testuser",
            author_id="999",
            created_at="2024-01-01T12:00:00Z",
            tweet_url=f"https://x.com/testuser/status/test{i}"
        )
        
        classified = classifier.classify_post(test_result)
        
        if classified:
            print(f"✅ Classified as: {classified.post_type.value.upper()}")
            if classified.invitation_link:
                print(f"   Link: {classified.invitation_link}")
            if classified.conditions:
                print(f"   Conditions: {classified.conditions}")
        else:
            print("❌ Not an invitation post")
        
        print()
    
    print("Demo completed successfully! 🎉")


if __name__ == "__main__":
    main()