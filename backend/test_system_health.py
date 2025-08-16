#!/usr/bin/env python3
"""
Comprehensive system health check for the email notification system.
"""

import logging
import sys
import os
import time

# Load environment configuration
def load_environment():
    """Load environment variables from config files"""
    dev_config = os.path.join(os.path.dirname(__file__), '..', 'config', 'development.env')
    if os.path.exists(dev_config):
        with open(dev_config, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

# Load environment before importing config
load_environment()

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from config import config
from database import health_check as db_health_check, get_db_with_retry, get_all_users
from utools_client import UtoolsClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_health():
    """Test database connectivity and health"""
    logger.info("🔍 Testing database health...")
    
    try:
        # Test basic connectivity
        if not db_health_check():
            logger.error("❌ Database health check failed")
            return False
        
        # Test user retrieval
        db = get_db_with_retry()
        if not db:
            logger.error("❌ Failed to get database connection")
            return False
        
        users = get_all_users(db)
        db.close()
        
        logger.info(f"✅ Database health: OK ({len(users)} users)")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database health check failed: {e}")
        return False

def test_utools_api_health():
    """Test Utools API connectivity and functionality"""
    logger.info("🔍 Testing Utools API health...")
    
    try:
        client = UtoolsClient(config.utools_api_key, config.utools_base_url)
        
        # Test basic search
        results, cursor = client.search_tweets("test", count=1)
        logger.info(f"✅ Utools API health: OK (search returned {len(results)} results)")
        return True
        
    except Exception as e:
        logger.error(f"❌ Utools API health check failed: {e}")
        return False

def test_resend_api_health():
    """Test Resend API configuration"""
    logger.info("🔍 Testing Resend API health...")
    
    try:
        if not config.resend_api_key:
            logger.error("❌ Resend API key not configured")
            return False
        
        if not config.from_email:
            logger.error("❌ From email not configured")
            return False
        
        # Test import
        import resend
        resend.api_key = config.resend_api_key
        
        logger.info(f"✅ Resend API health: OK (key: {config.resend_api_key[:10]}...)")
        return True
        
    except Exception as e:
        logger.error(f"❌ Resend API health check failed: {e}")
        return False

def test_monitoring_service_health():
    """Test monitoring service components"""
    logger.info("🔍 Testing monitoring service health...")
    
    try:
        # Import monitor components
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'monitor'))
        
        monitor_file = os.path.join(os.path.dirname(__file__), '..', 'monitor', 'main.py')
        import importlib.util
        spec = importlib.util.spec_from_file_location("monitor_main", monitor_file)
        monitor_main = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(monitor_main)
        
        # Test monitor initialization
        monitor = monitor_main.CometMonitor()
        
        logger.info(f"✅ Monitoring service health: OK")
        logger.info(f"   - Keywords: {len(monitor.search_keywords)}")
        logger.info(f"   - Interval: {monitor.monitoring_interval}s")
        return True
        
    except Exception as e:
        logger.error(f"❌ Monitoring service health check failed: {e}")
        return False

def test_configuration_completeness():
    """Test that all required configuration is present"""
    logger.info("🔍 Testing configuration completeness...")
    
    required_configs = [
        ('UTOOLS_API_KEY', config.utools_api_key),
        ('RESEND_API_KEY', config.resend_api_key),
        ('FROM_EMAIL', config.from_email),
        ('DATABASE_URL', config.database_url),
    ]
    
    missing_configs = []
    
    for name, value in required_configs:
        if not value:
            missing_configs.append(name)
    
    if missing_configs:
        logger.error(f"❌ Missing required configuration: {', '.join(missing_configs)}")
        return False
    
    logger.info("✅ Configuration completeness: OK")
    return True

def test_end_to_end_workflow_simulation():
    """Simulate the complete end-to-end workflow"""
    logger.info("🔍 Testing end-to-end workflow simulation...")
    
    try:
        # 1. Database connection
        db = get_db_with_retry()
        if not db:
            logger.error("❌ E2E: Database connection failed")
            return False
        
        users = get_all_users(db)
        db.close()
        
        # 2. API search
        client = UtoolsClient(config.utools_api_key, config.utools_base_url)
        results, cursor = client.search_tweets("comet", count=3)
        
        # 3. Classification (import components)
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'monitor'))
        
        monitor_file = os.path.join(os.path.dirname(__file__), '..', 'monitor', 'main.py')
        import importlib.util
        spec = importlib.util.spec_from_file_location("monitor_main", monitor_file)
        monitor_main = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(monitor_main)
        
        classifier = monitor_main.PostClassifier()
        classified_posts = []
        for result in results:
            classified = classifier.classify_post(result)
            if classified:
                classified_posts.append(classified)
        
        # 4. Email notification (mock)
        notifier = monitor_main.EmailNotifier()
        
        logger.info(f"✅ End-to-end workflow: OK")
        logger.info(f"   - Users: {len(users)}")
        logger.info(f"   - Search results: {len(results)}")
        logger.info(f"   - Classified posts: {len(classified_posts)}")
        return True
        
    except Exception as e:
        logger.error(f"❌ End-to-end workflow simulation failed: {e}")
        return False

def generate_health_report():
    """Generate a comprehensive health report"""
    logger.info("=" * 60)
    logger.info("🏥 COMET INVITATION HUNTER - SYSTEM HEALTH REPORT")
    logger.info("=" * 60)
    
    tests = [
        ("Database Health", test_database_health),
        ("Utools API Health", test_utools_api_health),
        ("Resend API Health", test_resend_api_health),
        ("Monitoring Service Health", test_monitoring_service_health),
        ("Configuration Completeness", test_configuration_completeness),
        ("End-to-End Workflow", test_end_to_end_workflow_simulation),
    ]
    
    results = {}
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            start_time = time.time()
            result = test_func()
            duration = time.time() - start_time
            
            results[test_name] = {
                'passed': result,
                'duration': duration
            }
            
            if result:
                passed += 1
            else:
                failed += 1
                
        except Exception as e:
            logger.error(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = {
                'passed': False,
                'duration': 0,
                'error': str(e)
            }
            failed += 1
    
    # Summary
    logger.info("=" * 60)
    logger.info("📊 HEALTH REPORT SUMMARY")
    logger.info("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result['passed'] else "❌ FAIL"
        duration = f"({result['duration']:.2f}s)"
        logger.info(f"{status} {test_name} {duration}")
        
        if not result['passed'] and 'error' in result:
            logger.info(f"     Error: {result['error']}")
    
    logger.info("=" * 60)
    logger.info(f"📈 OVERALL HEALTH: {passed}/{len(tests)} tests passed")
    
    if failed == 0:
        logger.info("🎉 SYSTEM STATUS: HEALTHY - All components working correctly!")
        logger.info("✅ The email notification system is ready for production use.")
    else:
        logger.info(f"⚠️  SYSTEM STATUS: DEGRADED - {failed} component(s) need attention")
        logger.info("❌ Please address the failed components before using the system.")
    
    logger.info("=" * 60)
    
    return failed == 0

def main():
    """Run comprehensive system health check"""
    logger.info("Starting comprehensive system health check...")
    
    if generate_health_report():
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())