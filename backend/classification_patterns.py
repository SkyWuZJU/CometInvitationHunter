"""
Centralized classification patterns for Comet Invitation Hunter.

This file contains all the patterns and keywords used to classify posts into different categories:
- Free invitations (posts with direct invitation links)
- Conditional invitations (posts requiring user actions to get invites)
- Comet-related content validation

Modify these patterns to adjust the classification behavior without changing code logic.
"""

import logging
from typing import Dict, Any, List

# Configure logging for this module
logger = logging.getLogger(__name__)

# Raw configuration values - modify these to adjust classification behavior
# These will be validated and potentially adjusted during import

# Direct Invitation Link Patterns
# These regex patterns identify posts containing actual Comet invitation links
# that users can click immediately to claim an invitation
_RAW_INVITATION_PATTERNS = [
    r'https://www\.perplexity\.ai/browser/claim/[A-Z0-9]+',  # Full HTTPS URLs
    r'perplexity\.ai/browser/claim/[A-Z0-9]+',              # URLs without protocol
    r'comet.*invitation',                                    # General comet invitation mentions
    r'comet.*invite',                                        # General comet invite mentions  
    r'comet.*access'                                         # General comet access mentions
]

# Conditional Sharing Keywords
# These keywords indicate that the post requires users to perform specific actions
# (like following, DMing, commenting) before receiving an invitation
_RAW_CONDITIONAL_KEYWORDS = [
    'dm me',                # Direct message requests
    'send dm',              # Send direct message
    'direct message',       # Full direct message phrase
    'follow and dm',        # Follow then DM requirement
    'follow me and dm',     # Follow me then DM requirement
    'comment below',        # Comment on post requirement
    'reply below',          # Reply to post requirement
    'retweet and dm',       # Retweet then DM requirement
    'rt and dm',            # RT (retweet) then DM requirement
    'follow for invite',    # Follow to get invite
    'follow to get',        # Follow to get something
    'like and dm',          # Like then DM requirement
    'like and comment'      # Like and comment requirement
]

# Comet-Related Keywords
# These keywords must be present in posts to be considered relevant to Comet invitations
# Used to filter out false positives from generic invitation/sharing posts
_RAW_COMET_KEYWORDS = [
    'comet',                    # Direct comet mentions
    'perplexity browser',       # Perplexity browser references
    'ai browser',               # AI browser references
    'perplexity.ai/browser',    # Direct URL references
    'browser invite'            # Browser invitation mentions
]

# Validate configuration and export validated values
def _validate_and_export_config() -> Dict[str, Any]:
    """Validate configuration values and return validated config."""
    try:
        from config_validation import validate_classification_config
        
        raw_config = {
            'INVITATION_PATTERNS': _RAW_INVITATION_PATTERNS,
            'CONDITIONAL_KEYWORDS': _RAW_CONDITIONAL_KEYWORDS,
            'COMET_KEYWORDS': _RAW_COMET_KEYWORDS,
        }
        
        validated_config = validate_classification_config(raw_config)
        logger.info("Classification patterns validated successfully")
        return validated_config
        
    except ImportError as e:
        logger.warning(f"Could not import config validation: {e}. Using raw values.")
        return {
            'INVITATION_PATTERNS': _RAW_INVITATION_PATTERNS,
            'CONDITIONAL_KEYWORDS': _RAW_CONDITIONAL_KEYWORDS,
            'COMET_KEYWORDS': _RAW_COMET_KEYWORDS,
        }
    except Exception as e:
        logger.error(f"Error validating classification patterns: {e}. Using raw values.")
        return {
            'INVITATION_PATTERNS': _RAW_INVITATION_PATTERNS,
            'CONDITIONAL_KEYWORDS': _RAW_CONDITIONAL_KEYWORDS,
            'COMET_KEYWORDS': _RAW_COMET_KEYWORDS,
        }

# Get validated configuration
_validated_config = _validate_and_export_config()

# Export validated values
INVITATION_PATTERNS = _validated_config['INVITATION_PATTERNS']
CONDITIONAL_KEYWORDS = _validated_config['CONDITIONAL_KEYWORDS']
COMET_KEYWORDS = _validated_config['COMET_KEYWORDS']