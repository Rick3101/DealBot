"""
Check data volume in Brambler tables to understand performance issues
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import initialize_database, get_db_manager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_data_volume():
    """Check the number of records in key Brambler tables."""
    try:
        initialize_database()
        db = get_db_manager()

        queries = {
            "Expeditions": "SELECT COUNT(*) FROM expeditions",
            "Expedition Pirates": "SELECT COUNT(*) FROM expedition_pirates",
            "Expedition Items": "SELECT COUNT(*) FROM expedition_items",
            "Item Consumptions": "SELECT COUNT(*) FROM item_consumptions",
        }

        print("\n" + "="*60)
        print("DATABASE VOLUME ANALYSIS")
        print("="*60)

        with db.get_connection() as conn:
            with conn.cursor() as cur:
                for table, query in queries.items():
                    cur.execute(query)
                    count = cur.fetchone()[0]
                    print(f"{table:.<40} {count:>10,} records")

                # Check specific indexes
                print("\n" + "="*60)
                print("INDEX STATUS CHECK")
                print("="*60)

                cur.execute("""
                    SELECT indexname, tablename
                    FROM pg_indexes
                    WHERE indexname LIKE '%brambler%'
                       OR indexname LIKE '%expedition%'
                    ORDER BY tablename, indexname
                """)

                indexes = cur.fetchall()
                if indexes:
                    for idx_name, tbl_name in indexes:
                        print(f"✓ {tbl_name:.<30} {idx_name}")
                else:
                    print("⚠ No Brambler-specific indexes found!")

                # Check query performance
                print("\n" + "="*60)
                print("QUERY PERFORMANCE TEST")
                print("="*60)

                import time

                # Test get_all_expedition_pirates query
                start = time.time()
                cur.execute("""
                    SELECT ep.id, ep.pirate_name, ep.original_name, ep.expedition_id,
                           ep.encrypted_identity, e.name as expedition_name,
                           e.owner_chat_id, ep.joined_at
                    FROM expedition_pirates ep
                    INNER JOIN Expeditions e ON ep.expedition_id = e.id
                    WHERE ep.expedition_id IS NOT NULL
                    ORDER BY ep.expedition_id DESC, ep.joined_at DESC
                    LIMIT 1000
                """)
                result = cur.fetchall()
                elapsed = time.time() - start
                print(f"get_all_expedition_pirates: {elapsed:.3f}s ({len(result)} records)")

                # Test get_all_encrypted_items query (need owner_chat_id)
                cur.execute("SELECT DISTINCT owner_chat_id FROM expeditions WHERE owner_chat_id IS NOT NULL LIMIT 1")
                owner_row = cur.fetchone()

                if owner_row:
                    owner_chat_id = owner_row[0]
                    start = time.time()
                    cur.execute("""
                        SELECT ei.id, ei.expedition_id, e.name as expedition_name,
                               ei.encrypted_product_name, ei.encrypted_mapping,
                               ei.anonymized_item_code, ei.item_type,
                               ei.quantity_required, ei.quantity_consumed,
                               ei.item_status, ei.created_at
                        FROM expedition_items ei
                        INNER JOIN Expeditions e ON ei.expedition_id = e.id
                        WHERE e.owner_chat_id = %s
                          AND ei.encrypted_mapping IS NOT NULL
                          AND ei.encrypted_mapping != ''
                        ORDER BY ei.created_at DESC
                        LIMIT 1000
                    """, (owner_chat_id,))
                    result = cur.fetchall()
                    elapsed = time.time() - start
                    print(f"get_all_encrypted_items: {elapsed:.3f}s ({len(result)} records)")

                # Test expeditions list query
                start = time.time()
                cur.execute("""
                    SELECT id, name, owner_chat_id, status, deadline, created_at, completed_at
                    FROM expeditions
                    ORDER BY created_at DESC
                    LIMIT 1000
                """)
                result = cur.fetchall()
                elapsed = time.time() - start
                print(f"get_expeditions_list: {elapsed:.3f}s ({len(result)} records)")

                print("\n" + "="*60)
                print("RECOMMENDATIONS")
                print("="*60)

                if elapsed > 1.0:
                    print("⚠ Queries are taking >1s - consider:")
                    print("  1. Running VACUUM ANALYZE on tables")
                    print("  2. Checking if indexes were created")
                    print("  3. Increasing work_mem for queries")
                else:
                    print("✓ Queries are performing well (<1s)")

        return True

    except Exception as e:
        logger.error(f"Error checking data volume: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = check_data_volume()
    sys.exit(0 if success else 1)
