"""
Configuration validation and error handling for Comet Invitation Hunter.

This module provides validation functions for configuration parameters and
graceful fallback mechanisms when configuration imports fail.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

# Default configuration values used as fallbacks
DEFAULT_SEARCH_CONFIG = {
    'SEARCH_KEYWORDS': [
        "perplexity.ai/browser/claim",
        "comet invitation",
        "comet invite", 
        "comet browser invite",
        "comet access",
        "perplexity browser invite",
        "ai browser invite"
    ],
    'MONITORING_INTERVAL': 300,
    'MAX_RESULTS_PER_KEYWORD': 200,
    'SEARCH_PRODUCT': "Latest",
    'API_REQUEST_DELAY': 2,
    'SEARCH_TIME_WINDOW': 300
}

DEFAULT_CLASSIFICATION_PATTERNS = {
    'INVITATION_PATTERNS': [
        r'https://www\.perplexity\.ai/browser/claim/[A-Z0-9]+',
        r'perplexity\.ai/browser/claim/[A-Z0-9]+',
        r'comet.*invitation',
        r'comet.*invite',
        r'comet.*access'
    ],
    'CONDITIONAL_KEYWORDS': [
        'dm me', 'send dm', 'direct message',
        'follow and dm', 'follow me and dm',
        'comment below', 'reply below',
        'retweet and dm', 'rt and dm',
        'follow for invite', 'follow to get',
        'like and dm', 'like and comment'
    ],
    'COMET_KEYWORDS': [
        'comet', 'perplexity browser', 'ai browser',
        'perplexity.ai/browser', 'browser invite'
    ]
}


def validate_search_keywords(keywords: List[str]) -> Tuple[bool, List[str], Optional[str]]:
    """
    Validate search keywords configuration.
    
    Args:
        keywords: List of search keywords to validate
        
    Returns:
        Tuple of (is_valid, validated_keywords, error_message)
    """
    if not isinstance(keywords, list):
        return False, DEFAULT_SEARCH_CONFIG['SEARCH_KEYWORDS'], "SEARCH_KEYWORDS must be a list"
    
    if not keywords:
        return False, DEFAULT_SEARCH_CONFIG['SEARCH_KEYWORDS'], "SEARCH_KEYWORDS cannot be empty"
    
    validated_keywords = []
    for keyword in keywords:
        if not isinstance(keyword, str):
            logger.warning(f"Skipping non-string keyword: {keyword}")
            continue
        
        keyword = keyword.strip()
        if not keyword:
            logger.warning("Skipping empty keyword")
            continue
            
        if len(keyword) > 500:
            logger.warning(f"Keyword too long (>500 chars), truncating: {keyword[:50]}...")
            keyword = keyword[:500]
        
        validated_keywords.append(keyword)
    
    if not validated_keywords:
        return False, DEFAULT_SEARCH_CONFIG['SEARCH_KEYWORDS'], "No valid keywords found after validation"
    
    return True, validated_keywords, None


def validate_monitoring_interval(interval: int) -> Tuple[bool, int, Optional[str]]:
    """
    Validate monitoring interval configuration.
    
    Args:
        interval: Monitoring interval in seconds
        
    Returns:
        Tuple of (is_valid, validated_interval, error_message)
    """
    if not isinstance(interval, (int, float)):
        return False, DEFAULT_SEARCH_CONFIG['MONITORING_INTERVAL'], "MONITORING_INTERVAL must be a number"
    
    interval = int(interval)
    
    if interval < 60:
        logger.warning(f"MONITORING_INTERVAL {interval}s is very short, using minimum of 60s")
        return True, 60, None
    
    if interval > 3600:
        logger.warning(f"MONITORING_INTERVAL {interval}s is very long, using maximum of 3600s")
        return True, 3600, None
    
    return True, interval, None


def validate_max_results(max_results: int) -> Tuple[bool, int, Optional[str]]:
    """
    Validate max results per keyword configuration.
    
    Args:
        max_results: Maximum results per keyword
        
    Returns:
        Tuple of (is_valid, validated_max_results, error_message)
    """
    if not isinstance(max_results, (int, float)):
        return False, DEFAULT_SEARCH_CONFIG['MAX_RESULTS_PER_KEYWORD'], "MAX_RESULTS_PER_KEYWORD must be a number"
    
    max_results = int(max_results)
    
    if max_results < 1:
        return False, DEFAULT_SEARCH_CONFIG['MAX_RESULTS_PER_KEYWORD'], "MAX_RESULTS_PER_KEYWORD must be at least 1"
    
    if max_results > 1000:
        logger.warning(f"MAX_RESULTS_PER_KEYWORD {max_results} is very high, using maximum of 1000")
        return True, 1000, None
    
    return True, max_results, None


def validate_api_delay(delay: float) -> Tuple[bool, float, Optional[str]]:
    """
    Validate API request delay configuration.
    
    Args:
        delay: Delay between API requests in seconds
        
    Returns:
        Tuple of (is_valid, validated_delay, error_message)
    """
    if not isinstance(delay, (int, float)):
        return False, DEFAULT_SEARCH_CONFIG['API_REQUEST_DELAY'], "API_REQUEST_DELAY must be a number"
    
    if delay < 0:
        return False, DEFAULT_SEARCH_CONFIG['API_REQUEST_DELAY'], "API_REQUEST_DELAY cannot be negative"
    
    if delay > 60:
        logger.warning(f"API_REQUEST_DELAY {delay}s is very long, using maximum of 60s")
        return True, 60.0, None
    
    return True, float(delay), None


def validate_search_product(product: str) -> Tuple[bool, str, Optional[str]]:
    """
    Validate search product configuration.
    
    Args:
        product: Search product type
        
    Returns:
        Tuple of (is_valid, validated_product, error_message)
    """
    if not isinstance(product, str):
        return False, DEFAULT_SEARCH_CONFIG['SEARCH_PRODUCT'], "SEARCH_PRODUCT must be a string"
    
    valid_products = ["Latest", "Top", "People", "Photos", "Videos"]
    
    if product not in valid_products:
        logger.warning(f"Invalid SEARCH_PRODUCT '{product}', using 'Latest'. Valid options: {valid_products}")
        return True, "Latest", None
    
    return True, product, None


def validate_regex_patterns(patterns: List[str]) -> Tuple[bool, List[str], Optional[str]]:
    """
    Validate regex patterns for classification.
    
    Args:
        patterns: List of regex patterns to validate
        
    Returns:
        Tuple of (is_valid, validated_patterns, error_message)
    """
    if not isinstance(patterns, list):
        return False, DEFAULT_CLASSIFICATION_PATTERNS['INVITATION_PATTERNS'], "Patterns must be a list"
    
    if not patterns:
        return False, DEFAULT_CLASSIFICATION_PATTERNS['INVITATION_PATTERNS'], "Patterns list cannot be empty"
    
    validated_patterns = []
    for pattern in patterns:
        if not isinstance(pattern, str):
            logger.warning(f"Skipping non-string pattern: {pattern}")
            continue
        
        pattern = pattern.strip()
        if not pattern:
            logger.warning("Skipping empty pattern")
            continue
        
        try:
            # Test if the regex pattern is valid
            re.compile(pattern)
            validated_patterns.append(pattern)
        except re.error as e:
            logger.error(f"Invalid regex pattern '{pattern}': {e}")
            continue
    
    if not validated_patterns:
        return False, DEFAULT_CLASSIFICATION_PATTERNS['INVITATION_PATTERNS'], "No valid regex patterns found"
    
    return True, validated_patterns, None


def validate_keyword_list(keywords: List[str], config_name: str, default_keywords: List[str]) -> Tuple[bool, List[str], Optional[str]]:
    """
    Validate a list of keywords (conditional or comet keywords).
    
    Args:
        keywords: List of keywords to validate
        config_name: Name of the configuration for logging
        default_keywords: Default keywords to use as fallback
        
    Returns:
        Tuple of (is_valid, validated_keywords, error_message)
    """
    if not isinstance(keywords, list):
        return False, default_keywords, f"{config_name} must be a list"
    
    if not keywords:
        return False, default_keywords, f"{config_name} cannot be empty"
    
    validated_keywords = []
    for keyword in keywords:
        if not isinstance(keyword, str):
            logger.warning(f"Skipping non-string keyword in {config_name}: {keyword}")
            continue
        
        keyword = keyword.strip().lower()
        if not keyword:
            logger.warning(f"Skipping empty keyword in {config_name}")
            continue
        
        if len(keyword) > 100:
            logger.warning(f"Keyword too long in {config_name}, truncating: {keyword[:20]}...")
            keyword = keyword[:100]
        
        validated_keywords.append(keyword)
    
    if not validated_keywords:
        return False, default_keywords, f"No valid keywords found in {config_name}"
    
    return True, validated_keywords, None


def validate_search_config(config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate entire search configuration dictionary.
    
    Args:
        config_dict: Dictionary containing search configuration
        
    Returns:
        Dictionary with validated configuration values
    """
    validated_config = {}
    
    # Validate search keywords
    keywords = config_dict.get('SEARCH_KEYWORDS', DEFAULT_SEARCH_CONFIG['SEARCH_KEYWORDS'])
    is_valid, validated_keywords, error = validate_search_keywords(keywords)
    if not is_valid:
        logger.error(f"Search keywords validation failed: {error}")
    validated_config['SEARCH_KEYWORDS'] = validated_keywords
    
    # Validate monitoring interval
    interval = config_dict.get('MONITORING_INTERVAL', DEFAULT_SEARCH_CONFIG['MONITORING_INTERVAL'])
    is_valid, validated_interval, error = validate_monitoring_interval(interval)
    if not is_valid:
        logger.error(f"Monitoring interval validation failed: {error}")
    validated_config['MONITORING_INTERVAL'] = validated_interval
    
    # Validate max results
    max_results = config_dict.get('MAX_RESULTS_PER_KEYWORD', DEFAULT_SEARCH_CONFIG['MAX_RESULTS_PER_KEYWORD'])
    is_valid, validated_max_results, error = validate_max_results(max_results)
    if not is_valid:
        logger.error(f"Max results validation failed: {error}")
    validated_config['MAX_RESULTS_PER_KEYWORD'] = validated_max_results
    
    # Validate API delay
    delay = config_dict.get('API_REQUEST_DELAY', DEFAULT_SEARCH_CONFIG['API_REQUEST_DELAY'])
    is_valid, validated_delay, error = validate_api_delay(delay)
    if not is_valid:
        logger.error(f"API delay validation failed: {error}")
    validated_config['API_REQUEST_DELAY'] = validated_delay
    
    # Validate search product
    product = config_dict.get('SEARCH_PRODUCT', DEFAULT_SEARCH_CONFIG['SEARCH_PRODUCT'])
    is_valid, validated_product, error = validate_search_product(product)
    if not is_valid:
        logger.error(f"Search product validation failed: {error}")
    validated_config['SEARCH_PRODUCT'] = validated_product
    
    # Set search time window (derived from monitoring interval)
    validated_config['SEARCH_TIME_WINDOW'] = validated_config['MONITORING_INTERVAL']
    
    return validated_config


def validate_classification_config(config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate entire classification configuration dictionary.
    
    Args:
        config_dict: Dictionary containing classification configuration
        
    Returns:
        Dictionary with validated configuration values
    """
    validated_config = {}
    
    # Validate invitation patterns
    patterns = config_dict.get('INVITATION_PATTERNS', DEFAULT_CLASSIFICATION_PATTERNS['INVITATION_PATTERNS'])
    is_valid, validated_patterns, error = validate_regex_patterns(patterns)
    if not is_valid:
        logger.error(f"Invitation patterns validation failed: {error}")
    validated_config['INVITATION_PATTERNS'] = validated_patterns
    
    # Validate conditional keywords
    keywords = config_dict.get('CONDITIONAL_KEYWORDS', DEFAULT_CLASSIFICATION_PATTERNS['CONDITIONAL_KEYWORDS'])
    is_valid, validated_keywords, error = validate_keyword_list(
        keywords, 'CONDITIONAL_KEYWORDS', DEFAULT_CLASSIFICATION_PATTERNS['CONDITIONAL_KEYWORDS']
    )
    if not is_valid:
        logger.error(f"Conditional keywords validation failed: {error}")
    validated_config['CONDITIONAL_KEYWORDS'] = validated_keywords
    
    # Validate comet keywords
    keywords = config_dict.get('COMET_KEYWORDS', DEFAULT_CLASSIFICATION_PATTERNS['COMET_KEYWORDS'])
    is_valid, validated_keywords, error = validate_keyword_list(
        keywords, 'COMET_KEYWORDS', DEFAULT_CLASSIFICATION_PATTERNS['COMET_KEYWORDS']
    )
    if not is_valid:
        logger.error(f"Comet keywords validation failed: {error}")
    validated_config['COMET_KEYWORDS'] = validated_keywords
    
    return validated_config


def log_configuration_summary(search_config: Dict[str, Any], classification_config: Dict[str, Any]):
    """
    Log a summary of the configuration values being used.
    
    Args:
        search_config: Validated search configuration
        classification_config: Validated classification configuration
    """
    logger.info("=== CONFIGURATION SUMMARY ===")
    logger.info("Search Configuration:")
    logger.info(f"  - Keywords: {len(search_config['SEARCH_KEYWORDS'])} configured")
    for i, keyword in enumerate(search_config['SEARCH_KEYWORDS'][:5], 1):
        logger.info(f"    {i}. '{keyword}'")
    if len(search_config['SEARCH_KEYWORDS']) > 5:
        logger.info(f"    ... and {len(search_config['SEARCH_KEYWORDS']) - 5} more")
    
    logger.info(f"  - Monitoring interval: {search_config['MONITORING_INTERVAL']} seconds")
    logger.info(f"  - Max results per keyword: {search_config['MAX_RESULTS_PER_KEYWORD']}")
    logger.info(f"  - API request delay: {search_config['API_REQUEST_DELAY']} seconds")
    logger.info(f"  - Search product: {search_config['SEARCH_PRODUCT']}")
    
    logger.info("Classification Configuration:")
    logger.info(f"  - Invitation patterns: {len(classification_config['INVITATION_PATTERNS'])} configured")
    logger.info(f"  - Conditional keywords: {len(classification_config['CONDITIONAL_KEYWORDS'])} configured")
    logger.info(f"  - Comet keywords: {len(classification_config['COMET_KEYWORDS'])} configured")
    logger.info("=== END CONFIGURATION SUMMARY ===")