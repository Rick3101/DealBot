#!/usr/bin/env python3
"""
Complete handler flow integration tests.
Tests entire conversation flows from start to finish with schema validation.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from telegram import Update, Message, User, Chat
from telegram.ext import ConversationHandler

# Import test infrastructure
from tests.mocks.schema_accurate_mock_database import get_schema_accurate_mock_db, reset_schema_mock_db

# Import handlers to test
from handlers.buy_handler import ModernBuyHandler, BUY_NAME, BUY_SELECT_PRODUCT, BUY_QUANTITY, BUY_PRICE
from handlers.login_handler import ModernLoginHandler, LOGIN_USERNAME, LOGIN_PASSWORD
from handlers.product_handler import ModernProductHandler, PRODUCT_MENU, PRODUCT_ADD_NAME, PRODUCT_ADD_EMOJI
from handlers.user_handler import ModernUserHandler

# Import services
from services.user_service import UserService
from services.product_service import ProductService
from services.sales_service import SalesService

# Import models
from models.user import CreateUserRequest, UserLevel
from models.product import CreateProductRequest


class MockTelegramUpdate:
    """Helper to create realistic Telegram update objects."""
    
    @staticmethod
    def create_message_update(text: str, chat_id: int = 12345, user_id: int = 67890):
        """Create a mock update with a text message."""
        user = User(id=user_id, first_name="Test", is_bot=False)
        chat = Chat(id=chat_id, type="private")
        message = Message(
            message_id=1,
            date=None,
            chat=chat,
            from_user=user,
            text=text
        )
        
        update = Update(update_id=1, message=message)
        return update
    
    @staticmethod
    def create_callback_update(data: str, chat_id: int = 12345, user_id: int = 67890):
        """Create a mock update with callback data."""
        user = User(id=user_id, first_name="Test", is_bot=False)
        chat = Chat(id=chat_id, type="private")
        
        # Mock callback query
        callback_query = Mock()
        callback_query.data = data
        callback_query.message = Message(
            message_id=1,
            date=None,
            chat=chat,
            from_user=user
        )
        callback_query.from_user = user
        
        update = Update(update_id=1, callback_query=callback_query)
        return update


@pytest.mark.integration
@pytest.mark.asyncio
class TestCompleteHandlerFlows:
    """Test complete conversation flows with schema validation."""
    
    def setup_method(self):
        """Set up each test with fresh mock database."""
        reset_schema_mock_db()
        self.mock_db = get_schema_accurate_mock_db()
        
        # Mock the database manager in services
        self.db_patcher = patch('database.get_db_manager')
        self.mock_db_manager = self.db_patcher.start()
        self.mock_db_manager.return_value = self.mock_db
        
        # Create services with mocked database
        self.user_service = UserService()
        self.product_service = ProductService()
        self.sales_service = SalesService()
        
        # Create handlers
        self.login_handler = ModernLoginHandler()
        self.product_handler = ModernProductHandler()
        self.buy_handler = ModernBuyHandler()
        self.user_handler = ModernUserHandler()
        
        # Mock context
        self.context = AsyncMock()
        self.context.bot = AsyncMock()
        self.context.user_data = {}
    
    def teardown_method(self):
        """Clean up after each test."""
        self.db_patcher.stop()
    
    async def test_complete_login_flow(self):
        """Test the complete login conversation flow."""
        chat_id = 12345
        
        # Step 1: Start login
        update = MockTelegramUpdate.create_message_update("/login", chat_id)
        result = await self.login_handler.login_start(update, self.context)
        assert result == LOGIN_USERNAME
        
        # Verify welcome message was sent
        self.context.bot.send_message.assert_called()
        args = self.context.bot.send_message.call_args[1]
        assert "usuário" in args['text'].lower()
        
        # Step 2: Enter username
        update = MockTelegramUpdate.create_message_update("test_user", chat_id)
        result = await self.login_handler.username_received(update, self.context)
        assert result == LOGIN_PASSWORD
        
        # Create user in database for login test
        user_request = CreateUserRequest(
            username="test_user",
            password="test_pass",
            nivel=UserLevel.ADMIN
        )
        await self.user_service.create_user(user_request)
        
        # Step 3: Enter password
        update = MockTelegramUpdate.create_message_update("test_pass", chat_id)
        result = await self.login_handler.password_received(update, self.context)
        assert result == ConversationHandler.END
        
        # Verify success message
        assert self.context.bot.send_message.call_count >= 2
    
    async def test_complete_product_creation_flow(self):
        """Test the complete product creation flow."""
        chat_id = 12345
        
        # Mock user authentication
        with patch('utils.permissions.check_permission_level', return_value=True):
            # Step 1: Start product menu
            update = MockTelegramUpdate.create_message_update("/product", chat_id)
            result = await self.product_handler.product_menu(update, self.context)
            assert result == PRODUCT_MENU
            
            # Step 2: Choose to add product
            update = MockTelegramUpdate.create_callback_update("add_product", chat_id)
            result = await self.product_handler.add_product_start(update, self.context)
            assert result == PRODUCT_ADD_NAME
            
            # Step 3: Enter product name
            update = MockTelegramUpdate.create_message_update("Test Product", chat_id)
            result = await self.product_handler.add_product_name(update, self.context)
            assert result == PRODUCT_ADD_EMOJI
            
            # Step 4: Enter product emoji
            update = MockTelegramUpdate.create_message_update("🔥", chat_id)
            result = await self.product_handler.add_product_emoji(update, self.context)
            
            # Should complete product creation
            assert result in [ConversationHandler.END, PRODUCT_MENU]
            
            # Verify product was created in database
            products = list(self.mock_db.data.get('produtos', {}).values())
            assert len(products) == 1
            assert products[0]['nome'] == "Test Product"
            assert products[0]['emoji'] == "🔥"
    
    async def test_complete_buy_flow_with_inventory_validation(self):
        """Test complete purchase flow with inventory checks."""
        chat_id = 12345
        
        # Setup: Create product and add stock
        product_request = CreateProductRequest(
            nome="Test Product",
            emoji="📦"
        )
        product = await self.product_service.create_product(product_request)
        
        # Add stock manually to database
        with self.mock_db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO estoque (produto_id, quantidade, preco, custo, quantidade_restante) VALUES (%s, %s, %s, %s, %s)",
                    (product.id, 10, 15.0, 10.0, 10)
                )
        
        # Create authenticated user
        user_request = CreateUserRequest(
            username="buyer_user",
            password="pass",
            nivel=UserLevel.ADMIN
        )
        await self.user_service.create_user(user_request)
        
        with patch('utils.permissions.check_permission_level', return_value=True), \
             patch('utils.permissions.get_authenticated_user', return_value=("buyer_user", "admin")):
            
            # Step 1: Start buy flow
            update = MockTelegramUpdate.create_message_update("/buy", chat_id)
            result = await self.buy_handler.buy_start(update, self.context)
            
            # For admin users, should skip name entry
            assert result == BUY_SELECT_PRODUCT
            
            # Step 2: Select product
            update = MockTelegramUpdate.create_callback_update(f"product_{product.id}", chat_id)
            result = await self.buy_handler.product_selected(update, self.context)
            assert result == BUY_QUANTITY
            
            # Step 3: Enter quantity
            update = MockTelegramUpdate.create_message_update("2", chat_id)
            result = await self.buy_handler.quantity_received(update, self.context)
            assert result == BUY_PRICE
            
            # Step 4: Enter price
            update = MockTelegramUpdate.create_message_update("15.50", chat_id)
            result = await self.buy_handler.price_received(update, self.context)
            assert result == ConversationHandler.END
            
            # Verify sale was created in database
            sales = list(self.mock_db.data.get('vendas', {}).values())
            assert len(sales) == 1
            assert sales[0]['comprador'] == "buyer_user"
            
            # Verify sale items were created
            items = list(self.mock_db.data.get('itensvenda', {}).values())
            assert len(items) == 1
            assert items[0]['quantidade'] == 2
            assert items[0]['valor_unitario'] == 15.50
    
    async def test_buy_flow_insufficient_stock_error(self):
        """Test buy flow properly handles insufficient stock."""
        chat_id = 12345
        
        # Setup: Create product with limited stock
        product_request = CreateProductRequest(
            nome="Limited Product",
            emoji="⚡"
        )
        product = await self.product_service.create_product(product_request)
        
        # Add minimal stock
        with self.mock_db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO estoque (produto_id, quantidade, preco, custo, quantidade_restante) VALUES (%s, %s, %s, %s, %s)",
                    (product.id, 1, 10.0, 5.0, 1)
                )
        
        with patch('utils.permissions.check_permission_level', return_value=True), \
             patch('utils.permissions.get_authenticated_user', return_value=("test_user", "admin")):
            
            # Start buy flow
            update = MockTelegramUpdate.create_message_update("/buy", chat_id)
            await self.buy_handler.buy_start(update, self.context)
            
            # Select product
            update = MockTelegramUpdate.create_callback_update(f"product_{product.id}", chat_id)
            await self.buy_handler.product_selected(update, self.context)
            
            # Try to buy more than available
            update = MockTelegramUpdate.create_message_update("5", chat_id)
            result = await self.buy_handler.quantity_received(update, self.context)
            
            # Should either ask for new quantity or show error
            # The exact behavior depends on your implementation
            assert result in [BUY_QUANTITY, ConversationHandler.END]
            
            # Should have sent an error message
            error_calls = [
                call for call in self.context.bot.send_message.call_args_list
                if 'estoque' in str(call).lower() or 'insufficient' in str(call).lower()
            ]
            assert len(error_calls) > 0
    
    async def test_user_management_flow(self):
        """Test complete user management flow."""
        chat_id = 12345
        
        with patch('utils.permissions.check_permission_level', return_value=True):
            # Step 1: Start user management
            update = MockTelegramUpdate.create_message_update("/user", chat_id)
            result = await self.user_handler.user_menu(update, self.context)
            
            # Should show user management menu
            self.context.bot.send_message.assert_called()
            
            # Step 2: Add new user
            update = MockTelegramUpdate.create_callback_update("add_user", chat_id)
            result = await self.user_handler.add_user_start(update, self.context)
            
            # Step 3: Enter username
            update = MockTelegramUpdate.create_message_update("new_user", chat_id)
            result = await self.user_handler.add_user_username(update, self.context)
            
            # Step 4: Enter password  
            update = MockTelegramUpdate.create_message_update("secure_pass", chat_id)
            result = await self.user_handler.add_user_password(update, self.context)
            
            # Verify user was created
            users = list(self.mock_db.data.get('usuarios', {}).values())
            assert len(users) == 1
            assert users[0]['username'] == "new_user"
    
    async def test_schema_validation_in_flows(self):
        """Test that schema validation catches issues during flows."""
        # This test specifically validates that our schema-accurate mock
        # catches column name issues like the data/data_venda problem
        
        chat_id = 12345
        
        # Create a product for purchase test
        product_request = CreateProductRequest(
            nome="Schema Test Product",
            emoji="🧪"
        )
        product = await self.product_service.create_product(product_request)
        
        # The schema mock should validate that queries use correct column names
        # If there's a mismatch, it should raise a psycopg2.ProgrammingError
        
        with self.mock_db.get_connection() as conn:
            with conn.cursor() as cursor:
                # This should work (correct column name)
                cursor.execute(
                    "INSERT INTO vendas (comprador) VALUES (%s) RETURNING id, comprador, data_venda",
                    ("test_buyer",)
                )
                result = cursor.fetchone()
                assert result is not None
                assert 'data_venda' in result
                
                # This should fail (incorrect column name)
                with pytest.raises(Exception) as excinfo:
                    cursor.execute(
                        "INSERT INTO vendas (comprador) VALUES (%s) RETURNING id, comprador, data",
                        ("test_buyer2",)
                    )
                
                assert 'does not exist' in str(excinfo.value)


@pytest.mark.integration
class TestHandlerFlowPerformance:
    """Test handler flow performance and resource usage."""
    
    def setup_method(self):
        """Set up performance test environment."""
        reset_schema_mock_db()
        self.mock_db = get_schema_accurate_mock_db()
    
    async def test_concurrent_buy_flows(self):
        """Test multiple concurrent buy flows don't interfere."""
        # Create multiple buy flows running simultaneously
        # This tests thread safety and database isolation
        
        tasks = []
        for i in range(5):
            chat_id = 10000 + i
            task = asyncio.create_task(self._simulate_buy_flow(chat_id, f"user_{i}"))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All flows should complete successfully
        for result in results:
            if isinstance(result, Exception):
                pytest.fail(f"Concurrent buy flow failed: {result}")
    
    async def _simulate_buy_flow(self, chat_id: int, username: str):
        """Simulate a complete buy flow for performance testing."""
        # This is a simplified version for performance testing
        # In real tests, you'd use the actual handlers
        
        with self.mock_db.get_connection() as conn:
            with conn.cursor() as cursor:
                # Simulate creating a sale
                cursor.execute(
                    "INSERT INTO vendas (comprador) VALUES (%s) RETURNING id",
                    (username,)
                )
                result = cursor.fetchone()
                assert result is not None