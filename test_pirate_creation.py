"""
Test script for pirate creation functionality.
Tests the new create_pirate method in BramblerService.
"""

import logging
from services.brambler_service import BramblerService
from services.expedition_service import ExpeditionService
from database import get_db_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_create_pirate():
    """Test pirate creation with auto-generated and custom names."""
    print("\n" + "="*60)
    print("PIRATE CREATION TEST")
    print("="*60 + "\n")

    try:
        # Initialize services
        brambler_service = BramblerService()
        expedition_service = ExpeditionService()

        # Get a test expedition
        print("1. Getting test expedition...")
        expeditions = expedition_service.get_all_expeditions()
        if not expeditions:
            print("   ERROR: No expeditions found. Please create an expedition first.")
            return

        test_expedition = expeditions[0]
        expedition_id = test_expedition.id
        print(f"   Using expedition: #{expedition_id} - {test_expedition.name}")

        # Test 1: Create pirate with auto-generated name
        print("\n2. Creating pirate with AUTO-GENERATED name...")
        original_name_1 = "TestBuyer_AutoGen"
        result_1 = brambler_service.create_pirate(
            expedition_id=expedition_id,
            original_name=original_name_1
        )

        if result_1:
            print(f"   SUCCESS: Created pirate")
            print(f"   - ID: {result_1['id']}")
            print(f"   - Original Name: {result_1['original_name']}")
            print(f"   - Pirate Name: {result_1['pirate_name']}")
            print(f"   - Expedition ID: {result_1['expedition_id']}")
        else:
            print("   ERROR: Failed to create pirate with auto-generated name")

        # Test 2: Create pirate with custom name
        print("\n3. Creating pirate with CUSTOM name...")
        original_name_2 = "TestBuyer_Custom"
        custom_pirate_name = "Capitao Teste o Magnifico"
        result_2 = brambler_service.create_pirate(
            expedition_id=expedition_id,
            original_name=original_name_2,
            pirate_name=custom_pirate_name
        )

        if result_2:
            print(f"   SUCCESS: Created pirate")
            print(f"   - ID: {result_2['id']}")
            print(f"   - Original Name: {result_2['original_name']}")
            print(f"   - Pirate Name: {result_2['pirate_name']}")
            print(f"   - Expedition ID: {result_2['expedition_id']}")
        else:
            print("   ERROR: Failed to create pirate with custom name")

        # Test 3: Try to create duplicate (should fail)
        print("\n4. Testing duplicate prevention...")
        result_3 = brambler_service.create_pirate(
            expedition_id=expedition_id,
            original_name=original_name_1  # Same as test 1
        )

        if result_3:
            print("   ERROR: Duplicate pirate was created (should have been prevented)")
        else:
            print("   SUCCESS: Duplicate creation prevented as expected")

        # Test 4: Get all pirates for the expedition
        print("\n5. Retrieving all pirates for expedition...")
        all_pirates = brambler_service.get_expedition_pirate_names(expedition_id)
        print(f"   Total pirates in expedition: {len(all_pirates)}")
        for pirate in all_pirates:
            if pirate.original_name in [original_name_1, original_name_2]:
                print(f"   - {pirate.pirate_name} (original: {pirate.original_name})")

        # Cleanup
        print("\n6. Cleaning up test data...")
        db_manager = get_db_manager()
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM expedition_pirates
                    WHERE expedition_id = %s AND original_name IN (%s, %s)
                """, (expedition_id, original_name_1, original_name_2))
                conn.commit()
                print(f"   Cleaned up {cur.rowcount} test pirates")

        print("\n" + "="*60)
        print("TEST COMPLETED SUCCESSFULLY")
        print("="*60 + "\n")

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\nERROR: Test failed - {e}\n")


if __name__ == "__main__":
    test_create_pirate()
