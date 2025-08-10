#!/usr/bin/env python3
"""
Test script to verify the monitor service works with the new configuration structure.
This test mocks external dependencies to focus on configuration loading and basic functionality.
"""

import sys
import os
import logging
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock

# Add paths
backend_dir = os.path.dirname(__file__)
root_dir = os.path.dirname(backend_dir)
monitor_dir = os.path.join(root_dir, 'monitor')
sys.path.append(backend_dir)
sys.path.append(root_dir)
sys.path.append(monitor_dir)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_monitor_service_with_current_config():
    """Test that the monitor service works with current configuration."""
    logger.info("=== Testing Monitor Service with Current Configuration ===")
    
    try:
        # Mock resend module before importing monitor
        sys.modules['resend'] = __import__('mock_resend')
        
        # Mock external dependencies
        with patch('monitor.main.get_db_with_retry', return_value=Mock()), \
             patch('monitor.main.config') as mock_config:
            
            # Set up mock config
            mock_config.utools_api_key = 'test-key'
            mock_config.utools_base_url = 'https://test.com'
            mock_config.resend_api_key = 'test-resend-key'
            mock_config.from_email = 'test@example.com'
            mock_config.log_level = 'INFO'
            
            # Import and test monitor components
            from monitor import main as monitor_main
            
            # Test monitor initialization
            monitor = monitor_main.CometMonitor()
            logger.info(f"✓ Monitor initialized with {len(monitor.search_keywords)} keywords")
            logger.info(f"  - Monitoring interval: {monitor.monitoring_interval}s")
            logger.info(f"  - Max results per keyword: {monitor.max_results_per_keyword}")
            
            # Test classifier initialization
            classifier = monitor_main.PostClassifier()
            logger.info(f"✓ Classifier initialized with {len(classifier.invitation_patterns)} patterns")
            logger.info(f"  - Conditional keywords: {len(classifier.conditional_keywords)}")
            logger.info(f"  - Comet keywords: {len(classifier.comet_keywords)}")
            
            # Test that configuration values are loaded correctly
            assert len(monitor.search_keywords) > 0, "Search keywords should not be empty"
            assert monitor.monitoring_interval > 0, "Monitoring interval should be positive"
            assert len(classifier.invitation_patterns) > 0, "Invitation patterns should not be empty"
            
            logger.info("✓ Monitor service test with current configuration passed")
            return True
            
    except Exception as e:
        logger.error(f"✗ Monitor service test failed: {e}")
        return False

def test_search_keyword_modification():
    """Test that modifying search keywords affects the monitor service."""
    logger.info("=== Testing Search Keyword Modification ===")
    
    # Create temporary directory for modified config
    temp_dir = tempfile.mkdtemp()
    sys.path.insert(0, temp_dir)
    
    try:
        # Create modified search config
        modified_config = '''
"""Modified search configuration for testing."""

_RAW_SEARCH_KEYWORDS = [
    "test keyword 1",
    "test keyword 2", 
    "modified comet invite"
]

_RAW_MONITORING_INTERVAL = 120
_RAW_MAX_RESULTS_PER_KEYWORD = 50
_RAW_SEARCH_PRODUCT = "Latest"
_RAW_API_REQUEST_DELAY = 1

# Simple export without validation for testing
SEARCH_KEYWORDS = _RAW_SEARCH_KEYWORDS
MONITORING_INTERVAL = _RAW_MONITORING_INTERVAL
MAX_RESULTS_PER_KEYWORD = _RAW_MAX_RESULTS_PER_KEYWORD
SEARCH_PRODUCT = _RAW_SEARCH_PRODUCT
API_REQUEST_DELAY = _RAW_API_REQUEST_DELAY
SEARCH_TIME_WINDOW = _RAW_MONITORING_INTERVAL
'''
        
        # Write modified config
        with open(os.path.join(temp_dir, 'search_config.py'), 'w') as f:
            f.write(modified_config)
        
        # Copy classification patterns to temp dir
        shutil.copy(os.path.join(backend_dir, 'classification_patterns.py'), temp_dir)
        
        # Clear module cache
        modules_to_remove = [mod for mod in sys.modules.keys() 
                           if mod in ['search_config', 'monitor.main']]
        for mod in modules_to_remove:
            del sys.modules[mod]
        
        # Mock resend module before importing monitor
        sys.modules['resend'] = __import__('mock_resend')
        
        # Mock external dependencies and test
        with patch('monitor.main.get_db_with_retry', return_value=Mock()), \
             patch('monitor.main.config') as mock_config:
            
            # Set up mock config
            mock_config.utools_api_key = 'test-key'
            mock_config.utools_base_url = 'https://test.com'
            mock_config.resend_api_key = 'test-resend-key'
            mock_config.from_email = 'test@example.com'
            mock_config.log_level = 'INFO'
            
            # Import modified configuration
            from search_config import SEARCH_KEYWORDS, MONITORING_INTERVAL
            
            # Verify modifications
            expected_keywords = ["test keyword 1", "test keyword 2", "modified comet invite"]
            assert SEARCH_KEYWORDS == expected_keywords, f"Expected {expected_keywords}, got {SEARCH_KEYWORDS}"
            assert MONITORING_INTERVAL == 120, f"Expected 120, got {MONITORING_INTERVAL}"
            
            # Test that monitor uses modified config
            from monitor import main as monitor_main
            monitor = monitor_main.CometMonitor()
            
            assert monitor.search_keywords == expected_keywords, "Monitor should use modified keywords"
            assert monitor.monitoring_interval == 120, "Monitor should use modified interval"
            
            logger.info(f"✓ Search keyword modification test passed")
            logger.info(f"  - Modified keywords: {monitor.search_keywords}")
            logger.info(f"  - Modified interval: {monitor.monitoring_interval}s")
            return True
            
    except Exception as e:
        logger.error(f"✗ Search keyword modification test failed: {e}")
        return False
    finally:
        # Clean up
        if temp_dir in sys.path:
            sys.path.remove(temp_dir)
        shutil.rmtree(temp_dir)

def test_classification_pattern_modification():
    """Test that modifying classification patterns affects the classifier."""
    logger.info("=== Testing Classification Pattern Modification ===")
    
    # Create temporary directory for modified config
    temp_dir = tempfile.mkdtemp()
    sys.path.insert(0, temp_dir)
    
    try:
        # Create modified classification config
        modified_config = '''
"""Modified classification patterns for testing."""

_RAW_INVITATION_PATTERNS = [
    r'test.*invitation.*link',
    r'modified.*pattern'
]

_RAW_CONDITIONAL_KEYWORDS = [
    'test dm me',
    'modified follow'
]

_RAW_COMET_KEYWORDS = [
    'test comet',
    'modified browser'
]

# Simple export without validation for testing
INVITATION_PATTERNS = _RAW_INVITATION_PATTERNS
CONDITIONAL_KEYWORDS = _RAW_CONDITIONAL_KEYWORDS
COMET_KEYWORDS = _RAW_COMET_KEYWORDS
'''
        
        # Write modified config
        with open(os.path.join(temp_dir, 'classification_patterns.py'), 'w') as f:
            f.write(modified_config)
        
        # Copy search config to temp dir
        shutil.copy(os.path.join(backend_dir, 'search_config.py'), temp_dir)
        
        # Clear module cache
        modules_to_remove = [mod for mod in sys.modules.keys() 
                           if mod in ['classification_patterns', 'monitor.main']]
        for mod in modules_to_remove:
            del sys.modules[mod]
        
        # Mock resend module before importing monitor
        sys.modules['resend'] = __import__('mock_resend')
        
        # Mock external dependencies and test
        with patch('monitor.main.get_db_with_retry', return_value=Mock()), \
             patch('monitor.main.config') as mock_config:
            
            # Set up mock config
            mock_config.utools_api_key = 'test-key'
            mock_config.utools_base_url = 'https://test.com'
            mock_config.resend_api_key = 'test-resend-key'
            mock_config.from_email = 'test@example.com'
            mock_config.log_level = 'INFO'
            
            # Import modified configuration
            from classification_patterns import INVITATION_PATTERNS, CONDITIONAL_KEYWORDS, COMET_KEYWORDS
            
            # Verify modifications
            expected_patterns = [r'test.*invitation.*link', r'modified.*pattern']
            expected_conditional = ['test dm me', 'modified follow']
            expected_comet = ['test comet', 'modified browser']
            
            assert INVITATION_PATTERNS == expected_patterns, f"Expected {expected_patterns}, got {INVITATION_PATTERNS}"
            assert CONDITIONAL_KEYWORDS == expected_conditional, f"Expected {expected_conditional}, got {CONDITIONAL_KEYWORDS}"
            assert COMET_KEYWORDS == expected_comet, f"Expected {expected_comet}, got {COMET_KEYWORDS}"
            
            # Test that classifier uses modified patterns
            from monitor import main as monitor_main
            classifier = monitor_main.PostClassifier()
            
            assert classifier.invitation_patterns == expected_patterns, "Classifier should use modified patterns"
            assert classifier.conditional_keywords == expected_conditional, "Classifier should use modified conditional keywords"
            assert classifier.comet_keywords == expected_comet, "Classifier should use modified comet keywords"
            
            logger.info(f"✓ Classification pattern modification test passed")
            logger.info(f"  - Modified patterns: {len(classifier.invitation_patterns)}")
            logger.info(f"  - Modified conditional keywords: {len(classifier.conditional_keywords)}")
            logger.info(f"  - Modified comet keywords: {len(classifier.comet_keywords)}")
            return True
            
    except Exception as e:
        logger.error(f"✗ Classification pattern modification test failed: {e}")
        return False
    finally:
        # Clean up
        if temp_dir in sys.path:
            sys.path.remove(temp_dir)
        shutil.rmtree(temp_dir)

def test_post_classification():
    """Test that post classification works correctly with the refactored system."""
    logger.info("=== Testing Post Classification ===")
    
    try:
        # Clear module cache to ensure we get fresh imports
        modules_to_remove = [mod for mod in sys.modules.keys() 
                           if mod in ['search_config', 'classification_patterns', 'monitor.main']]
        for mod in modules_to_remove:
            del sys.modules[mod]
        
        # Mock resend module before importing monitor
        sys.modules['resend'] = __import__('mock_resend')
        
        # Mock external dependencies
        with patch('monitor.main.get_db_with_retry', return_value=Mock()), \
             patch('monitor.main.config') as mock_config:
            
            # Set up mock config
            mock_config.utools_api_key = 'test-key'
            mock_config.utools_base_url = 'https://test.com'
            mock_config.resend_api_key = 'test-resend-key'
            mock_config.from_email = 'test@example.com'
            mock_config.log_level = 'INFO'
            
            # Import classifier with original configuration
            from monitor import main as monitor_main
            classifier = monitor_main.PostClassifier()
            
            # Create mock search results for testing
            mock_search_results = [
                Mock(
                    tweet_id="1",
                    content="Check out this comet invitation link: https://www.perplexity.ai/browser/claim/ABC123",
                    author_username="user1",
                    tweet_url="https://twitter.com/user1/status/1",
                    created_at="2024-01-01T12:00:00Z"
                ),
                Mock(
                    tweet_id="2", 
                    content="I have comet invites! DM me for access to the browser",
                    author_username="user2",
                    tweet_url="https://twitter.com/user2/status/2",
                    created_at="2024-01-01T12:01:00Z"
                ),
                Mock(
                    tweet_id="3",
                    content="Just got my new phone, loving it!",
                    author_username="user3", 
                    tweet_url="https://twitter.com/user3/status/3",
                    created_at="2024-01-01T12:02:00Z"
                )
            ]
            
            # Test classification
            classified_posts = []
            for result in mock_search_results:
                classified = classifier.classify_post(result)
                if classified:
                    classified_posts.append(classified)
            
            # Verify classifications
            assert len(classified_posts) == 2, f"Expected 2 classified posts, got {len(classified_posts)}"
            
            # Check first post (should be free)
            first_post = classified_posts[0]
            assert first_post.post_type == 'free', f"First post should be 'free', got '{first_post.post_type}'"
            assert first_post.invitation_link is not None, "First post should have invitation link"
            
            # Check second post (should be conditional)
            second_post = classified_posts[1]
            assert second_post.post_type == 'conditional', f"Second post should be 'conditional', got '{second_post.post_type}'"
            assert second_post.conditions is not None, "Second post should have conditions"
            
            logger.info(f"✓ Post classification test passed")
            logger.info(f"  - Classified {len(classified_posts)} posts")
            logger.info(f"  - Free posts: {sum(1 for p in classified_posts if p.post_type == 'free')}")
            logger.info(f"  - Conditional posts: {sum(1 for p in classified_posts if p.post_type == 'conditional')}")
            return True
            
    except Exception as e:
        logger.error(f"✗ Post classification test failed: {e}")
        return False

def main():
    """Run monitor service tests."""
    logger.info("Starting monitor service tests...")
    
    tests = [
        test_monitor_service_with_current_config,
        test_search_keyword_modification,
        test_classification_pattern_modification,
        test_post_classification
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            logger.error(f"Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    # Calculate summary
    total_tests = len(results)
    passed_tests = sum(results)
    failed_tests = total_tests - passed_tests
    
    logger.info("=" * 60)
    logger.info("MONITOR SERVICE TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total Tests: {total_tests}")
    logger.info(f"Passed: {passed_tests}")
    logger.info(f"Failed: {failed_tests}")
    logger.info(f"Success Rate: {(passed_tests / total_tests * 100):.1f}%")
    logger.info("=" * 60)
    
    return 0 if failed_tests == 0 else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)