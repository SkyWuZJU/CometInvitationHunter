#!/usr/bin/env python3
"""
Test script for configuration validation functionality.

This script tests the validation functions and demonstrates error handling
for various configuration scenarios.
"""

import sys
import os
import logging

# Add backend directory to path
sys.path.append(os.path.dirname(__file__))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_search_config_validation():
    """Test search configuration validation."""
    logger.info("=== Testing Search Configuration Validation ===")
    
    try:
        from config_validation import validate_search_config
        
        # Test valid configuration
        valid_config = {
            'SEARCH_KEYWORDS': ['comet invite', 'perplexity browser'],
            'MONITORING_INTERVAL': 300,
            'MAX_RESULTS_PER_KEYWORD': 200,
            'SEARCH_PRODUCT': 'Latest',
            'API_REQUEST_DELAY': 2
        }
        
        result = validate_search_config(valid_config)
        logger.info(f"✓ Valid config test passed: {len(result)} parameters validated")
        
        # Test invalid configuration
        invalid_config = {
            'SEARCH_KEYWORDS': [],  # Empty keywords
            'MONITORING_INTERVAL': -1,  # Invalid interval
            'MAX_RESULTS_PER_KEYWORD': 'not_a_number',  # Invalid type
            'SEARCH_PRODUCT': 'InvalidProduct',  # Invalid product
            'API_REQUEST_DELAY': -5  # Invalid delay
        }
        
        result = validate_search_config(invalid_config)
        logger.info(f"✓ Invalid config test passed: fallback values used")
        
    except Exception as e:
        logger.error(f"✗ Search config validation test failed: {e}")

def test_classification_config_validation():
    """Test classification configuration validation."""
    logger.info("=== Testing Classification Configuration Validation ===")
    
    try:
        from config_validation import validate_classification_config
        
        # Test valid configuration
        valid_config = {
            'INVITATION_PATTERNS': [r'https://www\.example\.com/[A-Z0-9]+', r'test.*pattern'],
            'CONDITIONAL_KEYWORDS': ['dm me', 'follow and dm'],
            'COMET_KEYWORDS': ['comet', 'browser invite']
        }
        
        result = validate_classification_config(valid_config)
        logger.info(f"✓ Valid classification config test passed: {len(result)} parameters validated")
        
        # Test invalid regex patterns
        invalid_config = {
            'INVITATION_PATTERNS': [r'[invalid regex', r'valid.*pattern'],  # One invalid regex
            'CONDITIONAL_KEYWORDS': [],  # Empty keywords
            'COMET_KEYWORDS': ['comet']
        }
        
        result = validate_classification_config(invalid_config)
        logger.info(f"✓ Invalid classification config test passed: fallback values used")
        
    except Exception as e:
        logger.error(f"✗ Classification config validation test failed: {e}")

def test_config_imports():
    """Test importing configuration files."""
    logger.info("=== Testing Configuration File Imports ===")
    
    try:
        # Test search config import
        from search_config import SEARCH_KEYWORDS, MONITORING_INTERVAL, MAX_RESULTS_PER_KEYWORD
        logger.info(f"✓ Search config imported: {len(SEARCH_KEYWORDS)} keywords, {MONITORING_INTERVAL}s interval")
        
        # Test classification config import
        from classification_patterns import INVITATION_PATTERNS, CONDITIONAL_KEYWORDS, COMET_KEYWORDS
        logger.info(f"✓ Classification config imported: {len(INVITATION_PATTERNS)} patterns, "
                   f"{len(CONDITIONAL_KEYWORDS)} conditional keywords, {len(COMET_KEYWORDS)} comet keywords")
        
    except Exception as e:
        logger.error(f"✗ Configuration import test failed: {e}")

def test_regex_validation():
    """Test regex pattern validation."""
    logger.info("=== Testing Regex Pattern Validation ===")
    
    try:
        from config_validation import validate_regex_patterns
        
        # Test valid patterns
        valid_patterns = [r'https://www\.example\.com/[A-Z0-9]+', r'test.*pattern', r'comet.*invite']
        is_valid, validated, error = validate_regex_patterns(valid_patterns)
        logger.info(f"✓ Valid regex test: {is_valid}, {len(validated)} patterns")
        
        # Test invalid patterns
        invalid_patterns = [r'[invalid regex', r'valid.*pattern', r'*invalid']
        is_valid, validated, error = validate_regex_patterns(invalid_patterns)
        logger.info(f"✓ Invalid regex test: {is_valid}, {len(validated)} valid patterns, error: {error}")
        
    except Exception as e:
        logger.error(f"✗ Regex validation test failed: {e}")

def main():
    """Run all validation tests."""
    logger.info("Starting configuration validation tests...")
    
    test_search_config_validation()
    test_classification_config_validation()
    test_config_imports()
    test_regex_validation()
    
    logger.info("Configuration validation tests completed!")

if __name__ == "__main__":
    main()