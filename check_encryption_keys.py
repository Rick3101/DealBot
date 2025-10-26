"""
Check which key was used to encrypt the pirate names in expedition 7
"""

from services.brambler_service import BramblerService
from utils.encryption import get_encryption_service

def check_keys():
    brambler = BramblerService()
    encryption = get_encryption_service()

    expedition_id = 7
    chat_id = 5094426438

    # Get pirate names
    pirates = brambler.get_expedition_pirate_names(expedition_id)

    print(f"=== Expedition {expedition_id} Pirate Names ===")
    print(f"Total pirates: {len(pirates)}\n")

    if pirates:
        first_pirate = pirates[0]
        print(f"First pirate: {first_pirate.pirate_name}")
        print(f"Has encrypted_mapping: {bool(first_pirate.encrypted_mapping)}")
        if first_pirate.encrypted_mapping:
            print(f"Encrypted data length: {len(first_pirate.encrypted_mapping)} chars")
            print(f"Encrypted data (first 50): {first_pirate.encrypted_mapping[:50]}...")

    # Get the keys
    print("\n=== Keys ===")

    # Get expedition owner_key from database
    query = "SELECT owner_key FROM Expeditions WHERE id = %s"
    row = brambler._execute_query(query, (expedition_id,), fetch_one=True)
    expedition_owner_key = row[0] if row else None

    print(f"Expedition owner_key: {expedition_owner_key}")
    if expedition_owner_key:
        print(f"  Length: {len(expedition_owner_key)} chars")

    # Get user master key
    user_master_key = encryption.generate_user_master_key(chat_id)
    print(f"\nUser master_key: {user_master_key}")
    print(f"  Length: {len(user_master_key)} chars")

    # Compare
    print(f"\n=== Comparison ===")
    print(f"Keys are same: {expedition_owner_key == user_master_key}")

    # Try decrypting with both keys
    if pirates and pirates[0].encrypted_mapping:
        encrypted_data = pirates[0].encrypted_mapping

        print("\n=== Decryption Tests ===")

        # Test with expedition owner_key
        print("\n1. Testing with expedition owner_key:")
        try:
            result = encryption.decrypt_name_mapping(encrypted_data, expedition_owner_key)
            print(f"   SUCCESS! Decrypted: {result}")
        except Exception as e:
            print(f"   FAILED: {str(e)[:100]}")

        # Test with user master_key
        print("\n2. Testing with user master_key:")
        try:
            result = encryption.decrypt_name_mapping(encrypted_data, user_master_key)
            print(f"   SUCCESS! Decrypted: {result}")
        except Exception as e:
            print(f"   FAILED: {str(e)[:100]}")

if __name__ == "__main__":
    check_keys()
