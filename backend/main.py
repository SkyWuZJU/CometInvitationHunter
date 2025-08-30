"""
FastAPI backend service for Comet Invitation Hunter.
Handles user verification and provides health monitoring.
"""

import traceback
from typing import Optional
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy.orm import Session

import sys
import os

# Import configuration and modules with proper path handling for Docker

try:
    from config import config
    from database import get_db, init_database, health_check, add_user
    from utools_client import UtoolsClient, UtoolsError, RateLimitError, AuthenticationError
    from twitter_oauth import TwitterOAuthClient, TwitterOAuthError, store_oauth_token_secret, get_oauth_token_secret, cleanup_oauth_token
except ImportError as e:
    logger.error(f"Import error: {e}")
    # Fallback for different import paths
    try:
        from backend.config import config
        from backend.database import get_db, init_database, health_check, add_user
        from backend.utools_client import UtoolsClient, UtoolsError, RateLimitError, AuthenticationError
        from backend.twitter_oauth import TwitterOAuthClient, TwitterOAuthError, store_oauth_token_secret, get_oauth_token_secret, cleanup_oauth_token
    except ImportError:
        # Last resort - try relative imports
        from .config import config
        from .database import get_db, init_database, health_check, add_user
        from .utools_client import UtoolsClient, UtoolsError, RateLimitError, AuthenticationError
        from .twitter_oauth import TwitterOAuthClient, TwitterOAuthError, store_oauth_token_secret, get_oauth_token_secret, cleanup_oauth_token

# Configure basic logging
import logging
from contextlib import contextmanager

# Set up basic logging
logging.basicConfig(
    level=getattr(logging, config.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Simple error context manager
@contextmanager
def error_context(operation, logger_instance, severity=None, reraise=True):
    try:
        yield
    except Exception as e:
        logger_instance.error(f"Error in {operation}: {e}")
        if reraise:
            raise

# Mock service monitor for now
class MockServiceMonitor:
    def __init__(self, service_name=None):
        self.monitoring_active = False
        self.service_name = service_name
        self.health_checker = MockHealthChecker()
    
    def start_monitoring(self, interval=30):
        self.monitoring_active = True
        logger.info(f"Service monitoring started for {self.service_name} (mock)")
    
    def stop_monitoring(self):
        self.monitoring_active = False
        logger.info(f"Service monitoring stopped for {self.service_name} (mock)")

class MockHealthChecker:
    def __init__(self):
        self.checks = {}
    
    def register_check(self, name, check_func, interval=30):
        self.checks[name] = {"func": check_func, "interval": interval}
        logger.info(f"Health check registered: {name} (mock)")

class MockGracefulDegradation:
    def __init__(self, service_name):
        self.service_name = service_name
        logger.info(f"Graceful degradation initialized for {service_name} (mock)")

service_monitor = MockServiceMonitor()

# Initialize service components with error handling
try:
    utools_client = UtoolsClient(
        api_key=config.utools_api_key,
        base_url=config.utools_base_url
    )
    logger.info("Utools client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Utools client: {e}")
    utools_client = None

try:
    twitter_oauth = TwitterOAuthClient(
        consumer_key=config.twitter_consumer_key,
        consumer_secret=config.twitter_consumer_secret,
        callback_url=config.twitter_callback_url
    )
    logger.info("Twitter OAuth client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Twitter OAuth client: {e}")
    twitter_oauth = None

# Initialize service monitoring
service_monitor = MockServiceMonitor("backend-api")

# Register health checks (mock functions will be defined below)
service_monitor.health_checker.register_check("database", lambda: health_check(), interval=30)
service_monitor.health_checker.register_check("utools_api", lambda: True, interval=60)
service_monitor.health_checker.register_check("email_service", lambda: True, interval=120)

# Initialize graceful degradation
graceful_degradation = MockGracefulDegradation("backend-api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown tasks"""
    # Startup
    logger.info("Starting Comet Invitation Hunter backend service...")
    
    # Initialize database
    if not init_database():
        logger.error("Failed to initialize database")
        raise RuntimeError("Database initialization failed")
    
    logger.info("Backend service started successfully")
    yield
    
    # Shutdown
    logger.info("Shutting down backend service...")


# Pydantic models for request/response validation
class UserVerificationRequest(BaseModel):
    """Request model for user verification endpoint"""
    email: EmailStr
    oauth_token: Optional[str] = None
    oauth_verifier: Optional[str] = None


class OAuthInitRequest(BaseModel):
    """Request model for OAuth initialization"""
    email: EmailStr


class OAuthInitResponse(BaseModel):
    """Response model for OAuth initialization"""
    success: bool
    oauth_url: Optional[str] = None
    error: Optional[str] = None


class FollowCheckRequest(BaseModel):
    """Request model for follow status check"""
    email: EmailStr
    screen_name: str


class FollowCheckResponse(BaseModel):
    """Response model for follow status check"""
    success: bool
    is_following: bool
    message: str


class CompleteVerificationRequest(BaseModel):
    """Request model for completing verification"""
    email: EmailStr


class UserVerificationResponse(BaseModel):
    """Response model for user verification endpoint"""
    success: bool
    message: str
    email: Optional[str] = None


class HealthResponse(BaseModel):
    """Response model for health check endpoint"""
    status: str
    database: bool
    utools_api: bool
    message: str


class ErrorResponse(BaseModel):
    """Standard error response model"""
    error: str
    message: str
    details: Optional[str] = None


# Initialize FastAPI app
app = FastAPI(
    title="Comet Invitation Hunter API",
    description="Backend service for monitoring and notifying about Comet browser invitations",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with consistent error format"""
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=f"HTTP_{exc.status_code}",
            message=exc.detail
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {exc}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred",
            details=str(exc) if config.log_level.upper() == "DEBUG" else None
        ).dict()
    )


# API Endpoints

@app.post(
    "/api/auth/twitter/init",
    response_model=OAuthInitResponse,
    status_code=status.HTTP_200_OK,
    summary="Initialize Twitter OAuth",
    description="Initialize Twitter OAuth flow and return authorization URL"
)
async def init_twitter_oauth(request: OAuthInitRequest):
    """
    Initialize Twitter OAuth flow.
    
    This endpoint:
    1. Validates the email address
    2. Generates Twitter OAuth authorization URL
    3. Returns the URL for frontend redirect
    
    The user will be redirected to Twitter for authorization.
    """
    logger.info(f"Initializing Twitter OAuth for email: {request.email}")
    
    try:
        # Validate Twitter OAuth configuration
        if not config.twitter_consumer_key or not config.twitter_consumer_secret:
            logger.error("Twitter OAuth credentials not configured")
            return OAuthInitResponse(
                success=False,
                error="Twitter OAuth is not properly configured. Please contact support."
            )
        
        # Get OAuth authorization URL
        authorization_url, oauth_token_secret = twitter_oauth.get_authorization_url()
        
        # Extract oauth_token from URL for storage
        from urllib.parse import urlparse, parse_qs
        parsed_url = urlparse(authorization_url)
        oauth_token = parse_qs(parsed_url.query).get('oauth_token', [None])[0]
        
        if oauth_token:
            # Store token secret temporarily (in production, use Redis or database)
            store_oauth_token_secret(oauth_token, oauth_token_secret)
        
        logger.info(f"Generated OAuth URL for email: {request.email}")
        return OAuthInitResponse(
            success=True,
            oauth_url=authorization_url
        )
        
    except TwitterOAuthError as e:
        logger.error(f"Twitter OAuth error: {e}")
        return OAuthInitResponse(
            success=False,
            error="Failed to initialize Twitter authentication. Please try again."
        )
    except Exception as e:
        logger.error(f"Unexpected error during OAuth init: {e}")
        return OAuthInitResponse(
            success=False,
            error="An unexpected error occurred. Please try again."
        )


@app.post(
    "/api/users/check-follow",
    response_model=FollowCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Check if user follows @0xSky99",
    description="Check following status without full OAuth flow"
)
async def check_follow_status(request: FollowCheckRequest):
    """
    Check if user follows @0xSky99 using Utools API.
    
    This endpoint allows re-checking follow status without going through
    the full OAuth flow again.
    """
    logger.info(f"Checking follow status for @{request.screen_name}")
    
    try:
        # Use Utools API to check following status with retry logic
        logger.info(f"Checking if @{request.screen_name} follows @0xSky99 (ID: {config.target_user_id})")
        
        # Try up to 2 times with a small delay (follow relationships might take time to propagate)
        import time
        max_retries = 2
        for attempt in range(max_retries):
            if attempt > 0:
                logger.info(f"Retry attempt {attempt} after 3 seconds...")
                time.sleep(3)
            
            is_following = utools_client.verify_user_follows(
                user_handle=request.screen_name,
                target_user_id=config.target_user_id
            )
            
            logger.info(f"Attempt {attempt + 1}: Utools API result for @{request.screen_name}: is_following={is_following}")
            
            if is_following:
                logger.info(f"@{request.screen_name} is now following @0xSky99")
                return FollowCheckResponse(
                    success=True,
                    is_following=True,
                    message="Great! You're now following @0xSky99. You can proceed."
                )
            elif attempt < max_retries - 1:
                logger.info(f"Not following yet, will retry in 3 seconds...")
        
        # If we get here, user is still not following after all retries
        logger.info(f"@{request.screen_name} is still not following @0xSky99 after {max_retries} attempts")
        return FollowCheckResponse(
            success=True,
            is_following=False,
            message=f"You still need to follow @0xSky99 on X to use this service. (Checked @{request.screen_name} at {datetime.now().strftime('%H:%M:%S')}). Note: It may take a few minutes for the follow to be detected."
        )
            
    except (UtoolsError, RateLimitError, AuthenticationError) as e:
        logger.error(f"Failed to check follow status: {e}")
        return FollowCheckResponse(
            success=False,
            is_following=False,
            message="Unable to check follow status. Please try again later."
        )
    except Exception as e:
        logger.error(f"Unexpected error checking follow status: {e}")
        return FollowCheckResponse(
            success=False,
            is_following=False,
            message="An unexpected error occurred. Please try again."
        )


@app.get(
    "/api/debug/followers/{user_id}",
    summary="Debug: Get followers for a user",
    description="Debug endpoint to check followers of a specific user"
)
async def debug_get_followers(user_id: str):
    """Debug endpoint to check followers"""
    try:
        followers = utools_client.get_followers(user_id)
        return {
            "user_id": user_id,
            "follower_count": len(followers),
            "followers": followers[:10],  # First 10 for debugging
            "target_user_in_followers": config.target_user_id in followers
        }
    except Exception as e:
        return {"error": str(e)}


@app.get(
    "/api/debug/user/{screen_name}",
    summary="Debug: Get user info by screen name",
    description="Debug endpoint to get user info"
)
async def debug_get_user(screen_name: str):
    """Debug endpoint to get user info"""
    try:
        user_info = utools_client.get_user_by_screen_name(screen_name)
        return {
            "screen_name": screen_name,
            "user_info": user_info
        }
    except Exception as e:
        return {"error": str(e)}


@app.get(
    "/api/debug/search",
    summary="Debug: Search tweets",
    description="Debug endpoint to test search functionality"
)
async def debug_search(keywords: str, count: int = 5):
    """Debug endpoint to test search"""
    try:
        results, next_cursor = utools_client.search_tweets(keywords, count)
        return {
            "keywords": keywords,
            "count": count,
            "results_found": len(results),
            "next_cursor": next_cursor,
            "results": [{"content": r.content, "author": r.author_username, "tweet_id": r.tweet_id} for r in results[:3]]
        }
    except Exception as e:
        return {"error": str(e)}


@app.post(
    "/api/users/complete-verification",
    response_model=UserVerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Complete user verification after follow check",
    description="Complete verification and store user email after follow status is confirmed"
)
async def complete_verification(request: CompleteVerificationRequest, db: Session = Depends(get_db)):
    """
    Complete user verification and store email after follow status is confirmed.
    """
    logger.info(f"Completing verification for email: {request.email}")
    
    try:
        # Store user email
        user = add_user(db, request.email)
        if user is None:
            logger.error(f"Failed to store user email: {request.email}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store user information. Please try again."
            )
        
        logger.info(f"Successfully stored user: {request.email}")
        return UserVerificationResponse(
            success=True,
            message="Verification successful! You will receive email notifications when new Comet invitations are found.",
            email=request.email
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during verification completion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during verification."
        )
    finally:
        db.close()


@app.post(
    "/api/users/verify",
    response_model=UserVerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify user and collect email",
    description="Verify that user follows @0xSky99 and store their email for notifications"
)
async def verify_user(
    request: UserVerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Verify user follows @0xSky99 using OAuth tokens and store email for notifications.
    
    This endpoint:
    1. Validates the provided email and OAuth tokens
    2. Uses Twitter OAuth to get user access tokens
    3. Verifies the user follows @0xSky99 using Twitter API
    4. Stores the verified email in the database
    5. Returns success/failure status with appropriate message
    
    Requirements covered: 1.1, 1.2, 1.3, 1.4, 1.5, 4.1, 4.2, 4.3
    """
    logger.info(f"Processing OAuth verification request for email: {request.email}")
    
    try:
        # Validate OAuth parameters
        if not request.oauth_token or not request.oauth_verifier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OAuth token and verifier are required."
            )
        
        # Get stored OAuth token secret
        oauth_token_secret = get_oauth_token_secret(request.oauth_token)
        if not oauth_token_secret:
            logger.error(f"OAuth token secret not found for token: {request.oauth_token}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OAuth token. Please try again."
            )
        
        try:
            # Exchange OAuth verifier for access token
            access_token, access_token_secret, user_info = twitter_oauth.get_access_token(
                request.oauth_token,
                oauth_token_secret,
                request.oauth_verifier
            )
            
            user_id = user_info.get('user_id')
            screen_name = user_info.get('screen_name')
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to get user information from Twitter."
                )
            
            logger.info(f"Successfully authenticated Twitter user: @{screen_name} (ID: {user_id})")
            
            # Verify user follows @0xSky99 using Utools API (fallback for limited API access)
            try:
                is_following = twitter_oauth.verify_user_follows(
                    access_token,
                    access_token_secret,
                    user_id,
                    config.target_user_id
                )
                logger.info(f"Twitter API verification successful for @{screen_name}")
            except TwitterOAuthError as twitter_error:
                logger.warning(f"Twitter API verification failed (likely due to API access level), using Utools API fallback: {twitter_error}")
                # Fallback to Utools API verification using screen_name
                try:
                    logger.info(f"Attempting Utools API verification for @{screen_name} following @0xSky99")
                    is_following = utools_client.verify_user_follows(
                        user_handle=screen_name,
                        target_user_id=config.target_user_id
                    )
                    logger.info(f"Utools API verification successful for @{screen_name}: following={is_following}")
                except (UtoolsError, RateLimitError, AuthenticationError) as utools_error:
                    logger.error(f"Both Twitter API and Utools API verification failed: {utools_error}")
                    raise TwitterOAuthError("Unable to verify following status. Please try again later.")
            
            if not is_following:
                logger.info(f"@{screen_name} is not following @0xSky99")
                # Store screen name for potential retry
                return UserVerificationResponse(
                    success=False,
                    message=f"You must follow @0xSky99 on X to use this service. Please follow the account and try again. (Authenticated as @{screen_name})"
                )
            
            # User is following, store email
            logger.info(f"@{screen_name} is following @0xSky99, storing email")
            
            user = add_user(db, request.email)
            if user is None:
                logger.error(f"Failed to store user email: {request.email}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to store user information. Please try again."
                )
            
            logger.info(f"Successfully verified and stored user: {request.email} (@{screen_name})")
            return UserVerificationResponse(
                success=True,
                message=f"Verification successful! You will receive email notifications when new Comet invitations are found.",
                email=request.email
            )
            
        except TwitterOAuthError as e:
            logger.error(f"Twitter OAuth error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Twitter authentication failed. Please try again."
            )
        finally:
            # Clean up stored OAuth token
            cleanup_oauth_token(request.oauth_token)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error during verification: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during verification."
        )
    finally:
        # Ensure database session is closed
        db.close()


@app.get(
    "/api/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check endpoint",
    description="Check the health status of the backend service and its dependencies"
)
async def health_check_endpoint():
    """
    Health check endpoint for service monitoring.
    
    This endpoint checks:
    1. Database connectivity
    2. Utools API accessibility
    3. Overall service status
    
    Returns detailed status information for monitoring purposes.
    
    Requirements covered: Service monitoring and health checks
    """
    logger.debug("Processing health check request")
    
    # Check database health
    db_healthy = health_check()
    
    # Check Utools API health (simple connectivity test)
    utools_healthy = False
    try:
        # Try a simple API call to test connectivity
        # We'll use a search with minimal parameters to avoid rate limiting
        utools_client._make_request("search", {
            "words": "test",
            "product": "Latest",
            "count": 1
        })
        utools_healthy = True
    except Exception as e:
        logger.warning(f"Utools API health check failed: {e}")
        utools_healthy = False
    
    # Determine overall status
    overall_healthy = db_healthy and utools_healthy
    
    status_code = status.HTTP_200_OK if overall_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    
    response = HealthResponse(
        status="healthy" if overall_healthy else "unhealthy",
        database=db_healthy,
        utools_api=utools_healthy,
        message="All systems operational" if overall_healthy else "Some systems are experiencing issues"
    )
    
    logger.info(f"Health check result: {response.status}")
    
    return JSONResponse(
        status_code=status_code,
        content=response.dict()
    )


# Unsubscribe endpoint
@app.get(
    "/api/unsubscribe",
    summary="Unsubscribe from notifications",
    description="Remove user email from notification list"
)
async def unsubscribe(email: str = None, batch: str = None, db: Session = Depends(get_db)):
    """
    Unsubscribe endpoint for removing users from email notifications.
    
    This is a placeholder implementation. In a full system, you would:
    1. Validate the unsubscribe request
    2. Remove the user from the database
    3. Show a confirmation page
    
    For now, this just returns a message.
    """
    logger.info(f"Unsubscribe request - email: {email}, batch: {batch}")
    
    return {
        "message": "Unsubscribe functionality will be implemented in a future update.",
        "email": email,
        "batch_id": batch,
        "status": "acknowledged"
    }


# Root endpoint for basic API information
@app.get("/", summary="API Information")
async def root():
    """Root endpoint providing basic API information"""
    return {
        "name": "Comet Invitation Hunter API",
        "version": "1.0.0",
        "description": "Backend service for monitoring Comet browser invitations",
        "endpoints": {
            "health": "/api/health",
            "oauth_init": "/api/auth/twitter/init",
            "verify": "/api/users/verify",
            "check_follow": "/api/users/check-follow",
            "complete_verification": "/api/users/complete-verification",
            "unsubscribe": "/api/unsubscribe"
        },
        "oauth_configured": bool(config.twitter_consumer_key and config.twitter_consumer_secret)
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on port {config.backend_port}")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=config.backend_port,
        reload=True,
        log_level=config.log_level.lower()
    )