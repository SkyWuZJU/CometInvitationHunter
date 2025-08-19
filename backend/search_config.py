"""
Centralized search configuration for Comet Invitation Hunter.

This file contains all search keywords and monitoring parameters used by the system.
Modify these values to adjust search strategy without changing code in multiple locations.
"""

import logging
from typing import Dict, Any

# Configure logging for this module
logger = logging.getLogger(__name__)

# Raw configuration values - modify these to adjust search strategy
# These will be validated and potentially adjusted during import

# Search Keywords - Modify these to adjust search strategy
# These keywords are used to search for Comet invitation posts on X/Twitter
# Each keyword should be specific enough to find relevant posts but broad enough to catch variations
_RAW_SEARCH_KEYWORDS = [
    "perplexity.ai/browser/claim", 
    "comet invitation",
    "comet invite",
    # "comet browser invite",
    # "comet access",
    "perplexity browser invite",
    "perplexity browser invitation",
    # "ai browser invite"
]

# Monitoring Parameters
# These control how often the system checks for new posts and API behavior

# How often to run monitoring cycles (in seconds)
_RAW_MONITORING_INTERVAL = 360

# Maximum number of search results to retrieve per keyword
# Default: 200 results per keyword
# Higher values get more comprehensive results but use more API quota
_RAW_MAX_RESULTS_PER_KEYWORD = 200

# Which Twitter product to search (Latest, Top, etc.)
# Default: "Latest" for most recent posts
# Options: "Latest", "Top", "People", "Photos", "Videos"
_RAW_SEARCH_PRODUCT = "Latest"

# Delay between keyword searches (in seconds)
# Default: 2 seconds between searches
# Increase if hitting rate limits, decrease for faster processing
_RAW_API_REQUEST_DELAY = 3

# Validate configuration and export validated values
def _validate_and_export_config() -> Dict[str, Any]:
    """Validate configuration values and return validated config."""
    try:
        from config_validation import validate_search_config
        
        raw_config = {
            'SEARCH_KEYWORDS': _RAW_SEARCH_KEYWORDS,
            'MONITORING_INTERVAL': _RAW_MONITORING_INTERVAL,
            'MAX_RESULTS_PER_KEYWORD': _RAW_MAX_RESULTS_PER_KEYWORD,
            'SEARCH_PRODUCT': _RAW_SEARCH_PRODUCT,
            'API_REQUEST_DELAY': _RAW_API_REQUEST_DELAY,
        }
        
        validated_config = validate_search_config(raw_config)
        logger.info("Search configuration validated successfully")
        return validated_config
        
    except ImportError as e:
        logger.warning(f"Could not import config validation: {e}. Using raw values.")
        return {
            'SEARCH_KEYWORDS': _RAW_SEARCH_KEYWORDS,
            'MONITORING_INTERVAL': _RAW_MONITORING_INTERVAL,
            'MAX_RESULTS_PER_KEYWORD': _RAW_MAX_RESULTS_PER_KEYWORD,
            'SEARCH_PRODUCT': _RAW_SEARCH_PRODUCT,
            'API_REQUEST_DELAY': _RAW_API_REQUEST_DELAY,
            'SEARCH_TIME_WINDOW': _RAW_MONITORING_INTERVAL
        }
    except Exception as e:
        logger.error(f"Error validating search configuration: {e}. Using raw values.")
        return {
            'SEARCH_KEYWORDS': _RAW_SEARCH_KEYWORDS,
            'MONITORING_INTERVAL': _RAW_MONITORING_INTERVAL,
            'MAX_RESULTS_PER_KEYWORD': _RAW_MAX_RESULTS_PER_KEYWORD,
            'SEARCH_PRODUCT': _RAW_SEARCH_PRODUCT,
            'API_REQUEST_DELAY': _RAW_API_REQUEST_DELAY,
            'SEARCH_TIME_WINDOW': _RAW_MONITORING_INTERVAL
        }

# Get validated configuration
_validated_config = _validate_and_export_config()

# Export validated values
SEARCH_KEYWORDS = _validated_config['SEARCH_KEYWORDS']
MONITORING_INTERVAL = _validated_config['MONITORING_INTERVAL']
MAX_RESULTS_PER_KEYWORD = _validated_config['MAX_RESULTS_PER_KEYWORD']
SEARCH_PRODUCT = _validated_config['SEARCH_PRODUCT']
API_REQUEST_DELAY = _validated_config['API_REQUEST_DELAY']
SEARCH_TIME_WINDOW = _validated_config['SEARCH_TIME_WINDOW']