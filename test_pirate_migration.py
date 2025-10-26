"""
Test script to verify pirate tables migration
"""

import logging
import os
from dotenv import load_dotenv
from database import initialize_database, get_db_manager
from services.brambler_service import BramblerService

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_migration():
    """Test the pirate migration."""
    logger.info("Testing pirate tables migration...")

    # Initialize database
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL not found in environment")
        return False

    initialize_database(database_url)

    try:
        # Create a test expedition first
        db_manager = get_db_manager()
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Create test expedition
                cursor.execute("""
                    INSERT INTO Expeditions (name, owner_chat_id, status, description)
                    VALUES (%s, %s, %s, %s) RETURNING id
                """, ("Test Migration Expedition", 12345, "active", "Test expedition for migration"))
                test_expedition_id = cursor.fetchone()[0]
                conn.commit()
                logger.info(f"Created test expedition with ID: {test_expedition_id}")

        # Test BramblerService methods
        brambler_service = BramblerService()

        # Test 1: Generate pirate names for expedition
        logger.info("\nTest 1: Generate pirate names for expedition")
        test_names = ["Alice", "Bob", "Charlie"]
        pirate_names = brambler_service.generate_pirate_names(
            expedition_id=test_expedition_id,
            original_names=test_names
        )
        logger.info(f"Generated {len(pirate_names)} pirate names")
        for pn in pirate_names:
            logger.info(f"  - {pn.original_name} -> {pn.pirate_name}")

        # Test 2: Get pirate name
        logger.info("\nTest 2: Get pirate name for expedition")
        pirate_name = brambler_service.get_pirate_name(test_expedition_id, "Alice")
        logger.info(f"Alice's pirate name: {pirate_name}")

        # Test 3: Get original name
        logger.info("\nTest 3: Get original name from pirate name")
        if pirate_name:
            original_name = brambler_service.get_original_name(test_expedition_id, pirate_name)
            logger.info(f"{pirate_name}'s original name: {original_name}")

        # Test 4: Get all expedition pirate names
        logger.info("\nTest 4: Get all expedition pirate names")
        all_pirates = brambler_service.get_expedition_pirate_names(test_expedition_id)
        logger.info(f"Total expedition pirates: {len(all_pirates)}")

        # Test 5: Remove pirate name
        logger.info("\nTest 5: Remove pirate name")
        success = brambler_service.remove_pirate_name(test_expedition_id, "Charlie")
        logger.info(f"Remove Charlie: {success}")

        # Test 6: Delete all expedition names
        logger.info("\nTest 6: Delete all expedition names")
        success = brambler_service.delete_expedition_names(test_expedition_id)
        logger.info(f"Delete all expedition names: {success}")

        # Verify deletion
        remaining = brambler_service.get_expedition_pirate_names(test_expedition_id)
        logger.info(f"Remaining pirates after deletion: {len(remaining)}")

        # Cleanup: Delete test expedition
        logger.info("\nCleaning up test expedition...")
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM Expeditions WHERE id = %s", (test_expedition_id,))
                conn.commit()
                logger.info(f"Deleted test expedition {test_expedition_id}")

        logger.info("\n" + "="*60)
        logger.info("All tests passed successfully!")
        logger.info("="*60)

        return True

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    import sys
    success = test_migration()
    sys.exit(0 if success else 1)
