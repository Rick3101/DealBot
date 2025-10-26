"""
Backfill Owner Keys for Existing Expeditions

This migration generates owner keys for expeditions that don't have them.
This is necessary for the pirate name decryption feature to work.

Run this script once to update existing expeditions.
"""

import logging
import os
from dotenv import load_dotenv
from database import get_database_manager, initialize_database
from utils.encryption import generate_owner_key

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def backfill_owner_keys(dry_run=True):
    """
    Backfill owner keys for expeditions that don't have them.

    Args:
        dry_run: If True, only show what would be updated without making changes
    """
    db_manager = get_database_manager()

    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Find expeditions without owner keys
                cur.execute("""
                    SELECT id, owner_chat_id, name
                    FROM expeditions
                    WHERE owner_key IS NULL OR owner_key = ''
                    ORDER BY id
                """)

                expeditions_to_update = cur.fetchall()

                if not expeditions_to_update:
                    logger.info("No expeditions found without owner keys")
                    return

                logger.info(f"Found {len(expeditions_to_update)} expeditions without owner keys")

                for expedition_id, owner_chat_id, name in expeditions_to_update:
                    logger.info(f"  - Expedition {expedition_id}: '{name}' (owner: {owner_chat_id})")

                if dry_run:
                    logger.info("\nDRY RUN MODE - No changes made")
                    logger.info("Run with dry_run=False to actually update the database")
                    return

                # Generate and update owner keys
                updated_count = 0
                for expedition_id, owner_chat_id, name in expeditions_to_update:
                    try:
                        # Generate owner key
                        owner_key = generate_owner_key(expedition_id, owner_chat_id)

                        # Update expedition
                        cur.execute("""
                            UPDATE expeditions
                            SET owner_key = %s, owner_user_id = %s
                            WHERE id = %s
                        """, (owner_key, owner_chat_id, expedition_id))

                        updated_count += 1
                        logger.info(f"✓ Updated expedition {expedition_id}: '{name}'")

                    except Exception as e:
                        logger.error(f"✗ Failed to update expedition {expedition_id}: {e}")

                # Commit all changes
                conn.commit()
                logger.info(f"\nSuccessfully updated {updated_count} expeditions")

    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        raise


def verify_owner_keys():
    """Verify that all expeditions now have owner keys."""
    db_manager = get_database_manager()

    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Count expeditions with and without owner keys
                cur.execute("""
                    SELECT
                        COUNT(*) as total,
                        COUNT(owner_key) as with_keys,
                        COUNT(*) - COUNT(owner_key) as without_keys
                    FROM expeditions
                """)

                total, with_keys, without_keys = cur.fetchone()

                logger.info(f"\nVerification Results:")
                logger.info(f"  Total expeditions: {total}")
                logger.info(f"  With owner keys: {with_keys}")
                logger.info(f"  Without owner keys: {without_keys}")

                if without_keys == 0:
                    logger.info(f"\n✓ All expeditions have owner keys!")
                else:
                    logger.warning(f"\n⚠ {without_keys} expeditions still missing owner keys")

    except Exception as e:
        logger.error(f"Verification failed: {e}", exc_info=True)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Backfill owner keys for expeditions")
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be updated without making changes'
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify owner keys after migration'
    )

    args = parser.parse_args()

    logger.info("="*60)
    logger.info("Expedition Owner Key Backfill Migration")
    logger.info("="*60)

    # Initialize database
    try:
        logger.info("Initializing database connection...")
        initialize_database()
        logger.info("Database initialized successfully\n")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        exit(1)

    if args.verify:
        verify_owner_keys()
    else:
        backfill_owner_keys(dry_run=args.dry_run)

        if not args.dry_run:
            logger.info("\nVerifying changes...")
            verify_owner_keys()

    logger.info("="*60)
    logger.info("Migration complete")
    logger.info("="*60)
