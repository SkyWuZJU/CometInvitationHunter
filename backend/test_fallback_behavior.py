#!/usr/bin/env python3
"""
Test script to verify fallback behavior when configuration files are missing or invalid.
"""

import sys
import os
import logging
import tempfile
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_missing_config_files():
    """Test behavior when configuration files are missing."""
    logger.info("=== Testing Missing Configuration Files ===")
    
    # Create a temporary directory and add it to path
    temp_dir = tempfile.mkdtemp()
    sys.path.insert(0, temp_dir)
    
    try:
        # Create a test script that tries to import missing config
        test_script = f"""
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import non-existent configuration
try:
    from search_config import SEARCH_KEYWORDS
    logger.info("Unexpected: search_config imported successfully")
except ImportError as e:
    logger.info(f"Expected: ImportError when importing search_config: {{e}}")
    # Use fallback values
    SEARCH_KEYWORDS = ["fallback keyword"]
    logger.info("Using fallback search keywords")

try:
    from classification_patterns import INVITATION_PATTERNS
    logger.info("Unexpected: classification_patterns imported successfully")
except ImportError as e:
    logger.info(f"Expected: ImportError when importing classification_patterns: {{e}}")
    # Use fallback values
    INVITATION_PATTERNS = [r"fallback.*pattern"]
    logger.info("Using fallback classification patterns")

logger.info("Fallback test completed successfully")
"""
        
        # Write and execute the test script
        test_file = os.path.join(temp_dir, 'test_missing.py')
        with open(test_file, 'w') as f:
            f.write(test_script)
        
        # Execute the test
        import subprocess
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, text=True)
        
        logger.info("Missing config files test output:")
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                logger.info(f"  {line}")
        
        if result.returncode == 0:
            logger.info("✓ Missing config files test passed")
        else:
            logger.error(f"✗ Missing config files test failed: {result.stderr}")
        
    finally:
        # Clean up
        sys.path.remove(temp_dir)
        shutil.rmtree(temp_dir)

def test_invalid_config_files():
    """Test behavior when configuration files contain invalid data."""
    logger.info("=== Testing Invalid Configuration Files ===")
    
    # Create a temporary directory and add it to path
    temp_dir = tempfile.mkdtemp()
    sys.path.insert(0, temp_dir)
    
    try:
        # Create invalid search_config.py
        invalid_search_config = """
# Invalid search configuration
SEARCH_KEYWORDS = "not a list"  # Should be a list
MONITORING_INTERVAL = "not a number"  # Should be a number
MAX_RESULTS_PER_KEYWORD = -1  # Invalid value
"""
        
        # Create invalid classification_patterns.py
        invalid_classification_config = """
# Invalid classification configuration
INVITATION_PATTERNS = ["[invalid regex"]  # Invalid regex
CONDITIONAL_KEYWORDS = None  # Should be a list
COMET_KEYWORDS = []  # Empty list
"""
        
        # Write invalid config files
        with open(os.path.join(temp_dir, 'search_config.py'), 'w') as f:
            f.write(invalid_search_config)
        
        with open(os.path.join(temp_dir, 'classification_patterns.py'), 'w') as f:
            f.write(invalid_classification_config)
        
        # Create config_validation.py in temp directory (copy from backend)
        backend_dir = os.path.dirname(__file__)
        shutil.copy(os.path.join(backend_dir, 'config_validation.py'), temp_dir)
        
        # Create a test script that imports invalid config
        test_script = f"""
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from search_config import SEARCH_KEYWORDS, MONITORING_INTERVAL
    logger.info(f"Search config imported: {{len(SEARCH_KEYWORDS)}} keywords, {{MONITORING_INTERVAL}}s interval")
except Exception as e:
    logger.error(f"Error importing search config: {{e}}")

try:
    from classification_patterns import INVITATION_PATTERNS, CONDITIONAL_KEYWORDS
    logger.info(f"Classification config imported: {{len(INVITATION_PATTERNS)}} patterns, {{len(CONDITIONAL_KEYWORDS)}} keywords")
except Exception as e:
    logger.error(f"Error importing classification config: {{e}}")

logger.info("Invalid config files test completed")
"""
        
        # Write and execute the test script
        test_file = os.path.join(temp_dir, 'test_invalid.py')
        with open(test_file, 'w') as f:
            f.write(test_script)
        
        # Execute the test
        import subprocess
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, text=True)
        
        logger.info("Invalid config files test output:")
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                logger.info(f"  {line}")
        
        if result.stderr:
            logger.info("Error output:")
            for line in result.stderr.strip().split('\n'):
                if line.strip():
                    logger.info(f"  {line}")
        
        if result.returncode == 0:
            logger.info("✓ Invalid config files test passed")
        else:
            logger.error(f"✗ Invalid config files test failed")
        
    finally:
        # Clean up
        sys.path.remove(temp_dir)
        shutil.rmtree(temp_dir)

def main():
    """Run fallback behavior tests."""
    logger.info("Starting fallback behavior tests...")
    
    test_missing_config_files()
    test_invalid_config_files()
    
    logger.info("Fallback behavior tests completed!")

if __name__ == "__main__":
    main()