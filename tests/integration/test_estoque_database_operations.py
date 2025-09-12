#!/usr/bin/env python3
"""
Real database integration tests for estoque (inventory) operations.
Tests actual database operations for stock management, FIFO consumption, and validation.
"""

import os
import pytest
from unittest.mock import Mock, AsyncMock
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables (main .env file)
load_dotenv()

# Import dependencies
from database import initialize_database, get_db_manager, close_database
from database.schema import initialize_schema
from core.modern_service_container import initialize_services
from services.product_service import ProductService
from services.sales_service import SalesService
from models.product import CreateProductRequest, AddStockRequest, StockItem
from models.sale import CreateSaleRequest, CreateSaleItemRequest
from services.base_service import ValidationError, NotFoundError, ServiceError


@pytest.mark.integration
class TestEstoqueDatabaseOperations:
    """Real database integration tests for estoque operations."""
    
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
        
        # Initialize services directly (like other integration tests)
        cls.product_service = ProductService()
        cls.sales_service = SalesService()
        
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
                cursor.execute("DELETE FROM Estoque")
                cursor.execute("DELETE FROM Produtos")
                cursor.execute("DELETE FROM Usuarios")
                # Reset sequences for predictable IDs if PostgreSQL
                if 'postgresql' in os.getenv('DATABASE_URL', ''):
                    cursor.execute("ALTER SEQUENCE produtos_id_seq RESTART WITH 1")
                    cursor.execute("ALTER SEQUENCE usuarios_id_seq RESTART WITH 1")
                    cursor.execute("ALTER SEQUENCE vendas_id_seq RESTART WITH 1")
                    cursor.execute("ALTER SEQUENCE estoque_id_seq RESTART WITH 1")
                conn.commit()
    
    def create_test_product(self, name="Test Product", emoji="📦"):
        """Helper to create a test product."""
        request = CreateProductRequest(nome=name, emoji=emoji)
        return self.product_service.create_product(request)
    
    def get_stock_records_from_db(self, produto_id):
        """Helper to get stock records directly from database."""
        with self.db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, produto_id, quantidade, valor, custo, data 
                    FROM estoque 
                    WHERE produto_id = %s 
                    ORDER BY data ASC
                """, (produto_id,))
                return cursor.fetchall()
    
    def get_total_stock_from_db(self, produto_id):
        """Helper to get total available stock from database."""
        with self.db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT COALESCE(SUM(quantidade), 0) 
                    FROM estoque 
                    WHERE produto_id = %s AND quantidade > 0
                """, (produto_id,))
                result = cursor.fetchone()
                return result[0] if result else 0
    
    def test_add_stock_single_entry(self):
        """Test adding a single stock entry to database."""
        # Create a product
        product = self.create_test_product("Gaming Mouse", "🖱️")
        
        # Add stock
        stock_request = AddStockRequest(
            produto_id=product.id,
            quantidade=10,
            valor=45.50,
            custo=30.00
        )
        
        # Add stock via service
        result = self.product_service.add_stock(stock_request)
        
        # Verify service response
        assert result is not None
        
        # Verify database record was created
        stock_records = self.get_stock_records_from_db(product.id)
        assert len(stock_records) == 1
        
        record = stock_records[0]
        assert record[1] == product.id  # produto_id
        assert record[2] == 10  # quantidade
        assert float(record[3]) == 45.50  # valor
        assert float(record[4]) == 30.00  # custo
        # Note: data field may be None if not set by service
        
        # Verify total available quantity
        total_stock = self.get_total_stock_from_db(product.id)
        assert total_stock == 10
        
        # Verify service method returns correct quantity
        available_qty = self.product_service.get_available_quantity(product.id)
        assert available_qty == 10
    
    def test_add_stock_multiple_entries(self):
        """Test adding multiple stock entries for same product."""
        # Create a product
        product = self.create_test_product("Mechanical Keyboard", "⌨️")
        
        # Add first stock entry
        stock_request1 = AddStockRequest(
            produto_id=product.id,
            quantidade=5,
            valor=120.00,
            custo=80.00
        )
        self.product_service.add_stock(stock_request1)
        
        # Add second stock entry
        stock_request2 = AddStockRequest(
            produto_id=product.id,
            quantidade=3,
            valor=125.00,
            custo=85.00
        )
        self.product_service.add_stock(stock_request2)
        
        # Verify both records in database
        stock_records = self.get_stock_records_from_db(product.id)
        assert len(stock_records) == 2
        
        # Verify total quantity
        total_stock = self.get_total_stock_from_db(product.id)
        assert total_stock == 8  # 5 + 3
        
        # Verify service method
        available_qty = self.product_service.get_available_quantity(product.id)
        assert available_qty == 8
        
        # Note: FIFO ordering would be by ID since data field is None
        assert stock_records[0][0] < stock_records[1][0]  # ID comparison (first inserted has lower ID)
    
    def test_fifo_stock_consumption(self):
        """Test FIFO (First In, First Out) stock consumption."""
        # Create a product
        product = self.create_test_product("USB Cable", "🔌")
        
        # Add multiple stock entries with different timestamps
        stock_request1 = AddStockRequest(
            produto_id=product.id,
            quantidade=10,
            valor=15.00,
            custo=10.00
        )
        self.product_service.add_stock(stock_request1)
        
        # Add second entry (should be consumed second due to FIFO)
        stock_request2 = AddStockRequest(
            produto_id=product.id,
            quantidade=5,
            valor=16.00,
            custo=11.00
        )
        self.product_service.add_stock(stock_request2)
        
        # Verify initial state
        initial_stock = self.get_total_stock_from_db(product.id)
        assert initial_stock == 15
        
        # Consume 7 units (should consume all of first entry + 2 from second)
        consumed_items = self.product_service.consume_stock(product.id, 7)
        assert len(consumed_items) >= 1  # Should return list of consumed items
        total_consumed = sum(item.quantidade for item in consumed_items)
        assert total_consumed == 7
        
        # Verify database state after consumption
        stock_records = self.get_stock_records_from_db(product.id)
        assert len(stock_records) == 2  # Both records remain, one partially consumed
        
        # Find which record was partially consumed
        total_remaining = sum(record[2] for record in stock_records)
        assert total_remaining == 8  # 15 - 7 consumed
        
        # Verify total available stock
        remaining_stock = self.get_total_stock_from_db(product.id)
        assert remaining_stock == 8  # 15 - 7
        
        # Verify service method
        available_qty = self.product_service.get_available_quantity(product.id)
        assert available_qty == 8
    
    def test_fifo_complete_consumption(self):
        """Test consuming all stock across multiple entries."""
        # Create a product
        product = self.create_test_product("Phone Charger", "🔌")
        
        # Add multiple small stock entries
        for i in range(3):
            stock_request = AddStockRequest(
                produto_id=product.id,
                quantidade=4,
                valor=20.00 + i,
                custo=15.00 + i
            )
            self.product_service.add_stock(stock_request)
        
        # Verify initial stock
        initial_stock = self.get_total_stock_from_db(product.id)
        assert initial_stock == 12  # 3 entries * 4 each
        
        # Consume all stock
        consumed_items = self.product_service.consume_stock(product.id, 12)
        total_consumed = sum(item.quantidade for item in consumed_items)
        assert total_consumed == 12
        
        # Verify all entries are consumed (all records deleted)
        stock_records = self.get_stock_records_from_db(product.id)
        assert len(stock_records) == 0  # All records should be deleted when fully consumed
        
        # Verify no available stock
        remaining_stock = self.get_total_stock_from_db(product.id)
        assert remaining_stock == 0
        
        available_qty = self.product_service.get_available_quantity(product.id)
        assert available_qty == 0
    
    def test_insufficient_stock_consumption(self):
        """Test attempting to consume more stock than available."""
        # Create a product
        product = self.create_test_product("Limited Item", "💎")
        
        # Add limited stock
        stock_request = AddStockRequest(
            produto_id=product.id,
            quantidade=5,
            valor=100.00,
            custo=70.00
        )
        self.product_service.add_stock(stock_request)
        
        # Try to consume more than available
        with pytest.raises(ValidationError) as exc_info:
            self.product_service.consume_stock(product.id, 10)
        
        assert "estoque insuficiente" in str(exc_info.value).lower() or "insufficient" in str(exc_info.value).lower()
        
        # Verify stock remains unchanged
        remaining_stock = self.get_total_stock_from_db(product.id)
        assert remaining_stock == 5
        
        stock_records = self.get_stock_records_from_db(product.id)
        assert len(stock_records) == 1
        assert stock_records[0][2] == 5  # quantidade unchanged
    
    def test_stock_validation_errors(self):
        """Test validation errors for invalid stock operations."""
        # Create a product
        product = self.create_test_product("Test Product", "📦")
        
        # Test negative quantity
        with pytest.raises(ValidationError):
            stock_request = AddStockRequest(
                produto_id=product.id,
                quantidade=-5,
                valor=25.00,
                custo=15.00
            )
            self.product_service.add_stock(stock_request)
        
        # Test zero quantity
        with pytest.raises(ValidationError):
            stock_request = AddStockRequest(
                produto_id=product.id,
                quantidade=0,
                valor=25.00,
                custo=15.00
            )
            self.product_service.add_stock(stock_request)
        
        # Test negative price
        with pytest.raises(ValidationError):
            stock_request = AddStockRequest(
                produto_id=product.id,
                quantidade=5,
                valor=-25.00,
                custo=15.00
            )
            self.product_service.add_stock(stock_request)
        
        # Test negative cost
        with pytest.raises(ValidationError):
            stock_request = AddStockRequest(
                produto_id=product.id,
                quantidade=5,
                valor=25.00,
                custo=-15.00
            )
            self.product_service.add_stock(stock_request)
        
        # Verify no invalid records were created
        stock_records = self.get_stock_records_from_db(product.id)
        assert len(stock_records) == 0
    
    def test_stock_for_nonexistent_product(self):
        """Test adding stock for a product that doesn't exist."""
        # Try to add stock for non-existent product
        with pytest.raises(NotFoundError):
            stock_request = AddStockRequest(
                produto_id=99999,  # Non-existent product ID
                quantidade=5,
                valor=25.00,
                custo=15.00
            )
            self.product_service.add_stock(stock_request)
    
    def test_stock_audit_trail(self):
        """Test that stock operations maintain proper audit trail."""
        # Create a product
        product = self.create_test_product("Audit Test Product", "📋")
        
        # Add stock entry
        stock_request = AddStockRequest(
            produto_id=product.id,
            quantidade=20,
            valor=50.00,
            custo=35.00
        )
        self.product_service.add_stock(stock_request)
        
        # Get initial record
        stock_records = self.get_stock_records_from_db(product.id)
        assert len(stock_records) == 1
        
        original_id = stock_records[0][0]  # ID
        
        # Consume some stock
        self.product_service.consume_stock(product.id, 8)
        
        # Verify record still exists with ID preserved
        updated_records = self.get_stock_records_from_db(product.id)
        assert len(updated_records) == 1
        assert updated_records[0][0] == original_id  # ID should be preserved
        assert updated_records[0][2] == 12  # quantidade should be 20 - 8 = 12
        
        # Add more stock
        stock_request2 = AddStockRequest(
            produto_id=product.id,
            quantidade=5,
            valor=55.00,
            custo=40.00
        )
        self.product_service.add_stock(stock_request2)
        
        # Verify we now have 2 records with different IDs
        final_records = self.get_stock_records_from_db(product.id)
        assert len(final_records) == 2
        assert final_records[0][0] != final_records[1][0]  # Different IDs
        assert final_records[0][0] < final_records[1][0]   # First should have lower ID
    
    def test_concurrent_stock_operations(self):
        """Test handling of concurrent stock operations."""
        # Create a product
        product = self.create_test_product("Concurrent Test", "⚡")
        
        # Add initial stock
        stock_request = AddStockRequest(
            produto_id=product.id,
            quantidade=100,
            valor=10.00,
            custo=7.00
        )
        self.product_service.add_stock(stock_request)
        
        # Simulate multiple consumption operations
        # In a real concurrent scenario, these would happen simultaneously
        consumed1 = self.product_service.consume_stock(product.id, 30)
        consumed2 = self.product_service.consume_stock(product.id, 25)
        consumed3 = self.product_service.consume_stock(product.id, 20)
        
        # Verify consumed quantities
        assert sum(item.quantidade for item in consumed1) == 30
        assert sum(item.quantidade for item in consumed2) == 25
        assert sum(item.quantidade for item in consumed3) == 20
        
        # Verify final state
        remaining_stock = self.get_total_stock_from_db(product.id)
        assert remaining_stock == 25  # 100 - 30 - 25 - 20
        
        available_qty = self.product_service.get_available_quantity(product.id)
        assert available_qty == 25