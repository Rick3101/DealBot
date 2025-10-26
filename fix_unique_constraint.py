"""Fix the unique constraint on expedition_pirates to allow multiple NULL original_names."""

import os
from dotenv import load_dotenv
from database import initialize_database, get_db_manager

# Load environment variables
load_dotenv()

# Initialize database
print("Initializing database connection...")
initialize_database()
db_manager = get_db_manager()

print("\nFixing unique constraint on expedition_pirates table...")

with db_manager.get_connection() as conn:
    with conn.cursor() as cur:
        # Drop the problematic constraint
        print("Dropping old constraint...")
        cur.execute("""
            ALTER TABLE expedition_pirates
            DROP CONSTRAINT IF EXISTS unique_original_name_when_not_null
        """)

        # The new behavior we want is:
        # - If original_name is NOT NULL, it should be unique per expedition
        # - If original_name IS NULL, allow multiple entries (one per pirate)
        #
        # We achieve this with a UNIQUE constraint on (expedition_id, original_name)
        # WITHOUT the NULLS NOT DISTINCT clause, which is the default PostgreSQL behavior
        # (NULLs are treated as distinct from each other)

        print("Creating new constraint that allows multiple NULLs...")
        cur.execute("""
            ALTER TABLE expedition_pirates
            ADD CONSTRAINT unique_original_name_when_not_null
            UNIQUE (expedition_id, original_name)
        """)

        conn.commit()

print("\nSuccess! The constraint has been fixed.")
print("Multiple pirates can now have NULL original_name values in the same expedition.")
print("\nYou can now run the migration script again: python migrations/encrypt_pirate_names.py")
