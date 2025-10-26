"""
Run Brambler Performance Optimization Migration
This script adds missing indexes to optimize the Brambler Management Console queries.
"""

import os
import sys
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_migration():
    """Run the Brambler performance optimization migration."""
    try:
        from database import initialize_database, get_db_manager

        # Initialize database connection
        logger.info("Initializing database connection...")
        initialize_database()

        db_manager = get_db_manager()

        # Read migration SQL
        migration_file = os.path.join(os.path.dirname(__file__), 'add_brambler_performance_indexes.sql')
        logger.info(f"Reading migration file: {migration_file}")

        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()

        # Execute migration
        logger.info("Executing migration...")
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Split and execute each statement
                statements = [s.strip() for s in migration_sql.split(';') if s.strip() and not s.strip().startswith('--')]

                for i, statement in enumerate(statements):
                    if statement:
                        logger.info(f"Executing statement {i+1}/{len(statements)}...")
                        logger.debug(f"SQL: {statement[:100]}...")
                        cur.execute(statement)

                conn.commit()

        logger.info("Migration completed successfully!")
        logger.info("Performance indexes have been added to the database.")
        logger.info("Please test the Brambler Management Console endpoints now.")

        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
