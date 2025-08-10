"""
Database migration utilities for Comet Invitation Hunter
"""
import logging
import sqlite3
from typing import List, Callable
from datetime import datetime
from database import engine, SessionLocal, Base
from sqlalchemy import text

logger = logging.getLogger(__name__)


class Migration:
    """Represents a single database migration"""
    
    def __init__(self, version: str, description: str, up_func: Callable, down_func: Callable = None):
        self.version = version
        self.description = description
        self.up_func = up_func
        self.down_func = down_func
        self.applied_at = None


class MigrationManager:
    """Manages database migrations"""
    
    def __init__(self):
        self.migrations: List[Migration] = []
        self._ensure_migration_table()
    
    def _ensure_migration_table(self):
        """Create migrations table if it doesn't exist"""
        try:
            with engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS migrations (
                        version VARCHAR(50) PRIMARY KEY,
                        description TEXT NOT NULL,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to create migrations table: {e}")
            raise
    
    def add_migration(self, migration: Migration):
        """Add a migration to the manager"""
        self.migrations.append(migration)
    
    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migration versions"""
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT version FROM migrations ORDER BY applied_at"))
                return [row[0] for row in result]
        except Exception as e:
            logger.error(f"Failed to get applied migrations: {e}")
            return []
    
    def get_pending_migrations(self) -> List[Migration]:
        """Get list of pending migrations"""
        applied = set(self.get_applied_migrations())
        return [m for m in self.migrations if m.version not in applied]
    
    def apply_migration(self, migration: Migration) -> bool:
        """Apply a single migration"""
        try:
            logger.info(f"Applying migration {migration.version}: {migration.description}")
            
            # Execute the migration
            migration.up_func()
            
            # Record the migration as applied
            with engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO migrations (version, description, applied_at)
                    VALUES (:version, :description, :applied_at)
                """), {
                    "version": migration.version,
                    "description": migration.description,
                    "applied_at": datetime.utcnow()
                })
                conn.commit()
            
            logger.info(f"Migration {migration.version} applied successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply migration {migration.version}: {e}")
            return False
    
    def rollback_migration(self, migration: Migration) -> bool:
        """Rollback a single migration"""
        if not migration.down_func:
            logger.error(f"Migration {migration.version} has no rollback function")
            return False
        
        try:
            logger.info(f"Rolling back migration {migration.version}: {migration.description}")
            
            # Execute the rollback
            migration.down_func()
            
            # Remove the migration record
            with engine.connect() as conn:
                conn.execute(text("DELETE FROM migrations WHERE version = :version"), 
                           {"version": migration.version})
                conn.commit()
            
            logger.info(f"Migration {migration.version} rolled back successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rollback migration {migration.version}: {e}")
            return False
    
    def migrate_up(self) -> bool:
        """Apply all pending migrations"""
        pending = self.get_pending_migrations()
        
        if not pending:
            logger.info("No pending migrations")
            return True
        
        logger.info(f"Applying {len(pending)} pending migrations")
        
        for migration in pending:
            if not self.apply_migration(migration):
                logger.error(f"Migration failed at {migration.version}")
                return False
        
        logger.info("All migrations applied successfully")
        return True
    
    def get_migration_status(self) -> dict:
        """Get current migration status"""
        applied = self.get_applied_migrations()
        pending = self.get_pending_migrations()
        
        return {
            "total_migrations": len(self.migrations),
            "applied_count": len(applied),
            "pending_count": len(pending),
            "applied_versions": applied,
            "pending_versions": [m.version for m in pending]
        }


# Initialize migration manager
migration_manager = MigrationManager()


# Migration functions
def migration_001_initial_schema():
    """Initial schema creation"""
    logger.info("Creating initial database schema")
    Base.metadata.create_all(bind=engine)


def migration_002_add_conditions_column():
    """Add conditions column to posts table for conditional sharing posts"""
    logger.info("Adding conditions column to posts table")
    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text("PRAGMA table_info(posts)"))
        columns = [row[1] for row in result]
        
        if 'conditions' not in columns:
            conn.execute(text("ALTER TABLE posts ADD COLUMN conditions TEXT"))
            conn.commit()
            logger.info("Added conditions column to posts table")
        else:
            logger.info("Conditions column already exists")


def migration_003_add_error_message_to_email_logs():
    """Add error_message column to email_logs table"""
    logger.info("Adding error_message column to email_logs table")
    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text("PRAGMA table_info(email_logs)"))
        columns = [row[1] for row in result]
        
        if 'error_message' not in columns:
            conn.execute(text("ALTER TABLE email_logs ADD COLUMN error_message TEXT"))
            conn.commit()
            logger.info("Added error_message column to email_logs table")
        else:
            logger.info("Error_message column already exists")


# Register migrations
migration_manager.add_migration(Migration(
    version="001",
    description="Initial schema creation",
    up_func=migration_001_initial_schema
))

migration_manager.add_migration(Migration(
    version="002", 
    description="Add conditions column to posts table",
    up_func=migration_002_add_conditions_column
))

migration_manager.add_migration(Migration(
    version="003",
    description="Add error_message column to email_logs table", 
    up_func=migration_003_add_error_message_to_email_logs
))


def run_migrations():
    """Run all pending migrations"""
    return migration_manager.migrate_up()


def get_migration_status():
    """Get current migration status"""
    return migration_manager.get_migration_status()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database migration utility")
    parser.add_argument("--status", action="store_true", help="Show migration status")
    parser.add_argument("--migrate", action="store_true", help="Run pending migrations")
    
    args = parser.parse_args()
    
    if args.status:
        status = get_migration_status()
        print(f"Migration Status:")
        print(f"  Total migrations: {status['total_migrations']}")
        print(f"  Applied: {status['applied_count']}")
        print(f"  Pending: {status['pending_count']}")
        if status['pending_versions']:
            print(f"  Pending versions: {', '.join(status['pending_versions'])}")
    
    elif args.migrate:
        if run_migrations():
            print("Migrations completed successfully")
        else:
            print("Migration failed")
            exit(1)
    
    else:
        parser.print_help()