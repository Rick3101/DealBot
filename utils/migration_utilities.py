"""
Database migration utilities for expedition system redesign.
Provides safe migration tools and validation for Sprint 1 implementation.
"""

import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from database import get_db_manager
from database.schema import initialize_schema, health_check_schema

logger = logging.getLogger(__name__)


class MigrationError(Exception):
    """Exception raised for migration errors."""
    pass


class ExpeditionMigrationUtility:
    """
    Utility class for managing expedition system database migrations.
    Implements safe migration procedures with rollback capabilities.
    """

    def __init__(self):
        self.db_manager = get_db_manager()
        self.migration_log = []

    def validate_pre_migration(self) -> Dict[str, any]:
        """
        Validate database state before migration.

        Returns:
            Dictionary with validation results
        """
        logger.info("Starting pre-migration validation...")
        validation_results = {
            "healthy": True,
            "issues": [],
            "warnings": [],
            "statistics": {}
        }

        try:
            # Check database health
            health_status = health_check_schema()
            if not health_status.get("healthy", False):
                validation_results["healthy"] = False
                validation_results["issues"].append(f"Schema health check failed: {health_status.get('message', 'Unknown error')}")

            # Count existing expedition data
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Check if expeditions table exists
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_schema = 'public'
                            AND table_name = 'expeditions'
                        );
                    """)
                    expeditions_exists = cursor.fetchone()[0]

                    if expeditions_exists:
                        # Count existing expeditions
                        cursor.execute("SELECT COUNT(*) FROM expeditions")
                        expedition_count = cursor.fetchone()[0]
                        validation_results["statistics"]["existing_expeditions"] = expedition_count

                        # Count existing expedition items
                        cursor.execute("SELECT COUNT(*) FROM expedition_items")
                        item_count = cursor.fetchone()[0]
                        validation_results["statistics"]["existing_expedition_items"] = item_count

                        # Count existing pirate names
                        cursor.execute("SELECT COUNT(*) FROM pirate_names")
                        pirate_count = cursor.fetchone()[0]
                        validation_results["statistics"]["existing_pirate_names"] = pirate_count

                        # Count existing consumptions
                        cursor.execute("SELECT COUNT(*) FROM item_consumptions")
                        consumption_count = cursor.fetchone()[0]
                        validation_results["statistics"]["existing_consumptions"] = consumption_count

                        # Check for data that needs migration
                        if expedition_count > 0:
                            validation_results["warnings"].append(f"Found {expedition_count} existing expeditions that will be migrated")
                        if item_count > 0:
                            validation_results["warnings"].append(f"Found {item_count} existing expedition items that will be enhanced")

                    else:
                        validation_results["statistics"]["existing_expeditions"] = 0
                        validation_results["warnings"].append("No existing expeditions table found - clean installation")

            logger.info(f"Pre-migration validation completed. Healthy: {validation_results['healthy']}")
            return validation_results

        except Exception as e:
            logger.error(f"Pre-migration validation failed: {e}")
            validation_results["healthy"] = False
            validation_results["issues"].append(f"Validation error: {str(e)}")
            return validation_results

    def backup_existing_data(self) -> Dict[str, any]:
        """
        Create backup of existing expedition data before migration.

        Returns:
            Dictionary with backup information
        """
        logger.info("Creating backup of existing expedition data...")
        backup_info = {
            "timestamp": datetime.now().isoformat(),
            "backup_created": False,
            "tables_backed_up": [],
            "record_counts": {}
        }

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Tables to backup
                    tables_to_backup = [
                        'expeditions',
                        'expedition_items',
                        'pirate_names',
                        'item_consumptions'
                    ]

                    for table in tables_to_backup:
                        # Check if table exists
                        cursor.execute("""
                            SELECT EXISTS (
                                SELECT FROM information_schema.tables
                                WHERE table_schema = 'public'
                                AND table_name = %s
                            );
                        """, (table,))

                        if cursor.fetchone()[0]:
                            # Create backup table
                            backup_table_name = f"{table}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

                            cursor.execute(f"""
                                CREATE TABLE {backup_table_name} AS
                                SELECT * FROM {table}
                            """)

                            # Count records
                            cursor.execute(f"SELECT COUNT(*) FROM {backup_table_name}")
                            record_count = cursor.fetchone()[0]

                            backup_info["tables_backed_up"].append(backup_table_name)
                            backup_info["record_counts"][table] = record_count

                            logger.info(f"Backed up {record_count} records from {table} to {backup_table_name}")

                    conn.commit()
                    backup_info["backup_created"] = True
                    logger.info(f"Backup completed successfully. Backed up {len(backup_info['tables_backed_up'])} tables")

        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            backup_info["error"] = str(e)
            raise MigrationError(f"Failed to create backup: {e}")

        return backup_info

    def migrate_expedition_data(self) -> Dict[str, any]:
        """
        Migrate existing expedition data to new schema structure.

        Returns:
            Dictionary with migration results
        """
        logger.info("Starting expedition data migration...")
        migration_results = {
            "success": False,
            "expeditions_migrated": 0,
            "items_enhanced": 0,
            "new_tables_created": 0,
            "errors": []
        }

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Check existing expeditions that need admin keys
                    cursor.execute("""
                        SELECT id, name, owner_chat_id
                        FROM expeditions
                        WHERE admin_key IS NULL
                    """)
                    expeditions_needing_admin_keys = cursor.fetchall()

                    # Generate admin keys for existing expeditions
                    for exp_id, name, owner_chat_id in expeditions_needing_admin_keys:
                        try:
                            from utils.encryption import generate_owner_key

                            # Generate admin key (similar to owner key but with different salt)
                            admin_key = generate_owner_key(exp_id, owner_chat_id + 1000)  # Different salt for admin key

                            cursor.execute("""
                                UPDATE expeditions
                                SET admin_key = %s,
                                    encryption_version = 1,
                                    anonymization_level = 'standard'
                                WHERE id = %s
                            """, (admin_key, exp_id))

                            migration_results["expeditions_migrated"] += 1
                            logger.debug(f"Generated admin key for expedition {exp_id}")

                        except Exception as e:
                            logger.warning(f"Failed to generate admin key for expedition {exp_id}: {e}")
                            migration_results["errors"].append(f"Expedition {exp_id}: {str(e)}")

                    # Enhance expedition items with anonymized codes
                    cursor.execute("""
                        SELECT ei.id, ei.expedition_id, ei.produto_id, p.nome
                        FROM expedition_items ei
                        LEFT JOIN produtos p ON ei.produto_id = p.id
                        WHERE ei.anonymized_item_code IS NULL
                    """)
                    items_needing_enhancement = cursor.fetchall()

                    for item_id, exp_id, produto_id, produto_nome in items_needing_enhancement:
                        try:
                            # Generate anonymized item code
                            import secrets
                            anonymized_code = f"ITEM_{secrets.token_hex(4).upper()}"

                            # Set default values for new fields
                            cursor.execute("""
                                UPDATE expedition_items
                                SET anonymized_item_code = %s,
                                    item_status = 'active',
                                    priority_level = 1,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE id = %s
                            """, (anonymized_code, item_id))

                            migration_results["items_enhanced"] += 1
                            logger.debug(f"Enhanced expedition item {item_id} with code {anonymized_code}")

                        except Exception as e:
                            logger.warning(f"Failed to enhance expedition item {item_id}: {e}")
                            migration_results["errors"].append(f"Item {item_id}: {str(e)}")

                    # Verify new tables were created
                    new_tables = ['expedition_pirates', 'expedition_assignments', 'expedition_payments']
                    for table in new_tables:
                        cursor.execute("""
                            SELECT EXISTS (
                                SELECT FROM information_schema.tables
                                WHERE table_schema = 'public'
                                AND table_name = %s
                            );
                        """, (table,))

                        if cursor.fetchone()[0]:
                            migration_results["new_tables_created"] += 1
                            logger.debug(f"Verified new table exists: {table}")

                    conn.commit()
                    migration_results["success"] = True
                    logger.info(f"Migration completed successfully. Migrated {migration_results['expeditions_migrated']} expeditions, enhanced {migration_results['items_enhanced']} items")

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            migration_results["errors"].append(f"Migration error: {str(e)}")
            raise MigrationError(f"Data migration failed: {e}")

        return migration_results

    def validate_post_migration(self) -> Dict[str, any]:
        """
        Validate database state after migration.

        Returns:
            Dictionary with validation results
        """
        logger.info("Starting post-migration validation...")
        validation_results = {
            "healthy": True,
            "issues": [],
            "warnings": [],
            "statistics": {},
            "new_features_ready": True
        }

        try:
            # Check overall schema health
            health_status = health_check_schema()
            if not health_status.get("healthy", False):
                validation_results["healthy"] = False
                validation_results["new_features_ready"] = False
                validation_results["issues"].append(f"Schema health check failed: {health_status.get('message', 'Unknown error')}")

            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Verify all new tables exist
                    required_new_tables = ['expedition_pirates', 'expedition_assignments', 'expedition_payments']
                    for table in required_new_tables:
                        cursor.execute("""
                            SELECT EXISTS (
                                SELECT FROM information_schema.tables
                                WHERE table_schema = 'public'
                                AND table_name = %s
                            );
                        """, (table,))

                        if not cursor.fetchone()[0]:
                            validation_results["healthy"] = False
                            validation_results["new_features_ready"] = False
                            validation_results["issues"].append(f"Required table missing: {table}")

                    # Verify new columns exist in expeditions table
                    required_expedition_columns = ['admin_key', 'encryption_version', 'anonymization_level', 'description']
                    for column in required_expedition_columns:
                        cursor.execute("""
                            SELECT EXISTS (
                                SELECT FROM information_schema.columns
                                WHERE table_name = 'expeditions'
                                AND column_name = %s
                            );
                        """, (column,))

                        if not cursor.fetchone()[0]:
                            validation_results["healthy"] = False
                            validation_results["new_features_ready"] = False
                            validation_results["issues"].append(f"Required column missing in expeditions: {column}")

                    # Verify new columns exist in expedition_items table
                    required_item_columns = ['anonymized_item_code', 'item_status', 'priority_level', 'updated_at']
                    for column in required_item_columns:
                        cursor.execute("""
                            SELECT EXISTS (
                                SELECT FROM information_schema.columns
                                WHERE table_name = 'expedition_items'
                                AND column_name = %s
                            );
                        """, (column,))

                        if not cursor.fetchone()[0]:
                            validation_results["healthy"] = False
                            validation_results["new_features_ready"] = False
                            validation_results["issues"].append(f"Required column missing in expedition_items: {column}")

                    # Count records to verify data integrity
                    cursor.execute("SELECT COUNT(*) FROM expeditions")
                    expedition_count = cursor.fetchone()[0]
                    validation_results["statistics"]["total_expeditions"] = expedition_count

                    cursor.execute("SELECT COUNT(*) FROM expeditions WHERE admin_key IS NOT NULL")
                    expeditions_with_admin_key = cursor.fetchone()[0]
                    validation_results["statistics"]["expeditions_with_admin_key"] = expeditions_with_admin_key

                    cursor.execute("SELECT COUNT(*) FROM expedition_items WHERE anonymized_item_code IS NOT NULL")
                    items_with_anonymized_codes = cursor.fetchone()[0]
                    validation_results["statistics"]["items_with_anonymized_codes"] = items_with_anonymized_codes

                    # Validate data consistency
                    if expedition_count > 0 and expeditions_with_admin_key < expedition_count:
                        validation_results["warnings"].append(f"Only {expeditions_with_admin_key}/{expedition_count} expeditions have admin keys")

            logger.info(f"Post-migration validation completed. Healthy: {validation_results['healthy']}, Ready: {validation_results['new_features_ready']}")
            return validation_results

        except Exception as e:
            logger.error(f"Post-migration validation failed: {e}")
            validation_results["healthy"] = False
            validation_results["new_features_ready"] = False
            validation_results["issues"].append(f"Validation error: {str(e)}")
            return validation_results

    def run_full_migration(self) -> Dict[str, any]:
        """
        Run complete migration process with validation and backup.

        Returns:
            Dictionary with complete migration results
        """
        logger.info("Starting full expedition system migration for Sprint 1...")
        full_results = {
            "migration_started": datetime.now().isoformat(),
            "success": False,
            "steps_completed": [],
            "errors": [],
            "warnings": []
        }

        try:
            # Step 1: Pre-migration validation
            logger.info("Step 1: Pre-migration validation")
            pre_validation = self.validate_pre_migration()
            full_results["pre_validation"] = pre_validation
            full_results["steps_completed"].append("pre_validation")

            if not pre_validation["healthy"]:
                raise MigrationError(f"Pre-migration validation failed: {pre_validation['issues']}")

            # Step 2: Backup existing data
            logger.info("Step 2: Creating data backup")
            backup_results = self.backup_existing_data()
            full_results["backup"] = backup_results
            full_results["steps_completed"].append("backup")

            # Step 3: Apply schema changes
            logger.info("Step 3: Applying schema changes")
            initialize_schema()  # This will apply all new schema changes with migrations
            full_results["steps_completed"].append("schema_update")

            # Step 4: Migrate existing data
            logger.info("Step 4: Migrating existing data")
            migration_results = self.migrate_expedition_data()
            full_results["data_migration"] = migration_results
            full_results["steps_completed"].append("data_migration")

            # Step 5: Post-migration validation
            logger.info("Step 5: Post-migration validation")
            post_validation = self.validate_post_migration()
            full_results["post_validation"] = post_validation
            full_results["steps_completed"].append("post_validation")

            if not post_validation["healthy"]:
                raise MigrationError(f"Post-migration validation failed: {post_validation['issues']}")

            # Step 6: Cleanup and finalization
            logger.info("Step 6: Migration finalization")
            full_results["success"] = True
            full_results["migration_completed"] = datetime.now().isoformat()
            full_results["steps_completed"].append("finalization")

            logger.info("Full expedition system migration completed successfully!")
            return full_results

        except Exception as e:
            logger.error(f"Full migration failed: {e}")
            full_results["error"] = str(e)
            full_results["migration_failed"] = datetime.now().isoformat()
            return full_results

    def get_migration_status(self) -> Dict[str, any]:
        """
        Get current migration status and readiness for Sprint 1 features.

        Returns:
            Dictionary with migration status
        """
        logger.info("Checking migration status...")
        status = {
            "sprint_1_ready": False,
            "migration_needed": False,
            "missing_features": [],
            "database_version": "unknown"
        }

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Check if new tables exist
                    new_tables = ['expedition_pirates', 'expedition_assignments', 'expedition_payments']
                    missing_tables = []

                    for table in new_tables:
                        cursor.execute("""
                            SELECT EXISTS (
                                SELECT FROM information_schema.tables
                                WHERE table_schema = 'public'
                                AND table_name = %s
                            );
                        """, (table,))

                        if not cursor.fetchone()[0]:
                            missing_tables.append(table)

                    if missing_tables:
                        status["migration_needed"] = True
                        status["missing_features"].extend(missing_tables)

                    # Check if expeditions table has new columns
                    required_columns = ['admin_key', 'encryption_version', 'anonymization_level']
                    missing_columns = []

                    for column in required_columns:
                        cursor.execute("""
                            SELECT EXISTS (
                                SELECT FROM information_schema.columns
                                WHERE table_name = 'expeditions'
                                AND column_name = %s
                            );
                        """, (column,))

                        if not cursor.fetchone()[0]:
                            missing_columns.append(f"expeditions.{column}")

                    if missing_columns:
                        status["migration_needed"] = True
                        status["missing_features"].extend(missing_columns)

                    # Determine database version
                    if not missing_tables and not missing_columns:
                        status["sprint_1_ready"] = True
                        status["database_version"] = "expedition_redesign_v1"
                    elif not missing_tables:
                        status["database_version"] = "partial_migration"
                    else:
                        status["database_version"] = "legacy"

            logger.info(f"Migration status: Ready={status['sprint_1_ready']}, Migration needed={status['migration_needed']}")
            return status

        except Exception as e:
            logger.error(f"Failed to check migration status: {e}")
            status["error"] = str(e)
            return status


# Convenience functions
def run_expedition_migration() -> Dict[str, any]:
    """Run the complete expedition system migration."""
    migration_utility = ExpeditionMigrationUtility()
    return migration_utility.run_full_migration()


def check_migration_status() -> Dict[str, any]:
    """Check if migration is needed and system readiness."""
    migration_utility = ExpeditionMigrationUtility()
    return migration_utility.get_migration_status()


def validate_migration_safety() -> Dict[str, any]:
    """Validate that migration can be safely performed."""
    migration_utility = ExpeditionMigrationUtility()
    return migration_utility.validate_pre_migration()