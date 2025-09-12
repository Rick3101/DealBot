"""
Tests for the commands handler module.
Validates dynamic command listing based on user permissions using proper mocking.
"""

import pytest
from unittest.mock import Mock, patch

from handlers.commands_handler import ModernCommandsHandler
from handlers.base_handler import HandlerRequest, HandlerResponse
from models.user import User, UserLevel


class TestCommandsHandler:
    """Test cases for commands handler functionality with proper mocking"""
    
    @pytest.fixture
    def commands_handler(self):
        """Create a real commands handler for testing"""
        return ModernCommandsHandler()
    
    @pytest.fixture
    def commands_request(self, mock_telegram_objects):
        """Create a commands handler request"""
        return HandlerRequest(
            update=mock_telegram_objects.update,
            context=mock_telegram_objects.context,
            user_data=mock_telegram_objects.context.user_data,
            chat_id=mock_telegram_objects.chat.id,
            user_id=mock_telegram_objects.user.id
        )
    
    @pytest.mark.asyncio
    async def test_commands_basic_execution(self, commands_handler, commands_request):
        """Test basic commands command execution"""
        # Mock user service to return a user
        mock_user = User(id=1, username="testuser", level=UserLevel.USER)
        
        with patch('handlers.commands_handler.get_user_service') as mock_get_user_service:
            mock_user_service = Mock()
            mock_user_service.get_user_by_chat_id.return_value = mock_user
            mock_get_user_service.return_value = mock_user_service
            
            response = await commands_handler.handle(commands_request)
        
        assert "Comandos Disponíveis" in response.message
        assert "/start" in response.message
        assert "/login" in response.message
    
    @pytest.mark.asyncio
    async def test_commands_for_user_level(self, commands_handler, commands_request):
        """Test commands display for user level"""
        # Mock user service to return a user with USER level
        mock_user = User(id=1, username="testuser", level=UserLevel.USER)
        
        with patch('handlers.commands_handler.get_user_service') as mock_get_user_service:
            mock_user_service = Mock()
            mock_user_service.get_user_by_chat_id.return_value = mock_user
            mock_get_user_service.return_value = mock_user_service
            
            response = await commands_handler.handle(commands_request)
        
        # Verify user-level commands are present
        assert "/start" in response.message
        assert "/login" in response.message
        assert "/commands" in response.message
        
        # Verify admin commands are NOT present
        assert "/buy" not in response.message
        assert "/product" not in response.message
    
    @pytest.mark.asyncio
    async def test_commands_for_admin_level(self, commands_handler, commands_request):
        """Test commands display for admin level"""
        # Mock user service to return a user with ADMIN level
        mock_user = User(id=1, username="adminuser", level=UserLevel.ADMIN)
        
        with patch('handlers.commands_handler.get_user_service') as mock_get_user_service:
            mock_user_service = Mock()
            mock_user_service.get_user_by_chat_id.return_value = mock_user
            mock_get_user_service.return_value = mock_user_service
            
            response = await commands_handler.handle(commands_request)
        
        # Verify user-level commands are present
        assert "/start" in response.message
        assert "/login" in response.message
        
        # Verify admin commands are present
        assert "/buy" in response.message
        assert "/estoque" in response.message
        
        # Verify owner commands are NOT present (since this is admin, not owner)
        assert "/product" not in response.message
        assert "/user" not in response.message
    
    @pytest.mark.asyncio
    async def test_commands_for_owner_level(self, commands_handler, commands_request):
        """Test commands display for owner level"""
        # Mock user service to return a user with OWNER level
        mock_user = User(id=1, username="owneruser", level=UserLevel.OWNER)
        
        with patch('handlers.commands_handler.get_user_service') as mock_get_user_service:
            mock_user_service = Mock()
            mock_user_service.get_user_by_chat_id.return_value = mock_user
            mock_get_user_service.return_value = mock_user_service
            
            response = await commands_handler.handle(commands_request)
        
        # Verify user-level commands are present
        assert "/start" in response.message
        assert "/login" in response.message
        
        # Verify admin commands are present
        assert "/buy" in response.message
        assert "/estoque" in response.message
        
        # Verify owner commands are present
        assert "/product" in response.message
        assert "/user" in response.message
    
    @pytest.mark.asyncio
    async def test_commands_for_unauthenticated_user(self, commands_handler, commands_request):
        """Test commands display for unauthenticated user"""
        # Mock user service to return None (no user found)
        with patch('handlers.commands_handler.get_user_service') as mock_get_user_service:
            mock_user_service = Mock()
            mock_user_service.get_user_by_chat_id.return_value = None
            mock_get_user_service.return_value = mock_user_service
            
            response = await commands_handler.handle(commands_request)
        
        # Should get login prompt
        assert "Execute /login primeiro" in response.message
    
    @pytest.mark.asyncio
    async def test_commands_formatting(self, commands_handler, commands_request):
        """Test that commands are properly formatted"""
        mock_user = User(id=1, username="testuser", level=UserLevel.ADMIN)
        
        with patch('handlers.commands_handler.get_user_service') as mock_get_user_service:
            mock_user_service = Mock()
            mock_user_service.get_user_by_chat_id.return_value = mock_user
            mock_get_user_service.return_value = mock_user_service
            
            response = await commands_handler.handle(commands_request)
        
        # Check formatting
        assert "📋 **Comandos Disponíveis:**" in response.message
        assert "👤 **Usuário:**" in response.message
        assert "👮 **Admin:**" in response.message
    
    @pytest.mark.asyncio
    async def test_commands_with_descriptions(self, commands_handler, commands_request):
        """Test that commands include descriptions"""
        mock_user = User(id=1, username="testuser", level=UserLevel.USER)
        
        with patch('handlers.commands_handler.get_user_service') as mock_get_user_service:
            mock_user_service = Mock()
            mock_user_service.get_user_by_chat_id.return_value = mock_user
            mock_get_user_service.return_value = mock_user_service
            
            response = await commands_handler.handle(commands_request)
        
        # Check that commands have descriptions
        assert "/start - Iniciar o bot" in response.message
        assert "/login - Fazer login" in response.message
        assert "/commands - Listar comandos" in response.message
    
    @pytest.mark.asyncio
    async def test_commands_categorized_display(self, commands_handler, commands_request):
        """Test that commands are properly categorized"""
        mock_user = User(id=1, username="owneruser", level=UserLevel.OWNER)
        
        with patch('handlers.commands_handler.get_user_service') as mock_get_user_service:
            mock_user_service = Mock()
            mock_user_service.get_user_by_chat_id.return_value = mock_user
            mock_get_user_service.return_value = mock_user_service
            
            response = await commands_handler.handle(commands_request)
        
        # Check that all categories are present for owner
        assert "👤 **Usuário:**" in response.message
        assert "👮 **Admin:**" in response.message
        assert "👑 **Owner:**" in response.message
    
    @pytest.mark.asyncio
    async def test_commands_dynamic_availability(self, commands_handler, commands_request):
        """Test that commands are dynamically shown based on permission level"""
        # Test with different user levels
        test_cases = [
            (UserLevel.USER, ["/start", "/login"], ["/buy", "/product"]),
            (UserLevel.ADMIN, ["/start", "/login", "/buy"], ["/product", "/user"]),
            (UserLevel.OWNER, ["/start", "/login", "/buy", "/product"], [])
        ]
        
        for level, should_have, should_not_have in test_cases:
            mock_user = User(id=1, username="testuser", level=level)
            
            with patch('handlers.commands_handler.get_user_service') as mock_get_user_service:
                mock_user_service = Mock()
                mock_user_service.get_user_by_chat_id.return_value = mock_user
                mock_get_user_service.return_value = mock_user_service
                
                response = await commands_handler.handle(commands_request)
            
            # Check commands that should be present
            for command in should_have:
                assert command in response.message, f"{command} should be present for {level.value}"
            
            # Check commands that should NOT be present
            for command in should_not_have:
                assert command not in response.message, f"{command} should NOT be present for {level.value}"
    
    @pytest.mark.asyncio
    async def test_commands_error_handling(self, commands_handler, commands_request):
        """Test error handling in commands display"""
        # Test when user service throws an exception
        with patch('handlers.commands_handler.get_user_service') as mock_get_user_service:
            mock_user_service = Mock()
            mock_user_service.get_user_by_chat_id.side_effect = Exception("Service error")
            mock_get_user_service.return_value = mock_user_service
            
            # Should raise the exception since the handler doesn't have try/catch
            with pytest.raises(Exception) as exc_info:
                await commands_handler.handle(commands_request)
            
            assert "Service error" in str(exc_info.value)