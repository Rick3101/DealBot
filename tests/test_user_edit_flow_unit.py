#!/usr/bin/env python3
"""
Unit tests for user handler flow functionality.
Tests conversation state transitions and method calls following the established pattern.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from telegram import Update, Message, User, Chat, CallbackQuery
from telegram.ext import ConversationHandler

# Import handler and states
from handlers.user_handler import (
    ModernUserHandler, 
    USER_MENU, 
    USER_ADD_USERNAME,
    USER_ADD_PASSWORD,
    USER_REMOVE_SELECT,
    USER_EDIT_SELECT, 
    USER_EDIT_PROPERTY, 
    USER_EDIT_VALUE
)

# Import models  
from models.user import User as UserModel, UserLevel


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
class TestUserEditFlowUnit:
    """Unit tests for user handler conversation states."""
    
    def setup_method(self):
        """Set up each test with mocked dependencies."""
        self.handler = ModernUserHandler()
        self.context = MockTelegramObjects.create_context()
        
        # Mock users for testing
        self.mock_users = [
            Mock(id=1, username="user1", level=UserLevel.USER),
            Mock(id=2, username="admin1", level=UserLevel.ADMIN)
        ]
    
    async def test_user_menu_add_selection(self):
        """Test user menu add selection - unit test coverage."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func):
            
            # Test add user selection
            update = MockTelegramObjects.create_update(callback_data="add_user", chat_id=chat_id)
            result = await self.handler.menu_selection(update, self.context)
            
            # Should transition to USER_ADD_USERNAME state
            assert result == USER_ADD_USERNAME
    
    async def test_user_menu_edit_selection(self):
        """Test user menu edit selection - unit test coverage."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('core.modern_service_container.get_user_service') as mock_get_service:
            
            # Mock the user service
            mock_service = Mock()
            mock_service.get_all_users.return_value = self.mock_users
            mock_get_service.return_value = mock_service
            
            # Test edit user selection
            update = MockTelegramObjects.create_update(callback_data="edit_user", chat_id=chat_id)
            result = await self.handler.menu_selection(update, self.context)
            
            # Should transition to USER_EDIT_SELECT state
            assert result == USER_EDIT_SELECT
            
            # Verify service was called
            mock_service.get_all_users.assert_called_once()
    
    async def test_user_add_username_input(self):
        """Test user add username input - unit test coverage."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func):
            
            # Test entering username
            update = MockTelegramObjects.create_update("newuser", chat_id=chat_id)
            result = await self.handler.add_username(update, self.context)
            
            # Should transition to USER_ADD_PASSWORD state
            assert result == USER_ADD_PASSWORD
            
            # Verify username is stored
            assert 'new_username' in self.context.user_data
            assert self.context.user_data['new_username'] == "newuser"
    
    async def test_user_add_password_input(self):
        """Test user add password input - unit test coverage."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('core.modern_service_container.get_user_service') as mock_get_service:
            
            # Mock the user service
            mock_service = Mock()
            mock_service.create_user.return_value = Mock(id=3, username="newuser")
            mock_get_service.return_value = mock_service
            
            # Store username from previous state
            self.context.user_data['new_username'] = "newuser"
            
            # Test entering password
            update = MockTelegramObjects.create_update("password123", chat_id=chat_id)
            result = await self.handler.add_password(update, self.context)
            
            # Should complete conversation or return to menu
            assert result in [ConversationHandler.END, USER_MENU]
            
            # Verify create was attempted
            mock_service.create_user.assert_called_once()
    
    async def test_user_edit_select_callback(self):
        """Test user edit select callback - unit test coverage."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('core.modern_service_container.get_user_service') as mock_get_service:
            
            # Mock the user service
            mock_service = Mock()
            mock_service.get_user_by_id.return_value = self.mock_users[0]
            mock_get_service.return_value = mock_service
            
            # Test selecting a user to edit
            update = MockTelegramObjects.create_update(callback_data="edit_user:1", chat_id=chat_id)
            result = await self.handler.edit_user_callback(update, self.context)
            
            # Should transition to USER_EDIT_PROPERTY state
            assert result == USER_EDIT_PROPERTY
            
            # Verify user ID is stored
            assert 'editing_user_id' in self.context.user_data
    
    async def test_user_edit_property_selection(self):
        """Test user edit property selection - unit test coverage."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func):
            
            # Store user info in context (simulating previous states)
            self.context.user_data['editing_user_id'] = 1
            self.context.user_data['editing_user'] = self.mock_users[0]
            
            # Test selecting property to edit (e.g., "username")
            update = MockTelegramObjects.create_update(callback_data="edit_username", chat_id=chat_id)
            result = await self.handler.edit_property_callback(update, self.context)
            
            # Should transition to USER_EDIT_VALUE state
            assert result == USER_EDIT_VALUE
            
            # Verify property type is stored
            assert 'editing_property' in self.context.user_data
    
    async def test_user_edit_new_value_input(self):
        """Test user edit new value input - unit test coverage."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('core.modern_service_container.get_user_service') as mock_get_service:
            
            # Mock the user service
            mock_service = Mock()
            mock_service.update_user.return_value = True
            mock_get_service.return_value = mock_service
            
            # Store editing context (simulating previous states)
            self.context.user_data['editing_user_id'] = 1
            self.context.user_data['editing_property'] = 'username'
            
            # Test entering new value
            update = MockTelegramObjects.create_update("newusername", chat_id=chat_id)
            result = await self.handler.edit_value_input(update, self.context)
            
            # Should complete conversation or return to menu
            assert result in [ConversationHandler.END, USER_MENU]
            
            # Verify update was attempted
            mock_service.update_user.assert_called_once()
    
    async def test_user_remove_callback(self):
        """Test user remove callback - unit test coverage."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('core.modern_service_container.get_user_service') as mock_get_service:
            
            # Mock the user service
            mock_service = Mock()
            mock_service.delete_user.return_value = True
            mock_get_service.return_value = mock_service
            
            # Test removing a user
            update = MockTelegramObjects.create_update(callback_data="remove_user:1", chat_id=chat_id)
            result = await self.handler.remove_user_callback(update, self.context)
            
            # Should complete conversation or return to menu
            assert result in [ConversationHandler.END, USER_MENU]
            
            # Verify delete was attempted
            mock_service.delete_user.assert_called_once()
    
    async def test_conversation_states_registration(self):
        """Test conversation handler has all required states - unit test coverage."""
        
        # Get the conversation handler
        conv_handler = self.handler.get_conversation_handler()
        
        # Verify all user flow states are registered
        required_states = [
            USER_MENU,
            USER_ADD_USERNAME,
            USER_ADD_PASSWORD,
            USER_REMOVE_SELECT,
            USER_EDIT_SELECT, 
            USER_EDIT_PROPERTY,
            USER_EDIT_VALUE
        ]
        
        for state in required_states:
            assert state in conv_handler.states, f"State {state} not registered in conversation handler"
    
    async def test_user_flow_cancel_handling(self):
        """Test cancel operation during user flow."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func):
            
            # Test cancel from any user state
            update = MockTelegramObjects.create_update(callback_data="cancel", chat_id=chat_id)
            
            # Test cancel from edit select state
            result = await self.handler.cancel(update, self.context)
            assert result == ConversationHandler.END
    
    async def test_user_flow_error_scenarios(self):
        """Test error scenarios in user flow."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('core.modern_service_container.get_user_service') as mock_get_service:
            
            # Mock service to raise an error
            mock_service = Mock()
            mock_service.get_all_users.side_effect = Exception("Database error")
            mock_get_service.return_value = mock_service
            
            # Test error handling in edit user start
            update = MockTelegramObjects.create_update(callback_data="edit_user", chat_id=chat_id)
            result = await self.handler.menu_selection(update, self.context)
            
            # Should handle error gracefully
            assert result in [ConversationHandler.END, USER_MENU]
    
    async def test_user_flow_input_validation(self):
        """Test input validation in user flow."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func):
            
            # Test empty username input
            update = MockTelegramObjects.create_update("", chat_id=chat_id)
            result = await self.handler.add_username(update, self.context)
            
            # Should stay in same state or show error
            assert result in [USER_ADD_USERNAME, USER_MENU, ConversationHandler.END]
    
    async def test_user_flow_state_persistence(self):
        """Test that user flow maintains state correctly across transitions."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('core.modern_service_container.get_user_service') as mock_get_service:
            
            # Mock the user service
            mock_service = Mock()
            mock_service.get_all_users.return_value = self.mock_users
            mock_service.get_user_by_id.return_value = self.mock_users[0]
            mock_get_service.return_value = mock_service
            
            # Step 1: Start edit
            update = MockTelegramObjects.create_update(callback_data="edit_user", chat_id=chat_id)
            result1 = await self.handler.menu_selection(update, self.context)
            assert result1 == USER_EDIT_SELECT
            
            # Step 2: Select user
            update = MockTelegramObjects.create_update(callback_data="edit_user:1", chat_id=chat_id)
            result2 = await self.handler.edit_user_callback(update, self.context)
            assert result2 == USER_EDIT_PROPERTY
            
            # Verify state is maintained
            assert 'editing_user_id' in self.context.user_data
            assert self.context.user_data['editing_user_id'] == 1


if __name__ == "__main__":
    pytest.main([__file__])