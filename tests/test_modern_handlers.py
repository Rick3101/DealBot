"""
Modern handler tests that properly test real handlers with mocked services.
This demonstrates the correct testing pattern for the modern architecture.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from telegram.ext import ConversationHandler

from handlers.base_handler import HandlerRequest, HandlerResponse
from handlers.user_handler import USER_ADD_USERNAME, USER_ADD_PASSWORD
from handlers.product_handler import PRODUCT_MENU, PRODUCT_ADD_NAME, PRODUCT_ADD_EMOJI


class TestModernHandlers:
    """Test real handlers with properly mocked services"""
    
    @pytest.mark.asyncio
    async def test_user_handler_complete_flow(self, user_handler, user_request, comprehensive_handler_mocks):
        """Test complete user creation flow using real handler"""
        
        # Step 1: Start user handler - should show menu
        response = await user_handler.handle(user_request)
        assert "deseja fazer" in response.message.lower()
        assert response.next_state == 0  # MENU state
        
        # Step 2: Add username directly (test individual method)
        user_request.update.message = Mock()
        user_request.update.message.text = "newuser"
        
        response = await user_handler.handle_add_username(user_request)
        assert "senha" in response.message.lower()
        assert response.next_state == USER_ADD_PASSWORD
        assert user_request.user_data["new_username"] == "newuser"
        
        # Step 3: Add password and complete creation
        user_request.update.message.text = "securepass123"
        
        response = await user_handler.handle_add_password(user_request)
        assert response.end_conversation == True
        assert "sucesso" in response.message.lower()
        
        # Verify business service was called
        comprehensive_handler_mocks['business_service'].handle_user_management.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_product_handler_basic_flow(self, product_handler, user_request, comprehensive_handler_mocks):
        """Test basic product creation flow using real handler"""
        
        # Step 1: Start product handler
        response = await product_handler.handle_start(user_request)
        assert "produto" in response.message.lower()
        assert response.next_state == PRODUCT_MENU
        
        # Step 2: Select add product option  
        user_request.update.callback_query = Mock()
        user_request.update.callback_query.data = "add"
        user_request.update.callback_query.answer = AsyncMock()
        user_request.update.message = None
        
        response = await product_handler.handle_menu_callback(user_request)
        assert "nome do produto" in response.message.lower()
        assert response.next_state == PRODUCT_ADD_NAME
        
        # Step 3: Add product name
        user_request.update.callback_query = None
        user_request.update.message = Mock()
        user_request.update.message.text = "Test Product"
        
        response = await product_handler.handle_add_name(user_request)
        assert "emoji" in response.message.lower()
        assert response.next_state == PRODUCT_ADD_EMOJI
        assert user_request.user_data["new_product_name"] == "Test Product"
        
        # Step 4: Add emoji
        user_request.update.message.text = "🧪"
        
        response = await product_handler.handle_add_emoji(user_request)
        # Should ask about media or complete creation
        assert response.next_state in [4, ConversationHandler.END]  # MEDIA_CONFIRM or END
        
    @pytest.mark.asyncio
    async def test_user_handler_duplicate_username(self, user_handler, user_request, comprehensive_handler_mocks):
        """Test user handler handling duplicate username"""
        
        # Configure user service to return True for username_exists
        comprehensive_handler_mocks['user_service'].username_exists.return_value = True
        
        # Try to add username
        user_request.update.message = Mock()
        user_request.update.message.text = "existinguser"
        
        response = await user_handler.handle_add_username(user_request)
        
        assert "❌" in response.message
        assert "já existe" in response.message.lower()
        assert response.next_state == USER_ADD_USERNAME
        
    @pytest.mark.asyncio
    async def test_product_handler_validation_error(self, product_handler, user_request, comprehensive_handler_mocks):
        """Test product handler with validation error"""
        
        # Try to add invalid product name
        user_request.update.message = Mock()
        user_request.update.message.text = ""  # Empty name
        
        response = await product_handler.handle_add_name(user_request)
        
        assert "❌" in response.message
        assert response.next_state == PRODUCT_ADD_NAME
        
    @pytest.mark.asyncio 
    async def test_service_error_handling(self, user_handler, user_request, comprehensive_handler_mocks):
        """Test that service errors bubble up properly"""
        
        # Configure the existing mock user service to raise error
        comprehensive_handler_mocks['user_service'].username_exists.side_effect = Exception("Database error")
        
        user_request.update.message = Mock()
        user_request.update.message.text = "testuser"
        
        # Should raise the exception
        with pytest.raises(Exception):
            await user_handler.handle_add_username(user_request)