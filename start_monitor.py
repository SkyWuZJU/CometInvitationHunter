#!/usr/bin/env python3
"""
Startup script for the Comet Invitation Hunter monitoring service.
This script starts the background monitoring service that continuously
searches for new Comet invitation posts and sends email notifications.
"""

import sys
import os
import signal
import time
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print(f"\n🛑 Received signal {signum}, shutting down monitoring service...")
    sys.exit(0)

def main():
    """Main function to start the monitoring service"""
    print("🚀 Starting Comet Invitation Hunter Monitoring Service")
    print("=" * 60)
    
    try:
        # Import and initialize the monitor
        from monitor.main import CometMonitor
        
        print("✓ Importing monitoring components...")
        monitor = CometMonitor()
        
        print("✓ Monitor initialized successfully")
        print(f"✓ Monitoring interval: {monitor.monitoring_interval} seconds")
        print(f"✓ Search keywords: {len(monitor.search_keywords)} configured")
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        print("=" * 60)
        print("🔍 Starting continuous monitoring...")
        print("Press Ctrl+C to stop")
        print("=" * 60)
        
        # Start the monitoring loop (async)
        import asyncio
        asyncio.run(monitor.start_monitoring())
        
    except KeyboardInterrupt:
        print("\n🛑 Monitoring service stopped by user")
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("Make sure all dependencies are installed")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error starting monitoring service: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()