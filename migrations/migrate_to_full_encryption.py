"""
Migration script to upgrade existing expedition pirates to FULL ENCRYPTION MODE.
This script encrypts all existing plain-text original_name fields and sets them to NULL.

WARNING: This is a ONE-WAY migration. Make sure you have backups before running!

Usage:
    python migrations/migrate_to_full_encryption.py [--dry-run] [--expedition-id ID]

Options:
    --dry-run       Show what would be changed without actually changing it
    --expedition-id Only migrate a specific expedition
"""

import sys
import os
import logging
from typing import Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_database_manager
from utils.encryption import get_encryption_service
from services.expedition_service import ExpeditionService
from services.brambler_service import BramblerService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FullEncryptionMigration:
    """Handles migration from plain-text to full encryption mode."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.db_manager = get_database_manager()
        self.encryption_service = get_encryption_service()
        self.expedition_service = ExpeditionService()
        self.brambler_service = BramblerService()

    def migrate_expedition(self, expedition_id: int) -> dict:
        """
        Migrate a single expedition to full encryption mode.

        Args:
            expedition_id: Expedition ID to migrate

        Returns:
            Dictionary with migration results
        """
        logger.info(f"{'[DRY RUN] ' if self.dry_run else ''}Migrating expedition {expedition_id}")

        # Get expedition and owner key
        expedition = self.expedition_service.get_expedition_by_id(expedition_id)
        if not expedition:
            return {"success": False, "error": f"Expedition {expedition_id} not found"}

        # Get or generate owner key
        owner_key = None
        with self.db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT owner_key FROM expeditions WHERE id = %s", (expedition_id,))
                result = cur.fetchone()
                if result and result[0]:
                    owner_key = result[0]

        if not owner_key:
            logger.warning(f"No owner key found for expedition {expedition_id}, generating new one")
            from utils.encryption import generate_owner_key
            owner_key = generate_owner_key(expedition_id, expedition.owner_chat_id)

            if not self.dry_run:
                with self.db_manager.get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "UPDATE expeditions SET owner_key = %s WHERE id = %s",
                            (owner_key, expedition_id)
                        )
                        conn.commit()
                logger.info(f"Generated and stored owner key for expedition {expedition_id}")

        # Get all pirates with plain-text original_name
        pirates_to_migrate = []
        with self.db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, pirate_name, original_name, encrypted_identity
                    FROM expedition_pirates
                    WHERE expedition_id = %s AND original_name IS NOT NULL
                """, (expedition_id,))
                pirates_to_migrate = cur.fetchall()

        if not pirates_to_migrate:
            logger.info(f"No pirates to migrate for expedition {expedition_id}")
            return {"success": True, "migrated_count": 0, "message": "Already encrypted"}

        logger.info(f"Found {len(pirates_to_migrate)} pirates to migrate")

        migrated_count = 0
        errors = []

        for pirate_id, pirate_name, original_name, existing_encrypted in pirates_to_migrate:
            try:
                # Skip if already has encrypted identity
                if existing_encrypted and existing_encrypted.strip():
                    logger.info(f"Pirate {pirate_name} already has encrypted identity, updating to NULL")
                    if not self.dry_run:
                        with self.db_manager.get_connection() as conn:
                            with conn.cursor() as cur:
                                cur.execute(
                                    "UPDATE expedition_pirates SET original_name = NULL WHERE id = %s",
                                    (pirate_id,)
                                )
                                conn.commit()
                    migrated_count += 1
                    continue

                # Create encrypted mapping
                mapping = {original_name: pirate_name}
                encrypted_identity = self.encryption_service.encrypt_name_mapping(
                    expedition_id,
                    mapping,
                    owner_key
                )

                logger.info(f"{'[DRY RUN] ' if self.dry_run else ''}Encrypting: {original_name} -> {pirate_name}")

                if not self.dry_run:
                    # Update database - set encrypted_identity and NULL out original_name
                    with self.db_manager.get_connection() as conn:
                        with conn.cursor() as cur:
                            cur.execute("""
                                UPDATE expedition_pirates
                                SET encrypted_identity = %s, original_name = NULL
                                WHERE id = %s
                            """, (encrypted_identity, pirate_id))
                            conn.commit()

                migrated_count += 1

            except Exception as e:
                error_msg = f"Failed to migrate pirate {pirate_id} ({pirate_name}): {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        result = {
            "success": len(errors) == 0,
            "expedition_id": expedition_id,
            "total_pirates": len(pirates_to_migrate),
            "migrated_count": migrated_count,
            "errors": errors
        }

        if self.dry_run:
            result["message"] = "DRY RUN - No changes were made"

        return result

    def migrate_all_expeditions(self) -> dict:
        """
        Migrate ALL expeditions to full encryption mode.

        Returns:
            Dictionary with overall migration results
        """
        logger.info(f"{'[DRY RUN] ' if self.dry_run else ''}Starting full migration of all expeditions")

        # Get all expedition IDs
        expedition_ids = []
        with self.db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM expeditions ORDER BY id")
                expedition_ids = [row[0] for row in cur.fetchall()]

        logger.info(f"Found {len(expedition_ids)} expeditions to migrate")

        results = []
        total_migrated = 0
        total_errors = 0

        for expedition_id in expedition_ids:
            result = self.migrate_expedition(expedition_id)
            results.append(result)
            total_migrated += result.get("migrated_count", 0)
            total_errors += len(result.get("errors", []))

        summary = {
            "success": total_errors == 0,
            "total_expeditions": len(expedition_ids),
            "total_pirates_migrated": total_migrated,
            "total_errors": total_errors,
            "results": results
        }

        if self.dry_run:
            summary["message"] = "DRY RUN - No changes were made"

        return summary

    def verify_encryption(self, expedition_id: int) -> dict:
        """
        Verify that encryption for an expedition is working correctly.

        Args:
            expedition_id: Expedition ID to verify

        Returns:
            Dictionary with verification results
        """
        logger.info(f"Verifying encryption for expedition {expedition_id}")

        # Get owner key
        owner_key = self.expedition_service.get_expedition_owner_key(
            expedition_id,
            0  # We don't need ownership validation for verification
        )

        if not owner_key:
            return {"success": False, "error": "No owner key found"}

        # Get all encrypted pirates
        with self.db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, pirate_name, original_name, encrypted_identity
                    FROM expedition_pirates
                    WHERE expedition_id = %s
                """, (expedition_id,))
                pirates = cur.fetchall()

        if not pirates:
            return {"success": True, "message": "No pirates to verify"}

        verification_results = []
        for pirate_id, pirate_name, original_name, encrypted_identity in pirates:
            result = {
                "pirate_id": pirate_id,
                "pirate_name": pirate_name,
                "has_plain_text": original_name is not None,
                "has_encrypted": bool(encrypted_identity and encrypted_identity.strip()),
                "can_decrypt": False,
                "decrypted_name": None
            }

            if encrypted_identity and encrypted_identity.strip():
                try:
                    decrypted_mapping = self.encryption_service.decrypt_name_mapping(
                        encrypted_identity,
                        owner_key
                    )
                    if decrypted_mapping and 'mapping' in decrypted_mapping:
                        mapping = decrypted_mapping['mapping']
                        for orig, pirate in mapping.items():
                            if pirate == pirate_name:
                                result["can_decrypt"] = True
                                result["decrypted_name"] = orig
                                break
                except Exception as e:
                    result["decrypt_error"] = str(e)

            verification_results.append(result)

        # Summary
        total_pirates = len(pirates)
        encrypted_count = sum(1 for r in verification_results if r["has_encrypted"])
        plain_text_count = sum(1 for r in verification_results if r["has_plain_text"])
        decryptable_count = sum(1 for r in verification_results if r["can_decrypt"])

        return {
            "success": True,
            "expedition_id": expedition_id,
            "total_pirates": total_pirates,
            "encrypted_count": encrypted_count,
            "plain_text_count": plain_text_count,
            "decryptable_count": decryptable_count,
            "fully_encrypted": plain_text_count == 0 and encrypted_count == total_pirates,
            "verification_details": verification_results
        }


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Migrate expedition pirates to full encryption mode')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without changing it')
    parser.add_argument('--expedition-id', type=int, help='Only migrate a specific expedition')
    parser.add_argument('--verify', action='store_true', help='Verify encryption instead of migrating')

    args = parser.parse_args()

    migration = FullEncryptionMigration(dry_run=args.dry_run)

    try:
        if args.verify:
            if not args.expedition_id:
                logger.error("--expedition-id is required for verification")
                sys.exit(1)

            result = migration.verify_encryption(args.expedition_id)
            logger.info("Verification Results:")
            logger.info(f"  Total Pirates: {result['total_pirates']}")
            logger.info(f"  Encrypted: {result['encrypted_count']}")
            logger.info(f"  Plain Text: {result['plain_text_count']}")
            logger.info(f"  Decryptable: {result['decryptable_count']}")
            logger.info(f"  Fully Encrypted: {result['fully_encrypted']}")

            if not result['fully_encrypted']:
                logger.warning("⚠️  Expedition is NOT fully encrypted!")
                for detail in result['verification_details']:
                    if detail['has_plain_text']:
                        logger.warning(f"  - {detail['pirate_name']} still has plain text original name")

        elif args.expedition_id:
            result = migration.migrate_expedition(args.expedition_id)
            logger.info(f"Migration completed for expedition {args.expedition_id}")
            logger.info(f"  Migrated: {result['migrated_count']} pirates")
            if result['errors']:
                logger.error(f"  Errors: {len(result['errors'])}")
                for error in result['errors']:
                    logger.error(f"    - {error}")
        else:
            result = migration.migrate_all_expeditions()
            logger.info("Migration completed for all expeditions")
            logger.info(f"  Total Expeditions: {result['total_expeditions']}")
            logger.info(f"  Total Pirates Migrated: {result['total_pirates_migrated']}")
            logger.info(f"  Total Errors: {result['total_errors']}")

        if args.dry_run:
            logger.info("\n⚠️  DRY RUN MODE - No changes were made to the database")
            logger.info("Run without --dry-run to apply changes")

    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
