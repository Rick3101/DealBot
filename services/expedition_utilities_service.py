"""
Expedition Utilities Service - Unified naming and anonymization system.
Handles both buyer anonymization (pirate names) and product alias management.
Consolidates BramblerService and ItemNamingService for better maintainability.
"""

import logging
import hashlib
import json
import secrets
import random
from typing import List, Optional, Dict
from datetime import datetime
import base64

from services.base_service import BaseService, ServiceError, ValidationError, NotFoundError
from core.interfaces import IBramblerService
from models.expedition import PirateName
from utils.encryption import get_encryption_service, generate_owner_key
from cryptography.fernet import Fernet


class ExpeditionUtilitiesService(BaseService, IBramblerService):
    """
    Service for pirate name anonymization and encryption.
    Handles generation, storage, and encryption of pirate names for expeditions.
    """

    # Pirate name components for generation
    PIRATE_ADJECTIVES = [
        "Fearsome", "Mighty", "Cunning", "Bold", "Brave", "Swift", "Dark", "Golden",
        "Iron", "Silver", "Crimson", "Black", "Wild", "Mad", "Clever", "Silent",
        "Thunder", "Storm", "Fire", "Ice", "Shadow", "Blood", "Steel", "Bronze",
        "Savage", "Ruthless", "Daring", "Fierce", "Grim", "Haunted", "Cursed",
        "Lucky", "Scarred", "One-Eyed", "Hook", "Peg-Leg", "Bearded", "Tattooed"
    ]

    PIRATE_NAMES = [
        "Blackbeard", "Redbeard", "Ironhook", "Silverblade", "Goldfang", "Stormeye",
        "Thunderbolt", "Firestorm", "Iceheart", "Bloodaxe", "Steelclaw", "Bonecrusher",
        "Seahawk", "Kraken", "Leviathan", "Tempest", "Maelstrom", "Whirlpool",
        "Cutlass", "Scimitar", "Rapier", "Dagger", "Saber", "Harpoon", "Anchor",
        "Compass", "Treasure", "Doubloon", "Skull", "Crossbones", "Parrot", "Monkey",
        "Shark", "Octopus", "Eel", "Barracuda", "Manta", "Stingray", "Coral", "Pearl"
    ]

    PIRATE_TITLES = [
        "the Terrible", "the Fearless", "the Bold", "the Swift", "the Dark",
        "the Golden", "the Iron", "the Silver", "the Crimson", "the Black",
        "the Mad", "the Clever", "the Silent", "the Loud", "the Quick",
        "the Slow", "the Tall", "the Short", "the Wide", "the Thin",
        "Blackheart", "Redheart", "Ironheart", "Silverheart", "Goldheart",
        "Stormheart", "Fireheart", "Iceheart", "Shadowheart", "Bloodheart",
        "of the Seven Seas", "of the Caribbean", "of the Pacific", "of the Atlantic",
        "the Destroyer", "the Conqueror", "the Hunter", "the Seeker", "the Finder",
        "the Lost", "the Found", "the Wanderer", "the Explorer", "the Navigator"
    ]

    def __init__(self):
        super().__init__()

    def generate_pirate_names(self, expedition_id: int, original_names: List[str]) -> List[PirateName]:
        """Generate and store pirate names for expedition anonymization."""
        if not original_names:
            return []

        self._log_operation("GeneratePirateNames", expedition_id=expedition_id, count=len(original_names))

        # Check if expedition exists
        expedition_query = "SELECT id FROM expeditions WHERE id = %s"
        expedition_result = self._execute_query(expedition_query, (expedition_id,), fetch_one=True)
        if not expedition_result:
            raise NotFoundError(f"Expedition {expedition_id} not found")

        # Generate unique pirate names
        used_pirate_names = self._get_used_pirate_names(expedition_id)
        generated_names = []

        for original_name in original_names:
            original_name = original_name.strip()
            if not original_name:
                continue

            # Check if name already exists for this expedition
            existing_query = """
                SELECT pirate_name FROM pirate_names
                WHERE expedition_id = %s AND original_name = %s
            """
            existing_result = self._execute_query(
                existing_query,
                (expedition_id, original_name),
                fetch_one=True
            )

            if existing_result:
                # Name already exists, skip
                continue

            # Generate unique pirate name
            pirate_name = self._generate_unique_pirate_name_for_expedition(
                expedition_id, used_pirate_names
            )
            used_pirate_names.add(pirate_name)

            # Create encryption key for this mapping
            owner_key = self._generate_owner_key()
            encrypted_mapping = self._create_encrypted_mapping(
                original_name, pirate_name, owner_key
            )

            # Insert into database
            insert_query = """
                INSERT INTO pirate_names (expedition_id, original_name, pirate_name, encrypted_mapping, created_at)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, expedition_id, original_name, pirate_name, encrypted_mapping, created_at
            """

            result = self._execute_query(
                insert_query,
                (expedition_id, original_name, pirate_name, encrypted_mapping, datetime.now()),
                fetch_one=True
            )

            if result:
                generated_names.append(PirateName.from_db_row(result))

        self.logger.info(f"Generated {len(generated_names)} pirate names for expedition {expedition_id}")
        return generated_names

    def get_pirate_name(self, expedition_id: int, original_name: str) -> Optional[str]:
        """Get pirate name for an original name in an expedition."""
        query = """
            SELECT pirate_name FROM pirate_names
            WHERE expedition_id = %s AND original_name = %s
        """

        result = self._execute_query(query, (expedition_id, original_name.strip()), fetch_one=True)
        return result[0] if result else None

    def get_original_name(self, expedition_id: int, pirate_name: str) -> Optional[str]:
        """Get original name from pirate name (owner access only)."""
        query = """
            SELECT original_name FROM pirate_names
            WHERE expedition_id = %s AND pirate_name = %s
        """

        result = self._execute_query(query, (expedition_id, pirate_name.strip()), fetch_one=True)
        return result[0] if result else None

    def encrypt_name_mapping(self, expedition_id: int, original_name: str, pirate_name: str, owner_key: str) -> str:
        """Create encrypted mapping between original and pirate names using secure AES-GCM encryption."""
        try:
            # Create name mapping dictionary
            name_mapping = {original_name: pirate_name}

            # Use secure encryption service
            encryption_service = get_encryption_service()
            encrypted_mapping = encryption_service.encrypt_name_mapping(expedition_id, name_mapping, owner_key)

            self._log_operation("EncryptNameMapping",
                              expedition_id=expedition_id,
                              original_name=original_name[:10] + "...",  # Log partial for privacy
                              pirate_name=pirate_name)

            return encrypted_mapping

        except Exception as e:
            self.logger.error(f"Failed to encrypt name mapping: {e}", exc_info=True)
            raise ServiceError(f"Encryption failed: {str(e)}")

    def decrypt_name_mapping(self, expedition_id: int, encrypted_mapping: str, owner_key: str) -> Optional[Dict[str, str]]:
        """Decrypt name mapping for owner access using secure AES-GCM decryption."""
        try:
            # Use secure encryption service
            encryption_service = get_encryption_service()
            decrypted_mapping = encryption_service.decrypt_name_mapping(encrypted_mapping, owner_key)

            if decrypted_mapping:
                self._log_operation("DecryptNameMapping",
                                  expedition_id=expedition_id,
                                  mappings_count=len(decrypted_mapping))

            return decrypted_mapping

        except Exception as e:
            self.logger.error(f"Failed to decrypt name mapping: {e}", exc_info=True)
            return None

    def get_expedition_pirate_names(self, expedition_id: int) -> List[PirateName]:
        """Get all pirate names for an expedition."""
        query = """
            SELECT id, expedition_id, original_name, pirate_name, encrypted_mapping, created_at
            FROM pirate_names
            WHERE expedition_id = %s
            ORDER BY created_at ASC
        """

        results = self._execute_query(query, (expedition_id,), fetch_all=True)
        return [PirateName.from_db_row(row) for row in results or []]

    def delete_expedition_names(self, expedition_id: int) -> bool:
        """Delete all pirate names for an expedition."""
        query = "DELETE FROM pirate_names WHERE expedition_id = %s"
        rows_affected = self._execute_query(query, (expedition_id,))

        self._log_operation("DeleteExpeditionNames", expedition_id=expedition_id, deleted=rows_affected)
        return rows_affected > 0

    def generate_unique_pirate_name(self) -> str:
        """Generate a unique pirate name."""
        return self._generate_unique_pirate_name_for_expedition(None, set())

    def _get_used_pirate_names(self, expedition_id: int) -> set:
        """Get all pirate names already used in an expedition."""
        query = "SELECT pirate_name FROM pirate_names WHERE expedition_id = %s"
        results = self._execute_query(query, (expedition_id,), fetch_all=True)
        return {row[0] for row in results or []}

    def _generate_unique_pirate_name_for_expedition(self, expedition_id: Optional[int], used_names: set) -> str:
        """Generate a unique pirate name for an expedition."""
        max_attempts = 100

        for attempt in range(max_attempts):
            # Generate random pirate name
            adjective = random.choice(self.PIRATE_ADJECTIVES)
            name = random.choice(self.PIRATE_NAMES)
            title = random.choice(self.PIRATE_TITLES)

            # Create different name patterns
            patterns = [
                f"{adjective} {name}",
                f"{name} {title}",
                f"{adjective} {name} {title}",
                f"Captain {name}",
                f"Admiral {adjective}",
                f"{name} the {adjective}",
                f"{adjective} Captain {name}"
            ]

            pirate_name = random.choice(patterns)

            # Check if name is unique
            if pirate_name not in used_names:
                # Also check global uniqueness if expedition_id provided
                if expedition_id is not None:
                    global_query = "SELECT 1 FROM pirate_names WHERE pirate_name = %s LIMIT 1"
                    existing = self._execute_query(global_query, (pirate_name,), fetch_one=True)
                    if not existing:
                        return pirate_name
                else:
                    return pirate_name

        # Fallback: add random number to ensure uniqueness
        base_name = f"{random.choice(self.PIRATE_ADJECTIVES)} {random.choice(self.PIRATE_NAMES)}"
        random_suffix = secrets.randbelow(10000)
        return f"{base_name} #{random_suffix}"

    def _get_consistent_pirate_name_for_buyer(self, buyer_name: str) -> str:
        """Get or create a consistent pirate name for a buyer across all expeditions."""
        # Check if buyer already has a consistent pirate name
        existing_query = """
            SELECT pirate_name FROM pirate_names
            WHERE original_name = %s
            LIMIT 1
        """
        existing_result = self._execute_query(existing_query, (buyer_name,), fetch_one=True)

        if existing_result:
            # Return existing consistent name
            return existing_result[0]

        # Generate new consistent name using hash-based deterministic approach
        return self._generate_deterministic_pirate_name(buyer_name)

    def _generate_deterministic_pirate_name(self, buyer_name: str) -> str:
        """Generate a deterministic pirate name based on buyer name hash."""
        import hashlib

        # Create a consistent hash from the buyer name
        hash_object = hashlib.md5(buyer_name.lower().encode())
        hash_hex = hash_object.hexdigest()

        # Use hash to select from lists deterministically
        adj_index = int(hash_hex[:2], 16) % len(self.PIRATE_ADJECTIVES)
        name_index = int(hash_hex[2:4], 16) % len(self.PIRATE_NAMES)
        title_index = int(hash_hex[4:6], 16) % len(self.PIRATE_TITLES)
        pattern_index = int(hash_hex[6:8], 16) % 5

        adjective = self.PIRATE_ADJECTIVES[adj_index]
        name = self.PIRATE_NAMES[name_index]
        title = self.PIRATE_TITLES[title_index]

        # Select pattern based on hash
        patterns = [
            f"{adjective} {name}",
            f"{name} {title}",
            f"{adjective} {name} {title}",
            f"Captain {name}",
            f"{adjective} {title}"
        ]

        pirate_name = patterns[pattern_index]

        # Check if name already exists globally
        global_query = "SELECT 1 FROM pirate_names WHERE pirate_name = %s LIMIT 1"
        existing = self._execute_query(global_query, (pirate_name,), fetch_one=True)

        if existing:
            # If collision, add buyer name suffix to make unique
            pirate_name = f"{pirate_name} ({buyer_name[:3].upper()})"

        return pirate_name

    def get_pirate_name_for_buyer(self, buyer_name: str) -> Optional[str]:
        """Get existing global pirate name for a buyer (expedition_id IS NULL)."""
        query = """
            SELECT pirate_name FROM pirate_names
            WHERE original_name = %s AND expedition_id IS NULL
            LIMIT 1
        """
        result = self._execute_query(query, (buyer_name,), fetch_one=True)
        return result[0] if result else None

    def get_buyer_for_pirate_name(self, pirate_name: str) -> Optional[str]:
        """Get buyer name for a global pirate name (expedition_id IS NULL)."""
        query = """
            SELECT original_name FROM pirate_names
            WHERE pirate_name = %s AND expedition_id IS NULL
            LIMIT 1
        """
        result = self._execute_query(query, (pirate_name,), fetch_one=True)
        return result[0] if result else None

    def get_all_pirate_mappings(self) -> dict:
        """Get all global buyer -> pirate name mappings (expedition_id IS NULL)."""
        query = """
            SELECT DISTINCT original_name, pirate_name
            FROM pirate_names
            WHERE expedition_id IS NULL
            ORDER BY original_name
        """
        results = self._execute_query(query, fetch_all=True)
        return {row[0]: row[1] for row in results or []}

    def get_all_unique_pirate_names(self) -> list:
        """Get all unique global pirate names from the system (expedition_id IS NULL)."""
        query = """
            SELECT DISTINCT pirate_name
            FROM pirate_names
            WHERE expedition_id IS NULL
            ORDER BY pirate_name
        """
        results = self._execute_query(query, fetch_all=True)
        return [row[0] for row in results or []]

    def add_pirate_to_expedition(self, expedition_id: int, buyer_name: str) -> bool:
        """Add a buyer's global pirate name to an expedition."""
        try:
            # Check if buyer has a global pirate name
            global_pirate_name = self.get_pirate_name_for_buyer(buyer_name)
            if not global_pirate_name:
                self.logger.warning(f"No global pirate name found for buyer {buyer_name}")
                return False

            # Check if this buyer is already in this expedition
            existing_pirates = self.get_expedition_pirate_names(expedition_id)
            if any(p.original_name == buyer_name for p in existing_pirates):
                self.logger.info(f"Buyer {buyer_name} already in expedition {expedition_id}")
                return True  # Already added

            # Add the global pirate name to this expedition
            query = """
                INSERT INTO pirate_names (expedition_id, original_name, pirate_name, encrypted_mapping)
                VALUES (%s, %s, %s, %s)
            """

            from utils.encryption import get_encryption_service, generate_owner_key
            encryption_service = get_encryption_service()

            # Create encrypted mapping for expedition reference (copying global mapping)
            mapping = {buyer_name: global_pirate_name}
            owner_key = generate_owner_key(expedition_id, 1)  # Using owner_user_id=1 as default
            encrypted_mapping = encryption_service.encrypt_name_mapping(expedition_id, mapping, owner_key)

            self._execute_query(query, (expedition_id, buyer_name, global_pirate_name, encrypted_mapping))

            self._log_operation("AddPirateToExpedition",
                              expedition_id=expedition_id,
                              buyer_name=buyer_name,
                              pirate_name=global_pirate_name)

            return True

        except Exception as e:
            self.logger.error(f"Failed to add pirate to expedition: {e}", exc_info=True)
            return False

    def create_global_pirate_mapping(self, buyer_name: str, pirate_name: str) -> bool:
        """Create a global pirate mapping (not expedition-specific)."""
        try:
            # Check if mapping already exists
            existing = self.get_pirate_name_for_buyer(buyer_name)
            if existing == pirate_name:
                return True  # Already exists with same name

            if existing:
                # Update existing mapping
                return self.create_or_update_global_pirate_mapping(buyer_name, pirate_name)

            # Create new mapping - use expedition_id = NULL for global mappings
            owner_key = self._generate_owner_key()
            encrypted_mapping = self._create_encrypted_mapping(buyer_name, pirate_name, owner_key)

            insert_query = """
                INSERT INTO pirate_names (expedition_id, original_name, pirate_name, encrypted_mapping, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """
            self._execute_query(
                insert_query,
                (None, buyer_name, pirate_name, encrypted_mapping, __import__('datetime').datetime.now()),
                fetch_one=False
            )

            self.logger.info(f"Created global pirate mapping: {buyer_name} -> {pirate_name}")
            return True

        except Exception as e:
            self.logger.error(f"Error creating global pirate mapping: {e}", exc_info=True)
            return False

    def create_or_update_global_pirate_mapping(self, buyer_name: str, pirate_name: str) -> bool:
        """Create or update a global pirate mapping."""
        try:
            # Check if buyer already has a mapping
            existing = self.get_pirate_name_for_buyer(buyer_name)

            if existing:
                # Update all existing mappings for this buyer
                owner_key = self._generate_owner_key()
                encrypted_mapping = self._create_encrypted_mapping(buyer_name, pirate_name, owner_key)

                update_query = """
                    UPDATE pirate_names
                    SET pirate_name = %s, encrypted_mapping = %s, created_at = %s
                    WHERE original_name = %s
                """
                self._execute_query(
                    update_query,
                    (pirate_name, encrypted_mapping, __import__('datetime').datetime.now(), buyer_name),
                    fetch_one=False
                )
                self.logger.info(f"Updated pirate mapping: {buyer_name} -> {pirate_name}")
            else:
                # Create new mapping
                return self.create_global_pirate_mapping(buyer_name, pirate_name)

            return True

        except Exception as e:
            self.logger.error(f"Error creating/updating global pirate mapping: {e}", exc_info=True)
            return False

    def _generate_owner_key(self) -> str:
        """Generate a secure key for owner access."""
        # Generate 32 bytes of random data for Fernet key
        key_bytes = secrets.token_bytes(32)
        return base64.urlsafe_b64encode(key_bytes).decode()

    def _create_encrypted_mapping(self, original_name: str, pirate_name: str, owner_key: str) -> str:
        """Create encrypted mapping using the owner key."""
        try:
            mapping_data = {
                'original': original_name,
                'pirate': pirate_name,
                'created': datetime.now().isoformat()
            }

            json_data = json.dumps(mapping_data)

            # Create Fernet cipher from owner key
            fernet = Fernet(owner_key.encode())
            encrypted_data = fernet.encrypt(json_data.encode())

            return base64.urlsafe_b64encode(encrypted_data).decode()

        except Exception as e:
            self.logger.error(f"Failed to create encrypted mapping: {e}")
            # Return a hash-based fallback
            combined = f"{original_name}:{pirate_name}:{datetime.now().isoformat()}"
            return hashlib.sha256(combined.encode()).hexdigest()

    # Product Anonymization Methods
    def encrypt_product_name(self, product_name: str, expedition_id: int, owner_key: str) -> str:
        """
        Encrypt product name for expedition item anonymization.

        Args:
            product_name: Original product name
            expedition_id: Expedition identifier
            owner_key: Owner's encryption key

        Returns:
            Encrypted product name
        """
        try:
            # Use encryption service for product names
            encryption_service = get_encryption_service()
            product_mapping = {product_name: f"encrypted_product_{expedition_id}"}
            encrypted_mapping = encryption_service.encrypt_name_mapping(expedition_id, product_mapping, owner_key)

            self._log_operation("EncryptProductName",
                              expedition_id=expedition_id,
                              product_name=product_name[:20] + "..." if len(product_name) > 20 else product_name)

            return encrypted_mapping

        except Exception as e:
            self.logger.error(f"Failed to encrypt product name: {e}", exc_info=True)
            raise ServiceError(f"Product encryption failed: {str(e)}")

    def decrypt_product_name(self, encrypted_product: str, owner_key: str) -> Optional[str]:
        """
        Decrypt product name for owner access.

        Args:
            encrypted_product: Encrypted product data
            owner_key: Owner's encryption key

        Returns:
            Decrypted product name or None if decryption fails
        """
        try:
            encryption_service = get_encryption_service()
            decrypted_mapping = encryption_service.decrypt_name_mapping(encrypted_product, owner_key)

            if decrypted_mapping:
                # Find the original product name in the mapping
                for original_name, encrypted_name in decrypted_mapping.items():
                    if encrypted_name.startswith("encrypted_product_"):
                        self._log_operation("DecryptProductName",
                                          product_name=original_name[:20] + "..." if len(original_name) > 20 else original_name)
                        return original_name

            return None

        except Exception as e:
            self.logger.error(f"Failed to decrypt product name: {e}", exc_info=True)
            return None

    def generate_anonymized_item_code(self, product_name: str, expedition_id: int) -> str:
        """
        Generate anonymized item code for product tracking.

        Args:
            product_name: Original product name
            expedition_id: Expedition identifier

        Returns:
            Anonymized item code
        """
        try:
            # Create a deterministic but anonymized code
            combined_data = f"{product_name.lower().strip()}_{expedition_id}"
            hash_digest = hashlib.sha256(combined_data.encode()).hexdigest()

            # Create a readable anonymized code
            code_prefix = "ITEM"
            code_suffix = hash_digest[:8].upper()
            anonymized_code = f"{code_prefix}_{expedition_id}_{code_suffix}"

            self._log_operation("GenerateAnonymizedCode",
                              expedition_id=expedition_id,
                              anonymized_code=anonymized_code)

            return anonymized_code

        except Exception as e:
            self.logger.error(f"Failed to generate anonymized item code: {e}", exc_info=True)
            # Fallback to simple format
            return f"ITEM_{expedition_id}_{secrets.randbelow(100000):05d}"

    def encrypt_item_notes(self, notes: str, expedition_id: int, owner_key: str) -> str:
        """
        Encrypt item notes for expedition privacy.

        Args:
            notes: Original notes text
            expedition_id: Expedition identifier
            owner_key: Owner's encryption key

        Returns:
            Encrypted notes
        """
        try:
            encryption_service = get_encryption_service()
            notes_mapping = {f"notes_{expedition_id}": notes}
            encrypted_mapping = encryption_service.encrypt_name_mapping(expedition_id, notes_mapping, owner_key)

            self._log_operation("EncryptItemNotes",
                              expedition_id=expedition_id,
                              notes_length=len(notes))

            return encrypted_mapping

        except Exception as e:
            self.logger.error(f"Failed to encrypt item notes: {e}", exc_info=True)
            raise ServiceError(f"Notes encryption failed: {str(e)}")

    def decrypt_item_notes(self, encrypted_notes: str, owner_key: str) -> Optional[str]:
        """
        Decrypt item notes for owner access.

        Args:
            encrypted_notes: Encrypted notes data
            owner_key: Owner's encryption key

        Returns:
            Decrypted notes or None if decryption fails
        """
        try:
            encryption_service = get_encryption_service()
            decrypted_mapping = encryption_service.decrypt_name_mapping(encrypted_notes, owner_key)

            if decrypted_mapping:
                # Find the notes in the mapping
                for key, notes in decrypted_mapping.items():
                    if key.startswith("notes_"):
                        self._log_operation("DecryptItemNotes",
                                          notes_length=len(notes))
                        return notes

            return None

        except Exception as e:
            self.logger.error(f"Failed to decrypt item notes: {e}", exc_info=True)
            return None

    def validate_encryption_key(self, owner_key: str, expedition_id: int) -> bool:
        """
        Validate that an owner key is valid for encryption operations.

        Args:
            owner_key: Owner's encryption key
            expedition_id: Expedition identifier

        Returns:
            True if key is valid, False otherwise
        """
        try:
            # Test encryption with a known test mapping
            test_mapping = {"test_name": "test_pirate"}
            encryption_service = get_encryption_service()

            return encryption_service.verify_owner_key(expedition_id, owner_key, test_mapping)

        except Exception as e:
            self.logger.error(f"Key validation failed: {e}", exc_info=True)
            return False

    def get_available_buyers(self) -> List[str]:
        """Get list of unique buyers from sales table for pirate generation."""
        query = """
            SELECT DISTINCT comprador
            FROM vendas
            WHERE comprador IS NOT NULL AND comprador != ''
            ORDER BY comprador
        """

        results = self._execute_query(query, fetch_all=True)
        return [row[0] for row in results or []]

    def generate_random_pirate_names_for_buyers(self, expedition_id: int, buyer_names: List[str]) -> List[PirateName]:
        """Generate consistent pirate names for a list of buyers."""
        if not buyer_names:
            return []

        self._log_operation("GenerateRandomPirateNames", expedition_id=expedition_id, count=len(buyer_names))

        # Check if expedition exists
        expedition_query = "SELECT id FROM expeditions WHERE id = %s"
        expedition_result = self._execute_query(expedition_query, (expedition_id,), fetch_one=True)
        if not expedition_result:
            raise NotFoundError(f"Expedition {expedition_id} not found")

        generated_names = []

        for buyer_name in buyer_names:
            buyer_name = buyer_name.strip()
            if not buyer_name:
                continue

            # Check if name already exists for this expedition
            existing_query = """
                SELECT pirate_name FROM pirate_names
                WHERE expedition_id = %s AND original_name = %s
            """
            existing_result = self._execute_query(
                existing_query,
                (expedition_id, buyer_name),
                fetch_one=True
            )

            if existing_result:
                # Name already exists, skip
                continue

            # Get consistent pirate name for this buyer (same across all expeditions)
            pirate_name = self._get_consistent_pirate_name_for_buyer(buyer_name)

            # Create encryption key for this mapping
            owner_key = self._generate_owner_key()
            encrypted_mapping = self._create_encrypted_mapping(
                buyer_name, pirate_name, owner_key
            )

            # Insert into database
            insert_query = """
                INSERT INTO pirate_names (expedition_id, original_name, pirate_name, encrypted_mapping, created_at)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, expedition_id, original_name, pirate_name, encrypted_mapping, created_at
            """

            result = self._execute_query(
                insert_query,
                (expedition_id, buyer_name, pirate_name, encrypted_mapping, datetime.now()),
                fetch_one=True
            )

            if result:
                generated_names.append(PirateName.from_db_row(result))

        self.logger.info(f"Generated {len(generated_names)} random pirate names for expedition {expedition_id}")
        return generated_names

    def assign_custom_pirate_name(self, expedition_id: int, buyer_name: str, custom_pirate_name: str) -> Optional[PirateName]:
        """Assign a custom pirate name to a buyer."""
        buyer_name = buyer_name.strip()
        custom_pirate_name = custom_pirate_name.strip()

        if not buyer_name or not custom_pirate_name:
            raise ValidationError("Both buyer name and pirate name are required")

        self._log_operation("AssignCustomPirateName",
                          expedition_id=expedition_id,
                          buyer_name=buyer_name[:10] + "...",
                          pirate_name=custom_pirate_name)

        # Check if expedition exists
        expedition_query = "SELECT id FROM expeditions WHERE id = %s"
        expedition_result = self._execute_query(expedition_query, (expedition_id,), fetch_one=True)
        if not expedition_result:
            raise NotFoundError(f"Expedition {expedition_id} not found")

        # Check if buyer already has a pirate name
        existing_query = """
            SELECT id FROM pirate_names
            WHERE expedition_id = %s AND original_name = %s
        """
        existing_result = self._execute_query(
            existing_query,
            (expedition_id, buyer_name),
            fetch_one=True
        )

        if existing_result:
            raise ValidationError(f"Buyer {buyer_name} already has a pirate name in this expedition")

        # Check if pirate name is already used
        name_check_query = """
            SELECT id FROM pirate_names
            WHERE expedition_id = %s AND pirate_name = %s
        """
        name_check_result = self._execute_query(
            name_check_query,
            (expedition_id, custom_pirate_name),
            fetch_one=True
        )

        if name_check_result:
            raise ValidationError(f"Pirate name '{custom_pirate_name}' is already used in this expedition")

        # Create encryption key for this mapping
        owner_key = self._generate_owner_key()
        encrypted_mapping = self._create_encrypted_mapping(
            buyer_name, custom_pirate_name, owner_key
        )

        # Insert into database
        insert_query = """
            INSERT INTO pirate_names (expedition_id, original_name, pirate_name, encrypted_mapping, created_at)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, expedition_id, original_name, pirate_name, encrypted_mapping, created_at
        """

        result = self._execute_query(
            insert_query,
            (expedition_id, buyer_name, custom_pirate_name, encrypted_mapping, datetime.now()),
            fetch_one=True
        )

        if result:
            self.logger.info(f"Assigned custom pirate name '{custom_pirate_name}' to buyer '{buyer_name}' in expedition {expedition_id}")
            return PirateName.from_db_row(result)

        return None

    def remove_pirate_name(self, expedition_id: int, original_name: str) -> bool:
        """Remove a pirate name mapping from an expedition."""
        query = """
            DELETE FROM pirate_names
            WHERE expedition_id = %s AND original_name = %s
        """

        rows_affected = self._execute_query(query, (expedition_id, original_name.strip()))

        self._log_operation("RemovePirateName",
                          expedition_id=expedition_id,
                          original_name=original_name[:10] + "...",
                          removed=rows_affected > 0)

        return rows_affected > 0

    # === ITEM NAMING AND PRODUCT ALIAS FUNCTIONALITY ===
    # Consolidated from ItemNamingService for unified naming utilities

    # Fantasy name components for product aliases
    FANTASY_PREFIXES = [
        "Mystical", "Ancient", "Legendary", "Sacred", "Enchanted", "Divine", "Celestial",
        "Ethereal", "Phantom", "Shadow", "Crystal", "Golden", "Silver", "Emerald",
        "Ruby", "Sapphire", "Diamond", "Blazing", "Frozen", "Thunder", "Storm",
        "Arcane", "Mystic", "Blessed", "Cursed", "Radiant", "Glowing", "Shimmering"
    ]

    FANTASY_SUFFIXES = [
        "of Power", "of Wisdom", "of Strength", "of Agility", "of Magic", "of Light",
        "of Darkness", "of Fire", "of Ice", "of Lightning", "of Earth", "of Wind",
        "of the Ancients", "of the Gods", "of Eternity", "of the Void", "of Dreams",
        "of Nightmares", "of Glory", "of Honor", "of Victory", "of Fortune",
        "of the Phoenix", "of the Dragon", "of the Stars", "of the Moon", "of the Sun"
    ]

    def get_available_products(self) -> List[str]:
        """Get all available product names from the database."""
        try:
            query = "SELECT nome FROM Produtos ORDER BY nome"
            rows = self._execute_query(query, fetch_all=True)
            return [row[0] for row in rows] if rows else []
        except Exception as e:
            self.logger.error(f"Error getting available products: {e}")
            return []

    def get_custom_name_for_product(self, product_name: str) -> Optional[str]:
        """Get the custom name for a product."""
        try:
            query = """
                SELECT custom_name FROM item_mappings
                WHERE product_name = %s
            """
            row = self._execute_query(query, (product_name,), fetch_one=True)
            return row[0] if row else None
        except Exception as e:
            self.logger.error(f"Error getting custom name for product {product_name}: {e}")
            return None

    def get_product_for_custom_name(self, custom_name: str) -> Optional[str]:
        """Get the original product name for a custom name."""
        try:
            query = """
                SELECT product_name FROM item_mappings
                WHERE custom_name = %s
            """
            row = self._execute_query(query, (custom_name,), fetch_one=True)
            return row[0] if row else None
        except Exception as e:
            self.logger.error(f"Error getting product for custom name {custom_name}: {e}")
            return None

    def create_global_item_mapping(self, product_name: str, custom_name: str) -> bool:
        """Create a global item name mapping."""
        try:
            # Check if custom name already exists for another product
            existing_product = self.get_product_for_custom_name(custom_name)
            if existing_product and existing_product != product_name:
                self.logger.warning(f"Custom name {custom_name} already exists for {existing_product}")
                return False

            # Use UPSERT to create or update mapping
            query = """
                INSERT INTO item_mappings (product_name, custom_name, is_fantasy_generated, created_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (product_name)
                DO UPDATE SET custom_name = EXCLUDED.custom_name,
                             updated_at = CURRENT_TIMESTAMP,
                             is_fantasy_generated = EXCLUDED.is_fantasy_generated
            """

            self._execute_query(query, (product_name, custom_name, True))

            self._log_operation("CreateItemMapping", product_name=product_name, custom_name=custom_name)
            return True

        except Exception as e:
            self.logger.error(f"Failed to create item mapping: {e}")
            return False

    def create_or_update_global_item_mapping(self, product_name: str, custom_name: str) -> bool:
        """Create or update a global item name mapping."""
        return self.create_global_item_mapping(product_name, custom_name)

    def get_all_item_mappings(self) -> Dict[str, str]:
        """Get all existing item name mappings."""
        try:
            query = """
                SELECT product_name, custom_name FROM item_mappings
                WHERE product_name IN (SELECT nome FROM Produtos)
                ORDER BY product_name
            """
            rows = self._execute_query(query, fetch_all=True)
            return {row[0]: row[1] for row in rows} if rows else {}
        except Exception as e:
            self.logger.error(f"Error getting all item mappings: {e}")
            return {}

    def generate_deterministic_fantasy_name(self, product_name: str) -> str:
        """Generate a deterministic fantasy name based on product name."""
        # Use hash to ensure deterministic generation
        hash_input = f"fantasy_item_{product_name.lower()}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)

        # Use hash to select prefix and suffix
        prefix_idx = hash_value % len(self.FANTASY_PREFIXES)
        suffix_idx = (hash_value // len(self.FANTASY_PREFIXES)) % len(self.FANTASY_SUFFIXES)

        prefix = self.FANTASY_PREFIXES[prefix_idx]
        suffix = self.FANTASY_SUFFIXES[suffix_idx]

        # Extract first word of product name for base
        base_name = product_name.split()[0] if product_name else "Item"

        return f"{prefix} {base_name} {suffix}"

    def delete_item_mapping(self, product_name: str) -> bool:
        """Delete an item name mapping."""
        try:
            query = """
                DELETE FROM item_mappings
                WHERE product_name = %s
            """
            rows_affected = self._execute_query(query, (product_name,), return_affected=True)

            if rows_affected > 0:
                self._log_operation("DeleteItemMapping", product_name=product_name)
                return True
            return False

        except Exception as e:
            self.logger.error(f"Error deleting item mapping for {product_name}: {e}")
            return False