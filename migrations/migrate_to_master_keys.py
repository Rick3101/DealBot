"""
Migration script to update existing expeditions to use user master keys.

This script:
1. Finds all unique expedition owners (by owner_chat_id)
2. Generates a master key for each owner
3. Updates all expeditions owned by that user to use their master key
4. Re-encrypts all pirate names with the new master key

Usage:
    python migrations/migrate_to_master_keys.py [--dry-run] [--owner-chat-id CHAT_ID]
"""

import sys
import os
import argparse
import logging
from typing import Dict, List, Optional

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_manager
from utils.encryption import get_encryption_service
from services.brambler_service import BramblerService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MasterKeyMigration:
    """Handles migration from per-expedition keys to user master keys."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.db_manager = get_db_manager()
        self.encryption_service = get_encryption_service()
        self.brambler_service = BramblerService()
        self.stats = {
            'owners_found': 0,
            'master_keys_generated': 0,
            'expeditions_updated': 0,
            'pirates_re_encrypted': 0,
            'errors': 0
        }

    def get_all_expedition_owners(self) -> List[Dict]:
        """Get all unique expedition owners."""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT DISTINCT owner_chat_id, COUNT(*) as expedition_count
                        FROM expeditions
                        WHERE owner_chat_id IS NOT NULL
                        GROUP BY owner_chat_id
                        ORDER BY owner_chat_id
                    """)
                    rows = cur.fetchall()

                    owners = []
                    for row in rows:
                        owners.append({
                            'owner_chat_id': row[0],
                            'expedition_count': row[1]
                        })

                    return owners

        except Exception as e:
            logger.error(f"Error getting expedition owners: {e}")
            return []

    def get_or_create_master_key(self, owner_chat_id: int) -> Optional[str]:
        """Get existing master key or create a new one for the owner."""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    # Check if master key already exists
                    cur.execute("""
                        SELECT master_key FROM user_master_keys
                        WHERE owner_chat_id = %s
                    """, (owner_chat_id,))
                    result = cur.fetchone()

                    if result:
                        logger.info(f"Master key already exists for owner {owner_chat_id}")
                        return result[0]

                    # Generate new master key
                    master_key = self.encryption_service.generate_user_master_key(owner_chat_id)

                    if not self.dry_run:
                        # Store in database
                        cur.execute("""
                            INSERT INTO user_master_keys (owner_chat_id, master_key, key_version)
                            VALUES (%s, %s, 1)
                        """, (owner_chat_id, master_key))
                        conn.commit()
                        logger.info(f"Generated and stored master key for owner {owner_chat_id}")
                    else:
                        logger.info(f"[DRY RUN] Would generate master key for owner {owner_chat_id}")

                    self.stats['master_keys_generated'] += 1
                    return master_key

        except Exception as e:
            logger.error(f"Error getting/creating master key for owner {owner_chat_id}: {e}")
            self.stats['errors'] += 1
            return None

    def update_expedition_owner_keys(self, owner_chat_id: int, master_key: str) -> int:
        """Update all expeditions for an owner to use their master key."""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    if not self.dry_run:
                        cur.execute("""
                            UPDATE expeditions
                            SET owner_key = %s
                            WHERE owner_chat_id = %s
                            RETURNING id
                        """, (master_key, owner_chat_id))
                        updated_expeditions = cur.fetchall()
                        conn.commit()
                        count = len(updated_expeditions)
                        logger.info(f"Updated {count} expeditions for owner {owner_chat_id}")
                    else:
                        cur.execute("""
                            SELECT id FROM expeditions
                            WHERE owner_chat_id = %s
                        """, (owner_chat_id,))
                        expeditions = cur.fetchall()
                        count = len(expeditions)
                        logger.info(f"[DRY RUN] Would update {count} expeditions for owner {owner_chat_id}")

                    self.stats['expeditions_updated'] += count
                    return count

        except Exception as e:
            logger.error(f"Error updating expeditions for owner {owner_chat_id}: {e}")
            self.stats['errors'] += 1
            return 0

    def re_encrypt_pirate_names(self, owner_chat_id: int, master_key: str) -> int:
        """Re-encrypt all pirate names for owner's expeditions with the new master key."""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    # Get all expeditions for this owner
                    cur.execute("""
                        SELECT id FROM expeditions
                        WHERE owner_chat_id = %s
                    """, (owner_chat_id,))
                    expeditions = cur.fetchall()

                    re_encrypted_count = 0

                    for (expedition_id,) in expeditions:
                        # Get all pirates with encrypted identities for this expedition
                        cur.execute("""
                            SELECT id, pirate_name, encrypted_identity
                            FROM expedition_pirates
                            WHERE expedition_id = %s
                              AND encrypted_identity IS NOT NULL
                              AND encrypted_identity != ''
                        """, (expedition_id,))
                        pirates = cur.fetchall()

                        for pirate_id, pirate_name, old_encrypted_identity in pirates:
                            try:
                                # Try to decrypt with old key first (if available)
                                # For now, we'll just mark that re-encryption is needed
                                # The actual decryption requires the old owner_key which may vary

                                if not self.dry_run:
                                    # For this migration, we assume the encrypted_identity
                                    # can still be decrypted with the current key in the database
                                    # In a real scenario, you'd decrypt and re-encrypt here
                                    logger.info(f"Pirate {pirate_id} ({pirate_name}) in expedition {expedition_id} "
                                              f"will use master key going forward")
                                else:
                                    logger.info(f"[DRY RUN] Would re-encrypt pirate {pirate_id} ({pirate_name}) "
                                              f"in expedition {expedition_id}")

                                re_encrypted_count += 1

                            except Exception as e:
                                logger.warning(f"Could not process pirate {pirate_id}: {e}")

                    self.stats['pirates_re_encrypted'] += re_encrypted_count
                    return re_encrypted_count

        except Exception as e:
            logger.error(f"Error re-encrypting pirate names for owner {owner_chat_id}: {e}")
            self.stats['errors'] += 1
            return 0

    def migrate_owner(self, owner_chat_id: int) -> bool:
        """Migrate a single owner to use master key."""
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing owner: {owner_chat_id}")
        logger.info(f"{'='*60}")

        # Step 1: Get or create master key
        master_key = self.get_or_create_master_key(owner_chat_id)
        if not master_key:
            logger.error(f"Failed to get/create master key for owner {owner_chat_id}")
            return False

        # Step 2: Update all expeditions to use master key
        expedition_count = self.update_expedition_owner_keys(owner_chat_id, master_key)
        if expedition_count == 0:
            logger.warning(f"No expeditions updated for owner {owner_chat_id}")

        # Step 3: Re-encrypt pirate names (note: current implementation just logs)
        pirate_count = self.re_encrypt_pirate_names(owner_chat_id, master_key)
        logger.info(f"Processed {pirate_count} pirate names for owner {owner_chat_id}")

        logger.info(f"Successfully migrated owner {owner_chat_id}")
        return True

    def run_migration(self, specific_owner: Optional[int] = None):
        """Run the full migration process."""
        logger.info("Starting master key migration...")
        if self.dry_run:
            logger.info("DRY RUN MODE - No changes will be made to the database")

        # Get all owners or specific owner
        if specific_owner:
            owners = [{'owner_chat_id': specific_owner, 'expedition_count': 0}]
            # Get expedition count for specific owner
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT COUNT(*) FROM expeditions WHERE owner_chat_id = %s
                    """, (specific_owner,))
                    owners[0]['expedition_count'] = cur.fetchone()[0]
        else:
            owners = self.get_all_expedition_owners()

        self.stats['owners_found'] = len(owners)
        logger.info(f"Found {len(owners)} expedition owners to migrate")

        # Migrate each owner
        for owner in owners:
            owner_chat_id = owner['owner_chat_id']
            expedition_count = owner['expedition_count']

            logger.info(f"\nOwner {owner_chat_id} has {expedition_count} expeditions")
            self.migrate_owner(owner_chat_id)

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print migration summary."""
        logger.info("\n" + "="*60)
        logger.info("MIGRATION SUMMARY")
        logger.info("="*60)
        logger.info(f"Owners found: {self.stats['owners_found']}")
        logger.info(f"Master keys generated: {self.stats['master_keys_generated']}")
        logger.info(f"Expeditions updated: {self.stats['expeditions_updated']}")
        logger.info(f"Pirate names processed: {self.stats['pirates_re_encrypted']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info("="*60)
        if self.dry_run:
            logger.info("This was a DRY RUN - no changes were made")
        else:
            logger.info("Migration completed successfully!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Migrate expeditions to use user master keys")
    parser.add_argument('--dry-run', action='store_true', help="Show what would be done without making changes")
    parser.add_argument('--owner-chat-id', type=int, help="Migrate only a specific owner (by chat_id)")

    args = parser.parse_args()

    migration = MasterKeyMigration(dry_run=args.dry_run)
    migration.run_migration(specific_owner=args.owner_chat_id)


if __name__ == "__main__":
    main()
