"""
Twitter OAuth 1.0a client for user authentication and verification.
"""

import logging
import requests
from typing import Optional, Tuple, Dict, Any
from requests_oauthlib import OAuth1Session
from urllib.parse import parse_qsl

logger = logging.getLogger(__name__)


class TwitterOAuthError(Exception):
    """Base exception for Twitter OAuth errors"""
    pass


class TwitterOAuthClient:
    """
    Twitter OAuth 1.0a client for authenticating users and verifying followers.
    
    This client handles the OAuth flow and uses the authenticated session
    to verify if users follow @0xSky99.
    """
    
    def __init__(self, consumer_key: str, consumer_secret: str, callback_url: str):
        """
        Initialize Twitter OAuth client.
        
        Args:
            consumer_key: Twitter API consumer key
            consumer_secret: Twitter API consumer secret
            callback_url: OAuth callback URL
        """
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.callback_url = callback_url
        
        # Twitter OAuth URLs
        self.request_token_url = "https://api.twitter.com/oauth/request_token"
        self.authorization_url = "https://api.twitter.com/oauth/authorize"
        self.access_token_url = "https://api.twitter.com/oauth/access_token"
        
        # Twitter API URLs
        self.api_base_url = "https://api.twitter.com/1.1"
        
    def get_authorization_url(self) -> Tuple[str, str]:
        """
        Get OAuth authorization URL and request token.
        
        Returns:
            Tuple of (authorization_url, oauth_token_secret)
            
        Raises:
            TwitterOAuthError: If request token request fails
        """
        try:
            # Create OAuth session
            oauth = OAuth1Session(
                self.consumer_key,
                client_secret=self.consumer_secret,
                callback_uri=self.callback_url
            )
            
            # Get request token
            response = oauth.fetch_request_token(self.request_token_url)
            oauth_token = response.get('oauth_token')
            oauth_token_secret = response.get('oauth_token_secret')
            
            if not oauth_token or not oauth_token_secret:
                raise TwitterOAuthError("Failed to get request token")
            
            # Generate authorization URL
            authorization_url = oauth.authorization_url(self.authorization_url)
            
            logger.info(f"Generated OAuth authorization URL for token: {oauth_token}")
            return authorization_url, oauth_token_secret
            
        except Exception as e:
            logger.error(f"Failed to get authorization URL: {e}")
            raise TwitterOAuthError(f"Failed to get authorization URL: {e}")
    
    def get_access_token(self, oauth_token: str, oauth_token_secret: str, oauth_verifier: str) -> Tuple[str, str, Dict[str, Any]]:
        """
        Exchange OAuth verifier for access token and get user info.
        
        Args:
            oauth_token: OAuth token from authorization
            oauth_token_secret: OAuth token secret from request token
            oauth_verifier: OAuth verifier from callback
            
        Returns:
            Tuple of (access_token, access_token_secret, user_info)
            
        Raises:
            TwitterOAuthError: If access token request fails
        """
        try:
            # Create OAuth session with request token
            oauth = OAuth1Session(
                self.consumer_key,
                client_secret=self.consumer_secret,
                resource_owner_key=oauth_token,
                resource_owner_secret=oauth_token_secret,
                verifier=oauth_verifier
            )
            
            # Get access token
            response = oauth.fetch_access_token(self.access_token_url)
            access_token = response.get('oauth_token')
            access_token_secret = response.get('oauth_token_secret')
            user_id = response.get('user_id')
            screen_name = response.get('screen_name')
            
            if not access_token or not access_token_secret:
                raise TwitterOAuthError("Failed to get access token")
            
            user_info = {
                'user_id': user_id,
                'screen_name': screen_name
            }
            
            logger.info(f"Successfully got access token for user: @{screen_name} (ID: {user_id})")
            return access_token, access_token_secret, user_info
            
        except Exception as e:
            logger.error(f"Failed to get access token: {e}")
            raise TwitterOAuthError(f"Failed to get access token: {e}")
    
    def verify_user_follows(self, access_token: str, access_token_secret: str, user_id: str, target_user_id: str) -> bool:
        """
        Verify if authenticated user follows target user.
        
        Args:
            access_token: User's OAuth access token
            access_token_secret: User's OAuth access token secret
            user_id: User's Twitter ID
            target_user_id: Target user's Twitter ID to check following
            
        Returns:
            True if user follows target, False otherwise
            
        Raises:
            TwitterOAuthError: If API request fails
        """
        try:
            # Create authenticated OAuth session
            oauth = OAuth1Session(
                self.consumer_key,
                client_secret=self.consumer_secret,
                resource_owner_key=access_token,
                resource_owner_secret=access_token_secret
            )
            
            # Check if user follows target
            url = f"{self.api_base_url}/friendships/show.json"
            params = {
                'source_id': user_id,
                'target_id': target_user_id
            }
            
            response = oauth.get(url, params=params)
            
            if response.status_code != 200:
                logger.error(f"Twitter API error: {response.status_code} - {response.text}")
                raise TwitterOAuthError(f"Twitter API error: {response.status_code}")
            
            data = response.json()
            relationship = data.get('relationship', {})
            source = relationship.get('source', {})
            following = source.get('following', False)
            
            logger.info(f"User {user_id} following status for {target_user_id}: {following}")
            return following
            
        except Exception as e:
            logger.error(f"Failed to verify following status: {e}")
            raise TwitterOAuthError(f"Failed to verify following status: {e}")


# In-memory storage for OAuth tokens (in production, use Redis or database)
oauth_token_storage: Dict[str, str] = {}


def store_oauth_token_secret(oauth_token: str, oauth_token_secret: str) -> None:
    """Store OAuth token secret temporarily"""
    oauth_token_storage[oauth_token] = oauth_token_secret


def get_oauth_token_secret(oauth_token: str) -> Optional[str]:
    """Retrieve OAuth token secret"""
    return oauth_token_storage.get(oauth_token)


def cleanup_oauth_token(oauth_token: str) -> None:
    """Clean up stored OAuth token secret"""
    oauth_token_storage.pop(oauth_token, None)