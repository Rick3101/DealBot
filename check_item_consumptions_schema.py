"""Check item_consumptions table schema."""

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
        print("\nitem_consumptions Table Schema:")
        print("="*80)

        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'item_consumptions'
            ORDER BY ordinal_position
        """)

        print(f"{'Column':<30} {'Type':<25} {'Nullable'}")
        print("-"*80)
        for row in cur.fetchall():
            col_name, data_type, nullable = row
            print(f"{col_name:<30} {data_type:<25} {nullable}")

        print("\n" + "="*80)
