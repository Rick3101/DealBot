"""
Test script to verify brambler decryption for expedition 7
"""

from core.modern_service_container import initialize_services, get_expedition_service, get_brambler_service

def test_decrypt():
    # Initialize services
    print("Initializing services...")
    initialize_services()
    # Get services
    expedition_service = get_expedition_service()
    brambler_service = get_brambler_service()

    expedition_id = 7

    # Get expedition details
    expedition = expedition_service.get_expedition_by_id(expedition_id)

    if not expedition:
        print(f"ERROR: Expedition {expedition_id} not found!")
        return

    print(f"Expedition: {expedition.name}")
    print(f"Owner Chat ID: {expedition.owner_chat_id}")
    print(f"Has owner_key: {hasattr(expedition, 'owner_key') and expedition.owner_key is not None}")

    if hasattr(expedition, 'owner_key') and expedition.owner_key:
        print(f"Owner Key (first 20 chars): {expedition.owner_key[:20]}...")
        print(f"Owner Key Length: {len(expedition.owner_key)}")
    else:
        print("WARNING: No owner_key found on expedition!")

    # Get pirate names
    pirate_names = brambler_service.get_expedition_pirate_names(expedition_id)
    print(f"\nTotal pirate names: {len(pirate_names)}")

    for pn in pirate_names[:3]:  # Show first 3
        print(f"  - Pirate: {pn.pirate_name}")
        print(f"    Original: {pn.original_name or '[ENCRYPTED]'}")
        print(f"    Has encrypted_identity: {bool(pn.encrypted_mapping)}")

    # Try to decrypt if owner_key exists
    if hasattr(expedition, 'owner_key') and expedition.owner_key:
        print("\n--- Testing Decryption ---")
        try:
            decrypted = brambler_service.decrypt_expedition_pirates(expedition_id, expedition.owner_key)
            print(f"Successfully decrypted {len(decrypted)} names:")
            for pirate, original in list(decrypted.items())[:3]:
                print(f"  {pirate} -> {original}")
        except Exception as e:
            print(f"Decryption failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_decrypt()
