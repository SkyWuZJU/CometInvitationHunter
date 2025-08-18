"""
Background monitoring service for Comet Invitation Hunter.
Continuously monitors X for Comet invitation posts and sends email notifications.
"""

import asyncio
import json
import logging
import re
import time
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
from dataclasses import dataclass

import resend

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from database import get_db_with_retry, add_post, log_email_batch, get_all_users, is_post_processed
from utools_client import UtoolsClient, UtoolsError, RateLimitError, SearchResult
from config import config

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import centralized search configuration with graceful fallback
try:
    from search_config import (
        SEARCH_KEYWORDS, 
        MONITORING_INTERVAL, 
        MAX_RESULTS_PER_KEYWORD,
        SEARCH_PRODUCT,
        API_REQUEST_DELAY
    )
    logger.info("Successfully imported centralized search configuration")
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
    # Fallback to default values
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

# Import centralized classification patterns with graceful fallback
try:
    from classification_patterns import (
        INVITATION_PATTERNS,
        CONDITIONAL_KEYWORDS,
        COMET_KEYWORDS
    )
    logger.info("Successfully imported centralized classification patterns")
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
    # Fallback to default values
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

# Log configuration status and values
def _log_startup_configuration():
    """Log configuration status and values at startup."""
    logger.info("=== COMET MONITOR STARTUP CONFIGURATION ===")
    
    # Log configuration loading status
    if search_config_loaded:
        logger.info("✓ Search configuration loaded from centralized config")
    else:
        logger.warning("⚠ Search configuration using fallback defaults")
    
    if classification_config_loaded:
        logger.info("✓ Classification patterns loaded from centralized config")
    else:
        logger.warning("⚠ Classification patterns using fallback defaults")
    
    # Log search configuration values
    logger.info("Search Configuration:")
    logger.info(f"  - Keywords: {len(SEARCH_KEYWORDS)} configured")
    for i, keyword in enumerate(SEARCH_KEYWORDS[:3], 1):
        logger.info(f"    {i}. '{keyword}'")
    if len(SEARCH_KEYWORDS) > 3:
        logger.info(f"    ... and {len(SEARCH_KEYWORDS) - 3} more")
    
    logger.info(f"  - Monitoring interval: {MONITORING_INTERVAL} seconds")
    logger.info(f"  - Max results per keyword: {MAX_RESULTS_PER_KEYWORD}")
    logger.info(f"  - API request delay: {API_REQUEST_DELAY} seconds")
    logger.info(f"  - Search product: {SEARCH_PRODUCT}")
    
    # Log classification configuration values
    logger.info("Classification Configuration:")
    logger.info(f"  - Invitation patterns: {len(INVITATION_PATTERNS)} configured")
    logger.info(f"  - Conditional keywords: {len(CONDITIONAL_KEYWORDS)} configured")
    logger.info(f"  - Comet keywords: {len(COMET_KEYWORDS)} configured")
    
    logger.info("=== END STARTUP CONFIGURATION ===")

# Log startup configuration
_log_startup_configuration()


@dataclass
class ClassifiedPost:
    """Represents a classified post with invitation information"""
    tweet_id: str
    content: str
    author_username: str
    post_type: str  # 'free' or 'conditional'
    invitation_link: Optional[str]
    tweet_url: str
    conditions: Optional[str]
    created_at: str


class PostClassifier:
    """Handles classification of posts into free vs conditional sharing"""
    
    def __init__(self):
        """Initialize classifier with imported patterns and validate regex patterns"""
        # Use imported patterns instead of hardcoded class variables
        self.invitation_patterns = self._validate_regex_patterns(INVITATION_PATTERNS, "INVITATION_PATTERNS")
        self.conditional_keywords = CONDITIONAL_KEYWORDS
        self.comet_keywords = COMET_KEYWORDS
        
        logger.info(f"PostClassifier initialized with {len(self.invitation_patterns)} invitation patterns, "
                   f"{len(self.conditional_keywords)} conditional keywords, "
                   f"and {len(self.comet_keywords)} comet keywords")
    
    def _validate_regex_patterns(self, patterns: List[str], pattern_name: str) -> List[str]:
        """
        Validate regex patterns and filter out invalid ones.
        
        Args:
            patterns: List of regex patterns to validate
            pattern_name: Name of the pattern list for logging
            
        Returns:
            List of valid regex patterns
        """
        valid_patterns = []
        
        for pattern in patterns:
            try:
                # Test if the regex pattern is valid by compiling it
                re.compile(pattern)
                valid_patterns.append(pattern)
            except re.error as e:
                logger.error(f"Invalid regex pattern in {pattern_name}: '{pattern}' - {e}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error validating pattern in {pattern_name}: '{pattern}' - {e}")
                continue
        
        if not valid_patterns:
            logger.error(f"No valid regex patterns found in {pattern_name}! Classification may not work properly.")
            # Return a basic fallback pattern
            return [r'https://www\.perplexity\.ai/browser/claim/[A-Z0-9]+']
        
        if len(valid_patterns) < len(patterns):
            logger.warning(f"Some regex patterns in {pattern_name} were invalid and removed. "
                          f"Using {len(valid_patterns)} out of {len(patterns)} patterns.")
        
        return valid_patterns
    
    def classify_post(self, search_result: SearchResult) -> Optional[ClassifiedPost]:
        """
        Classify a post as free or conditional sharing.
        
        Args:
            search_result: SearchResult object from Utools API
            
        Returns:
            ClassifiedPost if it's a valid invitation post, None otherwise
        """
        content = search_result.content
        content_lower = content.lower()
        
        logger.debug(f"Classifying post {search_result.tweet_id}: {content[:100]}...")
        
        # First check for conditional sharing (higher priority)
        has_conditional_keywords = any(keyword in content_lower for keyword in self.conditional_keywords)
        has_comet_keywords = any(keyword in content_lower for keyword in self.comet_keywords)
        
        if has_conditional_keywords and has_comet_keywords:
            conditions = self._extract_conditions(content)
            logger.info(f"Found conditional sharing post: {search_result.tweet_id}")
            return ClassifiedPost(
                tweet_id=search_result.tweet_id,
                content=content,
                author_username=search_result.author_username,
                post_type='conditional',
                invitation_link=None,
                tweet_url=search_result.tweet_url,
                conditions=conditions,
                created_at=search_result.created_at
            )
        
        # Then check for direct invitation links (free sharing)
        # Only check for actual URLs, not just keywords
        direct_link_patterns = [
            r'https://www\.perplexity\.ai/browser/claim/[A-Z0-9]+',
            r'perplexity\.ai/browser/claim/[A-Z0-9]+'
        ]
        
        for pattern in direct_link_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                invitation_link = self._extract_invitation_link(content)
                logger.info(f"Found free sharing post: {search_result.tweet_id}")
                return ClassifiedPost(
                    tweet_id=search_result.tweet_id,
                    content=content,
                    author_username=search_result.author_username,
                    post_type='free',
                    invitation_link=invitation_link,
                    tweet_url=search_result.tweet_url,
                    conditions=None,
                    created_at=search_result.created_at
                )
        
        logger.debug(f"Post {search_result.tweet_id} is not an invitation post")
        return None
    
    def _extract_invitation_link(self, content: str) -> Optional[str]:
        """Extract Comet invitation link from post content"""
        pattern = r'https://www\.perplexity\.ai/browser/claim/[A-Z0-9]+'
        match = re.search(pattern, content)
        return match.group(0) if match else None
    
    def _extract_conditions(self, content: str) -> str:
        """Extract sharing conditions from conditional posts"""
        content_lower = content.lower()
        conditions = []
        
        if 'dm me' in content_lower or 'send dm' in content_lower:
            conditions.append('Send DM to author')
        if 'follow' in content_lower and ('dm' in content_lower or 'invite' in content_lower):
            conditions.append('Follow the author')
        if 'comment' in content_lower or 'reply' in content_lower:
            conditions.append('Comment on the post')
        if 'retweet' in content_lower or 'rt' in content_lower:
            conditions.append('Retweet the post')
        if 'like' in content_lower:
            conditions.append('Like the post')
        
        return ', '.join(conditions) if conditions else 'Check post for requirements'


class EmailNotifier:
    """Handles email notifications for batched alerts using Resend API"""
    
    def __init__(self):
        self.resend_api_key = config.resend_api_key
        self.from_email = config.from_email
        
        # Initialize Resend client
        if self.resend_api_key:
            resend.api_key = self.resend_api_key
        else:
            logger.warning("RESEND_API_KEY not configured - email notifications will fail")
        
    def send_batch_notification(self, posts: List[ClassifiedPost], recipients: List[str]) -> bool:
        """
        Send batched email notification to all recipients using Resend API.
        
        Args:
            posts: List of classified posts to include
            recipients: List of email addresses to send to
            
        Returns:
            True if successful, False otherwise
        """
        if not posts or not recipients:
            logger.warning("No posts or recipients for email notification")
            return False
        
        if not self.resend_api_key:
            logger.error("Resend API key not configured - cannot send emails")
            return False
        
        batch_id = str(uuid.uuid4())[:8]
        logger.info(f"Sending batch notification {batch_id} with {len(posts)} posts to {len(recipients)} recipients")
        
        try:
            # Create email content
            subject = f"🚀 New Comet Invitations Found ({len(posts)} posts)"
            html_content = self._create_email_html(posts, batch_id)
            text_content = self._create_email_text(posts, batch_id)
            
            # Send email with retry logic
            success, error_message = self._send_email_with_retry(
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                recipients=recipients,
                batch_id=batch_id
            )
            
            # Log the batch
            db = get_db_with_retry()
            if db:
                try:
                    log_email_batch(
                        db=db,
                        batch_id=batch_id,
                        recipient_count=len(recipients),
                        posts_included=len(posts),
                        status="sent" if success else "failed",
                        error_message=error_message
                    )
                finally:
                    db.close()
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send batch notification {batch_id}: {e}")
            return False
    
    def _send_email_with_retry(self, subject: str, html_content: str, 
                              text_content: str, recipients: List[str], 
                              batch_id: str, max_retries: int = 3) -> tuple[bool, Optional[str]]:
        """Send email using Resend API with exponential backoff retry logic"""
        
        for attempt in range(max_retries):
            try:
                # Create unsubscribe link (placeholder for now)
                unsubscribe_url = f"https://your-domain.com/unsubscribe?batch={batch_id}"
                
                # Prepare email data for Resend API
                email_data = {
                    "from": f"Comet Hunter <{self.from_email}>",
                    "to": recipients,
                    "subject": subject,
                    "html": html_content,
                    "text": text_content,
                    "headers": {
                        "List-Unsubscribe": f"<{unsubscribe_url}>",
                        "List-Unsubscribe-Post": "List-Unsubscribe=One-Click"
                    },
                    "tags": [
                        {"name": "category", "value": "comet-invitations"},
                        {"name": "batch_id", "value": batch_id}
                    ]
                }
                
                # Send email using Resend API
                logger.debug(f"Sending email via Resend API (attempt {attempt + 1})")
                response = resend.Emails.send(email_data)
                
                # Check if response contains an ID (success indicator)
                if response and isinstance(response, dict) and 'id' in response:
                    logger.info(f"Email sent successfully via Resend to {len(recipients)} recipients (ID: {response['id']})")
                    return True, None
                elif response and hasattr(response, 'id'):
                    # Fallback for object-style response
                    logger.info(f"Email sent successfully via Resend to {len(recipients)} recipients (ID: {response.id})")
                    return True, None
                else:
                    logger.warning(f"Resend API returned unexpected response: {response}")
                    raise Exception(f"Unexpected Resend API response: {response}")
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Resend API attempt {attempt + 1} failed: {error_msg}")
                
                # Check if it's a rate limit error
                if "rate limit" in error_msg.lower() or "429" in error_msg:
                    wait_time = (2 ** attempt) * 5.0  # Longer wait for rate limits
                    logger.info(f"Rate limit detected, waiting {wait_time} seconds before retry...")
                elif attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 2.0  # Exponential backoff
                    logger.info(f"Retrying email send in {wait_time} seconds...")
                else:
                    # Last attempt failed
                    logger.error(f"All Resend API attempts failed after {max_retries} retries")
                    return False, error_msg
                
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
        
        return False, "Maximum retry attempts exceeded"
    
    def _create_email_html(self, posts: List[ClassifiedPost], batch_id: str) -> str:
        """Create HTML email content with improved styling and unsubscribe"""
        free_posts = [p for p in posts if p.post_type == 'free']
        conditional_posts = [p for p in posts if p.post_type == 'conditional']
        
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>New Comet Invitations Found</title>
            <style>
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; 
                    line-height: 1.6; 
                    color: #333; 
                    margin: 0; 
                    padding: 0; 
                    background-color: #f8f9fa;
                }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; }}
                .header {{ 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; 
                    padding: 30px 20px; 
                    text-align: center; 
                }}
                .header h1 {{ margin: 0; font-size: 28px; font-weight: 600; }}
                .header p {{ margin: 10px 0 0 0; font-size: 16px; opacity: 0.9; }}
                .content {{ padding: 30px 20px; }}
                .section-title {{ 
                    font-size: 20px; 
                    font-weight: 600; 
                    margin: 30px 0 15px 0; 
                    color: #2d3748; 
                }}
                .post {{ 
                    border: 1px solid #e2e8f0; 
                    margin: 20px 0; 
                    padding: 20px; 
                    border-radius: 8px; 
                    background-color: #ffffff;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }}
                .free {{ border-left: 4px solid #48bb78; }}
                .conditional {{ border-left: 4px solid #ed8936; }}
                .post-header {{ 
                    font-weight: 600; 
                    margin-bottom: 12px; 
                    color: #2d3748;
                    font-size: 16px;
                }}
                .post-content {{ 
                    margin: 15px 0; 
                    padding: 15px; 
                    background-color: #f7fafc; 
                    border-radius: 6px; 
                    font-size: 14px;
                    line-height: 1.5;
                }}
                .post-actions {{ margin-top: 15px; }}
                .invitation-link {{ 
                    background-color: #48bb78; 
                    color: white; 
                    padding: 10px 20px; 
                    text-decoration: none; 
                    border-radius: 6px; 
                    display: inline-block; 
                    font-weight: 500;
                    margin-right: 10px;
                }}
                .view-post-link {{
                    background-color: #4299e1;
                    color: white;
                    padding: 10px 20px;
                    text-decoration: none;
                    border-radius: 6px;
                    display: inline-block;
                    font-weight: 500;
                }}
                .conditions {{ 
                    background-color: #fef5e7; 
                    border: 1px solid #f6ad55;
                    padding: 12px; 
                    border-radius: 6px; 
                    margin-top: 15px; 
                    font-size: 14px;
                }}
                .conditions strong {{ color: #c05621; }}
                .footer {{ 
                    margin-top: 40px; 
                    padding: 30px 20px; 
                    background-color: #f7fafc; 
                    text-align: center; 
                    font-size: 12px; 
                    color: #718096; 
                    border-top: 1px solid #e2e8f0;
                }}
                .unsubscribe {{ 
                    margin-top: 15px; 
                    padding-top: 15px; 
                    border-top: 1px solid #e2e8f0; 
                }}
                .unsubscribe a {{ color: #718096; text-decoration: underline; }}
                @media (max-width: 600px) {{
                    .container {{ margin: 0; }}
                    .content {{ padding: 20px 15px; }}
                    .header {{ padding: 20px 15px; }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 New Comet Invitations Found!</h1>
                    <p>Found {len(posts)} new invitation posts</p>
                </div>
                
                <div class="content">
        """
        
        if free_posts:
            html += f"""
                    <h2 class="section-title">🎉 Free Invitations ({len(free_posts)})</h2>
                    <p style="color: #4a5568; margin-bottom: 20px;">These posts contain direct invitation links you can use immediately:</p>
            """
            
            for post in free_posts:
                html += f"""
                    <div class="post free">
                        <div class="post-header">@{post.author_username}</div>
                        <div class="post-content">{post.content}</div>
                        <div class="post-actions">
                            {f'<a href="{post.invitation_link}" class="invitation-link">🔗 Use Invitation Link</a>' if post.invitation_link else ''}
                            <a href="{post.tweet_url}" target="_blank" class="view-post-link">View on X</a>
                        </div>
                    </div>
                """
        
        if conditional_posts:
            html += f"""
                    <h2 class="section-title">📝 Conditional Invitations ({len(conditional_posts)})</h2>
                    <p style="color: #4a5568; margin-bottom: 20px;">These posts require you to complete certain actions to get an invitation:</p>
            """
            
            for post in conditional_posts:
                html += f"""
                    <div class="post conditional">
                        <div class="post-header">@{post.author_username}</div>
                        <div class="post-content">{post.content}</div>
                        <div class="conditions">
                            <strong>Requirements:</strong> {post.conditions}
                        </div>
                        <div class="post-actions">
                            <a href="{post.tweet_url}" target="_blank" class="view-post-link">View on X</a>
                        </div>
                    </div>
                """
        
        html += f"""
                </div>
                
                <div class="footer">
                    <p><strong>Comet Invitation Hunter</strong></p>
                    <p>Batch ID: {batch_id} | Sent at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
                    <p style="margin-top: 10px;">You're receiving this because you're a verified follower of @0xSky99</p>
                    
                    <div class="unsubscribe">
                        <p>Don't want these notifications? <a href="https://your-domain.com/unsubscribe?batch={batch_id}">Unsubscribe here</a></p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _create_email_text(self, posts: List[ClassifiedPost], batch_id: str) -> str:
        """Create plain text email content with unsubscribe"""
        free_posts = [p for p in posts if p.post_type == 'free']
        conditional_posts = [p for p in posts if p.post_type == 'conditional']
        
        text = f"""🚀 NEW COMET INVITATIONS FOUND!

Found {len(posts)} new invitation posts:

"""
        
        if free_posts:
            text += f"""🎉 FREE INVITATIONS ({len(free_posts)}):
These posts contain direct invitation links you can use immediately:

"""
            for post in free_posts:
                text += f"""@{post.author_username}:
{post.content}

{f'🔗 Invitation Link: {post.invitation_link}' if post.invitation_link else ''}
View on X: {post.tweet_url}

---

"""
        
        if conditional_posts:
            text += f"""📝 CONDITIONAL INVITATIONS ({len(conditional_posts)}):
These posts require you to complete certain actions:

"""
            for post in conditional_posts:
                text += f"""@{post.author_username}:
{post.content}

Requirements: {post.conditions}
View on X: {post.tweet_url}

---

"""
        
        text += f"""
═══════════════════════════════════════════════════════════════

COMET INVITATION HUNTER

Batch ID: {batch_id}
Sent at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

You're receiving this because you're a verified follower of @0xSky99

Don't want these notifications? 
Unsubscribe: https://your-domain.com/unsubscribe?batch={batch_id}
"""
        
        return text


class CometMonitor:
    """Main monitoring service that coordinates search, classification, and notifications"""
    
    def __init__(self):
        self.utools_client = UtoolsClient(
            api_key=config.utools_api_key,
            base_url=config.utools_base_url
        )
        self.classifier = PostClassifier()
        self.notifier = EmailNotifier()
        # Use imported configuration values with fallback to environment variable
        self.monitoring_interval = MONITORING_INTERVAL
        self.search_keywords = SEARCH_KEYWORDS
        self.max_results_per_keyword = MAX_RESULTS_PER_KEYWORD
        self.api_request_delay = API_REQUEST_DELAY
        self.search_product = SEARCH_PRODUCT
        self.is_running = False
        
        # Log configuration values being used
        logger.info("CometMonitor initialized with configuration:")
        logger.info(f"  - Monitoring interval: {self.monitoring_interval} seconds")
        logger.info(f"  - Search keywords: {len(self.search_keywords)} keywords")
        logger.info(f"  - Max results per keyword: {self.max_results_per_keyword}")
        logger.info(f"  - API request delay: {self.api_request_delay} seconds")
        logger.info(f"  - Search product: {self.search_product}")
        
        # Validate configuration values
        self._validate_monitor_configuration()
    
    def _validate_monitor_configuration(self):
        """Validate monitor configuration and log warnings for potential issues."""
        warnings = []
        
        # Validate monitoring interval
        if self.monitoring_interval < 60:
            warnings.append(f"Monitoring interval ({self.monitoring_interval}s) is very short - may hit rate limits")
        elif self.monitoring_interval > 1800:
            warnings.append(f"Monitoring interval ({self.monitoring_interval}s) is very long - may miss time-sensitive posts")
        
        # Validate search keywords
        if not self.search_keywords:
            warnings.append("No search keywords configured - monitor will not find any posts")
        elif len(self.search_keywords) > 20:
            warnings.append(f"Many search keywords ({len(self.search_keywords)}) - may hit rate limits quickly")
        
        # Validate max results
        if self.max_results_per_keyword > 500:
            warnings.append(f"Max results per keyword ({self.max_results_per_keyword}) is very high - may hit rate limits")
        elif self.max_results_per_keyword < 10:
            warnings.append(f"Max results per keyword ({self.max_results_per_keyword}) is very low - may miss posts")
        
        # Validate API delay
        if self.api_request_delay < 1:
            warnings.append(f"API request delay ({self.api_request_delay}s) is very short - may hit rate limits")
        elif self.api_request_delay > 10:
            warnings.append(f"API request delay ({self.api_request_delay}s) is very long - monitoring will be slow")
        
        # Log warnings if any
        if warnings:
            logger.warning("Configuration validation warnings:")
            for warning in warnings:
                logger.warning(f"  - {warning}")
        else:
            logger.info("Configuration validation passed - no issues detected")
        
    async def start_monitoring(self):
        """Start the continuous monitoring process"""
        logger.info("Starting Comet invitation monitoring service...")
        self.is_running = True
        
        while self.is_running:
            try:
                await self._monitoring_cycle()
                
                # Wait before next cycle
                logger.info(f"Monitoring cycle complete. Waiting {self.monitoring_interval} seconds...")
                await asyncio.sleep(self.monitoring_interval)
                
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, stopping monitoring...")
                self.is_running = False
                break
            except Exception as e:
                logger.error(f"Error in monitoring cycle: {e}")
                # Wait a bit before retrying to avoid rapid error loops
                await asyncio.sleep(60)
    
    def stop_monitoring(self):
        """Stop the monitoring process"""
        logger.info("Stopping monitoring service...")
        self.is_running = False
    
    async def _monitoring_cycle(self):
        """Execute one complete monitoring cycle"""
        logger.info("Starting monitoring cycle...")
        
        try:
            # Step 1: Search with all keywords simultaneously
            all_search_results = await self._search_all_keywords()
            logger.info(f"Found {len(all_search_results)} total search results")
            
            # Step 2: Deduplicate by tweet_id
            unique_results = self._deduplicate_results(all_search_results)
            logger.info(f"After deduplication: {len(unique_results)} unique posts")
            
            # Step 3: Process each post individually
            new_posts = await self._process_posts(unique_results)
            logger.info(f"Found {len(new_posts)} new invitation posts")
            
            # Step 4: Send batch notification if new posts found
            if new_posts:
                await self._send_notifications(new_posts)
            else:
                logger.info("No new posts to notify about")
                
        except Exception as e:
            logger.error(f"Error in monitoring cycle: {e}")
            raise
    
    async def _search_all_keywords(self) -> List[SearchResult]:
        """Search with all keywords using time filtering and pagination"""
        all_results = []
        
        for keyword in self.search_keywords:
            try:
                logger.info(f"Searching for keyword: '{keyword}' with time filtering and pagination")
                
                # Use time-filtered paginated search for comprehensive results
                results = self.utools_client.search_recent_tweets_paginated(
                    keywords=keyword,
                    monitoring_interval_seconds=self.monitoring_interval,
                    max_results=self.max_results_per_keyword,
                    product=self.search_product
                )
                
                all_results.extend(results)
                logger.info(f"Found {len(results)} results for '{keyword}' (time-filtered & paginated)")
                
                # Use configured delay between searches
                await asyncio.sleep(self.api_request_delay)
                
            except RateLimitError:
                logger.warning(f"Rate limit hit while searching for '{keyword}', skipping remaining keywords")
                break
            except UtoolsError as e:
                logger.error(f"Error searching for '{keyword}': {e}")
                continue
        
        return all_results
    
    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate posts by tweet ID"""
        seen_ids: Set[str] = set()
        unique_results = []
        
        for result in results:
            if result.tweet_id not in seen_ids:
                seen_ids.add(result.tweet_id)
                unique_results.append(result)
        
        return unique_results
    
    async def _process_posts(self, results: List[SearchResult]) -> List[ClassifiedPost]:
        """Process posts: classify and store new ones"""
        new_posts = []
        
        # Get database connection
        db = get_db_with_retry()
        if not db:
            logger.error("Failed to get database connection")
            return new_posts
        
        logger.info(f"Processing {len(results)} posts from time-filtered search")
        
        try:
            for result in results:
                try:
                    # Check if already processed (time filtering is now done during pagination)
                    if is_post_processed(db, result.tweet_id):
                        logger.debug(f"Post {result.tweet_id} already processed, skipping")
                        continue
                    
                    # Classify the post
                    classified_post = self.classifier.classify_post(result)
                    if not classified_post:
                        logger.debug(f"Post {result.tweet_id} is not an invitation post")
                        continue
                    
                    # Store in database
                    stored_post = add_post(
                        db=db,
                        tweet_id=classified_post.tweet_id,
                        content=classified_post.content,
                        author_username=classified_post.author_username,
                        post_type=classified_post.post_type,
                        tweet_url=classified_post.tweet_url,
                        invitation_link=classified_post.invitation_link,
                        conditions=classified_post.conditions
                    )
                    
                    if stored_post:
                        new_posts.append(classified_post)
                        logger.info(f"Stored new {classified_post.post_type} post: {classified_post.tweet_id}")
                    else:
                        logger.error(f"Failed to store post: {classified_post.tweet_id}")
                
                except Exception as e:
                    logger.error(f"Error processing post {result.tweet_id}: {e}")
                    continue
        
        finally:
            db.close()
        
        logger.info(f"Processed {len(new_posts)} new posts from time-filtered search")
        return new_posts
    
    async def _send_notifications(self, posts: List[ClassifiedPost]):
        """Send email notifications for new posts"""
        logger.info(f"Preparing to send notifications for {len(posts)} posts")
        
        # Get all verified users
        db = get_db_with_retry()
        if not db:
            logger.error("Failed to get database connection for notifications")
            return
        
        try:
            users = get_all_users(db)
            if not users:
                logger.warning("No verified users found for notifications")
                return
            
            recipients = [user.email for user in users]
            logger.info(f"Sending notifications to {len(recipients)} recipients")
            
            # Send batch notification
            success = self.notifier.send_batch_notification(posts, recipients)
            if success:
                logger.info("Batch notification sent successfully")
            else:
                logger.error("Failed to send batch notification")
        
        finally:
            db.close()


async def main():
    """Main entry point for the monitoring service"""
    logger.info("Initializing Comet Invitation Hunter monitoring service...")
    
    # Validate configuration
    if not config.utools_api_key:
        logger.error("UTOOLS_API_KEY not configured")
        return
    
    # Create monitor instance
    monitor = CometMonitor()
    
    try:
        # Start monitoring
        await monitor.start_monitoring()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        monitor.stop_monitoring()
        logger.info("Monitoring service stopped")


if __name__ == "__main__":
    asyncio.run(main())