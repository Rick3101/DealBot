#!/usr/bin/env python3
"""
Complete handler flow tests for all handlers in the system.
Tests entire conversation flows from start to finish with error scenarios.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from telegram import Update, Message, User, Chat, CallbackQuery
from telegram.ext import ConversationHandler
from models.user import UserLevel

# Import test infrastructure
from tests.mocks.schema_accurate_mock_database import get_schema_accurate_mock_db, reset_schema_mock_db

# Import all handlers
from handlers.buy_handler import ModernBuyHandler, BUY_NAME, BUY_SELECT_PRODUCT, BUY_QUANTITY, BUY_PRICE
from handlers.login_handler import ModernLoginHandler, LOGIN_USERNAME, LOGIN_PASSWORD  
from handlers.product_handler import ModernProductHandler, PRODUCT_MENU, PRODUCT_ADD_NAME, PRODUCT_ADD_EMOJI, PRODUCT_ADD_MEDIA_CONFIRM, PRODUCT_ADD_MEDIA, PRODUCT_EDIT_SELECT, PRODUCT_EDIT_PROPERTY, PRODUCT_EDIT_NEW_VALUE
from handlers.user_handler import ModernUserHandler, USER_MENU, USER_ADD_USERNAME, USER_ADD_PASSWORD, USER_REMOVE_SELECT, USER_EDIT_SELECT, USER_EDIT_PROPERTY, USER_EDIT_VALUE
from handlers.estoque_handler import ModernEstoqueHandler, ESTOQUE_MENU, ESTOQUE_ADD_SELECT, ESTOQUE_ADD_VALUES, ESTOQUE_VIEW
from handlers.pagamento_handler import ModernPagamentoHandler, PAGAMENTO_MENU, PAGAMENTO_VALOR
from handlers.relatorios_handler import ModernRelatoriosHandler, RELATORIO_MENU, RELATORIO_DIVIDA_NOME
from handlers.smartcontract_handler import ModernSmartContractHandler, SMARTCONTRACT_MENU, SMARTCONTRACT_TRANSACTION_DESC
from handlers.start_handler import ModernStartHandler
from handlers.lista_produtos_handler import ModernListaProdutosHandler
from handlers.commands_handler import ModernCommandsHandler

# Import services
from services.user_service import UserService
from services.product_service import ProductService  
from services.sales_service import SalesService
from services.smartcontract_service import SmartContractService

# Import models
from models.user import CreateUserRequest, UserLevel
from models.product import CreateProductRequest, AddStockRequest


class MockTelegramObjects:
    """Helper to create realistic Telegram objects for testing."""
    
    @staticmethod
    def create_update(text: str = None, callback_data: str = None, chat_id: int = 12345, user_id: int = 67890):
        """Create a mock update with message or callback."""
        user = User(id=user_id, first_name="Test", is_bot=False)
        chat = Chat(id=chat_id, type="private")
        
        if callback_data:
            # Create callback query update
            callback_query = Mock(spec=CallbackQuery)
            callback_query.data = callback_data
            callback_query.from_user = user
            callback_query.message = Message(message_id=1, date=None, chat=chat, from_user=user)
            callback_query.answer = AsyncMock()
            callback_query.edit_message_text = AsyncMock()
            
            update = Update(update_id=1, callback_query=callback_query)
        else:
            # Create message update
            message = Message(
                message_id=1,
                date=None,
                chat=chat,
                from_user=user,
                text=text or "/test"
            )
            update = Update(update_id=1, message=message)
            
        return update
    
    @staticmethod
    def create_context():
        """Create a mock context."""
        context = AsyncMock()
        context.bot = AsyncMock()
        context.user_data = {}
        context.chat_data = {}
        return context


@pytest.mark.handler_flows
@pytest.mark.asyncio
class TestAllHandlerFlows:
    """Test complete conversation flows for all handlers."""
    
    def setup_method(self):
        """Set up each test with fresh environment."""
        reset_schema_mock_db()
        self.mock_db = get_schema_accurate_mock_db()
        
        # Mock database manager and initialize database
        self.db_patcher = patch('database.get_db_manager')
        self.mock_db_manager = self.db_patcher.start()
        self.mock_db_manager.return_value = self.mock_db
        
        # Mock database initialization to prevent real database calls
        self.init_db_patcher = patch('database.initialize_database')
        self.mock_init_db = self.init_db_patcher.start()
        
        # Mock service-level database calls
        self.service_db_patcher = patch('services.base_service.get_db_manager')
        self.mock_service_db = self.service_db_patcher.start()
        self.mock_service_db.return_value = self.mock_db
        
        # Mock smartcontract service database calls
        self.smartcontract_db_patcher = patch('services.smartcontract_service.get_db_manager')
        self.mock_smartcontract_db = self.smartcontract_db_patcher.start()
        self.mock_smartcontract_db.return_value = self.mock_db
        
        # Create services with mocked database
        self.user_service = UserService()
        self.product_service = ProductService()
        self.sales_service = SalesService()
        self.smartcontract_service = SmartContractService()
        
        # Create all handlers
        self.login_handler = ModernLoginHandler()
        self.product_handler = ModernProductHandler()
        self.buy_handler = ModernBuyHandler()
        self.user_handler = ModernUserHandler()
        self.estoque_handler = ModernEstoqueHandler()
        self.pagamento_handler = ModernPagamentoHandler()
        self.relatorios_handler = ModernRelatoriosHandler()
        self.smartcontract_handler = ModernSmartContractHandler()
        self.start_handler = ModernStartHandler()
        self.lista_produtos_handler = ModernListaProdutosHandler()
        self.commands_handler = ModernCommandsHandler()
        
        # Mock context
        self.context = MockTelegramObjects.create_context()
    
    def teardown_method(self):
        """Clean up after each test."""
        self.db_patcher.stop()
        self.init_db_patcher.stop()
        self.service_db_patcher.stop()
        self.smartcontract_db_patcher.stop()
    
    # ===== LOGIN HANDLER TESTS =====
    
    async def test_login_handler_complete_flow(self):
        """Test complete login flow."""
        chat_id = 12345
        
        # Create user for login test
        user_request = CreateUserRequest(
            username="test_user",
            password="test_pass",
            nivel=UserLevel.ADMIN
        )
        await self.user_service.create_user(user_request)
        
        # Step 1: Start login
        update = MockTelegramObjects.create_update("/login", chat_id=chat_id)
        result = await self.login_handler.login_start(update, self.context)
        assert result == LOGIN_USERNAME
        
        # Step 2: Enter username
        update = MockTelegramObjects.create_update("test_user", chat_id=chat_id)
        result = await self.login_handler.username_received(update, self.context)
        assert result == LOGIN_PASSWORD
        
        # Step 3: Enter password
        update = MockTelegramObjects.create_update("test_pass", chat_id=chat_id)
        result = await self.login_handler.password_received(update, self.context)
        assert result == ConversationHandler.END
    
    async def test_login_handler_invalid_credentials(self):
        """Test login with invalid credentials."""
        chat_id = 12345
        
        # Step 1: Start login
        update = MockTelegramObjects.create_update("/login", chat_id=chat_id)
        await self.login_handler.login_start(update, self.context)
        
        # Step 2: Enter invalid username
        update = MockTelegramObjects.create_update("invalid_user", chat_id=chat_id)
        result = await self.login_handler.username_received(update, self.context)
        # Should either retry or end conversation
        assert result in [LOGIN_PASSWORD, ConversationHandler.END]
    
    # ===== PRODUCT HANDLER TESTS =====
    
    async def test_product_handler_add_product_flow(self):
        """Test complete product addition flow."""
        chat_id = 12345
        
        with patch('utils.permissions.check_permission_level', return_value=True):
            # Step 1: Start product menu
            update = MockTelegramObjects.create_update("/product", chat_id=chat_id)
            result = await self.product_handler.start_product(update, self.context)
            assert result == PRODUCT_MENU
            
            # Step 2: Add product
            update = MockTelegramObjects.create_update(callback_data="add_product", chat_id=chat_id)
            result = await self.product_handler.product_menu_selection(update, self.context)
            assert result == PRODUCT_ADD_NAME
            
            # Step 3: Enter name
            update = MockTelegramObjects.create_update("Test Product", chat_id=chat_id)
            result = await self.product_handler.product_add_name(update, self.context)
            assert result == PRODUCT_ADD_EMOJI
            
            # Step 4: Enter emoji
            update = MockTelegramObjects.create_update("🔥", chat_id=chat_id)
            result = await self.product_handler.product_add_emoji(update, self.context)
            
            # Should complete or ask for media
            assert result in [ConversationHandler.END, PRODUCT_MENU, PRODUCT_ADD_MEDIA_CONFIRM]
    
    async def test_product_handler_edit_product_flow(self):
        """Test product editing flow - focusing on conversation states."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch.object(self.product_service, 'get_all_products', return_value=[Mock(id=1, nome="Test Product", emoji="📝")]), \
             patch('core.modern_service_container.get_user_service', return_value=self.user_service), \
             patch('core.modern_service_container.get_product_service', return_value=self.product_service):
            
            # Start product menu
            update = MockTelegramObjects.create_update("/product", chat_id=chat_id)
            result = await self.product_handler.start_product(update, self.context)
            assert result == PRODUCT_MENU
            
            # Choose edit product
            update = MockTelegramObjects.create_update(callback_data="edit_product", chat_id=chat_id)
            result = await self.product_handler.product_menu_selection(update, self.context)
            assert result == PRODUCT_EDIT_SELECT
            
            # Select product to edit
            update = MockTelegramObjects.create_update(callback_data="edit_1", chat_id=chat_id)
            result = await self.product_handler.product_edit_select(update, self.context)
            assert result == PRODUCT_EDIT_PROPERTY
    
    # ===== USER HANDLER TESTS =====
    
    async def test_user_handler_add_user_flow(self):
        """Test complete user addition flow."""
        chat_id = 12345
        
        with patch('utils.permissions.check_permission_level', return_value=True):
            # Step 1: Start user menu
            update = MockTelegramObjects.create_update("/user", chat_id=chat_id)
            result = await self.user_handler.user_menu(update, self.context)
            assert result == USER_MENU
            
            # Step 2: Add user
            update = MockTelegramObjects.create_update(callback_data="add_user", chat_id=chat_id)
            result = await self.user_handler.add_user_start(update, self.context)
            assert result == USER_ADD_USERNAME
            
            # Step 3: Enter username
            update = MockTelegramObjects.create_update("new_user", chat_id=chat_id)
            result = await self.user_handler.add_user_username(update, self.context)
            assert result == USER_ADD_PASSWORD
            
            # Step 4: Enter password
            update = MockTelegramObjects.create_update("secure_pass", chat_id=chat_id)
            result = await self.user_handler.add_user_password(update, self.context)
            assert result in [ConversationHandler.END, USER_MENU]
    
    async def test_user_handler_edit_user_flow(self):
        """Test user editing flow."""
        chat_id = 12345
        
        # Create user first
        user_request = CreateUserRequest(
            username="edit_user",
            password="old_pass",
            nivel=UserLevel.USER
        )
        await self.user_service.create_user(user_request)
        
        with patch('utils.permissions.check_permission_level', return_value=True):
            # Start user menu
            update = MockTelegramObjects.create_update("/user", chat_id=chat_id)
            await self.user_handler.user_menu(update, self.context)
            
            # Choose edit user
            update = MockTelegramObjects.create_update(callback_data="edit_user", chat_id=chat_id)
            result = await self.user_handler.edit_user_start(update, self.context)
            assert result == USER_EDIT_SELECT
    
    # ===== ESTOQUE HANDLER TESTS =====
    
    async def test_estoque_handler_add_stock_flow(self):
        """Test complete stock addition flow."""
        chat_id = 12345
        
        # Create product first
        product_request = CreateProductRequest(nome="Stock Product", emoji="📦")
        product = await self.product_service.create_product(product_request)
        
        with patch('utils.permissions.check_permission_level', return_value=True):
            # Step 1: Start estoque menu
            update = MockTelegramObjects.create_update("/estoque", chat_id=chat_id)
            result = await self.estoque_handler.estoque_menu(update, self.context)
            assert result == ESTOQUE_MENU
            
            # Step 2: Choose add stock
            update = MockTelegramObjects.create_update(callback_data="add_stock", chat_id=chat_id)
            result = await self.estoque_handler.add_stock_start(update, self.context)
            assert result == ESTOQUE_ADD_SELECT
            
            # Step 3: Select product
            update = MockTelegramObjects.create_update(callback_data=f"stock_{product.id}", chat_id=chat_id)
            result = await self.estoque_handler.add_stock_select_product(update, self.context)
            assert result == ESTOQUE_ADD_VALUES
            
            # Step 4: Enter stock values (quantity / price / cost)
            update = MockTelegramObjects.create_update("10 / 15.50 / 10.00", chat_id=chat_id)
            result = await self.estoque_handler.add_stock_values(update, self.context)
            assert result in [ConversationHandler.END, ESTOQUE_MENU]
    
    async def test_estoque_handler_view_stock_flow(self):
        """Test stock viewing flow."""
        chat_id = 12345
        
        with patch('utils.permissions.check_permission_level', return_value=True):
            # Start estoque menu
            update = MockTelegramObjects.create_update("/estoque", chat_id=chat_id)
            await self.estoque_handler.estoque_menu(update, self.context)
            
            # Choose view stock
            update = MockTelegramObjects.create_update(callback_data="view_stock", chat_id=chat_id)
            result = await self.estoque_handler.view_stock(update, self.context)
            assert result in [ConversationHandler.END, ESTOQUE_MENU]
    
    # ===== PAGAMENTO HANDLER TESTS =====
    
    async def test_pagamento_handler_payment_flow(self):
        """Test complete payment flow."""
        chat_id = 12345
        
        # Create a sale with debt first
        product_request = CreateProductRequest(nome="Payment Product", emoji="💰")
        product = await self.product_service.create_product(product_request)
        
        with patch('utils.permissions.check_permission_level', return_value=True), \
             patch('utils.permissions.get_authenticated_user', return_value=("test_buyer", "admin")):
            
            # Create sale first (this creates debt)
            # ... (would need to create sale via buy handler or directly)
            
            # Step 1: Start payment
            update = MockTelegramObjects.create_update("/pagar", chat_id=chat_id)
            result = await self.pagamento_handler.pagamento_start(update, self.context)
            assert result == PAGAMENTO_VALOR
            
            # Step 2: Enter payment amount
            update = MockTelegramObjects.create_update("50.00", chat_id=chat_id)
            result = await self.pagamento_handler.pagamento_valor(update, self.context)
            assert result == ConversationHandler.END
    
    # ===== RELATORIOS HANDLER TESTS =====
    
    async def test_relatorios_handler_sales_report_flow(self):
        """Test sales report generation flow."""
        chat_id = 12345
        
        with patch('utils.permissions.check_permission_level', return_value=True):
            # Step 1: Start relatorios menu
            update = MockTelegramObjects.create_update("/relatorios", chat_id=chat_id)
            result = await self.relatorios_handler.relatorio_menu(update, self.context)
            assert result == RELATORIO_MENU
            
            # Step 2: Choose sales report
            update = MockTelegramObjects.create_update(callback_data="vendas", chat_id=chat_id)
            result = await self.relatorios_handler.relatorio_vendas(update, self.context)
            assert result in [ConversationHandler.END, RELATORIO_MENU]
    
    async def test_relatorios_handler_debt_report_flow(self):
        """Test debt report generation flow."""
        chat_id = 12345
        
        with patch('utils.permissions.check_permission_level', return_value=True):
            # Start relatorios menu
            update = MockTelegramObjects.create_update("/relatorios", chat_id=chat_id)
            await self.relatorios_handler.relatorio_menu(update, self.context)
            
            # Choose debt report
            update = MockTelegramObjects.create_update(callback_data="dividas", chat_id=chat_id)
            result = await self.relatorios_handler.relatorio_dividas_start(update, self.context)
            assert result == RELATORIO_DIVIDA_NOME
            
            # Enter buyer name
            update = MockTelegramObjects.create_update("test_buyer", chat_id=chat_id)
            result = await self.relatorios_handler.relatorio_dividas_nome(update, self.context)
            assert result == ConversationHandler.END
    
    # ===== SMARTCONTRACT HANDLER TESTS =====
    
    async def test_smartcontract_handler_create_contract_flow(self):
        """Test smart contract creation flow."""
        chat_id = 12345
        
        with patch('utils.permissions.check_permission_level', return_value=True):
            # Create contract directly (non-conversation)
            update = MockTelegramObjects.create_update("/smartcontract TEST123", chat_id=chat_id)
            result = await self.smartcontract_handler.create_contract(update, self.context)
            # Should complete immediately
            assert result in [None, ConversationHandler.END]
    
    async def test_smartcontract_handler_transaction_flow(self):
        """Test smart contract transaction flow."""
        chat_id = 12345
        
        # Create contract first
        with self.mock_db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO smartcontracts (codigo, criador_chat_id) VALUES (%s, %s) RETURNING id",
                    ("TEST123", chat_id)
                )
                contract = cursor.fetchone()
        
        with patch('utils.permissions.check_permission_level', return_value=True):
            # Step 1: Start transaction menu
            update = MockTelegramObjects.create_update("/transacao", chat_id=chat_id)
            result = await self.smartcontract_handler.transaction_menu(update, self.context)
            assert result == SMARTCONTRACT_MENU
            
            # Step 2: Enter transaction description
            update = MockTelegramObjects.create_update("Test transaction", chat_id=chat_id)
            result = await self.smartcontract_handler.transaction_description(update, self.context)
            assert result in [ConversationHandler.END, SMARTCONTRACT_MENU]
    
    # ===== SIMPLE HANDLER TESTS =====
    
    async def test_start_handler_flow(self):
        """Test start handler flow."""
        chat_id = 12345
        
        update = MockTelegramObjects.create_update("/start", chat_id=chat_id)
        result = await self.start_handler.start(update, self.context)
        
        # Should send welcome message
        self.context.bot.send_message.assert_called()
        assert result in [None, ConversationHandler.END]
    
    async def test_lista_produtos_handler_flow(self):
        """Test product listing handler flow."""
        chat_id = 12345
        
        # Create some products first
        product1 = await self.product_service.create_product(
            CreateProductRequest(nome="Product 1", emoji="🔥")
        )
        product2 = await self.product_service.create_product(
            CreateProductRequest(nome="Product 2", emoji="💎")
        )
        
        with patch('utils.permissions.check_permission_level', return_value=True):
            update = MockTelegramObjects.create_update("/lista_produtos", chat_id=chat_id)
            result = await self.lista_produtos_handler.lista_produtos(update, self.context)
            
            # Should send product list
            self.context.bot.send_message.assert_called()
            assert result in [None, ConversationHandler.END]
    
    async def test_commands_handler_flow(self):
        """Test commands handler flow."""
        chat_id = 12345
        
        with patch('utils.permissions.check_permission_level', return_value=True):
            update = MockTelegramObjects.create_update("/commands", chat_id=chat_id)
            result = await self.commands_handler.commands(update, self.context)
            
            # Should send commands list
            self.context.bot.send_message.assert_called()
            assert result in [None, ConversationHandler.END]


@pytest.mark.handler_flows
@pytest.mark.asyncio
class TestHandlerErrorScenarios:
    """Test error scenarios and edge cases for all handlers."""
    
    def setup_method(self):
        """Set up test environment."""
        reset_schema_mock_db()
        self.mock_db = get_schema_accurate_mock_db()
        
        with patch('database.get_db_manager', return_value=self.mock_db):
            self.context = MockTelegramObjects.create_context()
    
    async def test_handler_permission_denied_scenarios(self):
        """Test permission denied scenarios for all handlers."""
        chat_id = 12345
        
        handlers_to_test = [
            (ModernProductHandler(), "/product"),
            (ModernUserHandler(), "/user"),
            (ModernEstoqueHandler(), "/estoque"),
            (ModernBuyHandler(), "/buy"),
            (ModernPagamentoHandler(), "/pagar"),
            (ModernRelatoriosHandler(), "/relatorios"),
            (ModernSmartContractHandler(), "/smartcontract")
        ]
        
        with patch('utils.permissions.get_user_service') as mock_get_user_service:
            # Mock user service to return a user with insufficient permissions
            mock_user_service = Mock()
            mock_user_service.get_user_permission_level.return_value = UserLevel.USER  # Low permission level
            mock_get_user_service.return_value = mock_user_service
            for handler, command in handlers_to_test:
                update = MockTelegramObjects.create_update(command, chat_id=chat_id)
                
                # Should handle permission denial gracefully
                try:
                    # Call the appropriate entry method based on handler type
                    if hasattr(handler, 'start_product'):
                        result = await handler.start_product(update, self.context)
                    elif hasattr(handler, 'start_user'):
                        result = await handler.start_user(update, self.context)
                    elif hasattr(handler, 'start_estoque'):
                        result = await handler.start_estoque(update, self.context)
                    elif hasattr(handler, 'start_buy'):
                        result = await handler.start_buy(update, self.context)
                    elif hasattr(handler, 'start_pagamento'):
                        result = await handler.start_pagamento(update, self.context)
                    elif hasattr(handler, 'start_relatorios'):
                        result = await handler.start_relatorios(update, self.context)
                    elif hasattr(handler, 'start_smartcontract'):
                        result = await handler.start_smartcontract(update, self.context)
                    
                    # Result can vary, but should not crash
                    # Permission denial should either return None or trigger bot.send_message
                    assert result is None or self.context.bot.send_message.called
                except Exception as e:
                    # Permission denial should not raise exceptions, it should handle gracefully
                    pytest.fail(f"Handler {handler.__class__.__name__} should handle permission denial gracefully, but raised {e}")
    
    async def test_handler_invalid_input_scenarios(self):
        """Test invalid input handling across handlers."""
        chat_id = 12345
        
        # Test various invalid inputs
        invalid_inputs = [
            "",  # Empty string
            "   ",  # Whitespace only
            "🤖" * 1000,  # Very long input
            "<script>alert('xss')</script>",  # XSS attempt
            "'; DROP TABLE usuarios; --",  # SQL injection attempt
            "\x00\x01\x02",  # Binary data
        ]
        
        login_handler = ModernLoginHandler()
        
        for invalid_input in invalid_inputs:
            # Test with login handler as example
            update = MockTelegramObjects.create_update("/login", chat_id=chat_id)
            await login_handler.login_start(update, self.context)
            
            update = MockTelegramObjects.create_update(invalid_input, chat_id=chat_id)
            result = await login_handler.username_received(update, self.context)
            
            # Should handle gracefully
            assert result in [LOGIN_USERNAME, LOGIN_PASSWORD, ConversationHandler.END]
    
    async def test_handler_database_error_scenarios(self):
        """Test database error handling."""
        chat_id = 12345
        
        # Mock database to raise errors
        with patch('database.get_db_manager') as mock_db:
            mock_db.side_effect = Exception("Database connection failed")
            
            handlers = [
                ModernLoginHandler(),
                ModernProductHandler(),
                ModernUserHandler()
            ]
            
            for handler in handlers:
                update = MockTelegramObjects.create_update("/test", chat_id=chat_id)
                
                # Should handle database errors gracefully
                try:
                    result = await handler.__class__.__dict__[list(handler.__class__.__dict__.keys())[0]](handler, update, self.context)
                    # Should not crash
                    assert True
                except Exception as e:
                    # If it does raise an exception, it should be handled properly
                    assert "Database" in str(e) or isinstance(e, (ConnectionError, RuntimeError))


@pytest.mark.handler_flows
@pytest.mark.asyncio 
class TestHandlerPerformance:
    """Test handler performance and concurrency."""
    
    def setup_method(self):
        """Set up performance test environment."""
        reset_schema_mock_db()
        self.mock_db = get_schema_accurate_mock_db()
    
    async def test_concurrent_handler_operations(self):
        """Test multiple handlers operating concurrently."""
        tasks = []
        
        # Create multiple concurrent operations
        for i in range(10):
            chat_id = 10000 + i
            task = asyncio.create_task(self._simulate_handler_flow(chat_id))
            tasks.append(task)
        
        # Wait for all to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should complete successfully
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                pytest.fail(f"Concurrent handler {i} failed: {result}")
    
    async def _simulate_handler_flow(self, chat_id: int):
        """Simulate a handler flow for performance testing."""
        with patch('database.get_db_manager', return_value=self.mock_db):
            handler = ModernLoginHandler()
            context = MockTelegramObjects.create_context()
            
            update = MockTelegramObjects.create_update("/login", chat_id=chat_id)
            result = await handler.login_start(update, context)
            
            assert result in [LOGIN_USERNAME, ConversationHandler.END]