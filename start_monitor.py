#!/usr/bin/env python3
"""
Startup script for the Comet Invitation Hunter monitoring service.
"""

import os
import sys
import logging
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_environment():
    """Load environment variables from config files"""
    # Try to load development config first
    dev_config = Path(__file__).parent / "config" / "development.env"
    if dev_config.exists():
        logger.info(f"Loading development config from {dev_config}")
        with open(dev_config, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    else:
        logger.warning("Development config file not found")

def main():
    """Main entry point"""
    logger.info("Starting Comet Invitation Hunter monitoring service...")
    
    # Load environment configuration
    load_environment()
    
    # Import and run the monitor
    try:
        # Import here after path is set up
        import asyncio
        sys.path.append(os.path.join(os.path.dirname(__file__), 'monitor'))
        from monitor.main import main as monitor_main
        
        # Run the monitoring service
        asyncio.run(monitor_main())
        
    except ImportError as e:
        logger.error(f"Failed to import monitoring service: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Monitoring service failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()