#!/usr/bin/env python3
"""
Real database integration tests for buy handler.
Tests the complete purchase flow with actual database operations.
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
from core.modern_service_container import initialize_services, get_container
from core.config import get_config
from handlers.buy_handler import ModernBuyHandler, BUY_NAME, BUY_SELECT_PRODUCT, BUY_QUANTITY, BUY_PRICE
from services.product_service import ProductService
from services.sales_service import SalesService
from services.user_service import UserService
from models.product import CreateProductRequest, AddStockRequest
from models.user import CreateUserRequest, UserLevel
from telegram.ext import ConversationHandler


@pytest.mark.integration
class TestBuyHandlerRealDatabase:
    """Integration tests for buy handler with real database operations."""
    
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
        cls.user_service = UserService()
        
        # Create buy handler
        cls.buy_handler = ModernBuyHandler()
    
    @classmethod
    def teardown_class(cls):
        """Clean up test database."""
        close_database()
    
    def setup_method(self):
        """Set up fresh data for each test."""
        # Clean tables in correct order
        db_manager = get_db_manager()
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM ItensVenda")
                cursor.execute("DELETE FROM Pagamentos")
                cursor.execute("DELETE FROM Vendas")
                cursor.execute("DELETE FROM Estoque")
                cursor.execute("DELETE FROM Produtos")
                cursor.execute("DELETE FROM Usuarios")
                # Reset sequences for predictable IDs
                if 'postgresql' in os.getenv('DATABASE_URL', ''):
                    cursor.execute("ALTER SEQUENCE produtos_id_seq RESTART WITH 1")
                    cursor.execute("ALTER SEQUENCE usuarios_id_seq RESTART WITH 1")
                    cursor.execute("ALTER SEQUENCE vendas_id_seq RESTART WITH 1")
                    cursor.execute("ALTER SEQUENCE estoque_id_seq RESTART WITH 1")
                conn.commit()
    
    def create_test_user(self, username="testuser", nivel="admin", chat_id=12345):
        """Helper to create a test user."""
        request = CreateUserRequest(
            username=username,
            password="testpass123",
            level=UserLevel.ADMIN if nivel == "admin" else UserLevel.USER
        )
        user = self.user_service.create_user(request)
        # Set chat_id separately if needed
        if chat_id and hasattr(user, 'chat_id'):
            user.chat_id = chat_id
        return user
    
    def create_test_product(self, name="Test Product", emoji="📦"):
        """Helper to create a test product."""
        request = CreateProductRequest(nome=name, emoji=emoji)
        product = self.product_service.create_product(request)
        
        # Add stock
        stock_request = AddStockRequest(
            produto_id=product.id,
            quantidade=10,
            valor=50.0,
            custo=30.0
        )
        self.product_service.add_stock(stock_request)
        return product
    
    def create_mock_telegram_objects(self, user_id=12345, text="", chat_id=12345):
        """Create mock Telegram objects for testing."""
        update = Mock()
        context = Mock()
        
        # Setup user data and chat data
        context.user_data = {}
        context.chat_data = {}
        
        # Mock user
        user = Mock()
        user.id = user_id
        update.effective_user = user
        
        # Mock chat
        chat = Mock()
        chat.id = chat_id
        update.effective_chat = chat
        
        # Mock message
        message = Mock()
        message.text = text
        message.chat_id = chat_id
        message.from_user = user
        message.delete = AsyncMock()
        message.reply_text = AsyncMock()
        update.message = message
        
        return update, context
    
    def test_complete_purchase_flow_admin_user(self):
        """Test complete purchase flow for admin user."""
        # Setup test data
        user = self.create_test_user("admin_user", "admin", 12345)
        product = self.create_test_product("Gaming Mouse", "🖱️")
        
        # Create mock objects
        update, context = self.create_mock_telegram_objects(user_id=12345, chat_id=12345)
        
        # Step 1: Start buy command (admin skips name entry)
        result = self.buy_handler.handle_buy_command(update, context)
        assert result == BUY_SELECT_PRODUCT
        assert 'products' in context.user_data
        
        # Step 2: Select product
        update.message.text = "1"  # Select first product
        result = self.buy_handler.handle_product_selection(update, context)
        assert result == BUY_QUANTITY
        assert context.user_data['selected_product'] == product.id
        
        # Step 3: Enter quantity
        update.message.text = "2"
        result = self.buy_handler.handle_quantity_input(update, context)
        assert result == BUY_PRICE
        assert context.user_data['quantity'] == 2
        
        # Step 4: Enter price and complete purchase
        update.message.text = "45.50"
        result = self.buy_handler.handle_price_input(update, context)
        assert result == ConversationHandler.END
        
        # Verify purchase was recorded in database
        sales = self.sales_service.get_sales_by_buyer("admin_user")
        assert len(sales) == 1
        assert sales[0].comprador == "admin_user"
        assert sales[0].valor_total == 91.0  # 2 * 45.50
        
        # Verify stock was consumed (FIFO)
        available_stock = self.product_service.get_available_quantity(product.id)
        assert available_stock == 8  # 10 - 2
    
    def test_complete_purchase_flow_owner_user(self):
        """Test complete purchase flow for owner user (can specify buyer name)."""
        # Setup test data
        owner = self.create_test_user("owner_user", "owner", 12345)
        product = self.create_test_product("Mechanical Keyboard", "⌨️")
        
        # Create mock objects
        update, context = self.create_mock_telegram_objects(user_id=12345, chat_id=12345)
        
        # Step 1: Start buy command (owner enters buyer name)
        result = self.buy_handler.handle_buy_command(update, context)
        assert result == BUY_NAME
        
        # Step 2: Enter buyer name
        update.message.text = "customer123"
        result = self.buy_handler.handle_buyer_name(update, context)
        assert result == BUY_SELECT_PRODUCT
        assert context.user_data['buyer_name'] == "customer123"
        
        # Step 3: Select product
        update.message.text = "1"
        result = self.buy_handler.handle_product_selection(update, context)
        assert result == BUY_QUANTITY
        
        # Step 4: Enter quantity
        update.message.text = "1"
        result = self.buy_handler.handle_quantity_input(update, context)
        assert result == BUY_PRICE
        
        # Step 5: Complete purchase
        update.message.text = "120.00"
        result = self.buy_handler.handle_price_input(update, context)
        assert result == ConversationHandler.END
        
        # Verify purchase was recorded with correct buyer
        sales = self.sales_service.get_sales_by_buyer("customer123")
        assert len(sales) == 1
        assert sales[0].comprador == "customer123"
        assert sales[0].valor_total == 120.0
    
    def test_insufficient_stock_handling(self):
        """Test handling of insufficient stock during purchase."""
        # Setup test data with limited stock
        user = self.create_test_user("test_user", "admin", 12345)
        product = self.create_test_product("Limited Item", "💎")
        
        # Create mock objects
        update, context = self.create_mock_telegram_objects(user_id=12345)
        
        # Start purchase flow
        self.buy_handler.handle_buy_command(update, context)
        
        # Select product
        update.message.text = "1"
        self.buy_handler.handle_product_selection(update, context)
        
        # Try to buy more than available (we have 10, try to buy 15)
        update.message.text = "15"
        result = self.buy_handler.handle_quantity_input(update, context)
        
        # Should stay in quantity state due to insufficient stock
        assert result == BUY_QUANTITY
        # Should have sent error message about insufficient stock
        update.message.reply_text.assert_called()
        error_message = update.message.reply_text.call_args[0][0]
        assert "estoque insuficiente" in error_message.lower() or "insufficient" in error_message.lower()
    
    def test_secret_menu_product_access(self):
        """Test access to hidden products via secret menu."""
        # Setup hidden product (with special emoji)
        user = self.create_test_user("test_user", "admin", 12345)
        hidden_product = self.create_test_product("Secret Item", "🧪")
        
        # Create mock objects
        update, context = self.create_mock_telegram_objects(user_id=12345)
        
        # Start with secret phrase
        update.message.text = get_config().services.secret_menu_phrase
        result = self.buy_handler.handle_buy_command(update, context)
        
        # Should proceed to product selection with hidden products visible
        assert result == BUY_SELECT_PRODUCT
        assert 'products' in context.user_data
        assert 'show_hidden' in context.user_data
        assert context.user_data['show_hidden'] is True
    
    def test_purchase_validation_errors(self):
        """Test various validation errors during purchase."""
        user = self.create_test_user("test_user", "admin", 12345)
        product = self.create_test_product("Test Product", "📦")
        
        update, context = self.create_mock_telegram_objects(user_id=12345)
        
        # Start purchase
        self.buy_handler.handle_buy_command(update, context)
        update.message.text = "1"
        self.buy_handler.handle_product_selection(update, context)
        
        # Test invalid quantity
        update.message.text = "invalid_quantity"
        result = self.buy_handler.handle_quantity_input(update, context)
        assert result == BUY_QUANTITY  # Should stay in quantity state
        
        # Test valid quantity
        update.message.text = "2"
        result = self.buy_handler.handle_quantity_input(update, context)
        assert result == BUY_PRICE
        
        # Test invalid price
        update.message.text = "invalid_price"
        result = self.buy_handler.handle_price_input(update, context)
        assert result == BUY_PRICE  # Should stay in price state
    
    def test_database_transaction_rollback(self):
        """Test that database transactions are properly rolled back on errors."""
        user = self.create_test_user("test_user", "admin", 12345)
        product = self.create_test_product("Test Product", "📦")
        
        # Get initial stock count
        initial_stock = self.product_service.get_available_quantity(product.id)
        
        # Attempt purchase that will fail (simulate by corrupting data)
        update, context = self.create_mock_telegram_objects(user_id=12345)
        
        # Start normal flow
        self.buy_handler.handle_buy_command(update, context)
        update.message.text = "1"
        self.buy_handler.handle_product_selection(update, context)
        update.message.text = "2"
        self.buy_handler.handle_quantity_input(update, context)
        
        # Simulate an error condition by setting invalid context data
        context.user_data['selected_product'] = 99999  # Non-existent product
        update.message.text = "50.00"
        
        # This should handle the error gracefully
        result = self.buy_handler.handle_price_input(update, context)
        
        # Stock should remain unchanged due to rollback
        final_stock = self.product_service.get_available_quantity(product.id)
        assert final_stock == initial_stock
    
    def test_multiple_products_inventory_management(self):
        """Test inventory management with multiple products and FIFO."""
        user = self.create_test_user("test_user", "admin", 12345)
        
        # Create product with multiple stock entries
        product = self.create_test_product("Multi-Stock Item", "📚")
        
        # Add additional stock with different prices (FIFO test)
        stock_request2 = AddStockRequest(
            produto_id=product.id,
            quantidade=5,
            valor=60.0,
            custo=40.0
        )
        self.product_service.add_stock(stock_request2)
        
        # Total stock should be 15 (10 + 5)
        total_stock = self.product_service.get_available_quantity(product.id)
        assert total_stock == 15
        
        # Make purchase that consumes from first stock entry
        update, context = self.create_mock_telegram_objects(user_id=12345)
        
        self.buy_handler.handle_buy_command(update, context)
        update.message.text = "1"
        self.buy_handler.handle_product_selection(update, context)
        update.message.text = "8"  # Consume most of first stock entry
        self.buy_handler.handle_quantity_input(update, context)
        update.message.text = "55.00"
        self.buy_handler.handle_price_input(update, context)
        
        # Should have 7 remaining (15 - 8)
        remaining_stock = self.product_service.get_available_quantity(product.id)
        assert remaining_stock == 7
        
        # Verify sale was recorded
        sales = self.sales_service.get_sales_by_buyer("test_user")
        assert len(sales) == 1
        assert sales[0].valor_total == 440.0  # 8 * 55.00