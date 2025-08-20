"""
Utools API client for X (Twitter) integration.
Handles search functionality and follower verification.
"""

import json
import time
import logging
import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


logger = logging.getLogger(__name__)


class UtoolsError(Exception):
    """Base exception for Utools API errors"""
    pass


class RateLimitError(UtoolsError):
    """Raised when API rate limit is exceeded"""
    pass


class AuthenticationError(UtoolsError):
    """Raised when API authentication fails"""
    pass


class APIResponseError(UtoolsError):
    """Raised when API returns an error response"""
    pass


@dataclass
class SearchResult:
    """Represents a single tweet from search results"""
    tweet_id: str
    content: str
    author_username: str
    author_id: str
    created_at: str
    tweet_url: str


class UtoolsClient:
    """
    Client for interacting with Utools API for X (Twitter) operations.
    
    Provides functionality for:
    - Searching tweets by keywords
    - Verifying user followers
    - Handling rate limiting and errors
    """
    
    def __init__(self, api_key: str, base_url: str = "https://twitter.good6.top/api/base/apitools"):
        """
        Initialize Utools API client.
        
        Args:
            api_key: Utools API key for authentication
            base_url: Base URL for Utools API endpoints
        """
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 45
        
        # Rate limiting tracking
        self._last_request_time = 0
        self._min_request_interval = 1.0  # Minimum seconds between requests
    
    def get_since_time(self, minutes_ago: int = 5) -> str:
        """
        Generate a 'since' parameter for filtering recent tweets.
        
        Args:
            minutes_ago: How many minutes back to search (default: 5)
            
        Returns:
            Date string in YYYY-MM-DD format
            
        Note:
            The API seems to only support date-level filtering (YYYY-MM-DD),
            not minute-level filtering. This function provides the date for
            the time period, but actual minute-level filtering may need to be
            done client-side after receiving results.
        """
        target_time = datetime.now() - timedelta(minutes=minutes_ago)
        return target_time.strftime("%Y-%m-%d")
        
    def _make_request(self, endpoint: str, params: Dict[str, Any], retries: int = 3) -> Dict[str, Any]:
        """
        Make authenticated request to Utools API with rate limiting and error handling.
        
        Args:
            endpoint: API endpoint path
            params: Request parameters
            retries: Number of retry attempts for failed requests
            
        Returns:
            Parsed JSON response
            
        Raises:
            RateLimitError: When rate limit is exceeded
            AuthenticationError: When authentication fails
            APIResponseError: When API returns error response
            UtoolsError: For other API-related errors
        """
        # Add API key to parameters
        params = params.copy()
        params['apiKey'] = self.api_key
        
        # Rate limiting - ensure minimum interval between requests
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        url = f"{self.base_url}/{endpoint}"
        
        for attempt in range(retries + 1):
            try:
                self._last_request_time = time.time()
                
                logger.debug(f"Making request to {endpoint} (attempt {attempt + 1})")
                logger.debug(f"URL: {url}")
                logger.debug(f"Params: {params}")
                
                # Build URL with parameters for debugging
                import urllib.parse
                debug_url = f"{url}?{urllib.parse.urlencode(params)}"
                logger.debug(f"Full URL: {debug_url}")
                
                # Ensure proper URL encoding for special characters
                import urllib.parse
                encoded_params = {k: str(v) for k, v in params.items()}
                response = self.session.get(url, params=encoded_params)
                
                logger.debug(f"Response status: {response.status_code}")
                logger.debug(f"Response text: {response.text[:500]}...")
                
                # Handle HTTP errors
                if response.status_code == 429:
                    raise RateLimitError("API rate limit exceeded")
                elif response.status_code == 401:
                    raise AuthenticationError("Invalid API key or authentication failed")
                elif response.status_code != 200:
                    raise APIResponseError(f"HTTP {response.status_code}: {response.text}")
                
                # Parse JSON response
                try:
                    data = response.json()
                except json.JSONDecodeError as e:
                    raise APIResponseError(f"Invalid JSON response: {e}")
                
                # Check API response code
                if data.get("code") != 1:
                    error_msg = data.get("message", "Unknown API error")
                    if "rate limit" in error_msg.lower():
                        raise RateLimitError(f"API rate limit: {error_msg}")
                    else:
                        raise APIResponseError(f"API error: {error_msg}")
                
                logger.debug(f"Request to {endpoint} successful")
                return data
                
            except (RateLimitError, AuthenticationError) as e:
                # Don't retry rate limit or auth errors
                logger.error(f"Request to {endpoint} failed: {e}")
                raise e
            except requests.RequestException as e:
                if attempt == retries:
                    logger.error(f"Request to {endpoint} failed after {retries + 1} attempts: {e}")
                    raise UtoolsError(f"Request failed: {e}")
                
                # Exponential backoff for retries
                wait_time = (2 ** attempt) * 1.0
                logger.warning(f"Request failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                time.sleep(wait_time)
        
        raise UtoolsError("Maximum retries exceeded")
    
    def search_tweets(self, keywords: str, count: int = 50, product: str = "Latest", 
                     cursor: Optional[str] = None, since: Optional[str] = None, 
                     phrase: Optional[str] = None) -> tuple[List[SearchResult], Optional[str]]:
        """
        Search for tweets using specified keywords.
        
        Args:
            keywords: Search keywords
            count: Maximum number of results to return
            product: Search product type (Latest, Top, etc.)
            cursor: Cursor for pagination (optional)
            since: Start time filter (optional, format: YYYY-MM-DD)
            phrase: Exact phrase to match (optional, for future use)
            
        Returns:
            Tuple of (List of SearchResult objects, next_cursor for pagination)
            
        Raises:
            UtoolsError: When search fails
        """
        logger.info(f"Searching tweets for keywords: '{keywords}'")
        
        params = {
            "words": keywords,
            "product": product,
            "count": count
        }
        
        # Add optional parameters if provided
        if cursor:
            params["cursor"] = cursor
        if since:
            params["since"] = since
        if phrase:
            params["phrase"] = phrase
        
        try:
            response = self._make_request("search", params)
            
            # Parse the nested JSON string in the "data" field
            search_data = json.loads(response["data"])
            results, next_cursor = self._parse_search_results_with_cursor(search_data)
            
            logger.info(f"Found {len(results)} tweets for keywords: '{keywords}'")
            return results, next_cursor
            
        except json.JSONDecodeError as e:
            raise APIResponseError(f"Failed to parse search response data: {e}")
        except Exception as e:
            raise UtoolsError(f"Search failed for keywords '{keywords}': {e}")
    
    def search_tweets_paginated(self, keywords: str, max_results: int = 200, 
                               product: str = "Latest", since: Optional[str] = None,
                               phrase: Optional[str] = None, 
                               time_filter_seconds: Optional[int] = None) -> List[SearchResult]:
        """
        Search for tweets with automatic pagination to get more results.
        
        Args:
            keywords: Search keywords
            max_results: Maximum total results to return across all pages
            product: Search product type (Latest, Top, etc.)
            since: Start time filter (optional, format: YYYY-MM-DD)
            phrase: Exact phrase to match (optional, for future use)
            time_filter_seconds: Filter tweets by age in seconds (stop pagination when tweets are too old)
            
        Returns:
            List of SearchResult objects (up to max_results)
            
        Raises:
            UtoolsError: When search fails
        """
        all_results = []
        cursor = None
        page_size = min(50, max_results)  # API typically limits to 50 per request
        max_pages = 5  # Limit to prevent infinite loops
        page_count = 0
        
        logger.info(f"Starting paginated search for '{keywords}' (max_results: {max_results})")
        
        # Calculate cutoff time for filtering
        cutoff_time = None
        if time_filter_seconds:
            cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=time_filter_seconds + 60)
            logger.info(f"Time filter: stopping when tweets are older than {cutoff_time} (including 60s processing buffer)")
        
        while len(all_results) < max_results and page_count < max_pages:
            try:
                page_count += 1
                
                # Calculate how many results we still need
                remaining = max_results - len(all_results)
                current_count = min(page_size, remaining)
                
                # Make the search request
                results, next_cursor = self.search_tweets(
                    keywords=keywords,
                    count=current_count,
                    product=product,
                    cursor=cursor,
                    since=since,
                    phrase=phrase
                )
                
                if not results:
                    logger.info("No more results found, stopping pagination")
                    break
                
                # Apply time-based filtering during pagination
                filtered_results = []
                stop_pagination = False
                
                for result in results:
                    if cutoff_time:
                        try:
                            # Parse tweet creation time
                            tweet_time = datetime.strptime(result.created_at, '%a %b %d %H:%M:%S %z %Y')
                            if tweet_time < cutoff_time:
                                logger.info(f"Found tweet older than cutoff ({tweet_time} < {cutoff_time}), stopping pagination")
                                stop_pagination = True
                                break
                        except ValueError:
                            # If we can't parse the time, include the tweet to be safe
                            logger.debug(f"Could not parse tweet time: {result.created_at}")
                    
                    filtered_results.append(result)
                
                all_results.extend(filtered_results)
                logger.info(f"Page {page_count}: Got {len(results)} results, kept {len(filtered_results)}, total: {len(all_results)}")
                
                # Stop pagination if we found tweets older than cutoff
                if stop_pagination:
                    logger.info("Stopping pagination due to time filter")
                    break
                
                # Check if we have a cursor for next page
                if not next_cursor:
                    logger.info("No next cursor found, stopping pagination")
                    break
                
                cursor = next_cursor
                
                # Small delay between pages to be respectful to API
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error during paginated search on page {page_count}: {e}")
                break
        
        logger.info(f"Paginated search completed: {len(all_results)} total results across {page_count} pages")
        return all_results
    
    def search_recent_tweets(self, keywords: str, monitoring_interval_seconds: int = 300, 
                           count: int = 50, product: str = "Latest") -> List[SearchResult]:
        """
        Search for recent tweets within the monitoring interval.
        
        Args:
            keywords: Search keywords
            monitoring_interval_seconds: How far back to search in seconds (default: 300 = 5 minutes)
            count: Maximum number of results to return
            product: Search product type (Latest, Top, etc.)
            
        Returns:
            List of SearchResult objects
            
        Note:
            Due to API limitations, time filtering is done at day level.
            For precise minute-level filtering, additional client-side filtering
            of results may be needed based on created_at timestamps.
        """
        logger.info(f"Searching recent tweets for keywords: '{keywords}'")
        
        # Skip the since parameter as it causes "Unknown API error"
        # Instead, we'll filter client-side based on created_at timestamps
        results, _ = self.search_tweets(
            keywords=keywords,
            count=count,
            product=product
        )
        return results
    
    def search_recent_tweets_paginated(self, keywords: str, monitoring_interval_seconds: int = 300,
                                     max_results: int = 200, product: str = "Latest") -> List[SearchResult]:
        """
        Search for recent tweets with both time filtering and pagination.
        Convenience method that combines search_recent_tweets and search_tweets_paginated.
        
        Args:
            keywords: Search keywords
            monitoring_interval_seconds: How far back to search in seconds (default: 300 = 5 minutes)
            max_results: Maximum total results to return across all pages
            product: Search product type (Latest, Top, etc.)
            
        Returns:
            List of SearchResult objects
        """
        logger.info(f"Searching recent tweets with pagination for keywords: '{keywords}'")
        
        # Skip the since parameter as it causes "Unknown API error"
        # Instead, we'll filter client-side during pagination based on created_at timestamps
        return self.search_tweets_paginated(
            keywords=keywords,
            max_results=max_results,
            product=product,
            time_filter_seconds=monitoring_interval_seconds
        )
    
    def _parse_search_results(self, search_data: Dict[str, Any]) -> List[SearchResult]:
        """
        Parse complex Utools search response to extract tweet data (backward compatibility).
        
        Args:
            search_data: Parsed search response data
            
        Returns:
            List of SearchResult objects
        """
        results, _ = self._parse_search_results_with_cursor(search_data)
        return results
    
    def _parse_search_results_with_cursor(self, search_data: Dict[str, Any]) -> tuple[List[SearchResult], Optional[str]]:
        """
        Parse complex Utools search response to extract tweet data and cursor.
        
        Args:
            search_data: Parsed search response data
            
        Returns:
            Tuple of (List of SearchResult objects, next_cursor for pagination)
        """
        results = []
        next_cursor = None
        
        try:
            timeline = search_data["data"]["search_by_raw_query"]["search_timeline"]["timeline"]
            
            for instruction in timeline["instructions"]:
                if instruction["type"] == "TimelineAddEntries":
                    for entry in instruction["entries"]:
                        if entry["entryId"].startswith("tweet-"):
                            try:
                                tweet_result = entry["content"]["itemContent"]["tweet_results"]["result"]
                                if tweet_result["__typename"] == "Tweet":
                                    # Extract tweet data
                                    tweet_id = tweet_result["rest_id"]
                                    content = tweet_result["legacy"]["full_text"]
                                    author_username = tweet_result["core"]["user_results"]["result"]["legacy"]["screen_name"]
                                    author_id = tweet_result["core"]["user_results"]["result"]["rest_id"]
                                    created_at = tweet_result["legacy"]["created_at"]
                                    tweet_url = f"https://x.com/{author_username}/status/{tweet_id}"
                                    
                                    results.append(SearchResult(
                                        tweet_id=tweet_id,
                                        content=content,
                                        author_username=author_username,
                                        author_id=author_id,
                                        created_at=created_at,
                                        tweet_url=tweet_url
                                    ))
                            except KeyError as e:
                                logger.warning(f"Failed to parse tweet entry: {e}")
                                continue
                        elif entry["entryId"].startswith("cursor-bottom-"):
                            # Extract cursor for pagination
                            try:
                                cursor_content = entry["content"]
                                if "value" in cursor_content:
                                    next_cursor = cursor_content["value"]
                                    logger.debug(f"Found next cursor: {next_cursor}")
                            except KeyError as e:
                                logger.debug(f"Could not extract cursor: {e}")
                                
        except KeyError as e:
            logger.error(f"Error parsing search results structure: {e}")
            
        return results, next_cursor
    
    def get_user_by_screen_name(self, screen_name: str) -> Optional[Dict[str, Any]]:
        """
        Get user information by screen name (username).
        
        Args:
            screen_name: X username (without @)
            
        Returns:
            User data dictionary or None if not found
            
        Raises:
            UtoolsError: When request fails
        """
        logger.info(f"Getting user info for: @{screen_name}")
        
        params = {"screenName": screen_name}
        
        try:
            response = self._make_request("userByScreenNameV2", params)
            
            # Parse the nested JSON string in the "data" field
            user_data = json.loads(response["data"])
            
            if "data" in user_data and "user" in user_data["data"]:
                user_info = user_data["data"]["user"]["result"]
                logger.info(f"Found user @{screen_name} with ID: {user_info['rest_id']}")
                return user_info
            else:
                logger.warning(f"User @{screen_name} not found")
                return None
                
        except json.JSONDecodeError as e:
            raise APIResponseError(f"Failed to parse user response data: {e}")
        except Exception as e:
            raise UtoolsError(f"Failed to get user @{screen_name}: {e}")
    
    def get_followers(self, user_id: str) -> List[str]:
        """
        Get list of follower IDs for a user.
        
        Args:
            user_id: X user ID
            
        Returns:
            List of follower user IDs as strings
            
        Raises:
            UtoolsError: When request fails
        """
        logger.info(f"Getting followers for user ID: {user_id}")
        
        params = {
            "userId": user_id
        }
        
        try:
            response = self._make_request("followersIds", params)
            
            # Parse the nested JSON string in the "data" field
            followers_data = json.loads(response["data"])
            
            if "ids" in followers_data:
                follower_ids = [str(fid) for fid in followers_data["ids"]]
                logger.info(f"Found {len(follower_ids)} followers for user {user_id}")
                return follower_ids
            else:
                logger.warning(f"No followers data found for user {user_id}")
                return []
                
        except json.JSONDecodeError as e:
            raise APIResponseError(f"Failed to parse followers response data: {e}")
        except Exception as e:
            raise UtoolsError(f"Failed to get followers for user {user_id}: {e}")
    
    def verify_user_follows(self, user_handle: str, target_user_id: str = "1260183271930904577") -> bool:
        """
        Verify if a user follows a specific target user (@0xSky99 by default).
        
        Args:
            user_handle: Username to check (without @)
            target_user_id: ID of target user to check following status
            
        Returns:
            True if user follows target, False otherwise
            
        Raises:
            UtoolsError: When verification fails due to API errors
        """
        logger.info(f"Verifying if @{user_handle} follows user {target_user_id}")
        
        try:
            # Step 1: Get user ID from handle
            logger.info(f"Step 1: Getting user ID for @{user_handle}")
            user_info = self.get_user_by_screen_name(user_handle)
            if not user_info:
                logger.warning(f"User @{user_handle} not found")
                return False
            
            user_id = user_info["rest_id"]
            logger.info(f"Found user @{user_handle} with ID: {user_id}")
            
            # Step 2: Get target user's followers
            logger.info(f"Step 2: Getting followers for target user {target_user_id}")
            followers = self.get_followers(target_user_id)
            logger.info(f"Retrieved {len(followers)} followers for target user")
            
            # Step 3: Check if user is in followers list
            is_following = user_id in followers
            
            if is_following:
                logger.info(f"✅ @{user_handle} (ID: {user_id}) IS following user {target_user_id}")
            else:
                logger.info(f"❌ @{user_handle} (ID: {user_id}) is NOT following user {target_user_id}")
                # Log first few follower IDs for debugging
                if followers:
                    sample_followers = followers[:5]
                    logger.info(f"Sample follower IDs: {sample_followers}")
            
            return is_following
            
        except Exception as e:
            logger.error(f"Failed to verify if @{user_handle} follows {target_user_id}: {e}")
            raise UtoolsError(f"Follower verification failed: {e}")