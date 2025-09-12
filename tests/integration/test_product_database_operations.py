#!/usr/bin/env python3
"""
Real database integration tests for product operations.
Tests actual database operations for product CRUD, validation, and media handling.
"""

import os
import pytest
from unittest.mock import Mock, AsyncMock
from dotenv import load_dotenv

# Load environment variables (main .env file)
load_dotenv()

# Import dependencies
from database import initialize_database, get_db_manager, close_database
from database.schema import initialize_schema
from core.modern_service_container import initialize_services
from services.product_service import ProductService
from models.product import CreateProductRequest, UpdateProductRequest, Product, AddStockRequest
from services.base_service import ValidationError, NotFoundError, ServiceError, DuplicateError


@pytest.mark.integration
class TestProductDatabaseOperations:
    """Real database integration tests for product operations."""
    
    @classmethod
    def setup_class(cls):
        """Set up test database and services."""
        # Use database from environment (should be set in .env)
        test_db_url = os.getenv('DATABASE_URL')
        if not test_db_url:
            pytest.skip("No DATABASE_URL available for testing")
        
        # Initialize database
        initialize_database(database_url=test_db_url)
        initialize_schema()
        
        # Initialize service container
        initialize_services({})
        
        # Initialize services directly
        cls.product_service = ProductService()
        
        # Store database manager for direct queries
        cls.db_manager = get_db_manager()
    
    @classmethod
    def teardown_class(cls):
        """Clean up test database."""
        close_database()
    
    def setup_method(self):
        """Set up fresh data for each test."""
        # Clean tables in correct order
        with self.db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM ItensVenda")
                cursor.execute("DELETE FROM Pagamentos")
                cursor.execute("DELETE FROM Vendas")
                cursor.execute("DELETE FROM estoque")
                cursor.execute("DELETE FROM produtos")
                cursor.execute("DELETE FROM usuarios")
                # Reset sequences for predictable IDs if PostgreSQL
                if 'postgresql' in os.getenv('DATABASE_URL', ''):
                    cursor.execute("ALTER SEQUENCE produtos_id_seq RESTART WITH 1")
                    cursor.execute("ALTER SEQUENCE usuarios_id_seq RESTART WITH 1")
                    cursor.execute("ALTER SEQUENCE vendas_id_seq RESTART WITH 1")
                    cursor.execute("ALTER SEQUENCE estoque_id_seq RESTART WITH 1")
                conn.commit()
    
    def get_product_from_db(self, product_id):
        """Helper to get product record directly from database."""
        with self.db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, nome, emoji, media_file_id, data 
                    FROM produtos 
                    WHERE id = %s
                """, (product_id,))
                return cursor.fetchone()
    
    def get_all_products_from_db(self):
        """Helper to get all product records from database."""
        with self.db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, nome, emoji, media_file_id, data 
                    FROM produtos 
                    ORDER BY id ASC
                """)
                return cursor.fetchall()
    
    def product_exists_in_db(self, nome):
        """Helper to check if product exists by name."""
        with self.db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM produtos WHERE nome = %s", (nome,))
                return cursor.fetchone()[0] > 0
    
    def test_create_product_basic(self):
        """Test creating a basic product with name and emoji."""
        # Create product
        request = CreateProductRequest(
            nome="Gaming Mouse",
            emoji="🖱️"
        )
        
        product = self.product_service.create_product(request)
        
        # Verify service response
        assert product is not None
        assert product.id is not None
        assert product.nome == "Gaming Mouse"
        assert product.emoji == "🖱️"
        assert product.media_file_id is None
        
        # Verify database record
        db_record = self.get_product_from_db(product.id)
        assert db_record is not None
        assert db_record[0] == product.id  # id
        assert db_record[1] == "Gaming Mouse"  # nome
        assert db_record[2] == "🖱️"  # emoji
        assert db_record[3] is None  # media_file_id
        # data field may be None or timestamp
    
    def test_create_product_with_media(self):
        """Test creating a product with media file."""
        request = CreateProductRequest(
            nome="Wireless Headphones",
            emoji="🎧",
            media_file_id="BAACAgIAAxkBAAIC123456789"
        )
        
        product = self.product_service.create_product(request)
        
        # Verify service response
        assert product.nome == "Wireless Headphones"
        assert product.emoji == "🎧"
        assert product.media_file_id == "BAACAgIAAxkBAAIC123456789"
        
        # Verify database record
        db_record = self.get_product_from_db(product.id)
        assert db_record[3] == "BAACAgIAAxkBAAIC123456789"  # media_file_id
    
    def test_create_product_name_only(self):
        """Test creating a product with just name (minimal requirements)."""
        request = CreateProductRequest(nome="Basic Product")
        
        product = self.product_service.create_product(request)
        
        assert product.nome == "Basic Product"
        assert product.emoji is None
        assert product.media_file_id is None
        
        # Verify in database
        db_record = self.get_product_from_db(product.id)
        assert db_record[1] == "Basic Product"
        assert db_record[2] is None  # emoji
        assert db_record[3] is None  # media_file_id
    
    def test_create_product_duplicate_name(self):
        """Test that duplicate product names are rejected."""
        # Create first product
        request1 = CreateProductRequest(nome="Unique Product", emoji="⭐")
        self.product_service.create_product(request1)
        
        # Try to create second product with same name
        request2 = CreateProductRequest(nome="Unique Product", emoji="🌟")
        
        with pytest.raises(DuplicateError) as exc_info:
            self.product_service.create_product(request2)
        
        assert "already exists" in str(exc_info.value).lower()
        
        # Verify only one product exists in database
        products = self.get_all_products_from_db()
        assert len(products) == 1
    
    def test_create_product_validation_errors(self):
        """Test validation errors for invalid product data."""
        # Test empty name
        with pytest.raises(ValidationError):
            request = CreateProductRequest(nome="")
            self.product_service.create_product(request)
        
        # Test name too short
        with pytest.raises(ValidationError):
            request = CreateProductRequest(nome="A")
            self.product_service.create_product(request)
        
        # Test emoji too long
        with pytest.raises(ValidationError):
            request = CreateProductRequest(
                nome="Valid Product",
                emoji="🎮🎯🎲🎳🎨🎭🎪🎫🎬🎤🎧🎼"  # Very long emoji string
            )
            self.product_service.create_product(request)
        
        # Verify no invalid products were created
        products = self.get_all_products_from_db()
        assert len(products) == 0
    
    def test_get_product_by_id(self):
        """Test retrieving product by ID."""
        # Create a product
        request = CreateProductRequest(nome="Test Product", emoji="📦")
        created_product = self.product_service.create_product(request)
        
        # Retrieve by ID
        retrieved_product = self.product_service.get_product_by_id(created_product.id)
        
        assert retrieved_product is not None
        assert retrieved_product.id == created_product.id
        assert retrieved_product.nome == "Test Product"
        assert retrieved_product.emoji == "📦"
    
    def test_get_product_by_id_not_found(self):
        """Test retrieving non-existent product by ID."""
        product = self.product_service.get_product_by_id(99999)
        assert product is None
    
    def test_get_product_by_name(self):
        """Test retrieving product by name."""
        # Create a product
        request = CreateProductRequest(nome="Searchable Product", emoji="🔍")
        self.product_service.create_product(request)
        
        # Retrieve by name
        product = self.product_service.get_product_by_name("Searchable Product")
        
        assert product is not None
        assert product.nome == "Searchable Product"
        assert product.emoji == "🔍"
    
    def test_get_product_by_name_not_found(self):
        """Test retrieving non-existent product by name."""
        product = self.product_service.get_product_by_name("Non-existent Product")
        assert product is None
    
    def test_get_all_products(self):
        """Test retrieving all products."""
        # Create multiple products
        products_data = [
            ("Product A", "🅰️"),
            ("Product B", "🅱️"),
            ("Product C", "🅾️")
        ]
        
        created_products = []
        for nome, emoji in products_data:
            request = CreateProductRequest(nome=nome, emoji=emoji)
            product = self.product_service.create_product(request)
            created_products.append(product)
        
        # Retrieve all products
        all_products = self.product_service.get_all_products()
        
        assert len(all_products) == 3
        
        # Verify all products are present
        product_names = [p.nome for p in all_products]
        assert "Product A" in product_names
        assert "Product B" in product_names
        assert "Product C" in product_names
    
    def test_get_all_products_empty(self):
        """Test retrieving all products when none exist."""
        products = self.product_service.get_all_products()
        assert products == []
    
    def test_update_product_name(self):
        """Test updating product name."""
        # Create product
        request = CreateProductRequest(nome="Original Name", emoji="📝")
        product = self.product_service.create_product(request)
        
        # Update name
        update_request = UpdateProductRequest(
            product_id=product.id,
            nome="Updated Name"
        )
        updated_product = self.product_service.update_product(update_request)
        
        # Verify service response
        assert updated_product.nome == "Updated Name"
        assert updated_product.emoji == "📝"  # Should remain unchanged
        
        # Verify database
        db_record = self.get_product_from_db(product.id)
        assert db_record[1] == "Updated Name"
        assert db_record[2] == "📝"
    
    def test_update_product_emoji(self):
        """Test updating product emoji."""
        # Create product
        request = CreateProductRequest(nome="Test Product", emoji="📦")
        product = self.product_service.create_product(request)
        
        # Update emoji
        update_request = UpdateProductRequest(
            product_id=product.id,
            emoji="🎯"
        )
        updated_product = self.product_service.update_product(update_request)
        
        assert updated_product.nome == "Test Product"  # Should remain unchanged
        assert updated_product.emoji == "🎯"
        
        # Verify database
        db_record = self.get_product_from_db(product.id)
        assert db_record[1] == "Test Product"
        assert db_record[2] == "🎯"
    
    def test_update_product_media_file(self):
        """Test updating product media file."""
        # Create product
        request = CreateProductRequest(nome="Media Product", emoji="📸")
        product = self.product_service.create_product(request)
        
        # Update media file
        update_request = UpdateProductRequest(
            product_id=product.id,
            media_file_id="BAACAgIAAxkBAAIC987654321"
        )
        updated_product = self.product_service.update_product(update_request)
        
        assert updated_product.media_file_id == "BAACAgIAAxkBAAIC987654321"
        
        # Verify database
        db_record = self.get_product_from_db(product.id)
        assert db_record[3] == "BAACAgIAAxkBAAIC987654321"
    
    def test_update_product_all_fields(self):
        """Test updating all product fields at once."""
        # Create product
        request = CreateProductRequest(nome="Original", emoji="📦")
        product = self.product_service.create_product(request)
        
        # Update all fields
        update_request = UpdateProductRequest(
            product_id=product.id,
            nome="Completely Updated",
            emoji="🎯",
            media_file_id="BAACAgIAAxkBAAIC555555555"
        )
        updated_product = self.product_service.update_product(update_request)
        
        assert updated_product.nome == "Completely Updated"
        assert updated_product.emoji == "🎯"
        assert updated_product.media_file_id == "BAACAgIAAxkBAAIC555555555"
        
        # Verify database
        db_record = self.get_product_from_db(product.id)
        assert db_record[1] == "Completely Updated"
        assert db_record[2] == "🎯"
        assert db_record[3] == "BAACAgIAAxkBAAIC555555555"
    
    def test_update_product_not_found(self):
        """Test updating non-existent product."""
        update_request = UpdateProductRequest(
            product_id=99999,
            nome="Should Not Work"
        )
        
        with pytest.raises(NotFoundError):
            self.product_service.update_product(update_request)
    
    def test_update_product_duplicate_name(self):
        """Test updating product to duplicate name."""
        # Create two products
        request1 = CreateProductRequest(nome="Product One", emoji="1️⃣")
        product1 = self.product_service.create_product(request1)
        
        request2 = CreateProductRequest(nome="Product Two", emoji="2️⃣")
        product2 = self.product_service.create_product(request2)
        
        # Try to update product2 to have same name as product1
        update_request = UpdateProductRequest(
            product_id=product2.id,
            nome="Product One"
        )
        
        with pytest.raises(DuplicateError):
            self.product_service.update_product(update_request)
        
        # Verify product2 name unchanged in database
        db_record = self.get_product_from_db(product2.id)
        assert db_record[1] == "Product Two"
    
    def test_update_product_no_changes(self):
        """Test update request with no actual changes."""
        # Create product
        request = CreateProductRequest(nome="Unchanged Product", emoji="🔒")
        product = self.product_service.create_product(request)
        
        # Update with no changes
        update_request = UpdateProductRequest(product_id=product.id)
        
        with pytest.raises(ValidationError) as exc_info:
            self.product_service.update_product(update_request)
        
        assert "no updates" in str(exc_info.value).lower()
    
    def test_delete_product(self):
        """Test deleting a product."""
        # Create product
        request = CreateProductRequest(nome="Product To Delete", emoji="🗑️")
        product = self.product_service.create_product(request)
        
        # Verify it exists
        assert self.get_product_from_db(product.id) is not None
        
        # Delete product
        success = self.product_service.delete_product(product.id)
        assert success is True
        
        # Verify it's deleted from database
        assert self.get_product_from_db(product.id) is None
        
        # Verify service methods return None
        assert self.product_service.get_product_by_id(product.id) is None
    
    def test_delete_product_not_found(self):
        """Test deleting non-existent product."""
        with pytest.raises(NotFoundError):
            self.product_service.delete_product(99999)
    
    def test_delete_product_with_stock(self):
        """Test deleting product that has stock entries."""
        # Create product
        request = CreateProductRequest(nome="Product With Stock", emoji="📦")
        product = self.product_service.create_product(request)
        
        # Add stock
        stock_request = AddStockRequest(
            produto_id=product.id,
            quantidade=10,
            valor=25.00,
            custo=15.00
        )
        self.product_service.add_stock(stock_request)
        
        # Delete product (should cascade delete stock)
        success = self.product_service.delete_product(product.id)
        assert success is True
        
        # Verify product and stock are deleted
        assert self.get_product_from_db(product.id) is None
        
        # Verify stock was also deleted
        with self.db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM estoque WHERE produto_id = %s", (product.id,))
                stock_count = cursor.fetchone()[0]
                assert stock_count == 0
    
    def test_product_name_exists(self):
        """Test checking if product name exists."""
        # Create product
        request = CreateProductRequest(nome="Existing Product", emoji="✅")
        product = self.product_service.create_product(request)
        
        # Test existing name
        assert self.product_service.product_name_exists("Existing Product") is True
        
        # Test non-existing name
        assert self.product_service.product_name_exists("Non-existing Product") is False
        
        # Test case sensitivity
        assert self.product_service.product_name_exists("existing product") is False
    
    def test_product_name_exists_exclude_self(self):
        """Test checking product name exists excluding specific product."""
        # Create product
        request = CreateProductRequest(nome="Original Name", emoji="📝")
        product = self.product_service.create_product(request)
        
        # Should return False when excluding the product itself
        assert self.product_service.product_name_exists(
            "Original Name", 
            exclude_product_id=product.id
        ) is False
        
        # Should return True when not excluding
        assert self.product_service.product_name_exists("Original Name") is True
    
    def test_get_products_with_stock(self):
        """Test retrieving products with their stock information."""
        # Create products
        product1_req = CreateProductRequest(nome="Product With Stock", emoji="📦")
        product1 = self.product_service.create_product(product1_req)
        
        product2_req = CreateProductRequest(nome="Product Without Stock", emoji="📭")
        product2 = self.product_service.create_product(product2_req)
        
        # Add stock to product1 only
        stock_request = AddStockRequest(
            produto_id=product1.id,
            quantidade=15,
            valor=30.00,
            custo=20.00
        )
        self.product_service.add_stock(stock_request)
        
        # Get products with stock
        products_with_stock = self.product_service.get_products_with_stock()
        
        # Should return both products but with different stock quantities
        assert len(products_with_stock) == 2
        
        # Find each product in results
        product1_result = next((p for p in products_with_stock if p.product.id == product1.id), None)
        product2_result = next((p for p in products_with_stock if p.product.id == product2.id), None)
        
        assert product1_result is not None
        assert product2_result is not None
        
        # Verify stock quantities
        assert product1_result.total_quantity == 15
        assert product2_result.total_quantity == 0
    
    def test_concurrent_product_operations(self):
        """Test concurrent product operations."""
        # Create base product
        request = CreateProductRequest(nome="Concurrent Test Product", emoji="⚡")
        product = self.product_service.create_product(request)
        
        # Simulate concurrent updates (in real scenario these would be parallel)
        update1 = UpdateProductRequest(product_id=product.id, emoji="🔥")
        update2 = UpdateProductRequest(product_id=product.id, emoji="❄️")
        
        # Apply updates sequentially (simulating concurrent scenario)
        self.product_service.update_product(update1)
        final_product = self.product_service.update_product(update2)
        
        # Last update should win
        assert final_product.emoji == "❄️"
        
        # Verify in database
        db_record = self.get_product_from_db(product.id)
        assert db_record[2] == "❄️"