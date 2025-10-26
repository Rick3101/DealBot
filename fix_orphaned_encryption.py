"""
Fix orphaned encryption: the data was encrypted with a key that's no longer in the database.
We need to use the ORIGINAL expedition key we saved earlier.
"""

from services.brambler_service import BramblerService
from services.expedition_service import ExpeditionService

def fix_orphaned_encryption():
    brambler = BramblerService()
    expedition_service = ExpeditionService()

    # The ORIGINAL key that was used to encrypt the data
    ORIGINAL_EXPEDITION_KEY = 'Pvui5dey0XYYxJ5AukeTFY3ivgYIk8VQ7HlbarIVVkdbQ8w8HS0b-mGZIUMlG18_sfUCoikjX5lXpmRtiIjnKA=='

    # The NEW master key we want to use
    USER_MASTER_KEY = 'mWb1d2SV0p40ug4skGTPiAOy9rk-RpLBbpWyVgcqFEAL6c5gRIaE2t061K7n3K724s-cN5BwkvTnjUrxt6TcHQ=='

    expedition_id = 7

    print("="*60)
    print("Fixing Orphaned Encryption for Expedition 7")
    print("="*60)
    print(f"\nOriginal key (used for encryption): {ORIGINAL_EXPEDITION_KEY[:30]}...")
    print(f"New master key (target):            {USER_MASTER_KEY[:30]}...")

    # Get all pirate records using brambler service
    from utils.encryption import get_encryption_service
    encryption = get_encryption_service()

    query = """
        SELECT id, pirate_name, encrypted_identity
        FROM expedition_pirates
        WHERE expedition_id = %s
    """
    pirates = brambler._execute_query(query, (expedition_id,), fetch_all=True)
    print(f"\nFound {len(pirates)} pirates to re-encrypt\n")

    # Re-encrypt each one
    success_count = 0

    for pirate_id, pirate_name, encrypted_identity in pirates:
        try:
            # Decrypt with ORIGINAL key
            decrypted = encryption.decrypt_name_mapping(encrypted_identity, ORIGINAL_EXPEDITION_KEY)

            if decrypted and 'mapping' in decrypted:
                mapping = decrypted['mapping']
                print(f"[OK] Decrypted {pirate_name}")
                print(f"     Mapping: {mapping}")

                # Re-encrypt with MASTER key
                new_encrypted = encryption.encrypt_name_mapping(
                    expedition_id,
                    mapping,
                    USER_MASTER_KEY
                )

                # Update in database
                update_query = """
                    UPDATE expedition_pirates
                    SET encrypted_identity = %s
                    WHERE id = %s
                """
                brambler._execute_query(update_query, (new_encrypted, pirate_id))

                print(f"     Re-encrypted with master key\n")
                success_count += 1
            else:
                print(f"[X] Failed to decrypt {pirate_name}\n")

        except Exception as e:
            print(f"[X] Error with {pirate_name}: {str(e)[:80]}\n")

    # Update expedition to use master key
    exp_update = """
        UPDATE expeditions
        SET owner_key = %s
        WHERE id = %s
    """
    expedition_service._execute_query(exp_update, (USER_MASTER_KEY, expedition_id))

    print("="*60)
    print(f"Results: {success_count}/{len(pirates)} pirates re-encrypted")
    print(f"Expedition owner_key updated to master key")
    print("="*60)

    # Step 4: Verify
    print("\nVerifying decryption with master key...")
    decrypted_mappings = brambler.decrypt_expedition_pirates(expedition_id, USER_MASTER_KEY)

    print(f"\n[OK] Successfully decrypted {len(decrypted_mappings)} pirates:")
    for pirate, original in list(decrypted_mappings.items())[:5]:
        print(f"  {pirate} -> {original}")

    print("\n" + "="*60)
    print("MIGRATION COMPLETE!")
    print("="*60)
    print(f"\nYour master key (works for ALL your expeditions):")
    print(USER_MASTER_KEY)
    print("\nUse 'Load My Key' in the webapp to load this key automatically.")
    print("="*60 + "\n")

if __name__ == "__main__":
    fix_orphaned_encryption()
