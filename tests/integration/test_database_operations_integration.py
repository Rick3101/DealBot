#!/usr/bin/env python3
"""
Comprehensive test suite for database operations.
Tests critical business logic paths to catch issues early.
"""

import os
import pytest
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Import test dependencies
import tempfile
from database import initialize_database, get_db_manager, close_database
from database.schema import initialize_schema
from services.product_service import ProductService
from services.sales_service import SalesService
from services.user_service import UserService
from services.handler_business_service import HandlerBusinessService
from models.product import CreateProductRequest, AddStockRequest
from models.sale import CreateSaleRequest, CreateSaleItemRequest
from models.user import CreateUserRequest, UserLevel
from models.handler_models import PurchaseRequest, ProductSelectionRequest


class TestDatabaseOperations:
    """Test suite for database operations."""
    
    @classmethod
    def setup_class(cls):
        """Set up test database."""
        # Use test database URL or in-memory database for testing
        test_db_url = os.getenv('TEST_DATABASE_URL', os.getenv('DATABASE_URL'))
        if not test_db_url:
            pytest.skip("No database URL available for testing")
        
        # Initialize test database
        initialize_database(database_url=test_db_url)
        initialize_schema()
        
        # Initialize service container
        from core.modern_service_container import initialize_services
        initialize_services({})
        
        # Initialize services
        cls.product_service = ProductService()
        cls.sales_service = SalesService()
        cls.user_service = UserService()
        cls.business_service = HandlerBusinessService()
    
    @classmethod
    def teardown_class(cls):
        """Clean up test database."""
        close_database()
    
    def setup_method(self):
        """Set up fresh data for each test."""
        # Clean tables (in correct order due to foreign keys)
        db_manager = get_db_manager()
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM ItensVenda")
                cursor.execute("DELETE FROM Pagamentos") 
                cursor.execute("DELETE FROM Vendas")
                cursor.execute("DELETE FROM Estoque")
                cursor.execute("DELETE FROM Produtos")
                cursor.execute("DELETE FROM Usuarios")
                # Reset sequences to start from 1 for predictable IDs
                cursor.execute("ALTER SEQUENCE produtos_id_seq RESTART WITH 1")
                cursor.execute("ALTER SEQUENCE usuarios_id_seq RESTART WITH 1")
                cursor.execute("ALTER SEQUENCE vendas_id_seq RESTART WITH 1")
                cursor.execute("ALTER SEQUENCE estoque_id_seq RESTART WITH 1")
                conn.commit()
    
    def test_database_connection(self):
        """Test basic database connectivity."""
        db_manager = get_db_manager()
        assert db_manager is not None
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                assert result[0] == 1
    
    def test_create_product(self):
        """Test product creation."""
        request = CreateProductRequest(
            nome="Test Product",
            emoji="📦"
        )
        
        product = self.product_service.create_product(request)
        
        assert product.id is not None
        assert product.nome == "Test Product"
        assert product.emoji == "📦"
    
    def test_add_stock(self):
        """Test adding stock to product."""
        # Create product first
        product_request = CreateProductRequest(nome="Stock Test", emoji="📊")
        product = self.product_service.create_product(product_request)
        
        # Add stock
        stock_request = AddStockRequest(
            produto_id=product.id,
            quantidade=10,
            valor=100.0,
            custo=50.0
        )
        
        stock_item = self.product_service.add_stock(stock_request)
        
        assert stock_item.produto_id == product.id
        assert stock_item.quantidade == 10
        assert stock_item.valor == 100.0
        assert stock_item.custo == 50.0
    
    def test_get_available_quantity(self):
        """Test getting available stock quantity."""
        # Create product and add stock
        product_request = CreateProductRequest(nome="Quantity Test", emoji="🔢")
        product = self.product_service.create_product(product_request)
        
        stock_request = AddStockRequest(
            produto_id=product.id,
            quantidade=25,
            valor=200.0,
            custo=100.0
        )
        self.product_service.add_stock(stock_request)
        
        # Check available quantity
        available = self.product_service.get_available_quantity(product.id)
        assert available == 25
    
    def test_consume_stock_fifo(self):
        """Test FIFO stock consumption."""
        # Create product
        product_request = CreateProductRequest(nome="FIFO Test", emoji="📉")
        product = self.product_service.create_product(product_request)
        
        # Add multiple stock entries
        stock1 = AddStockRequest(produto_id=product.id, quantidade=10, valor=100.0, custo=50.0)
        stock2 = AddStockRequest(produto_id=product.id, quantidade=15, valor=120.0, custo=60.0)
        
        self.product_service.add_stock(stock1)
        self.product_service.add_stock(stock2)
        
        # Initial total: 25
        assert self.product_service.get_available_quantity(product.id) == 25
        
        # Consume 12 (should consume all of first batch + 2 from second)
        consumed = self.product_service.consume_stock(product.id, 12)
        
        # Check remaining quantity
        remaining = self.product_service.get_available_quantity(product.id)
        assert remaining == 13  # 25 - 12 = 13
        
        # Verify FIFO behavior by checking consumed items
        assert len(consumed) == 2  # Should have touched both stock entries
        assert consumed[0].quantidade == 10  # First entry fully consumed
        assert consumed[1].quantidade == 2   # Second entry partially consumed
    
    def test_create_user(self):
        """Test user creation."""
        request = CreateUserRequest(
            username="testuser",
            password="testpass",
            level=UserLevel.USER
        )
        
        user = self.user_service.create_user(request)
        
        assert user.id is not None
        assert user.username == "testuser"
        assert user.level == UserLevel.USER
    
    def test_create_sale(self):
        """Test sale creation."""
        # Create product with stock
        product_request = CreateProductRequest(nome="Sale Test", emoji="💰")
        product = self.product_service.create_product(product_request)
        
        stock_request = AddStockRequest(
            produto_id=product.id,
            quantidade=20,
            valor=150.0,
            custo=75.0
        )
        self.product_service.add_stock(stock_request)
        
        # Create sale items
        sale_items = [
            CreateSaleItemRequest(
                produto_id=product.id,
                quantidade=5,
                valor_unitario=150.0
            )
        ]
        
        # Create sale
        sale_request = CreateSaleRequest(
            comprador="Test Buyer",
            items=sale_items
        )
        
        sale = self.sales_service.create_sale(sale_request)
        
        assert sale.id is not None
        assert sale.comprador == "Test Buyer"
        assert len(sale.items) == 1
        assert sale.items[0].quantidade == 5
        assert sale.items[0].valor_unitario == 150.0
    
    def test_purchase_flow_end_to_end(self):
        """Test complete purchase flow through business service."""
        # Create product with stock
        product_request = CreateProductRequest(nome="Purchase Test", emoji="🛒")
        product = self.product_service.create_product(product_request)
        
        stock_request = AddStockRequest(
            produto_id=product.id,
            quantidade=30,
            valor=200.0,
            custo=100.0
        )
        self.product_service.add_stock(stock_request)
        
        # Create purchase request
        purchase_items = [
            ProductSelectionRequest(
                product_id=product.id,
                quantity=8,
                custom_price=200.0
            )
        ]
        
        purchase_request = PurchaseRequest(
            buyer_name="Test Customer",
            items=purchase_items,
            total_amount=1600.0,  # 8 * 200
            chat_id=12345
        )
        
        # Process purchase
        response = self.business_service.process_purchase(purchase_request)
        
        # Verify success
        assert response.success == True
        assert response.sale_id is not None
        assert response.total_amount == 1600.0
        assert "sucesso" in response.message.lower()
        
        # Verify stock was consumed
        remaining_stock = self.product_service.get_available_quantity(product.id)
        assert remaining_stock == 22  # 30 - 8 = 22
    
    def test_insufficient_stock_error(self):
        """Test error handling for insufficient stock."""
        # Create product with limited stock
        product_request = CreateProductRequest(nome="Limited Stock", emoji="⚠️")
        product = self.product_service.create_product(product_request)
        
        stock_request = AddStockRequest(
            produto_id=product.id,
            quantidade=5,
            valor=100.0,
            custo=50.0
        )
        self.product_service.add_stock(stock_request)
        
        # Try to purchase more than available
        purchase_items = [
            ProductSelectionRequest(
                product_id=product.id,
                quantity=10,  # More than the 5 available
                custom_price=100.0
            )
        ]
        
        purchase_request = PurchaseRequest(
            buyer_name="Greedy Customer",
            items=purchase_items,
            total_amount=1000.0,
            chat_id=12345
        )
        
        # Process purchase - should fail
        response = self.business_service.process_purchase(purchase_request)
        
        assert response.success == False
        assert "estoque insuficiente" in response.message.lower()
        assert len(response.warnings) > 0
        
        # Verify no stock was consumed
        remaining_stock = self.product_service.get_available_quantity(product.id)
        assert remaining_stock == 5  # Should be unchanged
    
    def test_multiple_products_purchase(self):
        """Test purchasing multiple different products."""
        # Create two products with stock
        product1_request = CreateProductRequest(nome="Product 1", emoji="1️⃣")
        product1 = self.product_service.create_product(product1_request)
        
        product2_request = CreateProductRequest(nome="Product 2", emoji="2️⃣")
        product2 = self.product_service.create_product(product2_request)
        
        # Add stock to both
        stock1_request = AddStockRequest(produto_id=product1.id, quantidade=15, valor=100.0, custo=50.0)
        stock2_request = AddStockRequest(produto_id=product2.id, quantidade=20, valor=200.0, custo=100.0)
        
        self.product_service.add_stock(stock1_request)
        self.product_service.add_stock(stock2_request)
        
        # Create purchase with both products
        purchase_items = [
            ProductSelectionRequest(product_id=product1.id, quantity=3, custom_price=100.0),
            ProductSelectionRequest(product_id=product2.id, quantity=2, custom_price=200.0)
        ]
        
        purchase_request = PurchaseRequest(
            buyer_name="Multi Customer",
            items=purchase_items,
            total_amount=700.0,  # (3*100) + (2*200)
            chat_id=12345
        )
        
        # Process purchase
        response = self.business_service.process_purchase(purchase_request)
        
        assert response.success == True
        
        # Verify both stocks were consumed correctly
        remaining1 = self.product_service.get_available_quantity(product1.id)
        remaining2 = self.product_service.get_available_quantity(product2.id)
        
        assert remaining1 == 12  # 15 - 3
        assert remaining2 == 18  # 20 - 2


if __name__ == "__main__":
    # Run tests if called directly
    print("Running database operation tests...")
    
    # Create test instance
    test_instance = TestDatabaseOperations()
    
    try:
        # Setup
        test_instance.setup_class()
        print("[OK] Test setup complete")
        
        # Run individual tests
        test_methods = [
            test_instance.test_database_connection,
            test_instance.test_create_product,
            test_instance.test_add_stock,
            test_instance.test_get_available_quantity,
            test_instance.test_consume_stock_fifo,
            test_instance.test_create_user,
            test_instance.test_create_sale,
            test_instance.test_purchase_flow_end_to_end,
            test_instance.test_insufficient_stock_error,
            test_instance.test_multiple_products_purchase,
        ]
        
        passed = 0
        failed = 0
        
        for test_method in test_methods:
            try:
                test_instance.setup_method()  # Clean slate for each test
                test_method()
                print(f"[OK] {test_method.__name__}")
                passed += 1
            except Exception as e:
                print(f"[FAIL] {test_method.__name__}: {e}")
                failed += 1
        
        print(f"\nTest Results: {passed} passed, {failed} failed")
        
        if failed == 0:
            print("SUCCESS: All tests passed!")
        else:
            print("ERROR: Some tests failed. Check the errors above.")
            
    finally:
        # Cleanup
        test_instance.teardown_class()
        print("[OK] Test cleanup complete")