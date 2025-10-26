"""
Simple re-encryption: decrypt with old key, encrypt with new key
"""

from services.brambler_service import BramblerService
from services.expedition_service import ExpeditionService
from utils.encryption import get_encryption_service

def simple_reencrypt():
    brambler = BramblerService()
    expedition_service = ExpeditionService()
    encryption = get_encryption_service()

    expedition_id = 7
    owner_chat_id = 5094426438

    # Get keys
    expedition = expedition_service.get_expedition_by_id(expedition_id)
    old_key = expedition.owner_key
    new_key = encryption.generate_user_master_key(owner_chat_id)

    print(f"Old key: {old_key[:30]}...")
    print(f"New key: {new_key[:30]}...")
    print()

    # Get all pirate records
    query = """
        SELECT id, pirate_name, encrypted_identity
        FROM expedition_pirates
        WHERE expedition_id = %s
    """
    rows = brambler._execute_query(query, (expedition_id,), fetch_all=True)

    print(f"Found {len(rows)} pirates to re-encrypt\n")

    success_count = 0
    fail_count = 0

    for pirate_id, pirate_name, encrypted_identity in rows:
        try:
            # Decrypt with old key using LOW-LEVEL decryption
            decrypted_data = encryption.decrypt_name_mapping(encrypted_identity, old_key)

            if decrypted_data and 'mapping' in decrypted_data:
                mapping = decrypted_data['mapping']
                print(f"[OK] Decrypted {pirate_name}: {mapping}")

                # Re-encrypt with new key
                new_encrypted = encryption.encrypt_name_mapping(
                    expedition_id,
                    mapping,
                    new_key
                )

                # Update database
                update_query = """
                    UPDATE expedition_pirates
                    SET encrypted_identity = %s
                    WHERE id = %s
                """
                brambler._execute_query(update_query, (new_encrypted, pirate_id))

                print(f"     Re-encrypted with new key\n")
                success_count += 1
            else:
                print(f"[X] Failed to decrypt {pirate_name} - no mapping data\n")
                fail_count += 1

        except Exception as e:
            print(f"[X] Error with {pirate_name}: {str(e)[:80]}\n")
            fail_count += 1

    # Update expedition owner_key
    update_exp = """
        UPDATE expeditions
        SET owner_key = %s
        WHERE id = %s
    """
    expedition_service._execute_query(update_exp, (new_key, expedition_id))

    print(f"\n{'='*60}")
    print(f"Results:")
    print(f"  Success: {success_count}")
    print(f"  Failed: {fail_count}")
    print(f"\nExpedition {expedition_id} owner_key updated to master key")
    print(f"{'='*60}\n")

    # Verify
    if success_count > 0:
        print("Verifying decryption with NEW master key...")
        decrypted = brambler.decrypt_expedition_pirates(expedition_id, new_key)
        print(f"\nDecrypted {len(decrypted)} pirates with master key:")
        for pirate, original in list(decrypted.items())[:3]:
            print(f"  {pirate} -> {original}")

if __name__ == "__main__":
    simple_reencrypt()
