"""
Diagnostic script to check Brambler encryption data in the database.
"""

import os
from database.connection import DatabaseManager
from dotenv import load_dotenv

def check_brambler_data():
    """Check what brambler data exists in the database."""
    load_dotenv()
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL not found in environment")
        return

    db = DatabaseManager(database_url)

    try:
        # Check expedition_pirates table
        print("=" * 80)
        print("CHECKING EXPEDITION_PIRATES TABLE")
        print("=" * 80)

        query = """
            SELECT
                ep.id,
                ep.expedition_id,
                e.name as expedition_name,
                e.owner_chat_id,
                ep.pirate_name,
                ep.original_name,
                CASE
                    WHEN ep.encrypted_identity IS NULL THEN 'NULL'
                    WHEN ep.encrypted_identity = '' THEN 'EMPTY'
                    ELSE 'HAS_DATA'
                END as encrypted_status,
                LENGTH(ep.encrypted_identity) as encrypted_length
            FROM expedition_pirates ep
            LEFT JOIN Expeditions e ON ep.expedition_id = e.id
            ORDER BY e.owner_chat_id, ep.expedition_id
            LIMIT 50
        """

        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()

                if not rows:
                    print("No pirates found in expedition_pirates table!")
                else:
                    print(f"\nFound {len(rows)} pirates:")
                    print("-" * 80)

                    for row in rows:
                        pirate_id, exp_id, exp_name, owner_chat_id, pirate_name, original_name, enc_status, enc_length = row
                        print(f"ID: {pirate_id} | Expedition: {exp_id} ({exp_name}) | Owner: {owner_chat_id}")
                        print(f"  Pirate Name: {pirate_name}")
                        print(f"  Original Name: {original_name}")
                        print(f"  Encrypted Identity: {enc_status} (length: {enc_length})")
                        print("-" * 80)

        # Check expedition_items table
        print("\n" + "=" * 80)
        print("CHECKING EXPEDITION_ITEMS TABLE")
        print("=" * 80)

        query = """
            SELECT
                ei.id,
                ei.expedition_id,
                e.name as expedition_name,
                e.owner_chat_id,
                ei.product_name,
                ei.encrypted_product_name,
                CASE
                    WHEN ei.encrypted_mapping IS NULL THEN 'NULL'
                    WHEN ei.encrypted_mapping = '' THEN 'EMPTY'
                    ELSE 'HAS_DATA'
                END as encrypted_status,
                LENGTH(ei.encrypted_mapping) as encrypted_length
            FROM expedition_items ei
            LEFT JOIN Expeditions e ON ei.expedition_id = e.id
            ORDER BY e.owner_chat_id, ei.expedition_id
            LIMIT 50
        """

        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()

                if not rows:
                    print("No items found in expedition_items table!")
                else:
                    print(f"\nFound {len(rows)} items:")
                    print("-" * 80)

                    for row in rows:
                        item_id, exp_id, exp_name, owner_chat_id, product_name, enc_product_name, enc_status, enc_length = row
                        print(f"ID: {item_id} | Expedition: {exp_id} ({exp_name}) | Owner: {owner_chat_id}")
                        print(f"  Product Name: {product_name}")
                        print(f"  Encrypted Product Name: {enc_product_name}")
                        print(f"  Encrypted Mapping: {enc_status} (length: {enc_length})")
                        print("-" * 80)

        # Summary statistics
        print("\n" + "=" * 80)
        print("SUMMARY STATISTICS")
        print("=" * 80)

        with db.get_connection() as conn:
            with conn.cursor() as cur:
                # Count pirates with encrypted identities
                cur.execute("""
                    SELECT COUNT(*)
                    FROM expedition_pirates
                    WHERE encrypted_identity IS NOT NULL AND encrypted_identity != ''
                """)
                encrypted_pirates_count = cur.fetchone()[0]

                # Count pirates without encrypted identities
                cur.execute("""
                    SELECT COUNT(*)
                    FROM expedition_pirates
                    WHERE encrypted_identity IS NULL OR encrypted_identity = ''
                """)
                unencrypted_pirates_count = cur.fetchone()[0]

                # Count items with encrypted mappings
                cur.execute("""
                    SELECT COUNT(*)
                    FROM expedition_items
                    WHERE encrypted_mapping IS NOT NULL AND encrypted_mapping != ''
                """)
                encrypted_items_count = cur.fetchone()[0]

                # Count items without encrypted mappings
                cur.execute("""
                    SELECT COUNT(*)
                    FROM expedition_items
                    WHERE encrypted_mapping IS NULL OR encrypted_mapping = ''
                """)
                unencrypted_items_count = cur.fetchone()[0]

                print(f"\nPirates with encrypted_identity: {encrypted_pirates_count}")
                print(f"Pirates WITHOUT encrypted_identity: {unencrypted_pirates_count}")
                print(f"Items with encrypted_mapping: {encrypted_items_count}")
                print(f"Items WITHOUT encrypted_mapping: {unencrypted_items_count}")

        print("\n" + "=" * 80)
        print("RECOMMENDATION:")
        print("=" * 80)
        if encrypted_pirates_count == 0 and encrypted_items_count == 0:
            print("NO ENCRYPTED DATA FOUND!")
            print("You need to create expeditions with the new encryption system.")
            print("The Brambler system only works with expeditions that have encrypted_identity data.")
        elif encrypted_pirates_count > 0 or encrypted_items_count > 0:
            print(f"Found {encrypted_pirates_count} encrypted pirates and {encrypted_items_count} encrypted items.")
            print("The decryption should work if you're using the correct owner key.")
            print("\nNext steps:")
            print("1. Verify you're using the correct master key")
            print("2. Check the backend logs for decryption errors")
            print("3. Try decrypting one item manually to see the error")

    except Exception as e:
        print(f"Error checking brambler data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_brambler_data()
