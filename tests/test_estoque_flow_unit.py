#!/usr/bin/env python3
"""
Unit tests for estoque (inventory) handler flow functionality.
Tests conversation state transitions and method calls following the established pattern.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from telegram import Update, Message, User, Chat, CallbackQuery
from telegram.ext import ConversationHandler

# Import handler and states
from handlers.estoque_handler import (
    ModernEstoqueHandler, 
    ESTOQUE_MENU, 
    ESTOQUE_ADD_SELECT,
    ESTOQUE_ADD_VALUES,
    ESTOQUE_VIEW
)

# Import models  
from models.product import Product


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


@pytest.mark.unit
@pytest.mark.asyncio
class TestEstoqueFlowUnit:
    """Unit tests for estoque handler conversation states."""
    
    def setup_method(self):
        """Set up each test with mocked dependencies."""
        self.handler = ModernEstoqueHandler()
        self.context = MockTelegramObjects.create_context()
        
        # Mock products for testing
        self.mock_products = [
            Mock(id=1, nome="Product 1", emoji="🔥"),
            Mock(id=2, nome="Product 2", emoji="💎")
        ]
    
    async def test_estoque_start_menu(self):
        """Test estoque start - should show main menu."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func):
            
            # Test starting estoque process
            update = MockTelegramObjects.create_update(text="/estoque", chat_id=chat_id)
            result = await self.handler.start_estoque(update, self.context)
            
            # Should transition to ESTOQUE_MENU state
            assert result == ESTOQUE_MENU
    
    async def test_estoque_menu_add_selection(self):
        """Test estoque menu add selection - unit test coverage."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('core.modern_service_container.get_product_service') as mock_get_service:
            
            # Mock the product service
            mock_service = Mock()
            mock_service.get_all_products.return_value = self.mock_products
            mock_get_service.return_value = mock_service
            
            # Test add stock selection
            update = MockTelegramObjects.create_update(callback_data="add_stock", chat_id=chat_id)
            result = await self.handler.estoque_menu_selection(update, self.context)
            
            # Should transition to ESTOQUE_ADD_SELECT state
            assert result == ESTOQUE_ADD_SELECT
            
            # Verify service was called
            mock_service.get_all_products.assert_called_once()
    
    async def test_estoque_menu_view_selection(self):
        """Test estoque menu view selection - unit test coverage."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('core.modern_service_container.get_product_service') as mock_get_service:
            
            # Mock the product service
            mock_service = Mock()
            mock_service.get_stock_report.return_value = [
                {'product': self.mock_products[0], 'quantity': 10, 'cost': 5.0},
                {'product': self.mock_products[1], 'quantity': 5, 'cost': 15.0}
            ]
            mock_get_service.return_value = mock_service
            
            # Test view stock selection
            update = MockTelegramObjects.create_update(callback_data="view_stock", chat_id=chat_id)
            result = await self.handler.estoque_menu_selection(update, self.context)
            
            # Should complete conversation or return to menu
            assert result in [ConversationHandler.END, ESTOQUE_MENU]
    
    async def test_estoque_select_product_callback(self):
        """Test estoque select product callback - unit test coverage."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('core.modern_service_container.get_product_service') as mock_get_service:
            
            # Mock the product service
            mock_service = Mock()
            mock_service.get_product_by_id.return_value = self.mock_products[0]
            mock_get_service.return_value = mock_service
            
            # Test selecting a product for stock addition
            update = MockTelegramObjects.create_update(callback_data="add_stock:1", chat_id=chat_id)
            result = await self.handler.estoque_select_product(update, self.context)
            
            # Should transition to ESTOQUE_ADD_VALUES state
            assert result == ESTOQUE_ADD_VALUES
            
            # Verify product is stored
            assert 'selected_product_id' in self.context.user_data
            assert self.context.user_data['selected_product_id'] == 1
    
    async def test_estoque_add_values_input(self):
        """Test estoque add values input - unit test coverage."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('core.modern_service_container.get_product_service') as mock_get_service:
            
            # Mock the product service
            mock_service = Mock()
            mock_service.add_stock.return_value = True
            mock_get_service.return_value = mock_service
            
            # Store product from previous state
            self.context.user_data['selected_product_id'] = 1
            
            # Test entering stock values (format: quantity / price / cost)
            update = MockTelegramObjects.create_update("10 / 15.0 / 8.0", chat_id=chat_id)
            result = await self.handler.estoque_add_values(update, self.context)
            
            # Should complete conversation or return to menu
            assert result in [ConversationHandler.END, ESTOQUE_MENU]
            
            # Verify stock addition was attempted
            mock_service.add_stock.assert_called_once()
    
    async def test_estoque_add_values_invalid_format(self):
        """Test estoque add values with invalid format - unit test coverage."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func):
            
            # Store product from previous state
            self.context.user_data['selected_product_id'] = 1
            
            # Test entering invalid format
            update = MockTelegramObjects.create_update("invalid format", chat_id=chat_id)
            result = await self.handler.estoque_add_values(update, self.context)
            
            # Should stay in same state or show error
            assert result in [ESTOQUE_ADD_VALUES, ESTOQUE_MENU, ConversationHandler.END]
    
    async def test_estoque_batch_add_values(self):
        """Test estoque batch add values - unit test coverage."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('core.modern_service_container.get_product_service') as mock_get_service:
            
            # Mock the product service
            mock_service = Mock()
            mock_service.add_stock.return_value = True
            mock_get_service.return_value = mock_service
            
            # Store product from previous state
            self.context.user_data['selected_product_id'] = 1
            
            # Test entering multiple stock entries
            update = MockTelegramObjects.create_update("10 / 15.0 / 8.0\n5 / 12.0 / 6.0", chat_id=chat_id)
            result = await self.handler.estoque_add_values(update, self.context)
            
            # Should complete conversation or return to menu
            assert result in [ConversationHandler.END, ESTOQUE_MENU]
    
    async def test_conversation_states_registration(self):
        """Test conversation handler has all required states - unit test coverage."""
        
        # Get the conversation handler
        conv_handler = self.handler.get_conversation_handler()
        
        # Verify all estoque flow states are registered
        required_states = [
            ESTOQUE_MENU,
            ESTOQUE_ADD_SELECT,
            ESTOQUE_ADD_VALUES
        ]
        
        for state in required_states:
            assert state in conv_handler.states, f"State {state} not registered in conversation handler"
    
    async def test_estoque_flow_cancel_handling(self):
        """Test cancel operation during estoque flow."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func):
            
            # Test cancel from any estoque state
            update = MockTelegramObjects.create_update(callback_data="cancel", chat_id=chat_id)
            
            # Test cancel
            result = await self.handler.cancel(update, self.context)
            assert result == ConversationHandler.END
    
    async def test_estoque_flow_error_scenarios(self):
        """Test error scenarios in estoque flow."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('core.modern_service_container.get_product_service') as mock_get_service:
            
            # Mock service to raise an error
            mock_service = Mock()
            mock_service.get_all_products.side_effect = Exception("Database error")
            mock_get_service.return_value = mock_service
            
            # Test error handling in add stock selection
            update = MockTelegramObjects.create_update(callback_data="add_stock", chat_id=chat_id)
            result = await self.handler.estoque_menu_selection(update, self.context)
            
            # Should handle error gracefully
            assert result in [ConversationHandler.END, ESTOQUE_MENU]
    
    async def test_estoque_flow_input_validation(self):
        """Test input validation in estoque flow."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func):
            
            # Store product from previous state
            self.context.user_data['selected_product_id'] = 1
            
            # Test empty input
            update = MockTelegramObjects.create_update("", chat_id=chat_id)
            result = await self.handler.estoque_add_values(update, self.context)
            
            # Should stay in same state or show error
            assert result in [ESTOQUE_ADD_VALUES, ESTOQUE_MENU, ConversationHandler.END]
    
    async def test_estoque_flow_state_persistence(self):
        """Test that estoque flow maintains state correctly across transitions."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('core.modern_service_container.get_product_service') as mock_get_service:
            
            # Mock the product service
            mock_service = Mock()
            mock_service.get_all_products.return_value = self.mock_products
            mock_service.get_product_by_id.return_value = self.mock_products[0]
            mock_get_service.return_value = mock_service
            
            # Step 1: Start estoque
            update = MockTelegramObjects.create_update(text="/estoque", chat_id=chat_id)
            result1 = await self.handler.start_estoque(update, self.context)
            assert result1 == ESTOQUE_MENU
            
            # Step 2: Select add stock
            update = MockTelegramObjects.create_update(callback_data="add_stock", chat_id=chat_id)
            result2 = await self.handler.estoque_menu_selection(update, self.context)
            assert result2 == ESTOQUE_ADD_SELECT
            
            # Step 3: Select product
            update = MockTelegramObjects.create_update(callback_data="add_stock:1", chat_id=chat_id)
            result3 = await self.handler.estoque_select_product(update, self.context)
            assert result3 == ESTOQUE_ADD_VALUES
            
            # Verify state is maintained
            assert 'selected_product_id' in self.context.user_data
            assert self.context.user_data['selected_product_id'] == 1


if __name__ == "__main__":
    pytest.main([__file__])