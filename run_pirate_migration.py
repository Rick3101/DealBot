"""
Pirate Tables Migration Runner
Safely migrates data from pirate_names to expedition_pirates table.
"""

import logging
import sys
import os
from dotenv import load_dotenv
from database import initialize_database, get_db_manager

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_migration():
    """Run the pirate tables migration."""
    logger.info("Starting pirate tables migration...")

    # Initialize database
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL not found in environment")
        return False

    initialize_database(database_url)
    db_manager = get_db_manager()

    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Step 1: Check current state
                logger.info("Checking current state...")

                cursor.execute("SELECT COUNT(*) FROM pirate_names WHERE expedition_id IS NOT NULL")
                pirate_names_expedition_count = cursor.fetchone()[0]
                logger.info(f"Pirate names (expedition-specific): {pirate_names_expedition_count}")

                cursor.execute("SELECT COUNT(*) FROM pirate_names WHERE expedition_id IS NULL")
                pirate_names_global_count = cursor.fetchone()[0]
                logger.info(f"Pirate names (global mappings): {pirate_names_global_count}")

                cursor.execute("SELECT COUNT(*) FROM expedition_pirates")
                expedition_pirates_count = cursor.fetchone()[0]
                logger.info(f"Expedition pirates: {expedition_pirates_count}")

                cursor.execute("SELECT COUNT(*) FROM item_mappings")
                item_mappings_count = cursor.fetchone()[0]
                logger.info(f"Item mappings: {item_mappings_count}")

                # Step 2: Migrate expedition-specific names
                logger.info("\nMigrating expedition-specific pirate names...")
                cursor.execute("""
                    INSERT INTO expedition_pirates (
                        expedition_id,
                        pirate_name,
                        original_name,
                        encrypted_identity,
                        joined_at
                    )
                    SELECT
                        expedition_id,
                        pirate_name,
                        original_name,
                        COALESCE(encrypted_mapping, ''),
                        created_at
                    FROM pirate_names
                    WHERE expedition_id IS NOT NULL
                    ON CONFLICT (expedition_id, original_name) DO NOTHING
                """)

                migrated_count = cursor.rowcount
                logger.info(f"Migrated {migrated_count} records to expedition_pirates")

                # Step 3: Verify migration
                logger.info("\nVerifying migration...")
                cursor.execute("SELECT COUNT(*) FROM expedition_pirates")
                new_expedition_pirates_count = cursor.fetchone()[0]
                logger.info(f"New expedition pirates count: {new_expedition_pirates_count}")

                # Step 4: Check for duplicates
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM pirate_names
                    WHERE expedition_id IS NOT NULL
                    AND (expedition_id, original_name) IN (
                        SELECT expedition_id, original_name
                        FROM expedition_pirates
                    )
                """)
                duplicate_count = cursor.fetchone()[0]
                logger.info(f"Records successfully migrated: {duplicate_count}")

                # Step 5: Show summary
                logger.info("\n" + "="*60)
                logger.info("MIGRATION SUMMARY")
                logger.info("="*60)
                logger.info(f"Total expedition-specific names in pirate_names: {pirate_names_expedition_count}")
                logger.info(f"Total global mappings in pirate_names: {pirate_names_global_count}")
                logger.info(f"Records migrated to expedition_pirates: {migrated_count}")
                logger.info(f"Total records in expedition_pirates: {new_expedition_pirates_count}")
                logger.info(f"Records in item_mappings: {item_mappings_count}")

                if duplicate_count == pirate_names_expedition_count:
                    logger.info("\n✓ All expedition-specific names successfully migrated!")
                else:
                    logger.warning(f"\n⚠ Warning: {pirate_names_expedition_count - duplicate_count} records not migrated")

                # Commit the transaction
                conn.commit()
                logger.info("\nMigration completed successfully!")

                return True

    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
