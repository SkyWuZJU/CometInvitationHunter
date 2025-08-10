#!/usr/bin/env python3
"""
Test script to verify monitor configuration loading without external dependencies.
"""

import sys
import os
import logging

# Add paths
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'monitor'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_configuration_loading():
    """Test that configuration loading works as expected."""
    logger.info("=== Testing Monitor Configuration Loading ===")
    
    try:
        # Test the configuration import logic from monitor/main.py
        # Import centralized search configuration with graceful fallback
        try:
            from search_config import (
                SEARCH_KEYWORDS, 
                MONITORING_INTERVAL, 
                MAX_RESULTS_PER_KEYWORD,
                SEARCH_PRODUCT,
                API_REQUEST_DELAY
            )
            logger.info("✓ Successfully imported centralized search configuration")
            search_config_loaded = True
        except ImportError as e:
            logger.warning(f"Failed to import search configuration: {e}. Using default values.")
            search_config_loaded = False
            # Fallback to default values if import fails
            SEARCH_KEYWORDS = [
                "perplexity.ai/browser/claim",
                "comet invitation",
                "comet invite", 
                "comet browser invite",
                "comet access",
                "perplexity browser invite",
                "ai browser invite"
            ]
            MONITORING_INTERVAL = 300
            MAX_RESULTS_PER_KEYWORD = 200
            SEARCH_PRODUCT = "Latest"
            API_REQUEST_DELAY = 2
        except Exception as e:
            logger.error(f"Unexpected error importing search configuration: {e}. Using default values.")
            search_config_loaded = False

        # Import centralized classification patterns with graceful fallback
        try:
            from classification_patterns import (
                INVITATION_PATTERNS,
                CONDITIONAL_KEYWORDS,
                COMET_KEYWORDS
            )
            logger.info("✓ Successfully imported centralized classification patterns")
            classification_config_loaded = True
        except ImportError as e:
            logger.warning(f"Failed to import classification patterns: {e}. Using default values.")
            classification_config_loaded = False
            # Fallback to default values if import fails
            INVITATION_PATTERNS = [
                r'https://www\.perplexity\.ai/browser/claim/[A-Z0-9]+',
                r'perplexity\.ai/browser/claim/[A-Z0-9]+',
                r'comet.*invitation',
                r'comet.*invite',
                r'comet.*access'
            ]
            CONDITIONAL_KEYWORDS = [
                'dm me', 'send dm', 'direct message',
                'follow and dm', 'follow me and dm',
                'comment below', 'reply below',
                'retweet and dm', 'rt and dm',
                'follow for invite', 'follow to get',
                'like and dm', 'like and comment'
            ]
            COMET_KEYWORDS = [
                'comet', 'perplexity browser', 'ai browser',
                'perplexity.ai/browser', 'browser invite'
            ]
        except Exception as e:
            logger.error(f"Unexpected error importing classification patterns: {e}. Using default values.")
            classification_config_loaded = False

        # Log configuration status
        logger.info("Configuration Loading Results:")
        logger.info(f"  - Search config loaded: {search_config_loaded}")
        logger.info(f"  - Classification config loaded: {classification_config_loaded}")
        logger.info(f"  - Search keywords: {len(SEARCH_KEYWORDS)} configured")
        logger.info(f"  - Monitoring interval: {MONITORING_INTERVAL} seconds")
        logger.info(f"  - Invitation patterns: {len(INVITATION_PATTERNS)} configured")
        logger.info(f"  - Conditional keywords: {len(CONDITIONAL_KEYWORDS)} configured")
        
        # Test regex pattern validation
        import re
        valid_patterns = []
        for pattern in INVITATION_PATTERNS:
            try:
                re.compile(pattern)
                valid_patterns.append(pattern)
            except re.error as e:
                logger.error(f"Invalid regex pattern: '{pattern}' - {e}")
        
        logger.info(f"  - Valid regex patterns: {len(valid_patterns)} out of {len(INVITATION_PATTERNS)}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Configuration loading test failed: {e}")
        return False

def main():
    """Run configuration loading test."""
    logger.info("Starting monitor configuration loading test...")
    
    success = test_configuration_loading()
    
    if success:
        logger.info("✓ Monitor configuration loading test completed successfully!")
    else:
        logger.error("✗ Monitor configuration loading test failed!")

if __name__ == "__main__":
    main()