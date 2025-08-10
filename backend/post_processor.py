"""
Post classification and processing system for Comet Invitation Hunter.

This module handles:
- Classification of posts as free or conditional sharing
- Pattern matching for Comet invitation links
- Post deduplication across multiple keyword searches
- Post storage with proper data validation
"""

import re
import logging
from typing import List, Optional, Dict, Any, Set
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse

try:
    from backend.utools_client import SearchResult
    from backend.database import get_db_with_retry, add_post, is_post_processed
except ImportError:
    from utools_client import SearchResult
    from database import get_db_with_retry, add_post, is_post_processed


logger = logging.getLogger(__name__)


class PostType(Enum):
    """Types of invitation posts"""
    FREE = "free"
    CONDITIONAL = "conditional"


@dataclass
class ClassifiedPost:
    """Represents a classified invitation post"""
    tweet_id: str
    content: str
    author_username: str
    post_type: PostType
    tweet_url: str
    invitation_link: Optional[str] = None
    conditions: Optional[str] = None
    created_at: Optional[str] = None


class PostClassifier:
    """
    Classifies X posts to identify Comet invitation sharing.
    
    Handles two types of posts:
    1. Free sharing: Posts with direct invitation links
    2. Conditional sharing: Posts requiring user actions (DM, follow, etc.)
    """
    
    # Patterns for identifying Comet invitation links
    INVITATION_LINK_PATTERNS = [
        r'https://www\.perplexity\.ai/browser/claim/[A-Z0-9]+',
        r'perplexity\.ai/browser/claim/[A-Z0-9]+',
        r'https://perplexity\.ai/browser/claim/[A-Z0-9]+',
    ]
    
    # Keywords that indicate Comet-related content
    COMET_KEYWORDS = [
        'comet',
        'perplexity browser',
        'ai browser',
        'perplexity.ai/browser',
        'comet browser',
        'comet invite',
        'comet invitation',
        'comet access'
    ]
    
    # Keywords that indicate conditional sharing
    CONDITIONAL_KEYWORDS = [
        'dm me',
        'send dm',
        'direct message',
        'follow and dm',
        'follow me and dm',
        'comment below',
        'reply below',
        'retweet and dm',
        'rt and dm',
        'follow for invite',
        'follow to get',
        'follow first',
        'must follow',
        'like and retweet',
        'like and rt',
        'drop your @',
        'drop @ below',
        'comment your @',
        'reply with @'
    ]
    
    def __init__(self):
        """Initialize the post classifier"""
        # Compile regex patterns for better performance
        self.invitation_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.INVITATION_LINK_PATTERNS]
        
    def classify_post(self, search_result: SearchResult) -> Optional[ClassifiedPost]:
        """
        Classify a search result as an invitation post.
        
        Args:
            search_result: SearchResult object from Utools API
            
        Returns:
            ClassifiedPost if it's an invitation post, None otherwise
        """
        content = search_result.content
        content_lower = content.lower()
        
        logger.debug(f"Classifying post {search_result.tweet_id}: {content[:100]}...")
        
        # First check if this is Comet-related content
        if not self._is_comet_related(content_lower):
            logger.debug(f"Post {search_result.tweet_id} is not Comet-related")
            return None
        
        # Check for direct invitation links (free sharing)
        invitation_link = self._extract_invitation_link(content)
        if invitation_link:
            logger.info(f"Found free sharing post {search_result.tweet_id} with link: {invitation_link}")
            return ClassifiedPost(
                tweet_id=search_result.tweet_id,
                content=content,
                author_username=search_result.author_username,
                post_type=PostType.FREE,
                tweet_url=search_result.tweet_url,
                invitation_link=invitation_link,
                created_at=search_result.created_at
            )
        
        # Check for conditional sharing indicators
        conditions = self._extract_conditions(content_lower)
        if conditions:
            logger.info(f"Found conditional sharing post {search_result.tweet_id} with conditions: {conditions}")
            return ClassifiedPost(
                tweet_id=search_result.tweet_id,
                content=content,
                author_username=search_result.author_username,
                post_type=PostType.CONDITIONAL,
                tweet_url=search_result.tweet_url,
                conditions=conditions,
                created_at=search_result.created_at
            )
        
        logger.debug(f"Post {search_result.tweet_id} is Comet-related but not an invitation post")
        return None
    
    def _is_comet_related(self, content_lower: str) -> bool:
        """Check if content is related to Comet browser"""
        return any(keyword in content_lower for keyword in self.COMET_KEYWORDS)
    
    def _extract_invitation_link(self, content: str) -> Optional[str]:
        """Extract Comet invitation link from post content"""
        for pattern in self.invitation_patterns:
            match = pattern.search(content)
            if match:
                link = match.group(0)
                # Ensure the link has proper protocol
                if not link.startswith('http'):
                    link = 'https://' + link
                
                # Validate the link format
                if self._validate_invitation_link(link):
                    return link
        
        return None
    
    def _validate_invitation_link(self, link: str) -> bool:
        """Validate that the invitation link has the correct format"""
        try:
            parsed = urlparse(link)
            if parsed.netloc != 'www.perplexity.ai' and parsed.netloc != 'perplexity.ai':
                return False
            
            # Check path format: /browser/claim/[CODE]
            path_parts = parsed.path.split('/')
            if len(path_parts) != 4 or path_parts[1] != 'browser' or path_parts[2] != 'claim':
                return False
            
            # Check that claim code exists and looks valid (alphanumeric)
            claim_code = path_parts[3]
            if not claim_code or not re.match(r'^[A-Z0-9]+$', claim_code):
                return False
            
            return True
        except Exception:
            return False
    
    def _extract_conditions(self, content_lower: str) -> Optional[str]:
        """Extract sharing conditions from conditional posts"""
        found_conditions = []
        
        # Check for specific conditional patterns in order of specificity
        # More specific patterns first to avoid conflicts
        
        # Follow-related conditions
        if any(keyword in content_lower for keyword in ['follow and dm', 'follow me and dm']):
            found_conditions.extend(['Follow the author', 'Send DM to author'])
        elif any(keyword in content_lower for keyword in ['follow first', 'must follow', 'follow me', 'follow for']):
            found_conditions.append('Follow the author')
        
        # DM-related conditions (check after follow+dm to avoid duplicates)
        elif any(keyword in content_lower for keyword in ['dm me', 'send dm', 'direct message']):
            found_conditions.append('Send DM to author')
        
        # Comment-related conditions
        if any(keyword in content_lower for keyword in ['comment below', 'reply below', 'drop your @', 'comment your @', 'reply with @']):
            found_conditions.append('Comment on the post')
        
        # Retweet-related conditions
        if any(keyword in content_lower for keyword in ['retweet and dm', 'rt and dm']):
            if 'Send DM to author' not in found_conditions:
                found_conditions.append('Send DM to author')
            found_conditions.append('Retweet the post')
        elif any(keyword in content_lower for keyword in ['like and retweet', 'like and rt']):
            found_conditions.extend(['Like the post', 'Retweet the post'])
        elif 'retweet' in content_lower or 'rt ' in content_lower:
            found_conditions.append('Retweet the post')
        
        # Like-related conditions
        if any(keyword in content_lower for keyword in ['like and', 'like this']) and 'Like the post' not in found_conditions:
            found_conditions.append('Like the post')
        
        # Remove duplicates while preserving order
        unique_conditions = []
        for condition in found_conditions:
            if condition not in unique_conditions:
                unique_conditions.append(condition)
        
        # If we found specific conditions, return them
        if unique_conditions:
            return ', '.join(unique_conditions)
        
        # If we found general conditional keywords but no specific conditions,
        # return a generic message
        if any(keyword in content_lower for keyword in self.CONDITIONAL_KEYWORDS):
            return 'Check post for specific requirements'
        
        return None


class PostProcessor:
    """
    Processes and manages Comet invitation posts.
    
    Handles deduplication, classification, and storage of posts.
    """
    
    def __init__(self):
        """Initialize the post processor"""
        self.classifier = PostClassifier()
    
    def process_search_results(self, search_results_by_keyword: Dict[str, List[SearchResult]]) -> List[ClassifiedPost]:
        """
        Process search results from multiple keywords.
        
        Args:
            search_results_by_keyword: Dictionary mapping keywords to their search results
            
        Returns:
            List of new classified invitation posts
        """
        logger.info(f"Processing search results from {len(search_results_by_keyword)} keywords")
        
        # Step 1: Combine all search results
        all_results = []
        for keyword, results in search_results_by_keyword.items():
            logger.info(f"Keyword '{keyword}' returned {len(results)} results")
            all_results.extend(results)
        
        logger.info(f"Total search results before deduplication: {len(all_results)}")
        
        # Step 2: Deduplicate by tweet_id
        unique_results = self._deduplicate_results(all_results)
        logger.info(f"Unique results after deduplication: {len(unique_results)}")
        
        # Step 3: Classify each post
        classified_posts = []
        for result in unique_results:
            classified_post = self.classifier.classify_post(result)
            if classified_post:
                classified_posts.append(classified_post)
        
        logger.info(f"Found {len(classified_posts)} invitation posts")
        
        # Step 4: Filter out already processed posts
        new_posts = self._filter_new_posts(classified_posts)
        logger.info(f"Found {len(new_posts)} new invitation posts")
        
        # Step 5: Store new posts
        stored_posts = self._store_posts(new_posts)
        logger.info(f"Successfully stored {len(stored_posts)} new posts")
        
        return stored_posts
    
    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate search results by tweet_id"""
        seen_ids: Set[str] = set()
        unique_results = []
        
        for result in results:
            if result.tweet_id not in seen_ids:
                seen_ids.add(result.tweet_id)
                unique_results.append(result)
            else:
                logger.debug(f"Removing duplicate tweet_id: {result.tweet_id}")
        
        return unique_results
    
    def _filter_new_posts(self, classified_posts: List[ClassifiedPost]) -> List[ClassifiedPost]:
        """Filter out posts that have already been processed"""
        db = get_db_with_retry()
        if not db:
            logger.error("Could not connect to database for filtering posts")
            return classified_posts
        
        try:
            new_posts = []
            for post in classified_posts:
                if not is_post_processed(db, post.tweet_id):
                    new_posts.append(post)
                else:
                    logger.debug(f"Post {post.tweet_id} already processed, skipping")
            
            return new_posts
        finally:
            db.close()
    
    def _store_posts(self, posts: List[ClassifiedPost]) -> List[ClassifiedPost]:
        """Store classified posts in the database"""
        if not posts:
            return []
        
        db = get_db_with_retry()
        if not db:
            logger.error("Could not connect to database for storing posts")
            return []
        
        try:
            stored_posts = []
            for post in posts:
                try:
                    # Validate post data before storing
                    if not self._validate_post_data(post):
                        logger.warning(f"Invalid post data for {post.tweet_id}, skipping")
                        continue
                    
                    # Store in database
                    db_post = add_post(
                        db=db,
                        tweet_id=post.tweet_id,
                        content=post.content,
                        author_username=post.author_username,
                        post_type=post.post_type.value,
                        tweet_url=post.tweet_url,
                        invitation_link=post.invitation_link,
                        conditions=post.conditions
                    )
                    
                    if db_post:
                        stored_posts.append(post)
                        logger.info(f"Stored post {post.tweet_id} ({post.post_type.value})")
                    else:
                        logger.error(f"Failed to store post {post.tweet_id}")
                        
                except Exception as e:
                    logger.error(f"Error storing post {post.tweet_id}: {e}")
                    continue
            
            return stored_posts
        finally:
            db.close()
    
    def _validate_post_data(self, post: ClassifiedPost) -> bool:
        """Validate post data before storage"""
        # Check required fields
        if not post.tweet_id or not post.content or not post.author_username or not post.tweet_url:
            logger.error(f"Missing required fields for post {post.tweet_id}")
            return False
        
        # Validate tweet_id format (should be numeric string)
        if not re.match(r'^\d+$', post.tweet_id):
            logger.error(f"Invalid tweet_id format: {post.tweet_id}")
            return False
        
        # Validate post_type
        if post.post_type not in [PostType.FREE, PostType.CONDITIONAL]:
            logger.error(f"Invalid post_type: {post.post_type}")
            return False
        
        # Validate free posts have invitation links
        if post.post_type == PostType.FREE and not post.invitation_link:
            logger.error(f"Free post {post.tweet_id} missing invitation_link")
            return False
        
        # Validate conditional posts have conditions
        if post.post_type == PostType.CONDITIONAL and not post.conditions:
            logger.error(f"Conditional post {post.tweet_id} missing conditions")
            return False
        
        # Validate URL format
        if not self._validate_url(post.tweet_url):
            logger.error(f"Invalid tweet_url: {post.tweet_url}")
            return False
        
        # Validate invitation link if present
        if post.invitation_link and not self.classifier._validate_invitation_link(post.invitation_link):
            logger.error(f"Invalid invitation_link: {post.invitation_link}")
            return False
        
        return True
    
    def _validate_url(self, url: str) -> bool:
        """Validate URL format"""
        try:
            parsed = urlparse(url)
            return bool(parsed.netloc and parsed.scheme in ['http', 'https'])
        except Exception:
            return False


# Convenience functions for external use
def process_posts(search_results_by_keyword: Dict[str, List[SearchResult]]) -> List[ClassifiedPost]:
    """
    Process search results and return new classified posts.
    
    Args:
        search_results_by_keyword: Dictionary mapping keywords to search results
        
    Returns:
        List of new classified invitation posts
    """
    processor = PostProcessor()
    return processor.process_search_results(search_results_by_keyword)


def classify_single_post(search_result: SearchResult) -> Optional[ClassifiedPost]:
    """
    Classify a single search result.
    
    Args:
        search_result: SearchResult to classify
        
    Returns:
        ClassifiedPost if it's an invitation post, None otherwise
    """
    classifier = PostClassifier()
    return classifier.classify_post(search_result)