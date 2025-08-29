#!/usr/bin/env python3
"""
Startup script for the Comet Invitation Hunter backend service.
"""

import os
import sys
import logging
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(backend_dir.parent))

# Load environment configuration
try:
    from backend.config import config
except ImportError:
    from config import config

def main():
    """Start the FastAPI backend service"""
    
    # Load environment file if specified
    env_file = os.getenv('ENV_FILE')
    if env_file and os.path.exists(env_file):
        config.load_env_file(env_file)
        print(f"✓ Loaded environment from: {env_file}")
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 Starting Comet Invitation Hunter Backend Service")
    print("=" * 60)
    print(f"Port: {config.backend_port}")
    print(f"Database: {config.database_url}")
    print(f"Log Level: {config.log_level}")
    print(f"CORS Origins: {config.cors_origins}")
    print("=" * 60)
    
    # Import and run the FastAPI app
    import uvicorn
    try:
        from backend.main import app
    except ImportError:
        from main import app
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=config.backend_port,
        log_level=config.log_level.lower(),
        reload=False  # Set to True for development
    )

if __name__ == "__main__":
    main()