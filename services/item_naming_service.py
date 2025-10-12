"""
Item Naming Service - Custom Item/Product Name Management
Handles custom display names/aliases for products with global mappings.
"""

import hashlib
import logging
import random
from typing import Dict, List, Optional

from services.base_service import BaseService, ServiceError, ValidationError, NotFoundError
from utils.input_sanitizer import InputSanitizer


class ItemNamingService(BaseService):
    """
    Service for managing custom item/product names.
    Similar to brambler service but for global item name mappings.
    """

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

    def get_available_products(self) -> List[str]:
        """
        Get all available product names from the products table.

        Returns:
            List of product names
        """
        try:
            query = "SELECT nome FROM Produtos ORDER BY nome"
            rows = self._execute_query(query, fetch_all=True)

            if not rows:
                return []

            product_names = [row[0] for row in rows if row[0]]
            self._log_operation("available_products_retrieved", count=len(product_names))
            return product_names

        except Exception as e:
            self.logger.error(f"Error getting available products: {e}", exc_info=True)
            return []

    def get_custom_name_for_product(self, product_name: str) -> Optional[str]:
        """
        Get the custom name for a product if it exists.

        Args:
            product_name: Original product name

        Returns:
            Custom name if exists, None otherwise
        """
        try:
            product_name = InputSanitizer.sanitize_text(product_name)
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
        """
        Get the original product name for a custom name.

        Args:
            custom_name: Custom display name

        Returns:
            Original product name if exists, None otherwise
        """
        try:
            custom_name = InputSanitizer.sanitize_text(custom_name)
            query = """
                SELECT product_name FROM item_mappings
                WHERE custom_name = %s
            """
            row = self._execute_query(query, (custom_name,), fetch_one=True)

            return row[0] if row else None

        except Exception as e:
            self.logger.error(f"Error getting product for custom name {custom_name}: {e}")
            return None

    def create_global_item_mapping(self, product_name: str, custom_name: str, chat_id: Optional[int] = None) -> bool:
        """
        Create a global item mapping.

        Args:
            product_name: Original product name
            custom_name: Custom display name
            chat_id: Optional chat ID of the creator

        Returns:
            True if successful, False otherwise
        """
        try:
            product_name = InputSanitizer.sanitize_text(product_name)
            custom_name = InputSanitizer.sanitize_text(custom_name)

            # Check if mapping already exists
            existing = self.get_custom_name_for_product(product_name)
            if existing:
                return True  # Already exists

            query = """
                INSERT INTO item_mappings (product_name, custom_name, is_fantasy_generated, created_by_chat_id)
                VALUES (%s, %s, %s, %s)
            """
            self._execute_query(query, (product_name, custom_name, True, chat_id))

            self._log_operation("global_item_mapping_created",
                              product=product_name, custom_name=custom_name)
            return True

        except Exception as e:
            self.logger.error(f"Error creating global item mapping: {e}")
            return False

    def create_or_update_global_item_mapping(self, product_name: str, custom_name: str, chat_id: Optional[int] = None) -> bool:
        """
        Create or update a global item mapping.

        Args:
            product_name: Original product name
            custom_name: Custom display name
            chat_id: Optional chat ID of the creator

        Returns:
            True if successful, False otherwise
        """
        try:
            product_name = InputSanitizer.sanitize_text(product_name)
            custom_name = InputSanitizer.sanitize_text(custom_name)

            # Check if mapping already exists
            existing = self.get_custom_name_for_product(product_name)

            if existing:
                # Update existing mapping
                query = """
                    UPDATE item_mappings
                    SET custom_name = %s, updated_at = CURRENT_TIMESTAMP, is_fantasy_generated = %s
                    WHERE product_name = %s
                """
                self._execute_query(query, (custom_name, False, product_name))
                self._log_operation("global_item_mapping_updated",
                                  product=product_name, custom_name=custom_name)
            else:
                # Create new mapping
                query = """
                    INSERT INTO item_mappings (product_name, custom_name, is_fantasy_generated, created_by_chat_id)
                    VALUES (%s, %s, %s, %s)
                """
                self._execute_query(query, (product_name, custom_name, False, chat_id))
                self._log_operation("global_item_mapping_created",
                                  product=product_name, custom_name=custom_name)

            return True

        except Exception as e:
            self.logger.error(f"Error creating/updating global item mapping: {e}")
            return False

    def get_all_item_mappings(self) -> Dict[str, str]:
        """
        Get all global item name mappings.

        Returns:
            Dictionary mapping original names to custom names
        """
        try:
            query = """
                SELECT product_name, custom_name FROM item_mappings
                ORDER BY product_name
            """
            rows = self._execute_query(query, fetch_all=True)

            mappings = {}
            if rows:
                for row in rows:
                    mappings[row[0]] = row[1]

            self._log_operation("all_item_mappings_retrieved", count=len(mappings))
            return mappings

        except Exception as e:
            self.logger.error(f"Error getting all item mappings: {e}")
            return {}

    def _generate_deterministic_fantasy_name(self, product_name: str) -> str:
        """
        Generate a deterministic fantasy name for a product.
        Uses the same approach as brambler service but for items.

        Args:
            product_name: Original product name

        Returns:
            Generated fantasy name
        """
        try:
            # Use MD5 hash for deterministic generation
            hash_value = hashlib.md5(product_name.encode()).hexdigest()

            # Fantasy name components
            prefixes = [
                "Místico", "Antigo", "Sagrado", "Lendário", "Mágico", "Encantado",
                "Divino", "Celestial", "Arcano", "Etéreo", "Sublime", "Supremo",
                "Raro", "Épico", "Único", "Poderoso", "Radiante", "Brilhante"
            ]

            suffixes = [
                "dos Deuses", "da Luz", "das Sombras", "do Tempo", "da Eternidade",
                "do Poder", "da Sabedoria", "da Força", "da Magia", "do Destino",
                "dos Elementos", "da Natureza", "do Cosmos", "da Vitória", "da Glória",
                "do Mistério", "da Harmonia", "da Perfeição"
            ]

            cores = [
                "Dourado", "Prateado", "Cristalino", "Flamejante", "Gelado",
                "Sombrio", "Luminoso", "Púrpura", "Esmeralda", "Rubi",
                "Safira", "Diamante", "Ônix", "Pérola", "Âmbar"
            ]

            # Use hash to select components deterministically
            prefix_idx = int(hash_value[:2], 16) % len(prefixes)
            color_idx = int(hash_value[2:4], 16) % len(cores)
            suffix_idx = int(hash_value[4:6], 16) % len(suffixes)

            # Create fantasy name
            fantasy_name = f"{prefixes[prefix_idx]} {product_name} {cores[color_idx]} {suffixes[suffix_idx]}"

            return fantasy_name

        except Exception as e:
            self.logger.error(f"Error generating fantasy name for {product_name}: {e}")
            return f"Místico {product_name} Encantado"

    def remove_item_mapping(self, product_name: str) -> bool:
        """
        Remove a global item mapping.

        Args:
            product_name: Original product name

        Returns:
            True if successful, False otherwise
        """
        try:
            product_name = InputSanitizer.sanitize_text(product_name)

            query = """
                DELETE FROM item_mappings
                WHERE product_name = %s
            """
            rows_affected = self._execute_query(query, (product_name,), return_affected=True)

            if rows_affected > 0:
                self._log_operation("global_item_mapping_removed", product=product_name)
                return True
            return False

        except Exception as e:
            self.logger.error(f"Error removing item mapping for {product_name}: {e}")
            return False

    def clear_all_item_mappings(self) -> bool:
        """
        Clear all global item mappings.

        Returns:
            True if successful, False otherwise
        """
        try:
            query = "DELETE FROM item_mappings"
            rows_affected = self._execute_query(query, return_affected=True)

            self._log_operation("all_item_mappings_cleared", count=rows_affected)
            return True

        except Exception as e:
            self.logger.error(f"Error clearing all item mappings: {e}")
            return False

    def get_mapping_details(self, product_name: str) -> Optional[Dict]:
        """
        Get detailed information about a specific mapping.

        Args:
            product_name: Original product name

        Returns:
            Dictionary with mapping details or None if not found
        """
        try:
            product_name = InputSanitizer.sanitize_text(product_name)
            query = """
                SELECT product_name, custom_name, description, is_fantasy_generated,
                       created_at, updated_at, created_by_chat_id
                FROM item_mappings
                WHERE product_name = %s
            """
            row = self._execute_query(query, (product_name,), fetch_one=True)

            if row:
                return {
                    'product_name': row[0],
                    'custom_name': row[1],
                    'description': row[2],
                    'is_fantasy_generated': row[3],
                    'created_at': row[4],
                    'updated_at': row[5],
                    'created_by_chat_id': row[6]
                }
            return None

        except Exception as e:
            self.logger.error(f"Error getting mapping details for {product_name}: {e}")
            return None

    def get_all_mapping_details(self) -> List[Dict]:
        """
        Get detailed information about all mappings.

        Returns:
            List of dictionaries with mapping details
        """
        try:
            query = """
                SELECT product_name, custom_name, description, is_fantasy_generated,
                       created_at, updated_at, created_by_chat_id
                FROM item_mappings
                ORDER BY product_name
            """
            rows = self._execute_query(query, fetch_all=True)

            mappings = []
            if rows:
                for row in rows:
                    mappings.append({
                        'product_name': row[0],
                        'custom_name': row[1],
                        'description': row[2],
                        'is_fantasy_generated': row[3],
                        'created_at': row[4],
                        'updated_at': row[5],
                        'created_by_chat_id': row[6]
                    })

            self._log_operation("all_mapping_details_retrieved", count=len(mappings))
            return mappings

        except Exception as e:
            self.logger.error(f"Error getting all mapping details: {e}")
            return []