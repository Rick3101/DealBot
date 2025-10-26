"""
Fix owner_user_id column type in expeditions table

Telegram chat IDs can exceed 32-bit INTEGER range.
This script changes owner_user_id from INTEGER to BIGINT.
"""

import logging
from dotenv import load_dotenv
from database import get_database_manager, initialize_database

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fix_owner_user_id_type():
    """Change owner_user_id column from INTEGER to BIGINT."""

    logger.info("="*60)
    logger.info("Fix owner_user_id Column Type Migration")
    logger.info("="*60)

    # Initialize database
    try:
        logger.info("Initializing database connection...")
        initialize_database()
        logger.info("Database initialized successfully\n")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False

    db_manager = get_database_manager()

    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Check current column type
                cur.execute("""
                    SELECT data_type
                    FROM information_schema.columns
                    WHERE table_name = 'expeditions'
                    AND column_name = 'owner_user_id'
                """)

                result = cur.fetchone()
                if not result:
                    logger.error("Column owner_user_id does not exist in expeditions table")
                    return False

                current_type = result[0]
                logger.info(f"Current owner_user_id column type: {current_type}")

                if current_type == 'bigint':
                    logger.info("Column is already BIGINT - no migration needed")
                    return True

                # Change column type
                logger.info("Changing owner_user_id from INTEGER to BIGINT...")
                cur.execute("""
                    ALTER TABLE expeditions
                    ALTER COLUMN owner_user_id TYPE BIGINT
                """)

                # Verify the change
                cur.execute("""
                    SELECT data_type
                    FROM information_schema.columns
                    WHERE table_name = 'expeditions'
                    AND column_name = 'owner_user_id'
                """)

                new_type = cur.fetchone()[0]
                logger.info(f"New owner_user_id column type: {new_type}")

                # Commit the change
                conn.commit()
                logger.info("Successfully changed owner_user_id to BIGINT")
                return True

    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        return False
    finally:
        logger.info("="*60)
        logger.info("Migration complete")
        logger.info("="*60)


if __name__ == "__main__":
    success = fix_owner_user_id_type()
    exit(0 if success else 1)
