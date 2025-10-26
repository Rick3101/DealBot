"""
Get the user master key for a specific chat_id (owner)
"""

from utils.encryption import get_encryption_service

def get_master_key():
    encryption = get_encryption_service()

    # Get master key for Morty (dev user)
    chat_id = 5094426438

    master_key = encryption.generate_user_master_key(chat_id)

    print(f"=== USER MASTER KEY for chat_id {chat_id} ===")
    print(f"Master Key: {master_key}")
    print(f"Length: {len(master_key)} characters")
    print(f"\nThis is the key the user should enter in the webapp to decrypt pirate names.")
    print(f"This key works for ALL expeditions owned by this user.")

if __name__ == "__main__":
    get_master_key()
