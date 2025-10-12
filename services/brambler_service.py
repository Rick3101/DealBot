"""
Brambler Service - Pirate Name Management for Buyers
Handles pirate name generation and mapping for buyer anonymization.
"""

import hashlib
import logging
from typing import Dict, List, Optional

from services.base_service import BaseService, ServiceError, ValidationError, NotFoundError
from core.interfaces import IBramblerService
from models.expedition import PirateName
from utils.input_sanitizer import InputSanitizer


class BramblerService(BaseService, IBramblerService):
    """
    Service for managing pirate names for buyer anonymization.
    Implements both the interface requirements and handler requirements.
    """

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

    def get_available_buyers(self) -> List[str]:
        """
        Get all available buyer names from the sales table.

        Returns:
            List of unique buyer names
        """
        try:
            query = "SELECT DISTINCT comprador FROM Vendas ORDER BY comprador"
            rows = self._execute_query(query, fetch_all=True)

            if not rows:
                return []

            buyer_names = [row[0] for row in rows if row[0]]
            self._log_operation("available_buyers_retrieved", count=len(buyer_names))
            return buyer_names

        except Exception as e:
            self.logger.error(f"Error getting available buyers: {e}", exc_info=True)
            return []

    def get_pirate_name_for_buyer(self, buyer_name: str) -> Optional[str]:
        """
        Get the pirate name for a buyer if it exists.

        Args:
            buyer_name: Original buyer name

        Returns:
            Pirate name if exists, None otherwise
        """
        try:
            buyer_name = InputSanitizer.sanitize_text(buyer_name)
            query = """
                SELECT pirate_name FROM pirate_names
                WHERE original_name = %s AND expedition_id IS NULL
            """
            row = self._execute_query(query, (buyer_name,), fetch_one=True)

            return row[0] if row else None

        except Exception as e:
            self.logger.error(f"Error getting pirate name for buyer {buyer_name}: {e}")
            return None

    def get_buyer_for_pirate_name(self, pirate_name: str) -> Optional[str]:
        """
        Get the original buyer name for a pirate name.

        Args:
            pirate_name: Pirate display name

        Returns:
            Original buyer name if exists, None otherwise
        """
        try:
            pirate_name = InputSanitizer.sanitize_text(pirate_name)
            query = """
                SELECT original_name FROM pirate_names
                WHERE pirate_name = %s AND expedition_id IS NULL
            """
            row = self._execute_query(query, (pirate_name,), fetch_one=True)

            return row[0] if row else None

        except Exception as e:
            self.logger.error(f"Error getting buyer for pirate name {pirate_name}: {e}")
            return None

    def create_global_pirate_mapping(self, buyer_name: str, pirate_name: str) -> bool:
        """
        Create a global pirate mapping (expedition_id = NULL).

        Args:
            buyer_name: Original buyer name
            pirate_name: Pirate display name

        Returns:
            True if successful, False otherwise
        """
        try:
            buyer_name = InputSanitizer.sanitize_text(buyer_name)
            pirate_name = InputSanitizer.sanitize_text(pirate_name)

            # Check if mapping already exists
            existing = self.get_pirate_name_for_buyer(buyer_name)
            if existing:
                return True  # Already exists

            query = """
                INSERT INTO pirate_names (original_name, pirate_name, expedition_id, encrypted_mapping)
                VALUES (%s, %s, NULL, '')
            """
            self._execute_query(query, (buyer_name, pirate_name))

            self._log_operation("global_pirate_mapping_created",
                              buyer=buyer_name, pirate_name=pirate_name)
            return True

        except Exception as e:
            self.logger.error(f"Error creating global pirate mapping: {e}")
            return False

    def create_or_update_global_pirate_mapping(self, buyer_name: str, pirate_name: str) -> bool:
        """
        Create or update a global pirate mapping.

        Args:
            buyer_name: Original buyer name
            pirate_name: Pirate display name

        Returns:
            True if successful, False otherwise
        """
        try:
            buyer_name = InputSanitizer.sanitize_text(buyer_name)
            pirate_name = InputSanitizer.sanitize_text(pirate_name)

            # Check if mapping already exists
            existing = self.get_pirate_name_for_buyer(buyer_name)

            if existing:
                # Update existing mapping
                query = """
                    UPDATE pirate_names
                    SET pirate_name = %s
                    WHERE original_name = %s AND expedition_id IS NULL
                """
                self._execute_query(query, (pirate_name, buyer_name))
                self._log_operation("global_pirate_mapping_updated",
                                  buyer=buyer_name, pirate_name=pirate_name)
            else:
                # Create new mapping
                query = """
                    INSERT INTO pirate_names (original_name, pirate_name, expedition_id, encrypted_mapping)
                    VALUES (%s, %s, NULL, '')
                """
                self._execute_query(query, (buyer_name, pirate_name))
                self._log_operation("global_pirate_mapping_created",
                                  buyer=buyer_name, pirate_name=pirate_name)

            return True

        except Exception as e:
            self.logger.error(f"Error creating/updating global pirate mapping: {e}")
            return False

    def get_all_pirate_mappings(self) -> Dict[str, str]:
        """
        Get all global pirate name mappings.

        Returns:
            Dictionary mapping original names to pirate names
        """
        try:
            query = """
                SELECT original_name, pirate_name FROM pirate_names
                WHERE expedition_id IS NULL
                ORDER BY original_name
            """
            rows = self._execute_query(query, fetch_all=True)

            mappings = {}
            if rows:
                for row in rows:
                    mappings[row[0]] = row[1]

            self._log_operation("all_pirate_mappings_retrieved", count=len(mappings))
            return mappings

        except Exception as e:
            self.logger.error(f"Error getting all pirate mappings: {e}")
            return {}

    def _generate_deterministic_pirate_name(self, buyer_name: str) -> str:
        """
        Generate a deterministic pirate name for a buyer.

        Args:
            buyer_name: Original buyer name

        Returns:
            Generated pirate name
        """
        try:
            # Use MD5 hash for deterministic generation
            hash_value = hashlib.md5(buyer_name.encode()).hexdigest()

            # Pirate name components
            prefixes = [
                "Capitão", "Almirante", "Corsário", "Bucaneiro", "Lorde", "Comandante",
                "Mestre", "Barão", "Conde", "Duque", "Sir", "Dom", "General", "Major",
                "Tenente", "Sargento", "Cabo", "Soldado"
            ]

            pirate_names = [
                "Barbas Negras", "Perna de Pau", "Garra de Ferro", "Olho de Águia",
                "Espada Sangrenta", "Barba Ruiva", "Dente de Ouro", "Mão de Ferro",
                "Coração de Pedra", "Alma Perdida", "Vento Negro", "Tempestade",
                "Trovão", "Relâmpago", "Furacão", "Maremoto", "Tsunami", "Terremoto"
            ]

            suffixes = [
                "o Terrível", "o Impiedoso", "o Sanguinário", "o Temido", "o Lendário",
                "o Maldito", "o Cruel", "o Feroz", "o Bravo", "o Valente", "o Audaz",
                "o Destemido", "das Sete Mares", "do Caribe", "do Pacífico", "do Atlântico"
            ]

            # Use hash to select components deterministically
            prefix_idx = int(hash_value[:2], 16) % len(prefixes)
            name_idx = int(hash_value[2:4], 16) % len(pirate_names)
            suffix_idx = int(hash_value[4:6], 16) % len(suffixes)

            # Create pirate name
            pirate_name = f"{prefixes[prefix_idx]} {pirate_names[name_idx]} {suffixes[suffix_idx]}"

            return pirate_name

        except Exception as e:
            self.logger.error(f"Error generating pirate name for {buyer_name}: {e}")
            return f"Capitão {buyer_name} o Misterioso"

    # Interface methods (IBramblerService)
    def generate_pirate_names(self, expedition_id: int, original_names: List[str]) -> List[PirateName]:
        """
        Generate and store pirate names for expedition anonymization.

        Args:
            expedition_id: Expedition ID
            original_names: List of original names to anonymize

        Returns:
            List of PirateName objects
        """
        try:
            pirate_names = []

            for original_name in original_names:
                # Check if pirate name already exists for this expedition
                existing_pirate = self.get_pirate_name(expedition_id, original_name)

                if existing_pirate:
                    # Use existing mapping
                    pirate_names.append(PirateName(
                        id=0,  # Placeholder ID
                        original_name=original_name,
                        pirate_name=existing_pirate,
                        expedition_id=expedition_id,
                        encrypted_mapping=''
                    ))
                else:
                    # Generate new pirate name
                    pirate_name = self._generate_deterministic_pirate_name(original_name)

                    # Store in database and get the ID
                    with self.db_manager.get_connection() as conn:
                        with conn.cursor() as cur:
                            cur.execute("""
                                INSERT INTO pirate_names (original_name, pirate_name, expedition_id, encrypted_mapping)
                                VALUES (%s, %s, %s, '') RETURNING id
                            """, (original_name, pirate_name, expedition_id))
                            new_id = cur.fetchone()[0]
                            conn.commit()

                    pirate_names.append(PirateName(
                        id=new_id,
                        original_name=original_name,
                        pirate_name=pirate_name,
                        expedition_id=expedition_id,
                        encrypted_mapping=''
                    ))

            self._log_operation("expedition_pirate_names_generated",
                              expedition_id=expedition_id, count=len(pirate_names))
            return pirate_names

        except Exception as e:
            self.logger.error(f"Error generating pirate names for expedition {expedition_id}: {e}")
            return []

    def get_pirate_name(self, expedition_id: int, original_name: str) -> Optional[str]:
        """
        Get pirate name for an original name in an expedition.

        Args:
            expedition_id: Expedition ID
            original_name: Original name

        Returns:
            Pirate name if exists, None otherwise
        """
        try:
            original_name = InputSanitizer.sanitize_text(original_name)
            # Use expedition_pirates table (new system)
            query = """
                SELECT pirate_name FROM expedition_pirates
                WHERE original_name = %s AND expedition_id = %s
            """
            row = self._execute_query(query, (original_name, expedition_id), fetch_one=True)

            return row[0] if row else None

        except Exception as e:
            self.logger.error(f"Error getting pirate name for {original_name} in expedition {expedition_id}: {e}")
            return None

    def get_original_name(self, expedition_id: int, pirate_name: str) -> Optional[str]:
        """
        Get original name from pirate name (owner access only).

        Args:
            expedition_id: Expedition ID
            pirate_name: Pirate name

        Returns:
            Original name if exists, None otherwise
        """
        try:
            pirate_name = InputSanitizer.sanitize_text(pirate_name)
            # Use expedition_pirates table (new system)
            query = """
                SELECT original_name FROM expedition_pirates
                WHERE pirate_name = %s AND expedition_id = %s
            """
            row = self._execute_query(query, (pirate_name, expedition_id), fetch_one=True)

            return row[0] if row else None

        except Exception as e:
            self.logger.error(f"Error getting original name for {pirate_name} in expedition {expedition_id}: {e}")
            return None

    def encrypt_name_mapping(self, expedition_id: int, original_name: str, pirate_name: str, owner_key: str) -> str:
        """
        Create encrypted mapping between original and pirate names.

        Args:
            expedition_id: Expedition ID
            original_name: Original name
            pirate_name: Pirate name
            owner_key: Owner encryption key

        Returns:
            Encrypted mapping string
        """
        try:
            # Simple encryption implementation using the owner key
            # In a real implementation, use proper encryption like AES
            from utils.encryption import encrypt_text

            mapping_data = f"{original_name}:{pirate_name}:{expedition_id}"
            encrypted = encrypt_text(mapping_data, owner_key)

            self._log_operation("name_mapping_encrypted",
                              expedition_id=expedition_id, original_name=original_name)
            return encrypted

        except Exception as e:
            self.logger.error(f"Error encrypting name mapping: {e}")
            return ""

    def decrypt_name_mapping(self, expedition_id: int, encrypted_mapping: str, owner_key: str) -> Optional[Dict[str, str]]:
        """
        Decrypt name mapping for owner access.

        Args:
            expedition_id: Expedition ID
            encrypted_mapping: Encrypted mapping data
            owner_key: Owner decryption key

        Returns:
            Dictionary mapping pirate names to original names if successful, None otherwise
        """
        try:
            from utils.encryption import decrypt_text

            decrypted = decrypt_text(encrypted_mapping, owner_key)
            parts = decrypted.split(":")

            if len(parts) >= 3:
                original_name = parts[0]
                pirate_name = parts[1]
                exp_id = int(parts[2])

                if exp_id == expedition_id:
                    return {pirate_name: original_name}

            return None

        except Exception as e:
            self.logger.error(f"Error decrypting name mapping: {e}")
            return None

    def get_expedition_pirate_names(self, expedition_id: int) -> List[PirateName]:
        """
        Get all pirate names for an expedition from the new expedition_pirates table.

        Args:
            expedition_id: Expedition ID

        Returns:
            List of PirateName objects for the expedition
        """
        try:
            # Use expedition_pirates table (new system)
            query = """
                SELECT id, original_name, pirate_name, encrypted_identity
                FROM expedition_pirates
                WHERE expedition_id = %s
                ORDER BY original_name
            """
            rows = self._execute_query(query, (expedition_id,), fetch_all=True)

            pirate_names = []
            if rows:
                for row in rows:
                    pirate_names.append(PirateName(
                        id=row[0],
                        original_name=row[1],
                        pirate_name=row[2],
                        expedition_id=expedition_id,
                        encrypted_mapping=row[3] or ''
                    ))

            self._log_operation("expedition_pirate_names_retrieved",
                              expedition_id=expedition_id, count=len(pirate_names))
            return pirate_names

        except Exception as e:
            self.logger.error(f"Error getting expedition pirate names: {e}")
            return []

    def delete_expedition_names(self, expedition_id: int) -> bool:
        """
        Delete all pirate names for an expedition.

        Args:
            expedition_id: Expedition ID

        Returns:
            True if successful, False otherwise
        """
        try:
            query = "DELETE FROM pirate_names WHERE expedition_id = %s"
            rows_affected = self._execute_query(query, (expedition_id,), return_affected=True)

            self._log_operation("expedition_names_deleted",
                              expedition_id=expedition_id, count=rows_affected)
            return True

        except Exception as e:
            self.logger.error(f"Error deleting expedition names: {e}")
            return False

    def generate_unique_pirate_name(self) -> str:
        """
        Generate a unique pirate name.

        Returns:
            Unique pirate name
        """
        try:
            import random
            import time

            # Use timestamp for uniqueness
            timestamp = str(int(time.time()))
            unique_seed = f"unique_{timestamp}_{random.randint(1000, 9999)}"

            return self._generate_deterministic_pirate_name(unique_seed)

        except Exception as e:
            self.logger.error(f"Error generating unique pirate name: {e}")
            return "Capitão Único o Misterioso"

    def encrypt_product_name(self, product_name: str, expedition_id: int, owner_key: str) -> str:
        """
        Encrypt product name for expedition item anonymization.

        Args:
            product_name: Product name to encrypt
            expedition_id: Expedition ID
            owner_key: Owner encryption key

        Returns:
            Encrypted product name
        """
        try:
            from utils.encryption import encrypt_text

            product_data = f"{product_name}:{expedition_id}"
            encrypted = encrypt_text(product_data, owner_key)

            self._log_operation("product_name_encrypted",
                              expedition_id=expedition_id, product_name=product_name)
            return encrypted

        except Exception as e:
            self.logger.error(f"Error encrypting product name: {e}")
            return ""

    def decrypt_product_name(self, encrypted_product: str, owner_key: str) -> Optional[str]:
        """
        Decrypt product name for owner access.

        Args:
            encrypted_product: Encrypted product name
            owner_key: Owner decryption key

        Returns:
            Decrypted product name if successful, None otherwise
        """
        try:
            from utils.encryption import decrypt_text

            decrypted = decrypt_text(encrypted_product, owner_key)
            parts = decrypted.split(":")

            if len(parts) >= 1:
                return parts[0]

            return None

        except Exception as e:
            self.logger.error(f"Error decrypting product name: {e}")
            return None

    def generate_anonymized_item_code(self, product_name: str, expedition_id: int) -> str:
        """
        Generate anonymized item code for product tracking.

        Args:
            product_name: Product name
            expedition_id: Expedition ID

        Returns:
            Anonymized item code
        """
        try:
            # Create a deterministic code based on product and expedition
            hash_input = f"{product_name}:{expedition_id}"
            hash_value = hashlib.md5(hash_input.encode()).hexdigest()

            # Create item code like "ITEM-ABC123"
            code_part = hash_value[:6].upper()
            item_code = f"ITEM-{code_part}"

            return item_code

        except Exception as e:
            self.logger.error(f"Error generating item code: {e}")
            return f"ITEM-{expedition_id:06d}"

    def encrypt_item_notes(self, notes: str, expedition_id: int, owner_key: str) -> str:
        """
        Encrypt item notes for expedition privacy.

        Args:
            notes: Notes to encrypt
            expedition_id: Expedition ID
            owner_key: Owner encryption key

        Returns:
            Encrypted notes
        """
        try:
            from utils.encryption import encrypt_text

            notes_data = f"{notes}:{expedition_id}"
            encrypted = encrypt_text(notes_data, owner_key)

            self._log_operation("item_notes_encrypted", expedition_id=expedition_id)
            return encrypted

        except Exception as e:
            self.logger.error(f"Error encrypting item notes: {e}")
            return ""

    def decrypt_item_notes(self, encrypted_notes: str, owner_key: str) -> Optional[str]:
        """
        Decrypt item notes for owner access.

        Args:
            encrypted_notes: Encrypted notes
            owner_key: Owner decryption key

        Returns:
            Decrypted notes if successful, None otherwise
        """
        try:
            from utils.encryption import decrypt_text

            decrypted = decrypt_text(encrypted_notes, owner_key)
            parts = decrypted.split(":")

            if len(parts) >= 1:
                return parts[0]

            return None

        except Exception as e:
            self.logger.error(f"Error decrypting item notes: {e}")
            return None

    def validate_encryption_key(self, owner_key: str, expedition_id: int) -> bool:
        """
        Validate that an owner key is valid for encryption operations.

        Args:
            owner_key: Owner encryption key
            expedition_id: Expedition ID

        Returns:
            True if key is valid, False otherwise
        """
        try:
            # Simple validation - check if key can encrypt/decrypt test data
            test_data = f"test:{expedition_id}"

            try:
                from utils.encryption import encrypt_text, decrypt_text

                encrypted = encrypt_text(test_data, owner_key)
                decrypted = decrypt_text(encrypted, owner_key)

                return decrypted == test_data

            except ImportError:
                # If encryption module doesn't exist, just check key format
                return len(owner_key) >= 8 and owner_key.isalnum()

        except Exception as e:
            self.logger.error(f"Error validating encryption key: {e}")
            return False

    def remove_pirate_mapping(self, buyer_name: str) -> bool:
        """
        Remove a global pirate mapping.

        Args:
            buyer_name: Original buyer name

        Returns:
            True if successful, False otherwise
        """
        try:
            buyer_name = InputSanitizer.sanitize_text(buyer_name)

            query = """
                DELETE FROM pirate_names
                WHERE original_name = %s AND expedition_id IS NULL
            """
            rows_affected = self._execute_query(query, (buyer_name,), return_affected=True)

            if rows_affected > 0:
                self._log_operation("global_pirate_mapping_removed", buyer=buyer_name)
                return True
            return False

        except Exception as e:
            self.logger.error(f"Error removing pirate mapping for {buyer_name}: {e}")
            return False

    def clear_all_pirate_mappings(self) -> bool:
        """
        Clear all global pirate mappings.

        Returns:
            True if successful, False otherwise
        """
        try:
            query = "DELETE FROM pirate_names WHERE expedition_id IS NULL"
            rows_affected = self._execute_query(query, return_affected=True)

            self._log_operation("all_pirate_mappings_cleared", count=rows_affected)
            return True

        except Exception as e:
            self.logger.error(f"Error clearing all pirate mappings: {e}")
            return False

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

            self._log_operation("add_pirate_to_expedition",
                              expedition_id=expedition_id,
                              buyer_name=buyer_name,
                              pirate_name=global_pirate_name)

            return True

        except Exception as e:
            self.logger.error(f"Failed to add pirate to expedition: {e}", exc_info=True)
            return False

    def generate_random_pirate_names_for_buyers(self, expedition_id: int, buyer_names: List[str]) -> List[PirateName]:
        """Generate consistent pirate names for a list of buyers."""
        try:
            if not buyer_names:
                return []

            generated_names = []

            for buyer_name in buyer_names:
                buyer_name = buyer_name.strip()
                if not buyer_name:
                    continue

                # Check if name already exists for this expedition
                existing_pirate = self.get_pirate_name(expedition_id, buyer_name)
                if existing_pirate:
                    # Name already exists, add to list
                    generated_names.append(PirateName(
                        original_name=buyer_name,
                        pirate_name=existing_pirate,
                        expedition_id=expedition_id
                    ))
                    continue

                # Generate new pirate name
                pirate_name = self._generate_deterministic_pirate_name(buyer_name)

                # Store in database
                query = """
                    INSERT INTO pirate_names (original_name, pirate_name, expedition_id, encrypted_mapping)
                    VALUES (%s, %s, %s, '')
                """
                self._execute_query(query, (buyer_name, pirate_name, expedition_id))

                generated_names.append(PirateName(
                    original_name=buyer_name,
                    pirate_name=pirate_name,
                    expedition_id=expedition_id
                ))

            self._log_operation("generate_random_pirate_names_for_buyers",
                              expedition_id=expedition_id, count=len(generated_names))
            return generated_names

        except Exception as e:
            self.logger.error(f"Error generating random pirate names: {e}", exc_info=True)
            return []

    def assign_custom_pirate_name(self, expedition_id: int, buyer_name: str, custom_pirate_name: str) -> Optional[PirateName]:
        """Assign a custom pirate name to a buyer."""
        try:
            buyer_name = buyer_name.strip()
            custom_pirate_name = custom_pirate_name.strip()

            if not buyer_name or not custom_pirate_name:
                self.logger.error("Both buyer name and pirate name are required")
                return None

            # Check if buyer already has a pirate name for this expedition
            existing_pirate = self.get_pirate_name(expedition_id, buyer_name)

            if existing_pirate:
                # Update existing mapping
                query = """
                    UPDATE pirate_names
                    SET pirate_name = %s
                    WHERE expedition_id = %s AND original_name = %s
                """
                self._execute_query(query, (custom_pirate_name, expedition_id, buyer_name))
            else:
                # Create new mapping
                query = """
                    INSERT INTO pirate_names (original_name, pirate_name, expedition_id, encrypted_mapping)
                    VALUES (%s, %s, %s, '')
                """
                self._execute_query(query, (buyer_name, custom_pirate_name, expedition_id))

            self._log_operation("assign_custom_pirate_name",
                              expedition_id=expedition_id,
                              buyer_name=buyer_name,
                              pirate_name=custom_pirate_name)

            return PirateName(
                original_name=buyer_name,
                pirate_name=custom_pirate_name,
                expedition_id=expedition_id
            )

        except Exception as e:
            self.logger.error(f"Error assigning custom pirate name: {e}", exc_info=True)
            return None

    def remove_pirate_name(self, expedition_id: int, buyer_name: str) -> bool:
        """Remove a pirate name mapping for a specific expedition."""
        try:
            buyer_name = buyer_name.strip()
            if not buyer_name:
                return False

            query = """
                DELETE FROM pirate_names
                WHERE expedition_id = %s AND original_name = %s
            """
            rows_affected = self._execute_query(query, (expedition_id, buyer_name), return_affected=True)

            if rows_affected > 0:
                self._log_operation("remove_pirate_name",
                                  expedition_id=expedition_id,
                                  buyer_name=buyer_name)
                return True
            return False

        except Exception as e:
            self.logger.error(f"Error removing pirate name: {e}", exc_info=True)
            return False