"""Get a valid chat_id from the database."""

import os
from dotenv import load_dotenv
load_dotenv()

from database import initialize_database, get_database_manager

initialize_database()

db = get_database_manager()

with db.get_connection() as conn:
    with conn.cursor() as cur:
        # First, get column names
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'usuarios'
            ORDER BY ordinal_position
        """)
        columns = [row[0] for row in cur.fetchall()]
        print(f"Columns: {columns}")

        # Get users with owner/admin level
        cur.execute("SELECT * FROM Usuarios WHERE nivel IN ('owner', 'admin') LIMIT 3")
        users = cur.fetchall()
        print(f"\n=== USERS (owner/admin) ===")
        for user in users:
            user_dict = dict(zip(columns, user))
            print(f"User: {user_dict}")
