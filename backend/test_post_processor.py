"""
Comprehensive tests for post classification and processing system.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict

from backend.post_processor import (
    PostClassifier, PostProcessor, PostType, ClassifiedPost,
    process_posts, classify_single_post
)
from backend.utools_client import SearchResult
from backend.database import Base, engine, SessionLocal, init_database


# Test data fixtures
@pytest.fixture
def sample_search_results():
    """Sample search results for testing"""
    return [
        SearchResult(
            tweet_id="1234567890",
            content="Check out this Comet browser invitation! https://www.perplexity.ai/browser/claim/ABC123XYZ",
            author_username="testuser1",
            author_id="111",
            created_at="2024-01-01T12:00:00Z",
            tweet_url="https://x.com/testuser1/status/1234567890"
        ),
        SearchResult(
            tweet_id="1234567891",
            content="I have Comet invites! DM me for access to the AI browser",
            author_username="testuser2",
            author_id="222",
            created_at="2024-01-01T12:01:00Z",
            tweet_url="https://x.com/testuser2/status/1234567891"
        ),
        SearchResult(
            tweet_id="1234567892",
            content="Just got my Comet browser access! It's amazing for AI-powered browsing",
            author_username="testuser3",
            author_id="333",
            created_at="2024-01-01T12:02:00Z",
            tweet_url="https://x.com/testuser3/status/1234567892"
        ),
        SearchResult(
            tweet_id="1234567893",
            content="Follow me and comment below for Comet browser invite! Must be following @0xSky99",
            author_username="testuser4",
            author_id="444",
            created_at="2024-01-01T12:03:00Z",
            tweet_url="https://x.com/testuser4/status/1234567893"
        )
    ]


@pytest.fixture
def test_db():
    """Create a test database"""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp()
    os.close(db_fd)
    
    # Update database URL for testing
    test_db_url = f"sqlite:///{db_path}"
    
    # Create test engine and session
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    test_engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    # Create tables
    Base.metadata.create_all(bind=test_engine)
    
    yield TestSessionLocal
    
    # Cleanup
    os.unlink(db_path)


class TestPostClassifier:
    """Test cases for PostClassifier"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.classifier = PostClassifier()
    
    def test_classify_free_sharing_post(self, sample_search_results):
        """Test classification of free sharing posts with direct links"""
        result = sample_search_results[0]  # Has direct invitation link
        classified = self.classifier.classify_post(result)
        
        assert classified is not None
        assert classified.post_type == PostType.FREE
        assert classified.invitation_link == "https://www.perplexity.ai/browser/claim/ABC123XYZ"
        assert classified.conditions is None
        assert classified.tweet_id == result.tweet_id
        assert classified.author_username == result.author_username
    
    def test_classify_conditional_sharing_post(self, sample_search_results):
        """Test classification of conditional sharing posts"""
        result = sample_search_results[1]  # Has DM requirement
        classified = self.classifier.classify_post(result)
        
        assert classified is not None
        assert classified.post_type == PostType.CONDITIONAL
        assert classified.invitation_link is None
        assert "Send DM to author" in classified.conditions
        assert classified.tweet_id == result.tweet_id
    
    def test_classify_non_invitation_post(self, sample_search_results):
        """Test that non-invitation posts are not classified"""
        result = sample_search_results[2]  # Just mentions Comet but no invitation
        classified = self.classifier.classify_post(result)
        
        assert classified is None
    
    def test_classify_complex_conditional_post(self, sample_search_results):
        """Test classification of complex conditional posts"""
        result = sample_search_results[3]  # Follow and comment requirements
        classified = self.classifier.classify_post(result)
        
        assert classified is not None
        assert classified.post_type == PostType.CONDITIONAL
        # The content is "Follow me and comment below for Comet browser invite! Must be following @0xSky99"
        # Should detect both follow and comment conditions
        assert "Follow the author" in classified.conditions
        assert "Comment on the post" in classified.conditions
    
    def test_extract_invitation_link_variations(self):
        """Test extraction of invitation links in various formats"""
        test_cases = [
            ("Get Comet access: https://www.perplexity.ai/browser/claim/XYZ789", "https://www.perplexity.ai/browser/claim/XYZ789"),
            ("Check this out perplexity.ai/browser/claim/ABC123", "https://perplexity.ai/browser/claim/ABC123"),
            ("Link: https://perplexity.ai/browser/claim/TEST456", "https://perplexity.ai/browser/claim/TEST456"),
            ("No link here", None),
            ("Invalid link: https://example.com/claim/ABC", None)
        ]
        
        for content, expected_link in test_cases:
            result = SearchResult("123", content, "user", "456", "2024-01-01", "https://x.com/user/status/123")
            classified = self.classifier.classify_post(result)
            
            if expected_link:
                assert classified is not None
                assert classified.invitation_link == expected_link
            else:
                # Should either be None or conditional (if it has Comet keywords)
                if classified:
                    assert classified.post_type == PostType.CONDITIONAL
    
    def test_validate_invitation_link(self):
        """Test invitation link validation"""
        valid_links = [
            "https://www.perplexity.ai/browser/claim/ABC123",
            "https://perplexity.ai/browser/claim/XYZ789",
            "https://www.perplexity.ai/browser/claim/TEST456DEF"
        ]
        
        invalid_links = [
            "https://example.com/browser/claim/ABC123",
            "https://www.perplexity.ai/claim/ABC123",
            "https://www.perplexity.ai/browser/ABC123",
            "https://www.perplexity.ai/browser/claim/",
            "https://www.perplexity.ai/browser/claim/abc123",  # lowercase
            "not-a-url"
        ]
        
        for link in valid_links:
            assert self.classifier._validate_invitation_link(link), f"Should be valid: {link}"
        
        for link in invalid_links:
            assert not self.classifier._validate_invitation_link(link), f"Should be invalid: {link}"
    
    def test_extract_conditions_variations(self):
        """Test extraction of various conditional sharing patterns"""
        test_cases = [
            ("DM me for Comet invite", ["Send DM to author"]),
            ("Follow and DM for access", ["Follow the author", "Send DM to author"]),
            ("Comment below for invite", ["Comment on the post"]),
            ("Like and retweet for Comet access", ["Like the post", "Retweet the post"]),
            ("Follow first then DM", ["Follow the author"]),  # "Follow first" is more specific
            ("Drop your @ below for invite", ["Comment on the post"]),
            ("Must follow for Comet browser invite", ["Follow the author"]),
            ("Some random text about Comet", None)  # No conditional keywords
        ]
        
        for content, expected_conditions in test_cases:
            conditions = self.classifier._extract_conditions(content.lower())
            if expected_conditions is None:
                # For generic cases, we might not extract specific conditions
                assert conditions is None or "Check post" in conditions
            else:
                assert conditions is not None
                for condition in expected_conditions:
                    assert condition in conditions
    
    def test_comet_keyword_detection(self):
        """Test detection of Comet-related keywords"""
        comet_related = [
            "Check out Comet browser!",
            "perplexity browser is amazing",
            "AI browser invitation",
            "comet invite available",
            "perplexity.ai/browser access"
        ]
        
        not_comet_related = [
            "Just a random tweet",
            "Check out this browser extension",
            "AI is the future",
            "Invitation to my party"
        ]
        
        for content in comet_related:
            assert self.classifier._is_comet_related(content.lower())
        
        for content in not_comet_related:
            assert not self.classifier._is_comet_related(content.lower())


class TestPostProcessor:
    """Test cases for PostProcessor"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.processor = PostProcessor()
    
    def test_deduplicate_results(self, sample_search_results):
        """Test deduplication of search results"""
        # Create duplicates
        duplicated_results = sample_search_results + [sample_search_results[0], sample_search_results[1]]
        
        unique_results = self.processor._deduplicate_results(duplicated_results)
        
        assert len(unique_results) == len(sample_search_results)
        tweet_ids = [r.tweet_id for r in unique_results]
        assert len(set(tweet_ids)) == len(tweet_ids)  # All unique
    
    @patch('backend.post_processor.get_db_with_retry')
    @patch('backend.post_processor.is_post_processed')
    def test_filter_new_posts(self, mock_is_processed, mock_get_db):
        """Test filtering of already processed posts"""
        # Mock database
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        # Mock some posts as already processed
        mock_is_processed.side_effect = lambda db, tweet_id: tweet_id in ["1234567890", "1234567892"]
        
        classified_posts = [
            ClassifiedPost("1234567890", "content1", "user1", PostType.FREE, "url1", "link1"),
            ClassifiedPost("1234567891", "content2", "user2", PostType.CONDITIONAL, "url2", conditions="DM me"),
            ClassifiedPost("1234567892", "content3", "user3", PostType.FREE, "url3", "link3"),
            ClassifiedPost("1234567893", "content4", "user4", PostType.CONDITIONAL, "url4", conditions="Follow me")
        ]
        
        new_posts = self.processor._filter_new_posts(classified_posts)
        
        assert len(new_posts) == 2
        assert new_posts[0].tweet_id == "1234567891"
        assert new_posts[1].tweet_id == "1234567893"
        mock_db.close.assert_called_once()
    
    def test_validate_post_data(self):
        """Test post data validation"""
        # Valid post
        valid_post = ClassifiedPost(
            tweet_id="1234567890",
            content="Test content",
            author_username="testuser",
            post_type=PostType.FREE,
            tweet_url="https://x.com/testuser/status/1234567890",
            invitation_link="https://www.perplexity.ai/browser/claim/ABC123"
        )
        assert self.processor._validate_post_data(valid_post)
        
        # Invalid posts
        invalid_posts = [
            # Missing tweet_id
            ClassifiedPost("", "content", "user", PostType.FREE, "https://x.com/user/status/123", "link"),
            # Invalid tweet_id format
            ClassifiedPost("abc123", "content", "user", PostType.FREE, "https://x.com/user/status/123", "link"),
            # Missing content
            ClassifiedPost("123", "", "user", PostType.FREE, "https://x.com/user/status/123", "link"),
            # Free post without invitation link
            ClassifiedPost("123", "content", "user", PostType.FREE, "https://x.com/user/status/123", None),
            # Conditional post without conditions
            ClassifiedPost("123", "content", "user", PostType.CONDITIONAL, "https://x.com/user/status/123", None, None),
            # Invalid URL
            ClassifiedPost("123", "content", "user", PostType.FREE, "not-a-url", "link"),
            # Invalid invitation link
            ClassifiedPost("123", "content", "user", PostType.FREE, "https://x.com/user/status/123", "invalid-link")
        ]
        
        for post in invalid_posts:
            assert not self.processor._validate_post_data(post)
    
    @patch('backend.post_processor.get_db_with_retry')
    @patch('backend.post_processor.is_post_processed')
    @patch('backend.post_processor.add_post')
    def test_process_search_results_integration(self, mock_add_post, mock_is_processed, mock_get_db, sample_search_results):
        """Test complete processing workflow"""
        # Mock database
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_is_processed.return_value = False  # All posts are new
        mock_add_post.return_value = Mock()  # Successful storage
        
        # Create search results by keyword
        search_results_by_keyword = {
            "comet invitation": sample_search_results[:2],
            "perplexity browser": sample_search_results[2:],
            "comet invite": [sample_search_results[0]]  # Duplicate
        }
        
        processed_posts = self.processor.process_search_results(search_results_by_keyword)
        
        # Should have 3 invitation posts (1 free, 2 conditional)
        # sample_search_results[0] = free (has direct link)
        # sample_search_results[1] = conditional (DM me)
        # sample_search_results[2] = not invitation (just mentions Comet)
        # sample_search_results[3] = conditional (follow and comment)
        assert len(processed_posts) == 3
        
        # Check that posts were classified correctly
        free_posts = [p for p in processed_posts if p.post_type == PostType.FREE]
        conditional_posts = [p for p in processed_posts if p.post_type == PostType.CONDITIONAL]
        
        assert len(free_posts) == 1
        assert len(conditional_posts) == 2
        
        # Verify database calls
        assert mock_add_post.call_count == 3


class TestConvenienceFunctions:
    """Test convenience functions"""
    
    @patch('backend.post_processor.PostProcessor')
    def test_process_posts_function(self, mock_processor_class):
        """Test process_posts convenience function"""
        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor
        mock_processor.process_search_results.return_value = ["result1", "result2"]
        
        search_results = {"keyword": []}
        result = process_posts(search_results)
        
        mock_processor_class.assert_called_once()
        mock_processor.process_search_results.assert_called_once_with(search_results)
        assert result == ["result1", "result2"]
    
    @patch('backend.post_processor.PostClassifier')
    def test_classify_single_post_function(self, mock_classifier_class):
        """Test classify_single_post convenience function"""
        mock_classifier = Mock()
        mock_classifier_class.return_value = mock_classifier
        mock_classifier.classify_post.return_value = "classified_result"
        
        search_result = Mock()
        result = classify_single_post(search_result)
        
        mock_classifier_class.assert_called_once()
        mock_classifier.classify_post.assert_called_once_with(search_result)
        assert result == "classified_result"


# Integration tests with real database
class TestDatabaseIntegration:
    """Integration tests with actual database operations"""
    
    @patch('backend.post_processor.get_db_with_retry')
    @patch('backend.post_processor.add_post')
    def test_store_posts_with_database_errors(self, mock_add_post, mock_get_db):
        """Test handling of database errors during post storage"""
        processor = PostProcessor()
        
        # Mock database connection failure
        mock_get_db.return_value = None
        
        posts = [
            ClassifiedPost("123", "content", "user", PostType.FREE, "url", "link")
        ]
        
        stored_posts = processor._store_posts(posts)
        assert len(stored_posts) == 0
        
        # Mock database operation failure
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_add_post.return_value = None  # Simulate failure
        
        stored_posts = processor._store_posts(posts)
        assert len(stored_posts) == 0


# Performance tests
class TestPerformance:
    """Performance-related tests"""
    
    def test_large_dataset_processing(self):
        """Test processing of large datasets"""
        processor = PostProcessor()
        
        # Create large dataset
        large_dataset = []
        for i in range(1000):
            large_dataset.append(SearchResult(
                tweet_id=str(i),
                content=f"Test content {i}",
                author_username=f"user{i}",
                author_id=str(i),
                created_at="2024-01-01T12:00:00Z",
                tweet_url=f"https://x.com/user{i}/status/{i}"
            ))
        
        # Add some duplicates
        large_dataset.extend(large_dataset[:100])
        
        # Test deduplication performance
        unique_results = processor._deduplicate_results(large_dataset)
        assert len(unique_results) == 1000
    
    def test_regex_pattern_performance(self):
        """Test regex pattern matching performance"""
        classifier = PostClassifier()
        
        # Test with many posts
        test_content = [
            "Check out https://www.perplexity.ai/browser/claim/ABC123",
            "DM me for Comet invite",
            "Just a regular tweet about AI",
            "Another tweet with comet browser mention"
        ] * 250  # 1000 posts total
        
        results = []
        for i, content in enumerate(test_content):
            result = SearchResult(
                tweet_id=str(i),
                content=content,
                author_username=f"user{i}",
                author_id=str(i),
                created_at="2024-01-01T12:00:00Z",
                tweet_url=f"https://x.com/user{i}/status/{i}"
            )
            classified = classifier.classify_post(result)
            if classified:
                results.append(classified)
        
        # Should find invitation posts efficiently
        assert len(results) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])