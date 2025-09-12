"""
Login handler tests using proven mocking strategy.
Tests core login functionality with comprehensive service mocking.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from telegram.ext import ConversationHandler

from handlers.login_handler import ModernLoginHandler, LOGIN_USERNAME, LOGIN_PASSWORD
from handlers.base_handler import HandlerRequest, HandlerResponse
from models.user import User, UserLevel
from services.base_service import ValidationError, ServiceError


class TestLoginHandler:
    """Test cases for login handler functionality with proper mocking"""
    
    @pytest.fixture
    def login_handler(self):
        """Create a real login handler for testing"""
        return ModernLoginHandler()
    
    @pytest.fixture
    def login_request(self, mock_telegram_objects):
        """Create a login handler request"""
        return HandlerRequest(
            update=mock_telegram_objects.update,
            context=mock_telegram_objects.context,
            user_data=mock_telegram_objects.context.user_data,
            chat_id=mock_telegram_objects.chat.id,
            user_id=mock_telegram_objects.user.id
        )
    
    @pytest.mark.asyncio
    async def test_login_basic_execution(self, login_handler, login_request):
        """Test basic login command execution"""
        # Basic handle() doesn't require service mocking - it just returns the username prompt
        response = await login_handler.handle(login_request)
        
        assert response is not None
        assert isinstance(response, HandlerResponse)
        assert "usuário" in response.message.lower() or "username" in response.message.lower()
    
    @pytest.mark.asyncio
    async def test_login_successful_authentication(self, login_handler, login_request):
        """Test successful authentication flow"""
        # Mock the HandlerBusinessService where it's imported in the login handler
        with patch('handlers.login_handler.HandlerBusinessService') as mock_business_service_class:
            mock_business_service = Mock()
            mock_response = Mock()
            mock_response.success = True
            mock_response.message = "Login realizado com sucesso!"
            mock_business_service.process_login = Mock(return_value=mock_response)
            mock_business_service_class.return_value = mock_business_service
            
            # Test complete form processing
            form_data = {
                "username": "validuser",
                "password": "validpass123"
            }
            
            response = await login_handler.process_form_data(login_request, form_data)
        
        # Verify successful login response
        assert response.end_conversation == True
        assert "sucesso" in response.message.lower()
    
    @pytest.mark.asyncio
    async def test_login_failed_authentication(self, login_handler, login_request):
        """Test failed authentication"""
        # Mock the HandlerBusinessService where it's imported in the login handler
        with patch('handlers.login_handler.HandlerBusinessService') as mock_business_service_class:
            mock_business_service = Mock()
            mock_response = Mock()
            mock_response.success = False
            mock_response.message = "❌ Credenciais inválidas"
            mock_business_service.process_login = Mock(return_value=mock_response)
            mock_business_service_class.return_value = mock_business_service
            
            response = await login_handler.process_form_data(login_request, {
                "username": "testuser", 
                "password": "wrongpass"
            })
        
        assert "❌" in response.message
        assert "credenciais" in response.message.lower() or "inválidas" in response.message.lower()
    
    @pytest.mark.asyncio
    async def test_login_service_error_handling(self, login_handler, login_request):
        """Test handling of service errors during login"""
        # Mock the HandlerBusinessService where it's imported in the login handler
        with patch('handlers.login_handler.HandlerBusinessService') as mock_business_service_class:
            mock_business_service = Mock()
            mock_business_service.process_login = Mock(side_effect=ServiceError("Database error"))
            mock_business_service_class.return_value = mock_business_service
            
            # The handler doesn't catch ServiceError, so we expect it to raise
            with pytest.raises(ServiceError):
                await login_handler.process_form_data(login_request, {
                    "username": "testuser",
                    "password": "testpass"
                })
    
    @pytest.mark.asyncio
    async def test_login_validation_error_handling(self, login_handler, login_request):
        """Test handling of validation errors"""
        # Mock the HandlerBusinessService where it's imported in the login handler
        with patch('handlers.login_handler.HandlerBusinessService') as mock_business_service_class:
            mock_business_service = Mock()
            mock_business_service.process_login = Mock(side_effect=ValidationError("Invalid input"))
            mock_business_service_class.return_value = mock_business_service
            
            # The handler doesn't catch ValidationError, so we expect it to raise
            with pytest.raises(ValidationError):
                await login_handler.process_form_data(login_request, {
                    "username": "testuser",
                    "password": "testpass"
                })
    
    @pytest.mark.asyncio
    async def test_login_username_state_flow(self, login_handler, login_request):
        """Test username input state flow"""
        # Basic handle() doesn't require service mocking
        response = await login_handler.handle(login_request)
        
        assert response.next_state == LOGIN_USERNAME
        assert "usuário" in response.message.lower() or "username" in response.message.lower()
    
    @pytest.mark.asyncio
    async def test_login_password_state_flow(self, login_handler, login_request):
        """Test password input state flow"""
        # Set up form data for password state
        login_request.user_data["username"] = "testuser"
        login_request.update.message.text = "validpass"
        
        with patch('handlers.login_handler.HandlerBusinessService') as mock_business_service_class:
            mock_business_service = Mock()
            mock_response = Mock()
            mock_response.success = True
            mock_response.message = "Login successful"
            mock_business_service.process_login = Mock(return_value=mock_response)
            mock_business_service_class.return_value = mock_business_service
            
            response = await login_handler.process_form_data(login_request, {
                "username": "testuser",
                "password": "validpass"
            })
        
        assert response.end_conversation == True
    
    @pytest.mark.parametrize("username,expected_valid", [
        ("validuser", True),
        ("a", False),      # Too short
        ("", False),       # Empty
        ("user_with_underscore", True),
        ("user123", True),
        ("x" * 200, False),  # Too long
    ])
    def test_username_validation(self, username, expected_valid):
        """Test username validation with various inputs"""
        from utils.input_sanitizer import InputSanitizer
        
        try:
            sanitized = InputSanitizer.sanitize_username(username)
            result = True
        except (ValueError, TypeError):
            result = False
        
        assert result == expected_valid
    
    @pytest.mark.parametrize("password,expected_valid", [
        ("validpass123", True),
        ("123", False),     # Too short
        ("", False),        # Empty
        ("x" * 200, False), # Too long
    ])
    def test_password_validation(self, password, expected_valid):
        """Test password validation with various inputs"""
        from utils.input_sanitizer import InputSanitizer
        
        try:
            sanitized = InputSanitizer.sanitize_password(password)
            result = True
        except (ValueError, TypeError):
            result = False
        
        assert result == expected_valid