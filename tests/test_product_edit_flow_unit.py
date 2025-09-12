#!/usr/bin/env python3
"""
Unit tests for product handler edit flow functionality.
Tests conversation state transitions and method calls that were missing coverage.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from telegram import Update, Message, User, Chat, CallbackQuery
from telegram.ext import ConversationHandler

# Import handler and states
from handlers.product_handler import (
    ModernProductHandler, 
    PRODUCT_MENU, 
    PRODUCT_EDIT_SELECT, 
    PRODUCT_EDIT_PROPERTY, 
    PRODUCT_EDIT_NEW_VALUE
)

# Import models  
from models.product import Product

# Import the proper MockTelegramObjects from conftest
from tests.conftest import MockTelegramObjects


@pytest.mark.unit
@pytest.mark.asyncio
class TestProductEditFlowUnit:
    """Unit tests for product edit flow conversation states."""
    
    def setup_method(self):
        """Set up each test with mocked dependencies."""
        self.handler = ModernProductHandler()
        
        # Create proper async mock context
        self.context = AsyncMock()
        self.context.user_data = {}
        self.context.chat_data = {}
        self.context.bot_data = {}
        self.context.args = []
        
        # Mock products for testing
        self.mock_products = [
            Mock(id=1, nome="Product 1", emoji="🔥"),
            Mock(id=2, nome="Product 2", emoji="💎")
        ]
    
    async def test_product_menu_edit_selection(self):
        """Test product menu edit selection - missing unit test coverage."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func):
            # Mock the product service - get_all_products is SYNCHRONOUS, not async
            mock_service = Mock()
            mock_service.get_all_products.return_value = self.mock_products  # Use .return_value, not AsyncMock
            
            # Patch the service directly in conftest auto-use fixture  
            with patch('core.modern_service_container.get_product_service', return_value=mock_service):
                # Test edit product selection  
                update = MockTelegramObjects.create_update(callback_data="edit_product", chat_id=chat_id)
                
                # Mock all telegram message functions to prevent API calls
                with patch('utils.message_cleaner.send_and_delete', new_callable=AsyncMock) as mock_send, \
                     patch('utils.message_cleaner.send_menu_with_delete', new_callable=AsyncMock) as mock_send_menu, \
                     patch('handlers.error_handler.send_and_delete', new_callable=AsyncMock):
                    result = await self.handler.product_menu_selection(update, self.context)
            
            # Should transition to PRODUCT_EDIT_SELECT state
            assert result == PRODUCT_EDIT_SELECT
            
            # Verify service was called
            mock_service.get_all_products.assert_called_once()
    
    async def test_product_edit_select_callback(self):
        """Test product edit select callback - missing unit test coverage."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('core.modern_service_container.get_product_service') as mock_get_service:
            
            # Mock the product service
            mock_service = Mock()
            mock_service.get_product_by_id.return_value = self.mock_products[0]
            mock_get_service.return_value = mock_service
            
            # Store product ID in context user_data (simulating previous state)
            self.context.user_data['editing_product_id'] = 1
            
            # Test selecting a product to edit
            update = MockTelegramObjects.create_update(callback_data="edit_1", chat_id=chat_id)
            result = await self.handler.product_edit_select(update, self.context)
            
            # Should transition to PRODUCT_EDIT_PROPERTY state
            assert result == PRODUCT_EDIT_PROPERTY
    
    async def test_product_edit_property_selection(self):
        """Test product edit property selection - missing unit test coverage."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func):
            
            # Store product info in context (simulating previous states)
            self.context.user_data['editing_product_id'] = 1
            self.context.user_data['editing_product'] = self.mock_products[0]
            
            # Test selecting property to edit (e.g., "name")
            update = MockTelegramObjects.create_update(callback_data="edit_name", chat_id=chat_id)
            result = await self.handler.product_edit_property(update, self.context)
            
            # Should transition to PRODUCT_EDIT_NEW_VALUE state
            assert result == PRODUCT_EDIT_NEW_VALUE
            
            # Verify property type is stored (handler uses 'edit_property', not 'editing_property')
            assert 'edit_property' in self.context.user_data
    
    async def test_product_edit_new_value_input(self):
        """Test product edit new value input - missing unit test coverage."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('core.modern_service_container.get_product_service') as mock_get_service:
            
            # Mock the product service
            mock_service = Mock()
            mock_service.update_product.return_value = True
            mock_get_service.return_value = mock_service
            
            # Store editing context (simulating previous states)
            self.context.user_data['editing_product_id'] = 1
            self.context.user_data['editing_property'] = 'name'
            
            # Test entering new value
            update = MockTelegramObjects.create_update("New Product Name", chat_id=chat_id)
            result = await self.handler.product_edit_new_value(update, self.context)
            
            # Should complete conversation or return to menu
            assert result in [ConversationHandler.END, PRODUCT_MENU]
            
            # Verify update was attempted
            mock_service.update_product.assert_called_once()
    
    async def test_conversation_states_registration(self):
        """Test conversation handler has all required states - missing unit test coverage."""
        
        # Get the conversation handler
        conv_handler = self.handler.get_conversation_handler()
        
        # Verify all edit flow states are registered
        required_states = [
            PRODUCT_MENU,
            PRODUCT_EDIT_SELECT, 
            PRODUCT_EDIT_PROPERTY,
            PRODUCT_EDIT_NEW_VALUE
        ]
        
        for state in required_states:
            assert state in conv_handler.states, f"State {state} not registered in conversation handler"
    
    async def test_edit_flow_cancel_handling(self):
        """Test cancel operation during edit flow."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func):
            
            # Test cancel from any edit state
            update = MockTelegramObjects.create_update(callback_data="cancel", chat_id=chat_id)
            
            # Test cancel from edit select state
            result = await self.handler.product_edit_select(update, self.context)
            assert result == ConversationHandler.END
    
    async def test_edit_flow_error_scenarios(self):
        """Test error scenarios in edit flow."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('core.modern_service_container.get_product_service') as mock_get_service:
            
            # Mock service to raise an error
            mock_service = Mock()
            mock_service.get_all_products.side_effect = Exception("Database error")
            mock_get_service.return_value = mock_service
            
            # Test error handling in edit product start
            update = MockTelegramObjects.create_update(callback_data="edit_product", chat_id=chat_id)
            result = await self.handler.product_menu_selection(update, self.context)
            
            # Should handle error gracefully
            assert result in [ConversationHandler.END, PRODUCT_MENU]
    
    async def test_edit_flow_input_validation(self):
        """Test input validation in edit flow."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func):
            
            # Store editing context
            self.context.user_data['editing_product_id'] = 1
            self.context.user_data['editing_property'] = 'name'
            
            # Test empty input
            update = MockTelegramObjects.create_update("", chat_id=chat_id)
            result = await self.handler.product_edit_new_value(update, self.context)
            
            # Should stay in same state or show error
            assert result in [PRODUCT_EDIT_NEW_VALUE, PRODUCT_MENU, ConversationHandler.END]
    
    async def test_edit_flow_state_persistence(self):
        """Test that edit flow maintains state correctly across transitions."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('core.modern_service_container.get_product_service') as mock_get_service:
            
            # Mock the product service
            mock_service = Mock()
            mock_service.get_all_products.return_value = self.mock_products
            mock_service.get_product_by_id.return_value = self.mock_products[0]
            mock_get_service.return_value = mock_service
            
            # Step 1: Start edit
            update = MockTelegramObjects.create_update(callback_data="edit_product", chat_id=chat_id)
            result1 = await self.handler.product_menu_selection(update, self.context)
            assert result1 == PRODUCT_EDIT_SELECT
            
            # Step 2: Select product
            update = MockTelegramObjects.create_update(callback_data="edit_1", chat_id=chat_id)
            result2 = await self.handler.product_edit_select(update, self.context)
            assert result2 == PRODUCT_EDIT_PROPERTY
            
            # Verify state is maintained
            assert 'editing_product_id' in self.context.user_data
            assert self.context.user_data['editing_product_id'] == 1


if __name__ == "__main__":
    pytest.main([__file__])