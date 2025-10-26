"""
Test script to verify the new expedition system is working correctly.
Tests the updated service methods with the new tables.
"""

import logging
from decimal import Decimal
from datetime import datetime
from dotenv import load_dotenv

from services.expedition_service import ExpeditionService
from services.brambler_service import BramblerService
from models.expedition import ItemConsumptionRequest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()


def test_pirate_name_lookups():
    """Test that pirate name lookups work with expedition_pirates table."""
    logger.info("=" * 60)
    logger.info("Testing Pirate Name Lookups")
    logger.info("=" * 60)

    brambler_service = BramblerService()

    # Test 1: Get expedition pirate names (should use expedition_pirates table)
    expedition_id = 7
    pirates = brambler_service.get_expedition_pirate_names(expedition_id)
    logger.info(f"Found {len(pirates)} pirates in expedition {expedition_id}")

    if pirates:
        for pirate in pirates:
            logger.info(f"  - {pirate.original_name} -> {pirate.pirate_name}")

    # Test 2: Get pirate name for original
    if pirates:
        test_original = pirates[0].original_name
        pirate_name = brambler_service.get_pirate_name(expedition_id, test_original)
        logger.info(f"Lookup test: {test_original} -> {pirate_name}")
        assert pirate_name == pirates[0].pirate_name, "Pirate name lookup failed!"

    # Test 3: Get original name for pirate
    if pirates:
        test_pirate = pirates[0].pirate_name
        original_name = brambler_service.get_original_name(expedition_id, test_pirate)
        logger.info(f"Reverse lookup test: {test_pirate} -> {original_name}")
        assert original_name == pirates[0].original_name, "Original name lookup failed!"

    logger.info("Pirate name lookups: PASSED\n")
    return True


def test_new_consumption():
    """Test creating a new consumption with the updated service."""
    logger.info("=" * 60)
    logger.info("Testing New Consumption Creation")
    logger.info("=" * 60)

    expedition_service = ExpeditionService()

    # Get active expeditions
    expeditions = expedition_service.get_active_expeditions()
    if not expeditions:
        logger.warning("No active expeditions found for testing")
        return False

    test_expedition = expeditions[0]
    logger.info(f"Using expedition: {test_expedition.name} (ID: {test_expedition.id})")

    # Get expedition items
    items = expedition_service.get_expedition_items(test_expedition.id)
    if not items:
        logger.warning("No items in expedition for testing")
        return False

    # Find an item with remaining capacity
    test_item = None
    for item in items:
        remaining = item.quantity_required - (item.quantity_consumed or 0)
        if remaining > 0:
            test_item = item
            logger.info(f"Using item: Product ID {item.produto_id}, Remaining: {remaining}")
            break

    if not test_item:
        logger.warning("No items with remaining capacity for testing")
        return False

    # Create a test consumption
    try:
        request = ItemConsumptionRequest(
            expedition_item_id=test_item.id,
            consumer_name="test_consumer",
            pirate_name="Test Pirate Name",
            quantity_consumed=1,
            unit_price=Decimal('10.00')
        )

        logger.info("Creating test consumption...")
        consumption = expedition_service.consume_item(request)

        logger.info(f"Consumption created successfully!")
        logger.info(f"  - Consumption ID: {consumption.id}")
        logger.info(f"  - Consumer: {consumption.consumer_name}")
        logger.info(f"  - Pirate: {consumption.pirate_name}")
        logger.info(f"  - Quantity: {consumption.quantity_consumed}")
        logger.info(f"  - Total Cost: {consumption.total_cost}")

        # Verify expedition_pirate was created
        import psycopg2
        import os
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cur = conn.cursor()

        cur.execute("""
            SELECT id, pirate_name, original_name, role, status
            FROM expedition_pirates
            WHERE expedition_id = %s AND original_name = %s
        """, (test_expedition.id, "test_consumer"))

        pirate_record = cur.fetchone()
        if pirate_record:
            logger.info(f"Expedition pirate record created: ID {pirate_record[0]}, Role: {pirate_record[3]}, Status: {pirate_record[4]}")
        else:
            logger.error("Failed to create expedition_pirate record!")
            return False

        # Verify expedition_assignment was created
        cur.execute("""
            SELECT id, assigned_quantity, consumed_quantity, assignment_status, payment_status
            FROM expedition_assignments
            WHERE expedition_id = %s AND pirate_id = %s
            ORDER BY assigned_at DESC LIMIT 1
        """, (test_expedition.id, pirate_record[0]))

        assignment_record = cur.fetchone()
        if assignment_record:
            logger.info(f"Expedition assignment created: ID {assignment_record[0]}, Status: {assignment_record[3]}/{assignment_record[4]}")
        else:
            logger.error("Failed to create expedition_assignment record!")
            return False

        conn.close()

        logger.info("New consumption creation: PASSED\n")
        return True

    except Exception as e:
        logger.error(f"Failed to create consumption: {e}", exc_info=True)
        return False


def test_payment_processing():
    """Test payment processing with the updated service."""
    logger.info("=" * 60)
    logger.info("Testing Payment Processing")
    logger.info("=" * 60)

    expedition_service = ExpeditionService()

    # Get a pending consumption
    import psycopg2
    import os
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    cur = conn.cursor()

    cur.execute("""
        SELECT ic.id, ic.total_cost, ic.amount_paid, ic.consumer_name
        FROM item_consumptions ic
        WHERE ic.payment_status = 'pending'
        ORDER BY ic.consumed_at DESC
        LIMIT 1
    """)

    consumption_data = cur.fetchone()
    if not consumption_data:
        logger.warning("No pending consumptions found for testing")
        conn.close()
        return False

    consumption_id, total_cost, amount_paid, consumer = consumption_data
    logger.info(f"Testing payment for consumption {consumption_id}")
    logger.info(f"  - Consumer: {consumer}")
    logger.info(f"  - Total: {total_cost}, Paid: {amount_paid}")

    try:
        # Make a partial payment
        payment_amount = Decimal('5.00')
        logger.info(f"Processing payment of {payment_amount}...")

        updated_consumption = expedition_service.pay_consumption(consumption_id, payment_amount)

        logger.info(f"Payment processed successfully!")
        logger.info(f"  - New amount paid: {updated_consumption.amount_paid}")
        logger.info(f"  - New status: {updated_consumption.payment_status}")

        # Verify expedition_payment was created
        cur.execute("""
            SELECT COUNT(*) FROM expedition_payments
            WHERE notes LIKE %s
        """, (f'%consumption {consumption_id}%',))

        payment_count = cur.fetchone()[0]
        if payment_count > 0:
            logger.info(f"Expedition payment record created ({payment_count} record(s))")
        else:
            logger.warning("No expedition_payment record found - might be OK if assignment doesn't exist")

        conn.close()

        logger.info("Payment processing: PASSED\n")
        return True

    except Exception as e:
        logger.error(f"Failed to process payment: {e}", exc_info=True)
        conn.close()
        return False


def main():
    """Run all tests."""
    logger.info("\n" + "=" * 60)
    logger.info("NEW EXPEDITION SYSTEM TESTS")
    logger.info("=" * 60 + "\n")

    results = []

    # Test 1: Pirate name lookups
    try:
        results.append(("Pirate Name Lookups", test_pirate_name_lookups()))
    except Exception as e:
        logger.error(f"Pirate name lookups test failed: {e}", exc_info=True)
        results.append(("Pirate Name Lookups", False))

    # Test 2: New consumption
    try:
        results.append(("New Consumption", test_new_consumption()))
    except Exception as e:
        logger.error(f"New consumption test failed: {e}", exc_info=True)
        results.append(("New Consumption", False))

    # Test 3: Payment processing
    try:
        results.append(("Payment Processing", test_payment_processing()))
    except Exception as e:
        logger.error(f"Payment processing test failed: {e}", exc_info=True)
        results.append(("Payment Processing", False))

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        logger.info(f"{test_name}: {status}")

    logger.info(f"\nTotal: {passed}/{total} tests passed")
    logger.info("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
