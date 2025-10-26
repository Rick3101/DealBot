"""
Test database health check after migration
"""

import logging
import os
from dotenv import load_dotenv
from database import initialize_database
from database.schema import health_check_schema

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_health_check():
    """Test database health check."""
    logger.info("Testing database health check...")

    # Initialize database
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL not found in environment")
        return False

    initialize_database(database_url)

    try:
        # Run health check
        health_status = health_check_schema()

        logger.info("\n" + "="*60)
        logger.info("Database Health Check Results")
        logger.info("="*60)
        logger.info(f"Healthy: {health_status.get('healthy', False)}")
        logger.info(f"Message: {health_status.get('message', 'No message')}")

        if 'missing_tables' in health_status:
            logger.warning(f"Missing tables: {health_status['missing_tables']}")

        if 'tables_count' in health_status:
            logger.info(f"Total required tables: {health_status['tables_count']}")

        logger.info("="*60)

        if health_status.get('healthy'):
            logger.info("\nHealth check PASSED!")
            return True
        else:
            logger.error("\nHealth check FAILED!")
            return False

    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    import sys
    success = test_health_check()
    sys.exit(0 if success else 1)
