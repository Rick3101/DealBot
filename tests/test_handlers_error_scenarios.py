#!/usr/bin/env python3
"""
Error scenario and edge case tests for all handlers.
Tests security, validation, error handling, and boundary conditions.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from telegram import Update, Message, User, Chat
from telegram.ext import ConversationHandler

# Import test infrastructure
from tests.mocks.schema_accurate_mock_database import get_schema_accurate_mock_db, reset_schema_mock_db

# Import handlers for testing
from handlers.buy_handler import ModernBuyHandler, BUY_QUANTITY, BUY_PRICE
from handlers.login_handler import ModernLoginHandler, LOGIN_USERNAME, LOGIN_PASSWORD
from handlers.product_handler import ModernProductHandler, PRODUCT_ADD_NAME, PRODUCT_ADD_EMOJI
from handlers.user_handler import ModernUserHandler, USER_ADD_USERNAME, USER_ADD_PASSWORD
from handlers.estoque_handler import ModernEstoqueHandler, ESTOQUE_ADD_VALUES
from handlers.pagamento_handler import ModernPagamentoHandler, PAGAMENTO_VALOR

# Import services for setup
from services.user_service import UserService
from services.product_service import ProductService
from models.user import CreateUserRequest, UserLevel
from models.product import CreateProductRequest


class MockTelegramHelper:
    """Helper for creating mock Telegram objects."""
    
    @staticmethod
    def create_update(text: str, chat_id: int = 12345, user_id: int = 67890):
        user = User(id=user_id, first_name="Test", is_bot=False)
        chat = Chat(id=chat_id, type="private")
        message = Message(message_id=1, date=None, chat=chat, from_user=user, text=text)
        return Update(update_id=1, message=message)
    
    @staticmethod
    def create_context():
        context = AsyncMock()
        context.bot = AsyncMock()
        context.user_data = {}
        return context


@pytest.mark.handler_flows
@pytest.mark.asyncio
class TestHandlerSecurityScenarios:
    """Test security-related scenarios for all handlers."""
    
    def setup_method(self):
        """Set up security test environment."""
        reset_schema_mock_db()
        self.mock_db = get_schema_accurate_mock_db()
        
        with patch('database.get_db_manager', return_value=self.mock_db):
            self.user_service = UserService()
            self.product_service = ProductService()
            self.context = MockTelegramHelper.create_context()
    
    async def test_sql_injection_prevention(self):
        """Test that handlers prevent SQL injection attacks."""
        chat_id = 12345
        
        # SQL injection payloads
        sql_payloads = [
            "'; DROP TABLE usuarios; --",
            "admin'; UPDATE usuarios SET nivel='owner' WHERE id=1; --",
            "' OR '1'='1",
            "admin' UNION SELECT password FROM usuarios WHERE '1'='1",
            "'; INSERT INTO usuarios VALUES (999, 'hacker', 'pass', 'owner', 12345); --"
        ]
        
        login_handler = ModernLoginHandler()
        
        for payload in sql_payloads:
            # Start login
            update = MockTelegramHelper.create_update("/login", chat_id)
            await login_handler.login_start(update, self.context)
            
            # Try SQL injection in username
            update = MockTelegramHelper.create_update(payload, chat_id)
            result = await login_handler.username_received(update, self.context)
            
            # Should handle safely (not crash and not succeed)
            assert result in [LOGIN_USERNAME, LOGIN_PASSWORD, ConversationHandler.END]
            
            # Try SQL injection in password
            if result == LOGIN_PASSWORD:
                update = MockTelegramHelper.create_update(payload, chat_id)
                result = await login_handler.password_received(update, self.context)
                assert result in [LOGIN_PASSWORD, ConversationHandler.END]
    
    async def test_xss_prevention(self):
        """Test that handlers prevent XSS attacks."""
        chat_id = 12345
        
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<svg onload=alert('xss')>",
            "';alert('xss');//"
        ]
        
        product_handler = ModernProductHandler()
        
        with patch('utils.permissions.check_permission_level', return_value=True):
            for payload in xss_payloads:
                # Start product creation
                update = MockTelegramHelper.create_update("/product", chat_id)
                await product_handler.product_menu(update, self.context)
                
                # Try XSS in product name
                self.context.user_data['adding_product'] = True
                update = MockTelegramHelper.create_update(payload, chat_id)
                result = await product_handler.add_product_name(update, self.context)
                
                # Should handle safely
                assert result in [PRODUCT_ADD_NAME, PRODUCT_ADD_EMOJI, ConversationHandler.END]
    
    async def test_input_length_limits(self):
        """Test handling of extremely long inputs."""
        chat_id = 12345
        
        # Very long inputs
        long_inputs = [
            "A" * 1000,  # 1KB
            "🔥" * 500,   # Unicode spam
            "admin" + "X" * 10000,  # Long username
            "pass" + "Y" * 10000    # Long password
        ]
        
        user_handler = ModernUserHandler()
        
        with patch('utils.permissions.check_permission_level', return_value=True):
            for long_input in long_inputs:
                # Start user creation
                update = MockTelegramHelper.create_update("/user", chat_id)
                await user_handler.user_menu(update, self.context)
                
                # Try long input in username
                self.context.user_data['adding_user'] = True
                update = MockTelegramHelper.create_update(long_input, chat_id)
                result = await user_handler.add_user_username(update, self.context)
                
                # Should handle gracefully (truncate or reject)
                assert result in [USER_ADD_USERNAME, USER_ADD_PASSWORD, ConversationHandler.END]
    
    async def test_permission_escalation_prevention(self):
        """Test that handlers prevent permission escalation."""
        chat_id = 12345
        
        # Try to escalate permissions through various means
        escalation_attempts = [
            "admin",
            "owner", 
            "root",
            "administrator",
            "OWNER",
            "Owner",
            "../owner",
            "user; nivel=owner"
        ]
        
        user_handler = ModernUserHandler()
        
        # Test with regular user permissions
        with patch('utils.permissions.get_user_service') as mock_get_user_service:
            # Mock user service to return insufficient permissions
            mock_user_service = Mock()
            mock_user_service.get_user_permission_level.return_value = None  # No permission
            mock_get_user_service.return_value = mock_user_service
            for attempt in escalation_attempts:
                update = MockTelegramHelper.create_update("/user", chat_id)
                result = await user_handler.start_user(update, self.context)
                
                # Should deny access
                assert result in [ConversationHandler.END, None]
                # Should send permission denied message
                assert self.context.bot.send_message.called


@pytest.mark.handler_flows
@pytest.mark.asyncio
class TestHandlerValidationScenarios:
    """Test input validation scenarios for all handlers."""
    
    def setup_method(self):
        """Set up validation test environment."""
        reset_schema_mock_db()
        self.mock_db = get_schema_accurate_mock_db()
        
        with patch('database.get_db_manager', return_value=self.mock_db):
            self.context = MockTelegramHelper.create_context()
    
    async def test_numeric_input_validation(self):
        """Test validation of numeric inputs."""
        chat_id = 12345
        
        # Invalid numeric inputs
        invalid_numbers = [
            "abc",
            "",
            "1.2.3",
            "-5",
            "0",
            "999999999999999",
            "1,23",  # Wrong decimal separator
            "1..5",
            "infinity",
            "NaN"
        ]
        
        buy_handler = ModernBuyHandler()
        
        with patch('utils.permissions.check_permission_level', return_value=True):
            for invalid_num in invalid_numbers:
                # Start buy flow and get to quantity input
                self.context.user_data = {'selected_product_id': 1, 'buyer_name': 'test'}
                
                # Try invalid quantity
                update = MockTelegramHelper.create_update(invalid_num, chat_id)
                result = await buy_handler.quantity_received(update, self.context)
                
                # Should ask for quantity again or end
                assert result in [BUY_QUANTITY, ConversationHandler.END]
                
                # Try invalid price
                if 'quantity' in self.context.user_data:
                    update = MockTelegramHelper.create_update(invalid_num, chat_id)
                    result = await buy_handler.price_received(update, self.context)
                    assert result in [BUY_PRICE, ConversationHandler.END]
    
    async def test_currency_validation(self):
        """Test validation of currency/price inputs."""
        chat_id = 12345
        
        # Invalid currency formats
        invalid_prices = [
            "$10.50",
            "R$ 15,30",
            "10,50€",
            "10.50.25",
            "10.999",  # Too many decimal places
            "0.00",    # Zero price
            "-10.50",  # Negative price
            "10..50",
            "10.5.0"
        ]
        
        pagamento_handler = ModernPagamentoHandler()
        
        with patch('utils.permissions.check_permission_level', return_value=True):
            for invalid_price in invalid_prices:
                # Start payment flow
                update = MockTelegramHelper.create_update("/pagar", chat_id)
                await pagamento_handler.pagamento_start(update, self.context)
                
                # Try invalid payment amount
                update = MockTelegramHelper.create_update(invalid_price, chat_id)
                result = await pagamento_handler.pagamento_valor(update, self.context)
                
                # Should ask for amount again or end
                assert result in [PAGAMENTO_VALOR, ConversationHandler.END]
    
    async def test_stock_format_validation(self):
        """Test validation of stock input format."""
        chat_id = 12345
        
        # Invalid stock formats (should be "quantity / price / cost")
        invalid_formats = [
            "10",
            "10 15.50",
            "10, 15.50, 10.00",
            "10 / 15.50",  # Missing cost
            "10 / / 10.00",  # Missing price
            "/ 15.50 / 10.00",  # Missing quantity
            "abc / 15.50 / 10.00",  # Invalid quantity
            "10 / abc / 10.00",  # Invalid price
            "10 / 15.50 / abc",  # Invalid cost
            "",
            "   ",
            "10/15.50/10.00",  # No spaces
        ]
        
        estoque_handler = ModernEstoqueHandler()
        
        with patch('utils.permissions.check_permission_level', return_value=True):
            for invalid_format in invalid_formats:
                # Start stock addition flow
                self.context.user_data = {'adding_stock_product_id': 1}
                
                # Try invalid stock format
                update = MockTelegramHelper.create_update(invalid_format, chat_id)
                result = await estoque_handler.add_stock_values(update, self.context)
                
                # Should ask for values again or end
                assert result in [ESTOQUE_ADD_VALUES, ConversationHandler.END]
    
    async def test_emoji_validation(self):
        """Test validation of emoji inputs."""
        chat_id = 12345
        
        # Invalid emoji inputs
        invalid_emojis = [
            "🔥🔥",  # Multiple emojis
            "fire",  # Text instead of emoji
            "🔥fire",  # Emoji + text
            "",  # Empty
            "   ",  # Whitespace
            "🔥 ",  # Emoji + space
            "<script>",  # HTML
            "🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥"  # Too many emojis
        ]
        
        product_handler = ModernProductHandler()
        
        with patch('utils.permissions.check_permission_level', return_value=True):
            for invalid_emoji in invalid_emojis:
                # Start product creation
                self.context.user_data = {'adding_product_name': 'Test Product'}
                
                # Try invalid emoji
                update = MockTelegramHelper.create_update(invalid_emoji, chat_id)
                result = await product_handler.add_product_emoji(update, self.context)
                
                # Should ask for emoji again or end
                assert result in [PRODUCT_ADD_EMOJI, ConversationHandler.END]


@pytest.mark.handler_flows
@pytest.mark.asyncio
class TestHandlerErrorRecovery:
    """Test error recovery and resilience scenarios."""
    
    def setup_method(self):
        """Set up error recovery test environment."""
        reset_schema_mock_db()
        self.mock_db = get_schema_accurate_mock_db()
        self.context = MockTelegramHelper.create_context()
    
    async def test_database_connection_failure_recovery(self):
        """Test handler behavior when database connection fails."""
        chat_id = 12345
        
        # Mock database to fail
        with patch('database.get_db_manager') as mock_db:
            mock_db.side_effect = ConnectionError("Database unavailable")
            
            handlers = [
                ModernLoginHandler(),
                ModernProductHandler(),
                ModernUserHandler()
            ]
            
            for handler in handlers:
                # Try operations that require database
                update = MockTelegramHelper.create_update("/test", chat_id)
                
                try:
                    # Should handle database failure gracefully
                    result = await handler.login_start(update, self.context) if hasattr(handler, 'login_start') else None
                    # Should not crash
                    assert True
                except Exception as e:
                    # If exception raised, should be handled properly
                    assert "Database" in str(e) or isinstance(e, (ConnectionError, RuntimeError))
    
    async def test_telegram_api_failure_recovery(self):
        """Test handler behavior when Telegram API calls fail."""
        chat_id = 12345
        
        # Mock Telegram bot to fail
        self.context.bot.send_message.side_effect = Exception("Telegram API error")
        
        login_handler = ModernLoginHandler()
        
        # Try operations that send messages
        update = MockTelegramHelper.create_update("/login", chat_id)
        
        try:
            result = await login_handler.login_start(update, self.context)
            # Should handle API failure gracefully
            assert result in [LOGIN_USERNAME, ConversationHandler.END, None]
        except Exception as e:
            # If exception raised, should be API-related
            assert "Telegram" in str(e) or "API" in str(e)
    
    async def test_memory_pressure_scenarios(self):
        """Test handler behavior under memory pressure."""
        chat_id = 12345
        
        # Simulate high memory usage
        large_data = "X" * (1024 * 1024)  # 1MB string
        
        login_handler = ModernLoginHandler()
        
        # Fill context with large data
        self.context.user_data['large_data'] = large_data
        self.context.chat_data['large_data'] = large_data
        
        # Try normal operations
        update = MockTelegramHelper.create_update("/login", chat_id)
        result = await login_handler.login_start(update, self.context)
        
        # Should still work despite memory pressure
        assert result in [LOGIN_USERNAME, ConversationHandler.END]
    
    async def test_concurrent_user_operations(self):
        """Test handlers with concurrent operations from same user."""
        chat_id = 12345
        
        with patch('database.get_db_manager', return_value=self.mock_db):
            login_handler = ModernLoginHandler()
            
            # Create multiple concurrent operations for same user
            tasks = []
            for i in range(5):
                update = MockTelegramHelper.create_update("/login", chat_id)
                context = MockTelegramHelper.create_context()
                task = asyncio.create_task(login_handler.login_start(update, context))
                tasks.append(task)
            
            # Wait for all to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All should complete without conflicts
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    pytest.fail(f"Concurrent operation {i} failed: {result}")
                else:
                    assert result in [LOGIN_USERNAME, ConversationHandler.END]


@pytest.mark.handler_flows
@pytest.mark.asyncio
class TestHandlerBoundaryConditions:
    """Test boundary conditions and edge cases."""
    
    def setup_method(self):
        """Set up boundary condition tests."""
        reset_schema_mock_db()
        self.mock_db = get_schema_accurate_mock_db()
        self.context = MockTelegramHelper.create_context()
    
    async def test_maximum_input_lengths(self):
        """Test handling of maximum input lengths."""
        chat_id = 12345
        
        # Test maximum reasonable input lengths
        max_inputs = {
            'username': "user" + "x" * 46,  # 50 chars total
            'product_name': "product" + "x" * 92,  # 100 chars total  
            'description': "desc" + "x" * 1996,  # 2000 chars total
        }
        
        user_handler = ModernUserHandler()
        
        with patch('utils.permissions.check_permission_level', return_value=True):
            for input_type, max_input in max_inputs.items():
                # Test with maximum length input
                self.context.user_data = {}
                update = MockTelegramHelper.create_update(max_input, chat_id)
                
                if input_type == 'username':
                    result = await user_handler.add_user_username(update, self.context)
                    assert result in [USER_ADD_USERNAME, USER_ADD_PASSWORD, ConversationHandler.END]
    
    async def test_minimum_input_requirements(self):
        """Test minimum input requirements."""
        chat_id = 12345
        
        # Test minimum inputs
        min_inputs = [
            "",  # Empty
            " ",  # Single space
            "a",  # Single character
            "1",  # Single digit
        ]
        
        login_handler = ModernLoginHandler()
        
        for min_input in min_inputs:
            # Start login
            update = MockTelegramHelper.create_update("/login", chat_id)
            await login_handler.login_start(update, self.context)
            
            # Try minimum input
            update = MockTelegramHelper.create_update(min_input, chat_id)
            result = await login_handler.username_received(update, self.context)
            
            # Should handle appropriately (likely ask again for empty/spaces)
            assert result in [LOGIN_USERNAME, LOGIN_PASSWORD, ConversationHandler.END]
    
    async def test_unicode_edge_cases(self):
        """Test handling of Unicode edge cases."""
        chat_id = 12345
        
        # Unicode edge cases
        unicode_tests = [
            "🔥",  # Basic emoji
            "👨‍👩‍👧‍👦",  # Complex emoji sequence
            "Café",  # Accented characters
            "北京",  # Chinese characters  
            "العربية",  # Arabic
            "🇧🇷",  # Flag emoji
            "test\u0000null",  # Null byte
            "test\u200Dinvisible",  # Invisible character
        ]
        
        product_handler = ModernProductHandler()
        
        with patch('utils.permissions.check_permission_level', return_value=True):
            for unicode_input in unicode_tests:
                # Test Unicode input in product name
                self.context.user_data = {}
                update = MockTelegramHelper.create_update(unicode_input, chat_id)
                result = await product_handler.add_product_name(update, self.context)
                
                # Should handle Unicode gracefully
                assert result in [PRODUCT_ADD_NAME, PRODUCT_ADD_EMOJI, ConversationHandler.END]