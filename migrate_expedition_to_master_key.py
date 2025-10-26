"""
Migrate expedition 7 to use user master key instead of expedition owner_key.
This allows the user to decrypt ALL their expeditions with ONE key.
"""

from services.brambler_service import BramblerService
from services.expedition_service import ExpeditionService
from utils.encryption import get_encryption_service

def migrate_expedition_to_master_key(expedition_id: int, owner_chat_id: int):
    """
    Re-encrypt all pirate names in an expedition to use the user's master key.

    Args:
        expedition_id: Expedition to migrate
        owner_chat_id: Owner's chat ID
    """
    brambler = BramblerService()
    expedition_service = ExpeditionService()
    encryption = get_encryption_service()

    print(f"\n{'='*60}")
    print(f"Migrating Expedition {expedition_id} to User Master Key")
    print(f"{'='*60}\n")

    # Step 1: Get expedition and verify ownership
    expedition = expedition_service.get_expedition_by_id(expedition_id)
    if not expedition:
        print(f"ERROR: Expedition {expedition_id} not found!")
        return False

    if expedition.owner_chat_id != owner_chat_id:
        print(f"ERROR: You don't own this expedition!")
        print(f"  Expedition owner: {expedition.owner_chat_id}")
        print(f"  Your chat_id: {owner_chat_id}")
        return False

    print(f"[OK] Expedition: {expedition.name}")
    print(f"[OK] Owner: {owner_chat_id}")

    # Step 2: Get the keys
    old_expedition_key = expedition.owner_key
    user_master_key = encryption.generate_user_master_key(owner_chat_id)

    print(f"\n--- Keys ---")
    print(f"Old expedition key: {old_expedition_key[:30]}...")
    print(f"User master key:    {user_master_key[:30]}...")

    if old_expedition_key == user_master_key:
        print("\n[OK] Already using master key! No migration needed.")
        return True

    # Step 3: Get all pirate names
    pirates = brambler.get_expedition_pirate_names(expedition_id)
    print(f"\n--- Pirate Names ---")
    print(f"Total pirates to migrate: {len(pirates)}")

    if not pirates:
        print("No pirate names to migrate!")
        return True

    # Step 4: Decrypt with old key and re-encrypt with master key
    print(f"\n--- Re-encrypting ---")
    migrated_count = 0
    failed_count = 0

    for pirate in pirates:
        try:
            # Decrypt with old expedition key
            if pirate.encrypted_mapping:
                decrypted = encryption.decrypt_name_mapping(
                    pirate.encrypted_mapping,
                    old_expedition_key
                )

                if decrypted and 'mapping' in decrypted:
                    mapping = decrypted['mapping']

                    # Re-encrypt with user master key
                    new_encrypted = encryption.encrypt_name_mapping(
                        expedition_id,
                        mapping,
                        user_master_key
                    )

                    # Update in database
                    query = """
                        UPDATE expedition_pirates
                        SET encrypted_identity = %s
                        WHERE id = %s
                    """
                    brambler._execute_query(query, (new_encrypted, pirate.id))

                    print(f"  [OK] {pirate.pirate_name}")
                    migrated_count += 1
                else:
                    print(f"  [X] {pirate.pirate_name} - failed to decrypt")
                    failed_count += 1
            else:
                print(f"  - {pirate.pirate_name} - no encrypted data")

        except Exception as e:
            print(f"  [X] {pirate.pirate_name} - error: {str(e)[:50]}")
            failed_count += 1

    # Step 5: Update expedition to use master key
    print(f"\n--- Updating Expedition ---")
    update_query = """
        UPDATE expeditions
        SET owner_key = %s
        WHERE id = %s
    """
    expedition_service._execute_query(update_query, (user_master_key, expedition_id))
    print(f"[OK] Expedition {expedition_id} now uses master key")

    # Step 6: Summary
    print(f"\n{'='*60}")
    print(f"Migration Complete!")
    print(f"{'='*60}")
    print(f"[OK] Migrated: {migrated_count} pirates")
    if failed_count > 0:
        print(f"[X] Failed: {failed_count} pirates")
    print(f"\nYour master key (save this!):")
    print(f"{user_master_key}")
    print(f"\nThis key now works for ALL your expeditions!")
    print(f"{'='*60}\n")

    return failed_count == 0


def verify_migration(expedition_id: int, owner_chat_id: int):
    """Verify that migration was successful."""
    brambler = BramblerService()
    expedition_service = ExpeditionService()
    encryption = get_encryption_service()

    print(f"\n{'='*60}")
    print(f"Verifying Migration")
    print(f"{'='*60}\n")

    # Get expedition
    expedition = expedition_service.get_expedition_by_id(expedition_id)
    user_master_key = encryption.generate_user_master_key(owner_chat_id)

    print(f"Expedition owner_key matches master key: {expedition.owner_key == user_master_key}")

    # Try to decrypt all pirates with master key
    print(f"\nTesting decryption with master key...")
    decrypted_mappings = brambler.decrypt_expedition_pirates(expedition_id, user_master_key)

    print(f"[OK] Successfully decrypted {len(decrypted_mappings)} pirates:")
    for pirate_name, original_name in list(decrypted_mappings.items())[:5]:
        print(f"  {pirate_name} -> {original_name}")

    if len(decrypted_mappings) > 5:
        print(f"  ... and {len(decrypted_mappings) - 5} more")

    print(f"\n{'='*60}")
    print(f"[OK] Migration Verified Successfully!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    EXPEDITION_ID = 7
    OWNER_CHAT_ID = 5094426438

    print("\nThis will migrate expedition to use ONE master key per user.")
    print("This allows you to decrypt ALL your expeditions with the SAME key!\n")

    # Run migration
    success = migrate_expedition_to_master_key(EXPEDITION_ID, OWNER_CHAT_ID)

    if success:
        # Verify it worked
        verify_migration(EXPEDITION_ID, OWNER_CHAT_ID)
        print("\n[OK] All done! Use 'Load My Key' in the webapp to get your master key.")
    else:
        print("\n[X] Migration failed! Check errors above.")
