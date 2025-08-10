#!/usr/bin/env python3
"""
Database initialization script for Comet Invitation Hunter
"""
import sys
import os
import logging
from pathlib import Path

# Add the backend directory to the Python path
sys.path.append(str(Path(__file__).parent))

from database import init_database, health_check, create_tables, drop_tables

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main initialization function"""
    logger.info("Starting database initialization...")
    
    # Check if database file exists
    db_path = "comet_hunter.db"
    db_exists = os.path.exists(db_path)
    
    if db_exists:
        logger.info(f"Database file {db_path} already exists")
        
        # Perform health check
        if health_check():
            logger.info("Database health check passed")
        else:
            logger.error("Database health check failed")
            return False
    else:
        logger.info(f"Creating new database at {db_path}")
    
    # Initialize database
    if init_database():
        logger.info("Database initialization successful")
        
        # Verify initialization
        if health_check():
            logger.info("Database verification successful")
            return True
        else:
            logger.error("Database verification failed")
            return False
    else:
        logger.error("Database initialization failed")
        return False


def reset_database():
    """Reset database by dropping and recreating all tables"""
    logger.warning("Resetting database - all data will be lost!")
    
    if drop_tables():
        logger.info("Tables dropped successfully")
        if create_tables():
            logger.info("Tables recreated successfully")
            return True
        else:
            logger.error("Failed to recreate tables")
            return False
    else:
        logger.error("Failed to drop tables")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize Comet Hunter database")
    parser.add_argument("--reset", action="store_true", 
                       help="Reset database (drops all tables and data)")
    
    args = parser.parse_args()
    
    try:
        if args.reset:
            success = reset_database()
        else:
            success = main()
        
        if success:
            logger.info("Database operation completed successfully")
            sys.exit(0)
        else:
            logger.error("Database operation failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)