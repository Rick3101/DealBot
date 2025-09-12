"""
Tests for basic handler functionality without specific handler imports.
Tests the base handler classes and patterns.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from telegram.ext import ConversationHandler

from handlers.base_handler import HandlerRequest, HandlerResponse, BaseHandler
from services.base_service import ValidationError, ServiceError, NotFoundError, DuplicateError


class TestHandlerRequest:
    """Test HandlerRequest dataclass"""
    
    def test_handler_request_creation(self, mock_telegram_objects):
        """Test creating HandlerRequest from mock objects"""
        request = HandlerRequest(
            update=mock_telegram_objects.update,
            context=mock_telegram_objects.context,
            user_data=mock_telegram_objects.context.user_data,
            chat_id=mock_telegram_objects.chat.id,
            user_id=mock_telegram_objects.user.id
        )
        
        assert request.update == mock_telegram_objects.update
        assert request.context == mock_telegram_objects.context
        assert request.chat_id == mock_telegram_objects.chat.id
        assert request.user_id == mock_telegram_objects.user.id
        assert request.user_data == mock_telegram_objects.context.user_data


class TestHandlerResponse:
    """Test HandlerResponse dataclass"""
    
    def test_handler_response_creation(self):
        """Test creating HandlerResponse with basic message"""
        response = HandlerResponse(message="Test message")
        
        assert response.message == "Test message"
        assert response.keyboard is None
        assert response.next_state is None
        assert response.end_conversation is False
        assert response.delay == 10
        assert response.protected is False
    
    def test_handler_response_with_all_fields(self):
        """Test creating HandlerResponse with all fields"""
        keyboard = Mock()
        response = HandlerResponse(
            message="Test message",
            keyboard=keyboard,
            next_state=5,
            end_conversation=True,
            delay=15,
            protected=True
        )
        
        assert response.message == "Test message"
        assert response.keyboard == keyboard
        assert response.next_state == 5
        assert response.end_conversation is True
        assert response.delay == 15
        assert response.protected is True


class MockTestHandler(BaseHandler):
    """Mock handler for testing BaseHandler functionality"""
    
    def __init__(self):
        super().__init__("test_handler")
    
    async def handle(self, request: HandlerRequest) -> HandlerResponse:
        """Basic handle implementation"""
        return HandlerResponse(message="Test response")
    
    def get_retry_state(self):
        """Return retry state"""
        return 1


class TestBaseHandler:
    """Test BaseHandler functionality"""
    
    def test_base_handler_creation(self):
        """Test creating BaseHandler instance"""
        handler = MockTestHandler()
        assert handler.name == "test_handler"
        assert handler.logger is not None
    
    def test_create_request(self, mock_telegram_objects):
        """Test creating request from update and context"""
        handler = MockTestHandler()
        request = handler.create_request(
            mock_telegram_objects.update,
            mock_telegram_objects.context
        )
        
        assert isinstance(request, HandlerRequest)
        assert request.update == mock_telegram_objects.update
        assert request.context == mock_telegram_objects.context
        assert request.chat_id == mock_telegram_objects.chat.id
        assert request.user_id == mock_telegram_objects.user.id
    
    @pytest.mark.asyncio
    async def test_handle_validation_error(self, mock_telegram_objects):
        """Test handling ValidationError"""
        handler = MockTestHandler()
        request = handler.create_request(
            mock_telegram_objects.update,
            mock_telegram_objects.context
        )
        
        error = ValidationError("Invalid input")
        response = await handler.handle_error(error, request)
        
        assert isinstance(response, HandlerResponse)
        assert "Invalid input" in response.message
        assert response.next_state == 1  # retry state
        assert response.delay == 5
    
    @pytest.mark.asyncio
    async def test_handle_not_found_error(self, mock_telegram_objects):
        """Test handling NotFoundError"""
        handler = MockTestHandler()
        request = handler.create_request(
            mock_telegram_objects.update,
            mock_telegram_objects.context
        )
        
        error = NotFoundError("Item not found")
        response = await handler.handle_error(error, request)
        
        assert isinstance(response, HandlerResponse)
        assert "não encontrado" in response.message
        assert response.end_conversation is True
    
    @pytest.mark.asyncio
    async def test_handle_duplicate_error(self, mock_telegram_objects):
        """Test handling DuplicateError"""
        handler = MockTestHandler()
        request = handler.create_request(
            mock_telegram_objects.update,
            mock_telegram_objects.context
        )
        
        error = DuplicateError("Already exists")
        response = await handler.handle_error(error, request)
        
        assert isinstance(response, HandlerResponse)
        assert "Already exists" in response.message
        assert response.next_state == 1  # retry state
        assert response.delay == 5
    
    @pytest.mark.asyncio
    async def test_handle_service_error(self, mock_telegram_objects):
        """Test handling ServiceError"""
        handler = MockTestHandler()
        request = handler.create_request(
            mock_telegram_objects.update,
            mock_telegram_objects.context
        )
        
        error = ServiceError("Database error")
        response = await handler.handle_error(error, request)
        
        assert isinstance(response, HandlerResponse)
        assert "Erro interno" in response.message
        assert response.next_state == 1  # retry state
        assert response.delay == 5
    
    @pytest.mark.asyncio
    async def test_handle_unexpected_error(self, mock_telegram_objects):
        """Test handling unexpected error"""
        handler = MockTestHandler()
        request = handler.create_request(
            mock_telegram_objects.update,
            mock_telegram_objects.context
        )
        
        error = Exception("Unexpected error")
        response = await handler.handle_error(error, request)
        
        assert isinstance(response, HandlerResponse)
        assert "Erro inesperado" in response.message
        assert response.end_conversation is True
    
    @pytest.mark.asyncio
    async def test_send_response_basic(self, mock_telegram_objects):
        """Test sending basic response"""
        handler = MockTestHandler()
        request = handler.create_request(
            mock_telegram_objects.update,
            mock_telegram_objects.context
        )
        
        response = HandlerResponse(message="Test message", end_conversation=True)
        
        with patch('handlers.base_handler.send_and_delete', new_callable=AsyncMock) as mock_send:
            result = await handler.send_response(response, request)
            
            assert result == ConversationHandler.END
            mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_response_with_keyboard(self, mock_telegram_objects):
        """Test sending response with keyboard"""
        handler = MockTestHandler()
        request = handler.create_request(
            mock_telegram_objects.update,
            mock_telegram_objects.context
        )
        
        keyboard = Mock()
        response = HandlerResponse(
            message="Test message", 
            keyboard=keyboard,
            next_state=2
        )
        
        with patch('handlers.base_handler.send_menu_with_delete', new_callable=AsyncMock) as mock_send:
            result = await handler.send_response(response, request)
            
            assert result == 2
            mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_user_permission_valid(self, mock_telegram_objects):
        """Test user permission validation with valid permission"""
        handler = MockTestHandler()
        request = handler.create_request(
            mock_telegram_objects.update,
            mock_telegram_objects.context
        )
        
        mock_user_service = Mock()
        mock_user_service.get_user_permission_level.return_value = Mock(value="admin")
        
        with patch('handlers.base_handler.get_user_service', return_value=mock_user_service):
            result = await handler.validate_user_permission(request, "admin")
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_user_permission_insufficient(self, mock_telegram_objects):
        """Test user permission validation with insufficient permission"""
        handler = MockTestHandler()
        request = handler.create_request(
            mock_telegram_objects.update,
            mock_telegram_objects.context
        )
        
        mock_user_service = Mock()
        mock_user_service.get_user_permission_level.return_value = Mock(value="user")
        
        with patch('handlers.base_handler.get_user_service', return_value=mock_user_service):
            result = await handler.validate_user_permission(request, "admin")
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_validate_user_permission_service_error(self, mock_telegram_objects):
        """Test user permission validation with service error"""
        handler = MockTestHandler()
        request = handler.create_request(
            mock_telegram_objects.update,
            mock_telegram_objects.context
        )
        
        mock_user_service = Mock()
        mock_user_service.get_user_permission_level.side_effect = ServiceError("Database error")
        
        with patch('handlers.base_handler.get_user_service', return_value=mock_user_service):
            result = await handler.validate_user_permission(request, "admin")
            
            assert result is False


class TestServiceErrorHandling:
    """Test service error handling patterns"""
    
    def test_validation_error_creation(self):
        """Test creating ValidationError"""
        error = ValidationError("Invalid input")
        assert str(error) == "Invalid input"
        assert isinstance(error, ServiceError)
    
    def test_not_found_error_creation(self):
        """Test creating NotFoundError"""
        error = NotFoundError("Item not found")
        assert str(error) == "Item not found"
        assert isinstance(error, ServiceError)
    
    def test_duplicate_error_creation(self):
        """Test creating DuplicateError"""
        error = DuplicateError("Already exists")
        assert str(error) == "Already exists"
        assert isinstance(error, ServiceError)