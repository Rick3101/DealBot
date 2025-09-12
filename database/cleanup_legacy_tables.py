"""
Database cleanup script to remove legacy tables that are no longer used.
"""

import logging
from database import get_db_manager

logger = logging.getLogger(__name__)


def cleanup_legacy_tables():
    """Remove legacy tables that are no longer used."""
    logger.info("Starting cleanup of legacy database tables...")
    
    db_manager = get_db_manager()
    
    # List of legacy tables to remove
    legacy_tables = [
        'FrasesStart',
        'frasesstart'  # lowercase version in case it exists
    ]
    
    cleanup_sql = """
    -- Drop legacy FrasesStart table if it exists
    DROP TABLE IF EXISTS FrasesStart CASCADE;
    DROP TABLE IF EXISTS frasesstart CASCADE;
    """
    
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Check which legacy tables exist
                for table in legacy_tables:
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = %s
                        );
                    """, (table,))
                    
                    exists = cursor.fetchone()[0]
                    if exists:
                        logger.info(f"Found legacy table: {table}")
                
                # Execute cleanup
                cursor.execute(cleanup_sql)
                conn.commit()
        
        logger.info("Legacy tables cleanup completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to cleanup legacy tables: {e}")
        return False


def verify_cleanup():
    """Verify that legacy tables have been removed."""
    logger.info("Verifying legacy tables cleanup...")
    
    db_manager = get_db_manager()
    legacy_tables = ['FrasesStart', 'frasesstart']
    
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                remaining_tables = []
                
                for table in legacy_tables:
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = %s
                        );
                    """, (table,))
                    
                    exists = cursor.fetchone()[0]
                    if exists:
                        remaining_tables.append(table)
                
                if remaining_tables:
                    logger.warning(f"Legacy tables still exist: {remaining_tables}")
                    return False
                else:
                    logger.info("All legacy tables successfully removed")
                    return True
                    
    except Exception as e:
        logger.error(f"Failed to verify cleanup: {e}")
        return False


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run cleanup
    success = cleanup_legacy_tables()
    if success:
        verify_cleanup()
    else:
        logger.error("Cleanup failed")