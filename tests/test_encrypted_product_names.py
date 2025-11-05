"""
Unit tests for encrypted product name generation feature.
Tests the generation, storage, and retrieval of encrypted product names.
"""

import pytest
import re
from decimal import Decimal
from datetime import datetime
from utils.encryption import generate_encrypted_product_name, generate_encrypted_product_name_random
from models.expedition import ExpeditionItem, ExpeditionItemWithProduct


class TestEncryptedProductNameGeneration:
    """Test encrypted product name generation utilities."""

    def test_generate_encrypted_product_name_format(self):
        """Test that generated names follow the correct format."""
        name = generate_encrypted_product_name(1, 100, 0)

        # Should match format: PREFIX-XXXX
        assert re.match(r'^(ITEM|CARGO|GOODS|SUPPLY)-[A-Z0-9]{4}$', name)

    def test_generate_encrypted_product_name_deterministic(self):
        """Test that same inputs generate same encrypted name."""
        name1 = generate_encrypted_product_name(1, 100, 0)
        name2 = generate_encrypted_product_name(1, 100, 0)

        assert name1 == name2, "Same inputs should generate same name"

    def test_generate_encrypted_product_name_unique_sequence(self):
        """Test that different sequence numbers generate different names."""
        name1 = generate_encrypted_product_name(1, 100, 0)
        name2 = generate_encrypted_product_name(1, 100, 1)
        name3 = generate_encrypted_product_name(1, 100, 2)

        assert name1 != name2, "Different sequences should generate different names"
        assert name2 != name3, "Different sequences should generate different names"
        assert name1 != name3, "Different sequences should generate different names"

    def test_generate_encrypted_product_name_unique_expedition(self):
        """Test that different expeditions generate different names."""
        name1 = generate_encrypted_product_name(1, 100, 0)
        name2 = generate_encrypted_product_name(2, 100, 0)

        assert name1 != name2, "Different expeditions should generate different names"

    def test_generate_encrypted_product_name_unique_product(self):
        """Test that different products generate different names."""
        name1 = generate_encrypted_product_name(1, 100, 0)
        name2 = generate_encrypted_product_name(1, 200, 0)

        assert name1 != name2, "Different products should generate different names"

    def test_generate_encrypted_product_name_random_format(self):
        """Test random encrypted name generation format."""
        name = generate_encrypted_product_name_random(1)

        # Should match format: PREFIX-XXXX
        assert re.match(r'^(ITEM|CARGO|GOODS|SUPPLY|MERCH|STOCK)-[A-Z0-9]{4}$', name)

    def test_generate_encrypted_product_name_random_uniqueness(self):
        """Test that random names are likely to be different."""
        names = [generate_encrypted_product_name_random(1) for _ in range(10)]

        # At least some names should be different (very high probability)
        unique_names = set(names)
        assert len(unique_names) > 5, "Random names should have high uniqueness"


class TestExpeditionItemModel:
    """Test ExpeditionItem model with encrypted names."""

    def test_expedition_item_with_encrypted_name(self):
        """Test creating ExpeditionItem with encrypted name."""
        item = ExpeditionItem(
            id=1,
            expedition_id=10,
            produto_id=100,
            quantity_required=50,
            quantity_consumed=25,
            encrypted_product_name="ITEM-A7B3",
            created_at=datetime.now()
        )

        assert item.encrypted_product_name == "ITEM-A7B3"

    def test_expedition_item_from_db_row_new_format(self):
        """Test creating ExpeditionItem from database row with encrypted name."""
        row = (1, 10, 100, 50, 25, "CARGO-X9Z2", datetime.now())

        item = ExpeditionItem.from_db_row(row)

        assert item.id == 1
        assert item.expedition_id == 10
        assert item.produto_id == 100
        assert item.quantity_required == 50
        assert item.quantity_consumed == 25
        assert item.encrypted_product_name == "CARGO-X9Z2"

    def test_expedition_item_from_db_row_old_format(self):
        """Test backward compatibility with old database format."""
        row = (1, 10, 100, 50, 25, datetime.now())

        item = ExpeditionItem.from_db_row(row)

        assert item.id == 1
        assert item.expedition_id == 10
        assert item.produto_id == 100
        assert item.quantity_required == 50
        assert item.quantity_consumed == 25
        assert item.encrypted_product_name is None  # Old format

    def test_expedition_item_to_dict_with_encrypted_name(self):
        """Test dictionary conversion includes encrypted name."""
        item = ExpeditionItem(
            id=1,
            expedition_id=10,
            produto_id=100,
            quantity_required=50,
            quantity_consumed=25,
            encrypted_product_name="ITEM-K7M9",
            created_at=datetime.now()
        )

        item_dict = item.to_dict()

        assert 'encrypted_product_name' in item_dict
        assert item_dict['encrypted_product_name'] == "ITEM-K7M9"

    def test_expedition_item_to_dict_without_encrypted_name(self):
        """Test dictionary conversion without encrypted name (backward compatibility)."""
        item = ExpeditionItem(
            id=1,
            expedition_id=10,
            produto_id=100,
            quantity_required=50,
            quantity_consumed=25,
            created_at=datetime.now()
        )

        item_dict = item.to_dict()

        assert 'encrypted_product_name' not in item_dict or item_dict.get('encrypted_product_name') is None


class TestExpeditionItemWithProductModel:
    """Test ExpeditionItemWithProduct model for API responses."""

    def test_expedition_item_with_product_encrypted_name(self):
        """Test creating ExpeditionItemWithProduct with encrypted name."""
        item = ExpeditionItemWithProduct(
            id=1,
            produto_id=100,
            product_name="Cocaine",
            product_emoji="",
            quantity_needed=50,
            unit_price=Decimal('25.50'),
            quantity_consumed=25,
            encrypted_product_name="ITEM-A7B3",
            original_product_name="Cocaine",
            added_at=datetime.now()
        )

        assert item.encrypted_product_name == "ITEM-A7B3"
        assert item.original_product_name == "Cocaine"

    def test_expedition_item_with_product_to_dict_encrypted(self):
        """Test that to_dict() uses encrypted name when available."""
        item = ExpeditionItemWithProduct(
            id=1,
            produto_id=100,
            product_name="Cocaine",
            product_emoji="",
            quantity_needed=50,
            unit_price=Decimal('25.50'),
            quantity_consumed=25,
            encrypted_product_name="ITEM-A7B3",
            original_product_name="Cocaine",
            added_at=datetime.now()
        )

        item_dict = item.to_dict()

        # Should use encrypted name as product_name
        assert item_dict['product_name'] == "ITEM-A7B3"
        assert item_dict['encrypted_product_name'] == "ITEM-A7B3"
        assert item_dict['original_product_name'] == "Cocaine"

    def test_expedition_item_with_product_to_dict_no_encrypted(self):
        """Test backward compatibility when no encrypted name is set."""
        item = ExpeditionItemWithProduct(
            id=1,
            produto_id=100,
            product_name="Cocaine",
            product_emoji="",
            quantity_needed=50,
            unit_price=Decimal('25.50'),
            quantity_consumed=25,
            added_at=datetime.now()
        )

        item_dict = item.to_dict()

        # Should use regular product name
        assert item_dict['product_name'] == "Cocaine"
        assert 'encrypted_product_name' not in item_dict or item_dict.get('encrypted_product_name') is None

    def test_expedition_item_with_product_from_db_row_new_format(self):
        """Test creating from database row with encrypted names."""
        row = (
            1,  # id
            100,  # produto_id
            "Cocaine",  # product_name
            "",  # product_emoji
            50,  # quantity_needed
            25.50,  # unit_price
            25,  # quantity_consumed
            datetime.now(),  # added_at
            "ITEM-A7B3",  # encrypted_product_name
            "Cocaine"  # original_product_name
        )

        item = ExpeditionItemWithProduct.from_db_row(row)

        assert item.encrypted_product_name == "ITEM-A7B3"
        assert item.original_product_name == "Cocaine"

    def test_expedition_item_with_product_from_db_row_old_format(self):
        """Test backward compatibility with old database format."""
        row = (
            1,  # id
            100,  # produto_id
            "Cocaine",  # product_name
            "",  # product_emoji
            50,  # quantity_needed
            25.50,  # unit_price
            25,  # quantity_consumed
            datetime.now()  # added_at
        )

        item = ExpeditionItemWithProduct.from_db_row(row)

        assert item.encrypted_product_name is None
        assert item.original_product_name is None


class TestEncryptedNameIntegration:
    """Integration tests for encrypted product names."""

    def test_encrypted_name_workflow(self):
        """Test complete workflow of encrypted name generation and usage."""
        expedition_id = 1
        product_id = 100
        sequence = 0

        # 1. Generate encrypted name
        encrypted_name = generate_encrypted_product_name(expedition_id, product_id, sequence)

        assert encrypted_name is not None
        assert len(encrypted_name) > 0

        # 2. Create ExpeditionItem with encrypted name
        item = ExpeditionItem(
            id=1,
            expedition_id=expedition_id,
            produto_id=product_id,
            quantity_required=50,
            quantity_consumed=0,
            encrypted_product_name=encrypted_name,
            created_at=datetime.now()
        )

        # 3. Convert to dict for API response
        item_dict = item.to_dict()

        assert item_dict['encrypted_product_name'] == encrypted_name

        # 4. Create ExpeditionItemWithProduct for full API response
        item_with_product = ExpeditionItemWithProduct(
            id=item.id,
            produto_id=item.produto_id,
            product_name="Cocaine",
            product_emoji="",
            quantity_needed=item.quantity_required,
            unit_price=Decimal('25.50'),
            quantity_consumed=item.quantity_consumed,
            encrypted_product_name=encrypted_name,
            original_product_name="Cocaine",
            added_at=item.created_at
        )

        # 5. Convert to API response dict
        api_dict = item_with_product.to_dict()

        # Verify encrypted name is used as product_name
        assert api_dict['product_name'] == encrypted_name
        assert api_dict['encrypted_product_name'] == encrypted_name
        assert api_dict['original_product_name'] == "Cocaine"

    def test_multiple_items_different_names(self):
        """Test that multiple items in same expedition get different encrypted names."""
        expedition_id = 1

        # Add 5 items to expedition
        encrypted_names = []
        for i in range(5):
            encrypted_name = generate_encrypted_product_name(expedition_id, 100 + i, i)
            encrypted_names.append(encrypted_name)

        # All names should be unique
        assert len(set(encrypted_names)) == 5, "All encrypted names should be unique"

    def test_same_product_different_expeditions(self):
        """Test same product in different expeditions gets different encrypted names."""
        product_id = 100

        # Add same product to 3 different expeditions
        encrypted_names = []
        for expedition_id in range(1, 4):
            encrypted_name = generate_encrypted_product_name(expedition_id, product_id, 0)
            encrypted_names.append(encrypted_name)

        # All names should be unique
        assert len(set(encrypted_names)) == 3, "Same product in different expeditions should get different names"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
