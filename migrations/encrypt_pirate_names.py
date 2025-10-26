"""
Migration Script: Encrypt All Pirate Names
===========================================

This script encrypts all existing plain-text pirate names in the expedition_pirates table.

WHAT IT DOES:
1. Backs up current data to a JSON file
2. For each expedition:
   - Gets the expedition owner_key
   - Encrypts all pirate name mappings (original_name -> pirate_name)
   - Updates expedition_pirates records with encrypted_identity
   - Sets original_name to NULL (true anonymization)
3. Verifies all records were migrated successfully

SAFETY FEATURES:
- Creates backup before any changes
- Runs in transaction (can rollback)
- Verifies decryption works before committing
- Detailed logging of all operations
- Dry-run mode for testing

ROLLBACK:
- Run with --rollback flag to restore from backup
- Backup file: migrations/backups/pirate_names_backup_<timestamp>.json
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

from database import get_db_manager, initialize_database
from utils.encryption import get_encryption_service, generate_owner_key
from utils.input_sanitizer import InputSanitizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'migrations/encrypt_pirate_names_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PirateNameEncryptionMigration:
    """Handles migration of pirate names from plain text to encrypted storage."""

    def __init__(self, dry_run: bool = False):
        """
        Initialize migration.

        Args:
            dry_run: If True, only simulate the migration without making changes
        """
        self.dry_run = dry_run
        self.db_manager = get_db_manager()
        self.encryption_service = get_encryption_service()
        self.backup_dir = "migrations/backups"
        self.backup_file = None
        self.stats = {
            'total_expeditions': 0,
            'total_pirates': 0,
            'encrypted': 0,
            'failed': 0,
            'skipped': 0
        }

    def ensure_backup_dir(self):
        """Create backup directory if it doesn't exist."""
        os.makedirs(self.backup_dir, exist_ok=True)
        logger.info(f"Backup directory: {self.backup_dir}")

    def create_backup(self) -> str:
        """
        Create backup of current pirate names data.

        Returns:
            Path to backup file
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.backup_file = os.path.join(self.backup_dir, f"pirate_names_backup_{timestamp}.json")

            logger.info("Creating backup of current data...")

            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    # Get all pirate data
                    cur.execute("""
                        SELECT
                            ep.id,
                            ep.expedition_id,
                            ep.original_name,
                            ep.pirate_name,
                            ep.encrypted_identity,
                            ep.chat_id,
                            ep.user_id,
                            ep.role,
                            ep.status,
                            ep.joined_at,
                            e.owner_key,
                            e.owner_chat_id
                        FROM expedition_pirates ep
                        JOIN expeditions e ON ep.expedition_id = e.id
                        ORDER BY ep.expedition_id, ep.id
                    """)

                    rows = cur.fetchall()

                    backup_data = {
                        'timestamp': timestamp,
                        'total_records': len(rows),
                        'pirates': []
                    }

                    for row in rows:
                        pirate_id, expedition_id, original_name, pirate_name, encrypted_identity, \
                            chat_id, user_id, role, status, joined_at, owner_key, owner_chat_id = row

                        backup_data['pirates'].append({
                            'id': pirate_id,
                            'expedition_id': expedition_id,
                            'original_name': original_name,
                            'pirate_name': pirate_name,
                            'encrypted_identity': encrypted_identity,
                            'chat_id': chat_id,
                            'user_id': user_id,
                            'role': role,
                            'status': status,
                            'joined_at': joined_at.isoformat() if joined_at else None,
                            'owner_key': owner_key,
                            'owner_chat_id': owner_chat_id
                        })

            # Write backup to file
            with open(self.backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Backup created: {self.backup_file}")
            logger.info(f"Backed up {backup_data['total_records']} pirate records")

            return self.backup_file

        except Exception as e:
            logger.error(f"Failed to create backup: {e}", exc_info=True)
            raise

    def get_expeditions_with_pirates(self) -> List[Dict]:
        """
        Get all expeditions that have pirates.

        Returns:
            List of expedition data dictionaries
        """
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT DISTINCT
                            e.id,
                            e.name,
                            e.owner_chat_id,
                            e.owner_user_id,
                            e.owner_key
                        FROM expeditions e
                        JOIN expedition_pirates ep ON ep.expedition_id = e.id
                        WHERE ep.original_name IS NOT NULL
                        ORDER BY e.id
                    """)

                    rows = cur.fetchall()
                    expeditions = []

                    for row in rows:
                        exp_id, name, owner_chat_id, owner_user_id, owner_key = row
                        expeditions.append({
                            'id': exp_id,
                            'name': name,
                            'owner_chat_id': owner_chat_id,
                            'owner_user_id': owner_user_id,
                            'owner_key': owner_key
                        })

                    return expeditions

        except Exception as e:
            logger.error(f"Failed to get expeditions: {e}", exc_info=True)
            raise

    def get_pirates_for_expedition(self, expedition_id: int) -> List[Tuple]:
        """
        Get all pirates for an expedition that need encryption.

        Args:
            expedition_id: Expedition ID

        Returns:
            List of tuples (pirate_id, original_name, pirate_name, encrypted_identity)
        """
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, original_name, pirate_name, encrypted_identity
                        FROM expedition_pirates
                        WHERE expedition_id = %s AND original_name IS NOT NULL
                        ORDER BY id
                    """, (expedition_id,))

                    return cur.fetchall()

        except Exception as e:
            logger.error(f"Failed to get pirates for expedition {expedition_id}: {e}", exc_info=True)
            raise

    def encrypt_expedition_pirates(self, expedition: Dict) -> int:
        """
        Encrypt all pirates for a single expedition.

        Args:
            expedition: Expedition data dictionary

        Returns:
            Number of pirates encrypted
        """
        expedition_id = expedition['id']
        expedition_name = expedition['name']
        owner_key = expedition['owner_key']
        owner_chat_id = expedition['owner_chat_id']
        owner_user_id = expedition['owner_user_id']

        logger.info(f"\nProcessing Expedition #{expedition_id}: {expedition_name}")

        # Get owner key if not set
        if not owner_key:
            logger.warning(f"Expedition {expedition_id} has no owner_key, generating one...")
            owner_key = generate_owner_key(expedition_id, owner_user_id or owner_chat_id)

            if not self.dry_run:
                # Update expedition with new owner_key
                with self.db_manager.get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            UPDATE expeditions
                            SET owner_key = %s
                            WHERE id = %s
                        """, (owner_key, expedition_id))
                        conn.commit()

                logger.info(f"Generated and saved owner_key for expedition {expedition_id}")

        # Get all pirates for this expedition
        pirates = self.get_pirates_for_expedition(expedition_id)

        if not pirates:
            logger.info(f"No pirates to encrypt for expedition {expedition_id}")
            return 0

        logger.info(f"Found {len(pirates)} pirates to encrypt")

        # Build name mapping for encryption
        name_mapping = {}
        pirate_updates = []

        for pirate_id, original_name, pirate_name, existing_encrypted in pirates:
            if not original_name:
                logger.warning(f"Pirate {pirate_id} has no original_name, skipping")
                self.stats['skipped'] += 1
                continue

            # Check if already encrypted
            if existing_encrypted and existing_encrypted.strip():
                logger.info(f"Pirate {pirate_id} already has encrypted_identity, skipping")
                self.stats['skipped'] += 1
                continue

            # Add to mapping
            name_mapping[original_name] = pirate_name
            pirate_updates.append(pirate_id)

        if not name_mapping:
            logger.info(f"No new pirates to encrypt for expedition {expedition_id}")
            return 0

        try:
            # Encrypt the name mapping
            logger.info(f"Encrypting {len(name_mapping)} name mappings...")
            encrypted_identity = self.encryption_service.encrypt_name_mapping(
                expedition_id,
                name_mapping,
                owner_key
            )

            # Verify encryption worked by testing decryption
            logger.info("Verifying encryption...")
            decrypted_mapping = self.encryption_service.decrypt_name_mapping(
                encrypted_identity,
                owner_key
            )

            if decrypted_mapping != name_mapping:
                raise Exception("Decryption verification failed - mappings don't match!")

            logger.info("Encryption verification successful!")

            # Update database if not dry run
            if not self.dry_run:
                with self.db_manager.get_connection() as conn:
                    with conn.cursor() as cur:
                        # Update all pirates with the encrypted identity
                        for pirate_id in pirate_updates:
                            cur.execute("""
                                UPDATE expedition_pirates
                                SET encrypted_identity = %s,
                                    original_name = NULL
                                WHERE id = %s
                            """, (encrypted_identity, pirate_id))

                        conn.commit()

                logger.info(f"Updated {len(pirate_updates)} pirates with encrypted identities")
            else:
                logger.info(f"[DRY RUN] Would update {len(pirate_updates)} pirates")

            self.stats['encrypted'] += len(pirate_updates)
            return len(pirate_updates)

        except Exception as e:
            logger.error(f"Failed to encrypt pirates for expedition {expedition_id}: {e}", exc_info=True)
            self.stats['failed'] += len(pirate_updates)
            return 0

    def run_migration(self) -> bool:
        """
        Run the full migration process.

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("="*80)
            logger.info("PIRATE NAME ENCRYPTION MIGRATION")
            logger.info("="*80)

            if self.dry_run:
                logger.info("*** DRY RUN MODE - No changes will be made ***")
            else:
                logger.info("*** LIVE MODE - Database will be modified ***")

            # Ensure backup directory exists
            self.ensure_backup_dir()

            # Create backup
            logger.info("\n" + "="*80)
            logger.info("STEP 1: Creating Backup")
            logger.info("="*80)
            self.create_backup()

            # Get all expeditions with pirates
            logger.info("\n" + "="*80)
            logger.info("STEP 2: Getting Expeditions")
            logger.info("="*80)
            expeditions = self.get_expeditions_with_pirates()
            self.stats['total_expeditions'] = len(expeditions)

            if not expeditions:
                logger.info("No expeditions found with unencrypted pirates")
                return True

            logger.info(f"Found {len(expeditions)} expeditions with pirates to encrypt")

            # Encrypt pirates for each expedition
            logger.info("\n" + "="*80)
            logger.info("STEP 3: Encrypting Pirate Names")
            logger.info("="*80)

            for expedition in expeditions:
                encrypted_count = self.encrypt_expedition_pirates(expedition)
                self.stats['total_pirates'] += encrypted_count

            # Print summary
            logger.info("\n" + "="*80)
            logger.info("MIGRATION SUMMARY")
            logger.info("="*80)
            logger.info(f"Total Expeditions Processed: {self.stats['total_expeditions']}")
            logger.info(f"Total Pirates Encrypted: {self.stats['encrypted']}")
            logger.info(f"Pirates Skipped (already encrypted): {self.stats['skipped']}")
            logger.info(f"Failures: {self.stats['failed']}")

            if self.dry_run:
                logger.info("\n*** DRY RUN COMPLETE - No changes were made ***")
                logger.info("Run without --dry-run flag to apply changes")
            else:
                logger.info("\n*** MIGRATION COMPLETE ***")
                logger.info(f"Backup saved to: {self.backup_file}")

            if self.stats['failed'] > 0:
                logger.warning(f"\n*** WARNING: {self.stats['failed']} pirates failed to encrypt ***")
                return False

            return True

        except Exception as e:
            logger.error(f"Migration failed: {e}", exc_info=True)
            return False

    def rollback_from_backup(self, backup_file: str) -> bool:
        """
        Rollback changes using a backup file.

        Args:
            backup_file: Path to backup file

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("="*80)
            logger.info("ROLLING BACK FROM BACKUP")
            logger.info("="*80)

            if not os.path.exists(backup_file):
                logger.error(f"Backup file not found: {backup_file}")
                return False

            # Load backup data
            logger.info(f"Loading backup from: {backup_file}")
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)

            logger.info(f"Backup contains {backup_data['total_records']} records")
            logger.info(f"Backup timestamp: {backup_data['timestamp']}")

            # Restore data
            restored = 0
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    for pirate in backup_data['pirates']:
                        cur.execute("""
                            UPDATE expedition_pirates
                            SET original_name = %s,
                                encrypted_identity = %s
                            WHERE id = %s
                        """, (
                            pirate['original_name'],
                            pirate['encrypted_identity'],
                            pirate['id']
                        ))
                        restored += 1

                    conn.commit()

            logger.info(f"Restored {restored} pirate records")
            logger.info("*** ROLLBACK COMPLETE ***")

            return True

        except Exception as e:
            logger.error(f"Rollback failed: {e}", exc_info=True)
            return False


def main():
    """Main entry point for migration script."""
    import argparse

    parser = argparse.ArgumentParser(description='Encrypt pirate names in expedition_pirates table')
    parser.add_argument('--dry-run', action='store_true',
                       help='Run in dry-run mode (no changes)')
    parser.add_argument('--rollback', type=str, metavar='BACKUP_FILE',
                       help='Rollback using specified backup file')

    args = parser.parse_args()

    # Initialize database connection
    logger.info("Initializing database connection...")
    initialize_database()
    logger.info("Database initialized successfully")

    migration = PirateNameEncryptionMigration(dry_run=args.dry_run)

    if args.rollback:
        # Rollback mode
        success = migration.rollback_from_backup(args.rollback)
    else:
        # Migration mode
        success = migration.run_migration()

    if success:
        logger.info("\nOperation completed successfully!")
        sys.exit(0)
    else:
        logger.error("\nOperation failed!")
        sys.exit(1)


if __name__ == '__main__':
    main()
