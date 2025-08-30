"""
Database models and utilities for Comet Invitation Hunter
"""
import os
import time
from datetime import datetime
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError, OperationalError, IntegrityError

import logging
import functools
from collections import namedtuple

# Handle welcome_email import for both local and Docker environments
try:
    from backend.welcome_email import welcome_email_sender
except ImportError:
    from welcome_email import welcome_email_sender

# Configure logging
logger = logging.getLogger(__name__)

# Simple retry configuration
RetryConfig = namedtuple('RetryConfig', ['max_retries', 'base_delay', 'max_delay', 'retryable_exceptions'])
DATABASE_RETRY_CONFIG = RetryConfig(
    max_retries=3,
    base_delay=1.0,
    max_delay=10.0,
    retryable_exceptions=(SQLAlchemyError, OperationalError)
)

def retry_with_backoff(config):
    """Simple retry decorator with exponential backoff"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(config.max_retries):
                try:
                    return func(*args, **kwargs)
                except config.retryable_exceptions as e:
                    if attempt < config.max_retries - 1:
                        wait_time = min(config.base_delay * (2 ** attempt), config.max_delay)
                        logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"All {config.max_retries} attempts failed: {e}")
                        raise
            return None
        return wrapper
    return decorator

# Database configuration - Use project root for consistent path
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(project_root, 'comet_hunter.db')}")

# SQLAlchemy setup
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    """User model for storing verified email addresses"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    verified_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class Post(Base):
    """Post model for storing processed X posts with invitation links"""
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    tweet_id = Column(String(50), unique=True, nullable=False, index=True)
    content = Column(Text, nullable=False)
    author_username = Column(String(50), nullable=False)
    post_type = Column(String(20), nullable=False)  # 'free' or 'conditional'
    invitation_link = Column(Text, nullable=True)
    tweet_url = Column(String(255), nullable=False)
    conditions = Column(Text, nullable=True)  # For conditional posts
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Post(id={self.id}, tweet_id={self.tweet_id}, type={self.post_type})>"


class EmailLog(Base):
    """Email log model for tracking notification batches"""
    __tablename__ = "email_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String(50), nullable=False, index=True)
    recipient_count = Column(Integer, nullable=False)
    posts_included = Column(Integer, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="sent")  # 'sent', 'failed', 'retrying'
    error_message = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<EmailLog(id={self.id}, batch_id={self.batch_id}, status={self.status})>"


# Database utility functions
def get_db() -> Session:
    """Get database session with automatic cleanup"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # Session will be closed by caller


@retry_with_backoff(DATABASE_RETRY_CONFIG._replace(
    retryable_exceptions=(SQLAlchemyError, OperationalError)
))
def get_db_with_retry() -> Optional[Session]:
    """Get database session with retry logic and exponential backoff"""
    try:
        db = SessionLocal()
        # Test the connection
        db.execute(text("SELECT 1"))
        logger.debug("Database connection established successfully")
        return db
    except SQLAlchemyError as e:
        logger.error(f"Database connection failed: {e}")
        raise


def create_tables():
    """Create all database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Failed to create database tables: {e}")
        return False


def drop_tables():
    """Drop all database tables (for testing/reset)"""
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("Database tables dropped successfully")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Failed to drop database tables: {e}")
        return False


def init_database():
    """Initialize database with tables and any required data"""
    try:
        logger.info("Initializing database...")
        create_tables()
        logger.info("Database initialization completed")
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False


def execute_with_retry(db: Session, operation, max_retries: int = 3):
    """Execute database operation with retry logic"""
    for attempt in range(max_retries):
        try:
            result = operation()
            db.commit()
            return result
        except SQLAlchemyError as e:
            logger.error(f"Database operation attempt {attempt + 1} failed: {e}")
            db.rollback()
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error("All database operation attempts failed")
                raise e


def health_check() -> bool:
    """Check database connectivity and health"""
    try:
        db = get_db_with_retry()
        if db is None:
            return False
        
        # Test basic query
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


# Database operation helpers
def add_user(db: Session, email: str) -> Optional[User]:
    """Add a new user with retry logic and send welcome email"""
    def operation():
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            logger.info(f"User with email {email} already exists")
            return existing_user
        
        # Create new user
        user = User(email=email)
        db.add(user)
        db.flush()  # Get the ID without committing
        logger.info(f"Added new user: {email}")
        return user
    
    try:
        # # Check if user already exists before attempting creation
        # existing_user = db.query(User).filter(User.email == email).first()
        # if existing_user:
        #     logger.info(f"User with email {email} already exists")
        #     return existing_user
            
        # Create new user
        user = execute_with_retry(db, operation)
        if user:
            # This is a new user, send welcome email
            try:
                email_sent = welcome_email_sender.send_welcome_email(email)
                if email_sent:
                    logger.info(f"Welcome email sent successfully to new user: {email}")
                else:
                    logger.warning(f"Failed to send welcome email to new user: {email}")
            except Exception as e:
                logger.error(f"Error sending welcome email to {email}: {e}")
                # Don't fail user creation if email fails
        return user
    except SQLAlchemyError as e:
        logger.error(f"Failed to add user {email}: {e}")
        return None


def add_post(db: Session, tweet_id: str, content: str, author_username: str, 
             post_type: str, tweet_url: str, invitation_link: str = None, 
             conditions: str = None) -> Optional[Post]:
    """Add a new post with retry logic"""
    def operation():
        # Check if post already exists
        existing_post = db.query(Post).filter(Post.tweet_id == tweet_id).first()
        if existing_post:
            logger.info(f"Post with tweet_id {tweet_id} already exists")
            return existing_post
        
        # Create new post
        post = Post(
            tweet_id=tweet_id,
            content=content,
            author_username=author_username,
            post_type=post_type,
            tweet_url=tweet_url,
            invitation_link=invitation_link,
            conditions=conditions
        )
        db.add(post)
        db.flush()  # Get the ID without committing
        logger.info(f"Added new post: {tweet_id}")
        return post
    
    try:
        return execute_with_retry(db, operation)
    except SQLAlchemyError as e:
        logger.error(f"Failed to add post {tweet_id}: {e}")
        return None


def log_email_batch(db: Session, batch_id: str, recipient_count: int, 
                   posts_included: int, status: str = "sent", 
                   error_message: str = None) -> Optional[EmailLog]:
    """Log email batch with retry logic"""
    def operation():
        email_log = EmailLog(
            batch_id=batch_id,
            recipient_count=recipient_count,
            posts_included=posts_included,
            status=status,
            error_message=error_message
        )
        db.add(email_log)
        db.flush()
        logger.info(f"Logged email batch: {batch_id}")
        return email_log
    
    try:
        return execute_with_retry(db, operation)
    except SQLAlchemyError as e:
        logger.error(f"Failed to log email batch {batch_id}: {e}")
        return None


def get_all_users(db: Session) -> List[User]:
    """Get all verified users"""
    try:
        return db.query(User).all()
    except SQLAlchemyError as e:
        logger.error(f"Failed to get users: {e}")
        return []


def is_post_processed(db: Session, tweet_id: str) -> bool:
    """Check if a post has already been processed"""
    try:
        post = db.query(Post).filter(Post.tweet_id == tweet_id).first()
        return post is not None
    except SQLAlchemyError as e:
        logger.error(f"Failed to check if post {tweet_id} is processed: {e}")
        return False


def get_recent_posts(db: Session, hours: int = 24) -> List[Post]:
    """Get posts from the last N hours"""
    try:
        from datetime import timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return db.query(Post).filter(Post.created_at >= cutoff_time).all()
    except SQLAlchemyError as e:
        logger.error(f"Failed to get recent posts: {e}")
        return []