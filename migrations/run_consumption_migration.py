"""
Migration Runner: Remove item_consumptions table and migrate to expedition_assignments
Date: 2025-11-03
Purpose: Consolidate consumption tracking into the modern assignment-based architecture
"""

import sys
import os
import logging
from pathlib import Path

# Add parent directory to path to import database modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_db_manager, initialize_database

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_item_consumptions_exists():
    """Check if item_consumptions table exists."""
    db_manager = get_db_manager()
    with db_manager.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'item_consumptions'
                );
            """)
            return cursor.fetchone()[0]


def get_record_counts():
    """Get record counts before migration."""
    db_manager = get_db_manager()
    counts = {}

    with db_manager.get_connection() as conn:
        with conn.cursor() as cursor:
            # Check if item_consumptions exists
            if check_item_consumptions_exists():
                cursor.execute("SELECT COUNT(*) FROM item_consumptions")
                counts['item_consumptions'] = cursor.fetchone()[0]
            else:
                counts['item_consumptions'] = 0

            cursor.execute("SELECT COUNT(*) FROM expedition_assignments")
            counts['expedition_assignments_before'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM expedition_payments")
            counts['expedition_payments_before'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM expedition_pirates")
            counts['expedition_pirates_before'] = cursor.fetchone()[0]

    return counts


def run_migration():
    """Run the full migration process."""
    logger.info("=" * 70)
    logger.info("STARTING MIGRATION: item_consumptions → expedition_assignments")
    logger.info("=" * 70)

    # Step 1: Check if table exists
    if not check_item_consumptions_exists():
        logger.info("✓ item_consumptions table does not exist - migration not needed or already completed")
        return True

    # Step 2: Get counts before migration
    logger.info("\nStep 1: Getting record counts before migration...")
    counts_before = get_record_counts()
    logger.info(f"  - item_consumptions: {counts_before['item_consumptions']} records")
    logger.info(f"  - expedition_assignments: {counts_before['expedition_assignments_before']} records")
    logger.info(f"  - expedition_payments: {counts_before['expedition_payments_before']} records")
    logger.info(f"  - expedition_pirates: {counts_before['expedition_pirates_before']} records")

    if counts_before['item_consumptions'] == 0:
        logger.info("\n✓ No records in item_consumptions to migrate")
        return True  # Don't drop here, let the main function handle it

    # Step 3: Read and execute migration SQL
    logger.info("\nStep 2: Running migration SQL script...")
    script_path = Path(__file__).parent / 'migrate_consumptions_to_assignments.sql'

    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            migration_sql = f.read()

        # Extract only the migration parts (not the drop statements)
        migration_parts = []
        current_section = []
        in_drop_section = False

        for line in migration_sql.split('\n'):
            if 'STEP 4:' in line or 'DROP' in line.upper():
                in_drop_section = True
            elif 'STEP 1:' in line or 'STEP 2:' in line:
                in_drop_section = False

            if not in_drop_section and line.strip() and not line.strip().startswith('--'):
                current_section.append(line)

        db_manager = get_db_manager()
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Execute the full migration script (without DROP statements)
                migration_sql_clean = '\n'.join(current_section)
                cursor.execute(migration_sql_clean)
                conn.commit()
                logger.info("  ✓ Migration SQL executed successfully")

    except Exception as e:
        logger.error(f"  ✗ Migration failed: {e}")
        return False

    # Step 4: Verify migration
    logger.info("\nStep 3: Verifying migration results...")
    counts_after = get_record_counts()
    logger.info(f"  - expedition_assignments: {counts_after['expedition_assignments_before']} records")
    logger.info(f"  - expedition_payments: {counts_after['expedition_payments_before']} records")
    logger.info(f"  - expedition_pirates: {counts_after['expedition_pirates_before']} records")

    # Calculate differences
    assignments_added = counts_after['expedition_assignments_before'] - counts_before['expedition_assignments_before']
    pirates_added = counts_after['expedition_pirates_before'] - counts_before['expedition_pirates_before']

    logger.info(f"\n  Migration Summary:")
    logger.info(f"  - Expedition assignments created: {assignments_added}")
    logger.info(f"  - Expedition pirates created: {pirates_added}")

    # Step 5: Check for unmigrated records
    logger.info("\nStep 4: Checking for unmigrated records...")
    db_manager = get_db_manager()
    with db_manager.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) as unmigrated_consumptions
                FROM item_consumptions ic
                WHERE NOT EXISTS (
                    SELECT 1 FROM expedition_assignments ea
                    JOIN expedition_pirates ep ON ea.pirate_id = ep.id
                    WHERE ea.expedition_id = ic.expedition_id
                        AND ep.pirate_name = ic.pirate_name
                        AND ea.expedition_item_id = ic.expedition_item_id
                        AND ea.assigned_at = ic.consumed_at
                )
            """)
            unmigrated = cursor.fetchone()[0]

            if unmigrated > 0:
                logger.warning(f"  ⚠ WARNING: {unmigrated} records were not migrated!")
                logger.warning("  Please review the migration script and data before dropping the table.")
                return False
            else:
                logger.info("  ✓ All records migrated successfully!")

    logger.info("\n" + "=" * 70)
    logger.info("MIGRATION COMPLETED SUCCESSFULLY")
    logger.info("=" * 70)
    logger.info("\nNext steps:")
    logger.info("1. Test your application to ensure everything works correctly")
    logger.info("2. Run drop_table() to remove the old item_consumptions table")
    logger.info("3. Or manually run the DROP statements from the SQL script")

    return True


def drop_table(force=False):
    """Drop the item_consumptions table and all related indexes."""
    logger.info("\n" + "=" * 70)
    logger.info("DROPPING item_consumptions TABLE")
    logger.info("=" * 70)

    if not check_item_consumptions_exists():
        logger.info("✓ Table already dropped or does not exist")
        return True

    if not force:
        logger.info("\nWARNING: This will permanently delete the item_consumptions table!")
        logger.info("Make sure you have:")
        logger.info("  1. Backed up your database")
        logger.info("  2. Verified the migration was successful")
        logger.info("  3. Tested your application")

        response = input("\nAre you sure you want to drop the table? (type 'YES' to confirm): ")

        if response != 'YES':
            logger.info("Table drop cancelled by user")
            return False
    else:
        logger.info("\nForce drop enabled - skipping confirmation...")

    db_manager = get_db_manager()
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Drop indexes first
                logger.info("\nDropping indexes...")
                indexes = [
                    'idx_itemconsumptions_expedition',
                    'idx_itemconsumptions_expeditionitem',
                    'idx_itemconsumptions_consumer',
                    'idx_itemconsumptions_payment',
                    'idx_itemconsumptions_consumed',
                    'idx_itemconsumptions_payment_date',
                    'idx_itemconsumptions_exp_consumer_date',
                    'idx_itemconsumptions_exp_payment_cost',
                    'idx_itemconsumptions_date_expedition',
                    'idx_consumptions_expedition_payment_consumed'
                ]

                for index in indexes:
                    try:
                        cursor.execute(f"DROP INDEX IF EXISTS {index}")
                        logger.info(f"  ✓ Dropped index: {index}")
                    except Exception as e:
                        logger.warning(f"  ⚠ Could not drop index {index}: {e}")

                # Drop table
                logger.info("\nDropping table...")
                cursor.execute("DROP TABLE IF EXISTS item_consumptions CASCADE")
                conn.commit()
                logger.info("  ✓ Table item_consumptions dropped successfully")

        logger.info("\n" + "=" * 70)
        logger.info("TABLE DROPPED SUCCESSFULLY")
        logger.info("=" * 70)
        return True

    except Exception as e:
        logger.error(f"\n✗ Failed to drop table: {e}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Migrate item_consumptions to expedition_assignments')
    parser.add_argument('--drop', action='store_true', help='Drop the item_consumptions table after confirming migration')
    parser.add_argument('--force-drop', action='store_true', help='Force drop the table without confirmation (dangerous!)')

    args = parser.parse_args()

    # Initialize database connection
    logger.info("Initializing database connection...")
    initialize_database()
    logger.info("Database connection initialized\n")

    # Run migration
    success = run_migration()

    if not success:
        logger.error("\nMigration failed. Please review the errors above.")
        sys.exit(1)

    # Drop table if requested
    if args.force_drop:
        drop_table(force=True)
    elif args.drop:
        drop_table(force=False)
    else:
        logger.info("\nMigration complete! To drop the old table, run:")
        logger.info("  python migrations/run_consumption_migration.py --drop")
