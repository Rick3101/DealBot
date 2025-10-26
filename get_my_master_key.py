"""
Simple script to get your master decryption key.
This key works for ALL your expeditions!
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize database
from database import initialize_database
from utils.encryption import get_encryption_service
from database import get_db_manager

def get_master_key(chat_id: int):
    """Get or generate master key for a user."""
    encryption_service = get_encryption_service()
    db_manager = get_db_manager()

    # Generate the key (deterministic - always the same for this chat_id)
    master_key = encryption_service.generate_user_master_key(chat_id)

    # Check if it's already stored in database
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT created_at, last_accessed, key_version
                FROM user_master_keys
                WHERE owner_chat_id = %s
            """, (chat_id,))
            result = cur.fetchone()

            if result:
                created_at, last_accessed, key_version = result
                print(f"[INFO] Master key found in database")
                print(f"       Created: {created_at}")
                print(f"       Last accessed: {last_accessed}")
                print(f"       Version: {key_version}")
            else:
                # Store it
                cur.execute("""
                    INSERT INTO user_master_keys (owner_chat_id, master_key, key_version)
                    VALUES (%s, %s, 1)
                    RETURNING created_at
                """, (chat_id, master_key))
                created_at = cur.fetchone()[0]
                conn.commit()
                print(f"[INFO] Generated and stored new master key")
                print(f"       Created: {created_at}")

    return master_key


def main():
    """Main entry point."""
    print("="*70)
    print("YOUR MASTER DECRYPTION KEY")
    print("="*70)

    # Get chat_id from command line or prompt
    if len(sys.argv) > 1:
        try:
            chat_id = int(sys.argv[1])
        except ValueError:
            print("[ERROR] Invalid chat_id. Please provide a valid number.")
            print("\nUsage: python get_my_master_key.py YOUR_CHAT_ID")
            sys.exit(1)
    else:
        print("\nPlease enter your Telegram chat ID:")
        try:
            chat_id = int(input("Chat ID: ").strip())
        except ValueError:
            print("[ERROR] Invalid input. Chat ID must be a number.")
            sys.exit(1)

    print(f"\nLooking up master key for chat_id: {chat_id}")
    print("-"*70)

    try:
        # Initialize database
        initialize_database()

        # Get the master key
        master_key = get_master_key(chat_id)

        print("\n" + "="*70)
        print("YOUR MASTER KEY:")
        print("="*70)
        print(master_key)
        print("="*70)

        print("\n[SUCCESS] This key works for ALL your expeditions!")
        print("[TIP] Save this key somewhere safe - you'll need it to decrypt pirate names.")

        print("\n" + "="*70)
        print("HOW TO USE THIS KEY:")
        print("="*70)
        print("1. Save this key in a secure location (password manager recommended)")
        print("2. Use it to decrypt pirate names in ANY of your expeditions")
        print("3. API endpoint: POST /api/brambler/decrypt/<expedition_id>")
        print("4. Include this key in the request body as 'owner_key'")
        print("\nExample:")
        print(f'  curl -X POST http://localhost:5000/api/brambler/decrypt/123 \\')
        print(f'    -H "X-Chat-ID: {chat_id}" \\')
        print(f'    -H "Content-Type: application/json" \\')
        print(f'    -d \'{{\"owner_key\": \"{master_key}\"}}\'')

    except Exception as e:
        print(f"\n[ERROR] Failed to get master key: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
