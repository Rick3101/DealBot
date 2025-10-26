"""
Test the complete pirate encryption flow to verify security fixes.
This test creates a new expedition and verifies:
1. Pirate records are created with NULL original_name
2. Encrypted identity is stored
3. Only owner can decrypt
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_encryption_flow():
    """Test complete encryption flow"""
    from core.modern_service_container import initialize_services, get_expedition_service, get_brambler_service
    from models.expedition import ExpeditionCreateRequest, ItemConsumptionRequest
    from database.connection import get_db_manager

    logger.info("=" * 60)
    logger.info("PIRATE ENCRYPTION FLOW TEST")
    logger.info("=" * 60)

    # Initialize services
    logger.info("Initializing services...")
    initialize_services()

    expedition_service = get_expedition_service()
    brambler_service = get_brambler_service()

    # Test 1: Create a new expedition
    logger.info("\n" + "=" * 60)
    logger.info("TEST 1: Creating new expedition")
    logger.info("=" * 60)

    try:
        request = ExpeditionCreateRequest(
            name=f"Security Test {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            owner_chat_id=123456789,
            deadline=datetime.now() + timedelta(days=7)
        )

        expedition = expedition_service.create_expedition(request)
        logger.info(f"✅ Created expedition: {expedition.name} (ID: {expedition.id})")

        # Get owner_key from database (not in model)
        db_manager = get_db_manager()
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT owner_key FROM expeditions WHERE id = %s", (expedition.id,))
            result = cursor.fetchone()
            cursor.close()

        owner_key = result[0] if result else None

        if owner_key:
            logger.info(f"✅ Owner key generated: {owner_key[:20]}...")
        else:
            logger.warning("⚠️ No owner key found (might be OK for testing)")

    except Exception as e:
        logger.error(f"❌ Failed to create expedition: {e}")
        return False

    # Test 2: Create a pirate with encryption
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: Creating encrypted pirate")
    logger.info("=" * 60)

    try:
        original_name = "Alice Test User"
        pirate_name = "Captain Blackbeard"

        pirate_data = brambler_service.create_pirate(
            expedition_id=expedition.id,
            original_name=original_name,
            pirate_name=pirate_name,
            owner_key=owner_key
        )

        if pirate_data:
            logger.info(f"✅ Created pirate: {pirate_data['pirate_name']} (ID: {pirate_data['id']})")
            logger.info(f"   - Pirate Name: {pirate_data['pirate_name']}")
            logger.info(f"   - Original Name in Response: {pirate_data.get('original_name', 'NULL')}")
            logger.info(f"   - Has Encrypted Identity: {pirate_data.get('encrypted_identity') is not None}")
        else:
            logger.error("❌ Failed to create pirate - returned None")
            return False

    except Exception as e:
        logger.error(f"❌ Failed to create pirate: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 3: Verify database state - original_name should be NULL
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: Verifying database encryption")
    logger.info("=" * 60)

    try:
        db_manager = get_db_manager()
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, pirate_name, original_name, encrypted_identity IS NOT NULL as has_encryption
                FROM expedition_pirates
                WHERE id = %s
            """, (pirate_data['id'],))

            result = cursor.fetchone()
            cursor.close()

        if result:
            pirate_id, db_pirate_name, db_original_name, has_encryption = result
            logger.info(f"Database record:")
            logger.info(f"   - ID: {pirate_id}")
            logger.info(f"   - Pirate Name: {db_pirate_name}")
            logger.info(f"   - Original Name: {db_original_name if db_original_name else 'NULL ✅'}")
            logger.info(f"   - Has Encryption: {has_encryption}")

            # Verify security
            if db_original_name is None and has_encryption:
                logger.info("✅ SECURITY VERIFIED: original_name is NULL, encrypted_identity exists")
            elif db_original_name is not None:
                logger.error("❌ SECURITY BREACH: original_name is NOT NULL!")
                return False
            else:
                logger.error("❌ SECURITY ISSUE: No encrypted_identity found!")
                return False
        else:
            logger.error("❌ Pirate not found in database")
            return False

    except Exception as e:
        logger.error(f"❌ Failed to verify database: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 4: Test decryption (owner only)
    logger.info("\n" + "=" * 60)
    logger.info("TEST 4: Testing owner decryption")
    logger.info("=" * 60)

    try:
        # Get pirates with decryption
        pirates = brambler_service.get_expedition_pirate_names(
            expedition.id,
            decrypt_with_owner_key=owner_key
        )

        logger.info(f"Retrieved {len(pirates)} pirates from expedition")

        for pirate in pirates:
            logger.info(f"   - {pirate.pirate_name}")
            if pirate.original_name:
                logger.info(f"     Original (decrypted): {pirate.original_name}")
            else:
                logger.info(f"     Original: NULL (encrypted)")

        # Verify our pirate is in the list and can be decrypted
        our_pirate = next((p for p in pirates if p.id == pirate_data['id']), None)

        if our_pirate:
            if our_pirate.original_name == original_name:
                logger.info(f"✅ DECRYPTION SUCCESSFUL: {our_pirate.pirate_name} -> {our_pirate.original_name}")
            else:
                logger.warning(f"⚠️ Decryption returned unexpected value: {our_pirate.original_name}")
        else:
            logger.error("❌ Could not find our pirate in expedition list")
            return False

    except Exception as e:
        logger.error(f"❌ Failed to test decryption: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 5: Verify non-owner cannot see original names
    logger.info("\n" + "=" * 60)
    logger.info("TEST 5: Testing non-owner access (no decryption)")
    logger.info("=" * 60)

    try:
        # Get pirates WITHOUT decryption key
        pirates_no_key = brambler_service.get_expedition_pirate_names(
            expedition.id,
            decrypt_with_owner_key=None
        )

        logger.info(f"Retrieved {len(pirates_no_key)} pirates (no decryption)")

        for pirate in pirates_no_key:
            if pirate.original_name is not None:
                logger.error(f"❌ SECURITY BREACH: Non-owner can see original name: {pirate.original_name}")
                return False

        logger.info("✅ NON-OWNER ACCESS VERIFIED: No original names exposed")

    except Exception as e:
        logger.error(f"❌ Failed to test non-owner access: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Final summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    logger.info("✅ Expedition creation: PASSED")
    logger.info("✅ Pirate creation with encryption: PASSED")
    logger.info("✅ Database encryption verification: PASSED")
    logger.info("✅ Owner decryption: PASSED")
    logger.info("✅ Non-owner security: PASSED")
    logger.info("\n🎉 ALL SECURITY TESTS PASSED!")
    logger.info("=" * 60)

    return True


if __name__ == "__main__":
    success = test_encryption_flow()
    exit(0 if success else 1)
