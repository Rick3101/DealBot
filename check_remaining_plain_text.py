"""Check which pirate still has plain text."""

import os
from dotenv import load_dotenv
from database import initialize_database, get_db_manager

# Load environment variables
load_dotenv()

# Initialize database
initialize_database()
db_manager = get_db_manager()

with db_manager.get_connection() as conn:
    with conn.cursor() as cur:
        print("\nPirates with Plain Text (original_name IS NOT NULL):")
        print("="*80)
        cur.execute("""
            SELECT id, expedition_id, pirate_name, original_name,
                   encrypted_identity IS NOT NULL AND encrypted_identity != '' as has_encrypted
            FROM expedition_pirates
            WHERE original_name IS NOT NULL
            ORDER BY id
        """)

        for row in cur.fetchall():
            pirate_id, exp_id, pirate_name, original_name, has_encrypted = row
            print(f"\nID: {pirate_id}")
            print(f"Expedition: {exp_id}")
            print(f"Pirate Name: {pirate_name}")
            print(f"Original Name: {original_name}")
            print(f"Has Encryption: {has_encrypted}")
            print("-"*80)
