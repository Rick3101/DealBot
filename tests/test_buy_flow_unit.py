#!/usr/bin/env python3
"""
Unit tests for buy handler flow functionality.
Tests conversation state transitions and method calls following the established pattern.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from telegram import Update, Message, User, Chat, CallbackQuery
from telegram.ext import ConversationHandler

# Import handler and states
from handlers.buy_handler import (
    ModernBuyHandler, 
    BUY_NAME, 
    BUY_SELECT_PRODUCT,
    BUY_QUANTITY,
    BUY_PRICE
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
class TestBuyFlowUnit:
    """Unit tests for buy handler conversation states."""
    
    def setup_method(self):
        """Set up each test with mocked dependencies."""
        self.handler = ModernBuyHandler()
        self.context = MockTelegramObjects.create_context()
        
        # Mock products for testing
        self.mock_products = [
            Mock(id=1, nome="Product 1", emoji="🔥", preco=10.0),
            Mock(id=2, nome="Product 2", emoji="💎", preco=20.0)
        ]
    
    async def test_buy_start_owner_flow(self):
        """Test buy start for owner - should ask for buyer name."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('utils.permissions.get_user_permission_level') as mock_get_level:
            
            # Mock owner permission
            mock_get_level.return_value = 'owner'
            
            # Test starting buy process as owner
            update = MockTelegramObjects.create_update(text="/buy", chat_id=chat_id)
            result = await self.handler.start_buy(update, self.context)
            
            # Should transition to BUY_NAME state for owner
            assert result == BUY_NAME
    
    async def test_buy_start_admin_flow(self):
        """Test buy start for admin - should go directly to product selection."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('utils.permissions.get_user_permission_level') as mock_get_level, \
             patch('core.modern_service_container.get_product_service') as mock_get_service:
            
            # Mock admin permission and service
            mock_get_level.return_value = 'admin'
            mock_service = Mock()
            mock_service.get_available_products.return_value = self.mock_products
            mock_get_service.return_value = mock_service
            
            # Test starting buy process as admin
            update = MockTelegramObjects.create_update(text="/buy", chat_id=chat_id)
            result = await self.handler.start_buy(update, self.context)
            
            # Should transition to BUY_SELECT_PRODUCT state for admin
            assert result == BUY_SELECT_PRODUCT
    
    async def test_buy_set_name_input(self):
        """Test buy set name input - unit test coverage."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('core.modern_service_container.get_product_service') as mock_get_service:
            
            # Mock the product service
            mock_service = Mock()
            mock_service.get_available_products.return_value = self.mock_products
            mock_get_service.return_value = mock_service
            
            # Test entering buyer name
            update = MockTelegramObjects.create_update("John Doe", chat_id=chat_id)
            result = await self.handler.buy_set_name(update, self.context)
            
            # Should transition to BUY_SELECT_PRODUCT state
            assert result == BUY_SELECT_PRODUCT
            
            # Verify buyer name is stored
            assert 'buyer_name' in self.context.user_data
            assert self.context.user_data['buyer_name'] == "John Doe"
    
    async def test_buy_select_product_callback(self):
        """Test buy select product callback - unit test coverage."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('core.modern_service_container.get_product_service') as mock_get_service:
            
            # Mock the product service
            mock_service = Mock()
            mock_service.get_product_by_id.return_value = self.mock_products[0]
            mock_get_service.return_value = mock_service
            
            # Test selecting a product
            update = MockTelegramObjects.create_update(callback_data="buyproduct:1", chat_id=chat_id)
            result = await self.handler.buy_select_product(update, self.context)
            
            # Should transition to BUY_QUANTITY state
            assert result == BUY_QUANTITY
            
            # Verify product is stored
            assert 'selected_product' in self.context.user_data
    
    async def test_buy_set_quantity_input(self):
        """Test buy set quantity input - unit test coverage."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func):
            
            # Store product from previous state
            self.context.user_data['selected_product'] = self.mock_products[0]
            
            # Test entering quantity
            update = MockTelegramObjects.create_update("5", chat_id=chat_id)
            result = await self.handler.buy_set_quantity(update, self.context)
            
            # Should transition to BUY_PRICE state
            assert result == BUY_PRICE
            
            # Verify quantity is stored
            assert 'quantity' in self.context.user_data
            assert self.context.user_data['quantity'] == 5
    
    async def test_buy_set_price_input(self):
        """Test buy set price input - unit test coverage."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('core.modern_service_container.get_sales_service') as mock_get_service:
            
            # Mock the sales service
            mock_service = Mock()
            mock_service.create_sale.return_value = Mock(id=1, total=50.0)
            mock_get_service.return_value = mock_service
            
            # Store purchase data from previous states
            self.context.user_data['selected_product'] = self.mock_products[0]
            self.context.user_data['quantity'] = 5
            self.context.user_data['buyer_name'] = "John Doe"
            
            # Test entering price
            update = MockTelegramObjects.create_update("10.00", chat_id=chat_id)
            result = await self.handler.buy_set_price(update, self.context)
            
            # Should complete conversation
            assert result == ConversationHandler.END
            
            # Verify sale was created
            mock_service.create_sale.assert_called_once()
    
    async def test_buy_secret_menu_access(self):
        """Test secret menu access with special phrase."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('core.modern_service_container.get_product_service') as mock_get_service:
            
            # Mock the product service for secret products
            mock_service = Mock()
            mock_service.get_secret_products.return_value = [
                Mock(id=99, nome="Secret Product", emoji="🧪", preco=100.0)
            ]
            mock_get_service.return_value = mock_service
            
            # Test entering secret phrase
            update = MockTelegramObjects.create_update("wubba lubba dub dub", chat_id=chat_id)
            result = await self.handler.check_secret_menu(update, self.context)
            
            # Should stay in BUY_SELECT_PRODUCT with secret products shown
            assert result == BUY_SELECT_PRODUCT
    
    async def test_buy_finalize_callback(self):
        """Test buy finalize callback - unit test coverage."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('core.modern_service_container.get_sales_service') as mock_get_service:
            
            # Mock the sales service
            mock_service = Mock()
            mock_service.finalize_purchase.return_value = True
            mock_get_service.return_value = mock_service
            
            # Store purchase data
            self.context.user_data['purchase_items'] = [
                {'product': self.mock_products[0], 'quantity': 2}
            ]
            
            # Test finalizing purchase
            update = MockTelegramObjects.create_update(callback_data="buy_finalizar", chat_id=chat_id)
            result = await self.handler.buy_select_product(update, self.context)
            
            # Should complete conversation
            assert result == ConversationHandler.END
    
    async def test_conversation_states_registration(self):
        """Test conversation handler has all required states - unit test coverage."""
        
        # Get the conversation handler
        conv_handler = self.handler.get_conversation_handler()
        
        # Verify all buy flow states are registered
        required_states = [
            BUY_NAME,
            BUY_SELECT_PRODUCT,
            BUY_QUANTITY,
            BUY_PRICE
        ]
        
        for state in required_states:
            assert state in conv_handler.states, f"State {state} not registered in conversation handler"
    
    async def test_buy_flow_cancel_handling(self):
        """Test cancel operation during buy flow."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func):
            
            # Test cancel from any buy state
            update = MockTelegramObjects.create_update(callback_data="buy_cancelar", chat_id=chat_id)
            
            # Test cancel
            result = await self.handler.cancel(update, self.context)
            assert result == ConversationHandler.END
    
    async def test_buy_flow_error_scenarios(self):
        """Test error scenarios in buy flow."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('core.modern_service_container.get_product_service') as mock_get_service:
            
            # Mock service to raise an error
            mock_service = Mock()
            mock_service.get_available_products.side_effect = Exception("Database error")
            mock_get_service.return_value = mock_service
            
            # Test error handling in product selection
            update = MockTelegramObjects.create_update(text="/buy", chat_id=chat_id)
            result = await self.handler.start_buy(update, self.context)
            
            # Should handle error gracefully
            assert result in [ConversationHandler.END, BUY_SELECT_PRODUCT]
    
    async def test_buy_flow_input_validation(self):
        """Test input validation in buy flow."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func):
            
            # Test invalid quantity (non-numeric)
            update = MockTelegramObjects.create_update("invalid", chat_id=chat_id)
            result = await self.handler.buy_set_quantity(update, self.context)
            
            # Should stay in same state or show error
            assert result in [BUY_QUANTITY, ConversationHandler.END]
    
    async def test_buy_flow_state_persistence(self):
        """Test that buy flow maintains state correctly across transitions."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('utils.permissions.get_user_permission_level') as mock_get_level, \
             patch('core.modern_service_container.get_product_service') as mock_get_service:
            
            # Mock admin permission and service
            mock_get_level.return_value = 'admin'
            mock_service = Mock()
            mock_service.get_available_products.return_value = self.mock_products
            mock_service.get_product_by_id.return_value = self.mock_products[0]
            mock_get_service.return_value = mock_service
            
            # Step 1: Start buy as admin
            update = MockTelegramObjects.create_update(text="/buy", chat_id=chat_id)
            result1 = await self.handler.start_buy(update, self.context)
            assert result1 == BUY_SELECT_PRODUCT
            
            # Step 2: Select product
            update = MockTelegramObjects.create_update(callback_data="buyproduct:1", chat_id=chat_id)
            result2 = await self.handler.buy_select_product(update, self.context)
            assert result2 == BUY_QUANTITY
            
            # Verify state is maintained
            assert 'selected_product' in self.context.user_data


if __name__ == "__main__":
    pytest.main([__file__])