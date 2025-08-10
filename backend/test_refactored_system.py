#!/usr/bin/env python3
"""
Comprehensive test script to verify the refactored Comet Invitation Hunter system.

This script tests:
1. Monitor service functionality with new configuration structure
2. Search keyword modification and verification
3. Classification pattern modification and verification
4. System produces identical results to original implementation
5. Error handling when configuration files are missing or invalid
"""

import sys
import os
import logging
import tempfile
import shutil
import json
import re
from typing import List, Dict, Any
from unittest.mock import Mock, patch

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

class SystemTester:
    """Comprehensive system tester for the refactored Comet Invitation Hunter."""
    
    def __init__(self):
        self.test_results = []
        self.temp_dirs = []
    
    def log_test_result(self, test_name: str, success: bool, message: str = ""):
        """Log a test result."""
        status = "✓ PASS" if success else "✗ FAIL"
        logger.info(f"{status}: {test_name}")
        if message:
            logger.info(f"    {message}")
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message
        })
    
    def test_monitor_service_functionality(self) -> bool:
        """Test that the monitoring service works with new configuration structure."""
        logger.info("=== Testing Monitor Service Functionality ===")
        
        try:
            # Import the monitor components
            from monitor import main as monitor_main
            CometMonitor = monitor_main.CometMonitor
            PostClassifier = monitor_main.PostClassifier
            
            # Test monitor initialization
            monitor = CometMonitor()
            self.log_test_result("Monitor initialization", True, 
                               f"Monitor created with {len(monitor.search_keywords)} keywords")
            
            # Test classifier initialization
            classifier = PostClassifier()
            self.log_test_result("Classifier initialization", True,
                               f"Classifier created with {len(classifier.invitation_patterns)} patterns")
            
            # Test configuration loading
            has_search_config = hasattr(monitor, 'search_keywords') and len(monitor.search_keywords) > 0
            has_monitoring_interval = hasattr(monitor, 'monitoring_interval') and monitor.monitoring_interval > 0
            
            self.log_test_result("Configuration loading", has_search_config and has_monitoring_interval,
                               f"Keywords: {len(monitor.search_keywords)}, Interval: {monitor.monitoring_interval}s")
            
            return True
            
        except Exception as e:
            self.log_test_result("Monitor service functionality", False, str(e))
            return False
    
    def test_search_keyword_modification(self) -> bool:
        """Test modifying search keywords and verify they are used in searches."""
        logger.info("=== Testing Search Keyword Modification ===")
        
        # Create temporary directory for modified config
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
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
            backend_dir = os.path.dirname(__file__)
            shutil.copy(os.path.join(backend_dir, 'classification_patterns.py'), temp_dir)
            
            # Import and test modified configuration
            import importlib
            if 'search_config' in sys.modules:
                importlib.reload(sys.modules['search_config'])
            
            from search_config import SEARCH_KEYWORDS, MONITORING_INTERVAL
            
            # Verify modifications
            expected_keywords = ["test keyword 1", "test keyword 2", "modified comet invite"]
            keywords_match = SEARCH_KEYWORDS == expected_keywords
            interval_match = MONITORING_INTERVAL == 120
            
            self.log_test_result("Search keyword modification", keywords_match and interval_match,
                               f"Keywords: {SEARCH_KEYWORDS}, Interval: {MONITORING_INTERVAL}")
            
            # Test that monitor uses modified config
            from monitor import main as monitor_main
            CometMonitor = monitor_main.CometMonitor
            monitor = CometMonitor()
            
            monitor_uses_modified = monitor.search_keywords == expected_keywords
            self.log_test_result("Monitor uses modified keywords", monitor_uses_modified,
                               f"Monitor keywords: {monitor.search_keywords}")
            
            return keywords_match and interval_match and monitor_uses_modified
            
        except Exception as e:
            self.log_test_result("Search keyword modification", False, str(e))
            return False
        finally:
            # Clean up path
            if temp_dir in sys.path:
                sys.path.remove(temp_dir)
    
    def test_classification_pattern_modification(self) -> bool:
        """Test modifying classification patterns and verify they affect post classification."""
        logger.info("=== Testing Classification Pattern Modification ===")
        
        # Create temporary directory for modified config
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
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
            backend_dir = os.path.dirname(__file__)
            shutil.copy(os.path.join(backend_dir, 'search_config.py'), temp_dir)
            
            # Import and test modified configuration
            import importlib
            if 'classification_patterns' in sys.modules:
                importlib.reload(sys.modules['classification_patterns'])
            
            from classification_patterns import INVITATION_PATTERNS, CONDITIONAL_KEYWORDS, COMET_KEYWORDS
            
            # Verify modifications
            expected_patterns = [r'test.*invitation.*link', r'modified.*pattern']
            expected_conditional = ['test dm me', 'modified follow']
            expected_comet = ['test comet', 'modified browser']
            
            patterns_match = INVITATION_PATTERNS == expected_patterns
            conditional_match = CONDITIONAL_KEYWORDS == expected_conditional
            comet_match = COMET_KEYWORDS == expected_comet
            
            self.log_test_result("Classification pattern modification", 
                               patterns_match and conditional_match and comet_match,
                               f"Patterns: {len(INVITATION_PATTERNS)}, Keywords: {len(CONDITIONAL_KEYWORDS)}")
            
            # Test that classifier uses modified patterns
            from monitor import main as monitor_main
            PostClassifier = monitor_main.PostClassifier
            classifier = PostClassifier()
            
            classifier_uses_modified = (classifier.invitation_patterns == expected_patterns and
                                      classifier.conditional_keywords == expected_conditional and
                                      classifier.comet_keywords == expected_comet)
            
            self.log_test_result("Classifier uses modified patterns", classifier_uses_modified,
                               f"Classifier patterns: {len(classifier.invitation_patterns)}")
            
            return patterns_match and conditional_match and comet_match and classifier_uses_modified
            
        except Exception as e:
            self.log_test_result("Classification pattern modification", False, str(e))
            return False
        finally:
            # Clean up path
            if temp_dir in sys.path:
                sys.path.remove(temp_dir)
    
    def test_identical_results_to_original(self) -> bool:
        """Test that the system produces identical results to the original implementation."""
        logger.info("=== Testing Identical Results to Original Implementation ===")
        
        try:
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
            
            # Test classification with current implementation
            from monitor import main as monitor_main
            PostClassifier = monitor_main.PostClassifier
            classifier = PostClassifier()
            
            classified_posts = []
            for result in mock_search_results:
                classified = classifier.classify_post(result)
                if classified:
                    classified_posts.append(classified)
            
            # Verify expected classifications
            expected_classifications = 2  # First two posts should be classified
            actual_classifications = len(classified_posts)
            
            classifications_match = actual_classifications == expected_classifications
            self.log_test_result("Classification results match expected", classifications_match,
                               f"Expected: {expected_classifications}, Actual: {actual_classifications}")
            
            # Verify post types
            if classified_posts:
                first_post_type = classified_posts[0].post_type
                first_is_free = first_post_type == 'free'
                self.log_test_result("Free invitation detected correctly", first_is_free,
                                   f"First post type: {first_post_type}")
                
                if len(classified_posts) > 1:
                    second_post_type = classified_posts[1].post_type
                    second_is_conditional = second_post_type == 'conditional'
                    self.log_test_result("Conditional invitation detected correctly", second_is_conditional,
                                       f"Second post type: {second_post_type}")
                    
                    return classifications_match and first_is_free and second_is_conditional
                
                return classifications_match and first_is_free
            
            return classifications_match
            
        except Exception as e:
            self.log_test_result("Identical results to original", False, str(e))
            return False
    
    def test_error_handling_missing_config(self) -> bool:
        """Test error handling when configuration files are missing."""
        logger.info("=== Testing Error Handling for Missing Configuration ===")
        
        # Create temporary directory without config files
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        sys.path.insert(0, temp_dir)
        
        try:
            # Remove any existing modules from cache
            modules_to_remove = [mod for mod in sys.modules.keys() 
                               if mod in ['search_config', 'classification_patterns', 'monitor.main']]
            for mod in modules_to_remove:
                del sys.modules[mod]
            
            # Try to import monitor with missing config files
            from monitor import main as monitor_main
            CometMonitor = monitor_main.CometMonitor
            PostClassifier = monitor_main.PostClassifier
            
            # Test that monitor still works with fallback values
            monitor = CometMonitor()
            has_fallback_keywords = len(monitor.search_keywords) > 0
            has_fallback_interval = monitor.monitoring_interval > 0
            
            self.log_test_result("Monitor fallback with missing config", 
                               has_fallback_keywords and has_fallback_interval,
                               f"Fallback keywords: {len(monitor.search_keywords)}")
            
            # Test that classifier still works with fallback values
            classifier = PostClassifier()
            has_fallback_patterns = len(classifier.invitation_patterns) > 0
            has_fallback_keywords = len(classifier.conditional_keywords) > 0
            
            self.log_test_result("Classifier fallback with missing config",
                               has_fallback_patterns and has_fallback_keywords,
                               f"Fallback patterns: {len(classifier.invitation_patterns)}")
            
            return (has_fallback_keywords and has_fallback_interval and 
                   has_fallback_patterns and has_fallback_keywords)
            
        except Exception as e:
            self.log_test_result("Error handling missing config", False, str(e))
            return False
        finally:
            # Clean up path
            if temp_dir in sys.path:
                sys.path.remove(temp_dir)
    
    def test_error_handling_invalid_config(self) -> bool:
        """Test error handling when configuration files contain invalid data."""
        logger.info("=== Testing Error Handling for Invalid Configuration ===")
        
        # Create temporary directory with invalid config files
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        sys.path.insert(0, temp_dir)
        
        try:
            # Create invalid search config
            invalid_search_config = '''
# Invalid search configuration that will cause errors
SEARCH_KEYWORDS = "not a list"  # Should be a list
MONITORING_INTERVAL = "not a number"  # Should be a number
MAX_RESULTS_PER_KEYWORD = -1  # Invalid value
SEARCH_PRODUCT = None  # Invalid value
API_REQUEST_DELAY = "invalid"  # Should be a number
SEARCH_TIME_WINDOW = None  # Invalid value
'''
            
            # Create invalid classification config
            invalid_classification_config = '''
# Invalid classification configuration
INVITATION_PATTERNS = ["[invalid regex"]  # Invalid regex pattern
CONDITIONAL_KEYWORDS = None  # Should be a list
COMET_KEYWORDS = "not a list"  # Should be a list
'''
            
            # Write invalid configs
            with open(os.path.join(temp_dir, 'search_config.py'), 'w') as f:
                f.write(invalid_search_config)
            
            with open(os.path.join(temp_dir, 'classification_patterns.py'), 'w') as f:
                f.write(invalid_classification_config)
            
            # Copy config_validation.py if it exists
            backend_dir = os.path.dirname(__file__)
            config_validation_path = os.path.join(backend_dir, 'config_validation.py')
            if os.path.exists(config_validation_path):
                shutil.copy(config_validation_path, temp_dir)
            
            # Remove any existing modules from cache
            modules_to_remove = [mod for mod in sys.modules.keys() 
                               if mod in ['search_config', 'classification_patterns', 'monitor.main']]
            for mod in modules_to_remove:
                del sys.modules[mod]
            
            # Try to import monitor with invalid config files
            from monitor import main as monitor_main
            CometMonitor = monitor_main.CometMonitor
            PostClassifier = monitor_main.PostClassifier
            
            # Test that monitor still works despite invalid config
            monitor = CometMonitor()
            monitor_works = (hasattr(monitor, 'search_keywords') and 
                           len(monitor.search_keywords) > 0 and
                           hasattr(monitor, 'monitoring_interval') and
                           monitor.monitoring_interval > 0)
            
            self.log_test_result("Monitor handles invalid config", monitor_works,
                               f"Monitor created with {len(monitor.search_keywords)} keywords")
            
            # Test that classifier still works despite invalid config
            classifier = PostClassifier()
            classifier_works = (hasattr(classifier, 'invitation_patterns') and
                              len(classifier.invitation_patterns) > 0 and
                              hasattr(classifier, 'conditional_keywords') and
                              len(classifier.conditional_keywords) > 0)
            
            self.log_test_result("Classifier handles invalid config", classifier_works,
                               f"Classifier created with {len(classifier.invitation_patterns)} patterns")
            
            return monitor_works and classifier_works
            
        except Exception as e:
            self.log_test_result("Error handling invalid config", False, str(e))
            return False
        finally:
            # Clean up path
            if temp_dir in sys.path:
                sys.path.remove(temp_dir)
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return summary."""
        logger.info("Starting comprehensive system testing...")
        
        # Run all tests
        tests = [
            self.test_monitor_service_functionality,
            self.test_search_keyword_modification,
            self.test_classification_pattern_modification,
            self.test_identical_results_to_original,
            self.test_error_handling_missing_config,
            self.test_error_handling_invalid_config
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                logger.error(f"Test {test.__name__} failed with exception: {e}")
        
        # Calculate summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        summary = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            'results': self.test_results
        }
        
        return summary
    
    def cleanup(self):
        """Clean up temporary directories."""
        for temp_dir in self.temp_dirs:
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Failed to clean up temp directory {temp_dir}: {e}")

def main():
    """Run comprehensive system tests."""
    tester = SystemTester()
    
    try:
        summary = tester.run_all_tests()
        
        # Print summary
        logger.info("=" * 60)
        logger.info("COMPREHENSIVE SYSTEM TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Tests: {summary['total_tests']}")
        logger.info(f"Passed: {summary['passed_tests']}")
        logger.info(f"Failed: {summary['failed_tests']}")
        logger.info(f"Success Rate: {summary['success_rate']:.1f}%")
        
        if summary['failed_tests'] > 0:
            logger.info("\nFailed Tests:")
            for result in summary['results']:
                if not result['success']:
                    logger.info(f"  - {result['test']}: {result['message']}")
        
        logger.info("=" * 60)
        
        # Return appropriate exit code
        return 0 if summary['failed_tests'] == 0 else 1
        
    finally:
        tester.cleanup()

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)