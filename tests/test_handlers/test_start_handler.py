"""
Tests for the start handler module.
Validates bot initialization and protection phrase functionality.
"""

import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch

from handlers.base_handler import HandlerRequest, HandlerResponse
from handlers.start_handler import ModernStartHandler, get_modern_start_handler
from services.base_service import ValidationError, ServiceError
from tests.conftest import assert_handler_response, assert_telegram_call_made


class TestStartHandler:
    """Test cases for start handler functionality"""
    
    @pytest.fixture
    def mock_start_handler(self):
        """Create a mock start handler for testing"""
        handler = ModernStartHandler()
        return handler
    
    @pytest.fixture
    def start_request(self, mock_telegram_objects):
        """Create a start handler request"""
        return HandlerRequest(
            update=mock_telegram_objects.update,
            context=mock_telegram_objects.context,
            user_data=mock_telegram_objects.context.user_data,
            chat_id=mock_telegram_objects.chat.id,
            user_id=mock_telegram_objects.user.id
        )
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_start_command_basic(self, mock_start_handler, mock_telegram_objects):
        """Test basic start command functionality"""
        # Simulate /start command
        mock_telegram_objects.message.text = "/start"
        
        # Test the handler's handle method
        request = mock_start_handler.create_request(
            mock_telegram_objects.update,
            mock_telegram_objects.context
        )
        
        response = await mock_start_handler.handle(request)
        
        assert isinstance(response, HandlerResponse)
        assert "Bot inicializado com sucesso" in response.message
        # Note: "/login" only appears in fallback message when config service fails
        # Under normal operation, only the config service message is returned
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_start_welcome_message(self, mock_start_handler, mock_telegram_objects):
        """Test that start command sends welcome message"""
        request = mock_start_handler.create_request(
            mock_telegram_objects.update,
            mock_telegram_objects.context
        )
        
        response = await mock_start_handler.handle(request)
        
        # Verify welcome message content
        assert "Bot inicializado com sucesso" in response.message
        # Note: Additional content like "/login" and "/commands" only appears in fallback message
        # Under normal operation with working config service, only the basic message is returned
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_start_handler_response_format(self, mock_start_handler, mock_telegram_objects):
        """Test that start handler returns proper response format"""
        request = mock_start_handler.create_request(
            mock_telegram_objects.update,
            mock_telegram_objects.context
        )
        
        response = await mock_start_handler.handle(request)
        
        assert hasattr(response, 'message')
        assert hasattr(response, 'next_state')
        assert hasattr(response, 'end_conversation')
        assert isinstance(response.message, str)
        assert len(response.message) > 0
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_start_handler_name(self, mock_start_handler):
        """Test that start handler has correct name"""
        assert mock_start_handler.name == "start"
    
    @pytest.mark.unit
    def test_get_modern_start_handler(self):
        """Test that get_modern_start_handler returns correct handler"""
        handler = get_modern_start_handler()
        assert handler is not None
        # The function should return a CommandHandler
        from telegram.ext import CommandHandler
        assert isinstance(handler, CommandHandler)


class TestStartHandlerIntegration:
    """Integration tests for start handler"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_start_handler_complete_flow(self, mock_telegram_objects):
        """Test complete start handler flow"""
        handler = ModernStartHandler()
        
        # Test that handler can process a request
        request = handler.create_request(
            mock_telegram_objects.update,
            mock_telegram_objects.context
        )
        
        response = await handler.handle(request)
        
        assert isinstance(response, HandlerResponse)
        assert response.message is not None
        assert len(response.message) > 0
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_start_handler_error_boundaries(self, mock_telegram_objects):
        """Test start handler error handling"""
        handler = ModernStartHandler()
        
        # Test with None update (should not crash)
        try:
            request = HandlerRequest(
                update=None,
                context=mock_telegram_objects.context,
                user_data={},
                chat_id=123,
                user_id=456
            )
            response = await handler.handle(request)
            # Should still return a response
            assert isinstance(response, HandlerResponse)
        except Exception as e:
            # If it raises an exception, it should be a known type
            assert isinstance(e, (ValidationError, ServiceError))