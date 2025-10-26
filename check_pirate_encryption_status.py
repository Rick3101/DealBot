"""Quick script to check the current state of pirate encryption in the database."""

import os
from dotenv import load_dotenv
from database import initialize_database, get_db_manager

# Load environment variables
load_dotenv()

# Initialize database
initialize_database()
db_manager = get_db_manager()

# Query current state
with db_manager.get_connection() as conn:
    with conn.cursor() as cur:
        # Get counts
        cur.execute("""
            SELECT
                COUNT(*) as total_pirates,
                SUM(CASE WHEN original_name IS NOT NULL THEN 1 ELSE 0 END) as with_plain_text,
                SUM(CASE WHEN encrypted_identity IS NOT NULL AND encrypted_identity != '' THEN 1 ELSE 0 END) as with_encryption,
                SUM(CASE WHEN original_name IS NULL AND (encrypted_identity IS NOT NULL AND encrypted_identity != '') THEN 1 ELSE 0 END) as fully_encrypted
            FROM expedition_pirates
        """)

        stats = cur.fetchone()

        print("\n" + "="*80)
        print("CURRENT PIRATE ENCRYPTION STATUS")
        print("="*80)
        print(f"Total Pirates: {stats[0]}")
        print(f"With Plain Text (original_name IS NOT NULL): {stats[1]}")
        print(f"With Encryption (has encrypted_identity): {stats[2]}")
        print(f"Fully Encrypted (NULL original_name + encrypted_identity): {stats[3]}")
        print("="*80)

        # Get some examples
        print("\nSample Records:")
        print("-"*80)
        cur.execute("""
            SELECT id, expedition_id, pirate_name,
                   original_name IS NOT NULL as has_plain,
                   encrypted_identity IS NOT NULL AND encrypted_identity != '' as has_encrypted
            FROM expedition_pirates
            ORDER BY id DESC
            LIMIT 10
        """)

        print(f"{'ID':<5} {'Exp':<5} {'Pirate Name':<35} {'Plain?':<8} {'Encrypted?'}")
        print("-"*80)
        for row in cur.fetchall():
            pirate_id, exp_id, pirate_name, has_plain, has_encrypted = row
            print(f"{pirate_id:<5} {exp_id:<5} {pirate_name:<35} {'Yes' if has_plain else 'No':<8} {'Yes' if has_encrypted else 'No'}")

        print("="*80 + "\n")
