"""
Quick Drop: Remove pirate_names table completely
Date: 2025-11-03
Purpose: Drop pirate_names table since expedition_pirates handles all anonymization
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_db_manager, initialize_database

print("Initializing database...")
initialize_database()

db_manager = get_db_manager()

print("\nDropping pirate_names table and indexes...")

with db_manager.get_connection() as conn:
    with conn.cursor() as cursor:
        # Drop indexes
        print("  Dropping indexes...")
        cursor.execute("DROP INDEX IF EXISTS idx_piratenames_expedition")
        cursor.execute("DROP INDEX IF EXISTS idx_piratenames_original")
        cursor.execute("DROP INDEX IF EXISTS idx_piratenames_exp_original")
        print("  [OK] Indexes dropped")

        # Drop table
        print("  Dropping table...")
        cursor.execute("DROP TABLE IF EXISTS pirate_names CASCADE")
        conn.commit()
        print("  [OK] Table pirate_names dropped")

print("\n[SUCCESS] pirate_names table removed successfully!")
