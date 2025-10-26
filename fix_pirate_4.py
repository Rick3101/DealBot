"""Fix pirate ID 4 by setting original_name to NULL (data is already encrypted)."""

import os
from dotenv import load_dotenv
from database import initialize_database, get_db_manager

# Load environment variables
load_dotenv()

# Initialize database
initialize_database()
db_manager = get_db_manager()

print("\nFixing Pirate ID 4...")
print("="*80)

with db_manager.get_connection() as conn:
    with conn.cursor() as cur:
        # Verify the pirate has encrypted_identity
        cur.execute("""
            SELECT id, pirate_name, original_name, encrypted_identity
            FROM expedition_pirates
            WHERE id = 4
        """)

        pirate = cur.fetchone()
        if pirate:
            pirate_id, pirate_name, original_name, encrypted_identity = pirate
            print(f"Current State:")
            print(f"  ID: {pirate_id}")
            print(f"  Pirate Name: {pirate_name}")
            print(f"  Original Name: {original_name}")
            print(f"  Has Encrypted Identity: {bool(encrypted_identity and encrypted_identity.strip())}")

            if encrypted_identity and encrypted_identity.strip():
                print(f"\nEncrypted identity exists, setting original_name to NULL...")
                cur.execute("""
                    UPDATE expedition_pirates
                    SET original_name = NULL
                    WHERE id = 4
                """)
                conn.commit()
                print("Success! Pirate 4 is now fully encrypted.")
            else:
                print("\nWARNING: No encrypted identity found, skipping update.")
        else:
            print("Pirate ID 4 not found.")

print("\n" + "="*80)
