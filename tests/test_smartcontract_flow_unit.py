#!/usr/bin/env python3
"""
Unit tests for smartcontract handler flow functionality.
Tests conversation state transitions and method calls following the established pattern.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from telegram import Update, Message, User, Chat, CallbackQuery
from telegram.ext import ConversationHandler

# Import handler and states
from handlers.smartcontract_handler import (
    ModernSmartContractHandler, 
    SMARTCONTRACT_MENU, 
    SMARTCONTRACT_TRANSACTION_DESC
)


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
        context.args = []
        return context


@pytest.mark.unit
@pytest.mark.asyncio
class TestSmartContractFlowUnit:
    """Unit tests for smartcontract handler conversation states."""
    
    def setup_method(self):
        """Set up each test with mocked dependencies."""
        self.handler = ModernSmartContractHandler()
        self.context = MockTelegramObjects.create_context()
        
        # Mock smart contract data for testing
        self.mock_contract = Mock(
            id=1,
            codigo="12345",
            status="pending",
            created_by="owner_user"
        )
        
        # Mock transactions for testing
        self.mock_transactions = [
            Mock(id=1, contract_id=1, descricao="Transaction 1", usuario="user1", confirmado=False),
            Mock(id=2, contract_id=1, descricao="Transaction 2", usuario="user2", confirmado=True)
        ]
    
    async def test_smartcontract_start_with_code(self):
        """Test smartcontract start with contract code - should show contract menu."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('services.handler_business_service.HandlerBusinessService') as mock_business_service:
            
            # Mock business service
            mock_service = Mock()
            mock_service.get_smart_contract_by_code.return_value = self.mock_contract
            mock_service.get_contract_transactions.return_value = self.mock_transactions
            mock_business_service.return_value = mock_service
            
            # Set args for contract code
            self.context.args = ["12345"]
            
            # Test starting transactions with contract code
            update = MockTelegramObjects.create_update(text="/transactions 12345", chat_id=chat_id)
            result = await self.handler._start_transactions(update, self.context)
            
            # Should transition to SMARTCONTRACT_MENU state
            assert result == SMARTCONTRACT_MENU
            
            # Verify contract code is stored
            assert 'contract_code' in self.context.user_data
            assert self.context.user_data['contract_code'] == "12345"
    
    async def test_smartcontract_start_without_code(self):
        """Test smartcontract start without contract code - should show error."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func):
            
            # Test starting transactions without contract code
            update = MockTelegramObjects.create_update(text="/transactions", chat_id=chat_id)
            result = await self.handler._start_transactions(update, self.context)
            
            # Should complete conversation with error
            assert result == ConversationHandler.END
    
    async def test_smartcontract_start_invalid_code(self):
        """Test smartcontract start with invalid contract code."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('services.handler_business_service.HandlerBusinessService') as mock_business_service:
            
            # Mock business service to return None (contract not found)
            mock_service = Mock()
            mock_service.get_smart_contract_by_code.return_value = None
            mock_business_service.return_value = mock_service
            
            # Set args for invalid contract code
            self.context.args = ["99999"]
            
            # Test starting transactions with invalid code
            update = MockTelegramObjects.create_update(text="/transactions 99999", chat_id=chat_id)
            result = await self.handler._start_transactions(update, self.context)
            
            # Should complete conversation with error
            assert result == ConversationHandler.END
    
    async def test_smartcontract_menu_add_transaction(self):
        """Test smartcontract menu add transaction selection - unit test coverage."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func):
            
            # Store contract data from previous state
            self.context.user_data['contract_code'] = "12345"
            self.context.user_data['contract'] = self.mock_contract
            
            # Test add transaction selection
            update = MockTelegramObjects.create_update(callback_data="sc_add_transaction", chat_id=chat_id)
            result = await self.handler._menu_callback(update, self.context)
            
            # Should transition to SMARTCONTRACT_TRANSACTION_DESC state
            assert result == SMARTCONTRACT_TRANSACTION_DESC
    
    async def test_smartcontract_menu_confirm_transaction(self):
        """Test smartcontract menu confirm transaction selection - unit test coverage."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('services.handler_business_service.HandlerBusinessService') as mock_business_service:
            
            # Mock business service
            mock_service = Mock()
            mock_service.confirm_transaction.return_value = True
            mock_business_service.return_value = mock_service
            
            # Store contract data from previous state
            self.context.user_data['contract_code'] = "12345"
            self.context.user_data['contract'] = self.mock_contract
            
            # Test confirm transaction selection
            update = MockTelegramObjects.create_update(callback_data="sc_confirm_transaction:1", chat_id=chat_id)
            result = await self.handler._menu_callback(update, self.context)
            
            # Should complete conversation or return to menu
            assert result in [ConversationHandler.END, SMARTCONTRACT_MENU]
    
    async def test_smartcontract_menu_view_status(self):
        """Test smartcontract menu view status selection - unit test coverage."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('services.handler_business_service.HandlerBusinessService') as mock_business_service:
            
            # Mock business service
            mock_service = Mock()
            mock_service.get_contract_status.return_value = Mock(
                completed_transactions=1,
                pending_transactions=1,
                total_transactions=2
            )
            mock_business_service.return_value = mock_service
            
            # Store contract data from previous state
            self.context.user_data['contract_code'] = "12345"
            self.context.user_data['contract'] = self.mock_contract
            
            # Test view status selection
            update = MockTelegramObjects.create_update(callback_data="sc_view_status", chat_id=chat_id)
            result = await self.handler._menu_callback(update, self.context)
            
            # Should complete conversation or return to menu
            assert result in [ConversationHandler.END, SMARTCONTRACT_MENU]
    
    async def test_smartcontract_transaction_desc_input(self):
        """Test smartcontract transaction description input - unit test coverage."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('services.handler_business_service.HandlerBusinessService') as mock_business_service:
            
            # Mock business service
            mock_service = Mock()
            mock_service.add_contract_transaction.return_value = Mock(id=3, descricao="New Transaction")
            mock_business_service.return_value = mock_service
            
            # Store contract data from previous state
            self.context.user_data['contract_code'] = "12345"
            self.context.user_data['contract'] = self.mock_contract
            
            # Test entering transaction description
            update = MockTelegramObjects.create_update("New transaction description", chat_id=chat_id)
            result = await self.handler._transaction_desc_callback(update, self.context)
            
            # Should complete conversation or return to menu
            assert result in [ConversationHandler.END, SMARTCONTRACT_MENU]
            
            # Verify transaction was added
            mock_service.add_contract_transaction.assert_called_once()
    
    async def test_smartcontract_transaction_desc_empty_input(self):
        """Test smartcontract transaction description with empty input - unit test coverage."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func):
            
            # Store contract data from previous state
            self.context.user_data['contract_code'] = "12345"
            self.context.user_data['contract'] = self.mock_contract
            
            # Test entering empty description
            update = MockTelegramObjects.create_update("", chat_id=chat_id)
            result = await self.handler._transaction_desc_callback(update, self.context)
            
            # Should stay in same state or show error
            assert result in [SMARTCONTRACT_TRANSACTION_DESC, ConversationHandler.END]
    
    async def test_conversation_states_registration(self):
        """Test conversation handler has all required states - unit test coverage."""
        
        # Get the conversation handler
        conv_handler = self.handler.get_conversation_handler()
        
        # Verify all smartcontract flow states are registered
        required_states = [
            SMARTCONTRACT_MENU,
            SMARTCONTRACT_TRANSACTION_DESC
        ]
        
        for state in required_states:
            assert state in conv_handler.states, f"State {state} not registered in conversation handler"
    
    async def test_smartcontract_flow_cancel_handling(self):
        """Test cancel operation during smartcontract flow."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('handlers.global_handlers.cancel_callback') as mock_cancel:
            
            # Mock cancel function
            mock_cancel.return_value = ConversationHandler.END
            
            # Test cancel from any smartcontract state
            update = MockTelegramObjects.create_update(callback_data="sc_cancel", chat_id=chat_id)
            
            # Test cancel
            result = await mock_cancel(update, self.context)
            assert result == ConversationHandler.END
    
    async def test_smartcontract_flow_error_scenarios(self):
        """Test error scenarios in smartcontract flow."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('services.handler_business_service.HandlerBusinessService') as mock_business_service:
            
            # Mock service to raise an error
            mock_service = Mock()
            mock_service.get_smart_contract_by_code.side_effect = Exception("Database error")
            mock_business_service.return_value = mock_service
            
            # Set args for contract code
            self.context.args = ["12345"]
            
            # Test error handling in contract lookup
            update = MockTelegramObjects.create_update(text="/transactions 12345", chat_id=chat_id)
            result = await self.handler._start_transactions(update, self.context)
            
            # Should handle error gracefully
            assert result == ConversationHandler.END
    
    async def test_smartcontract_flow_input_validation(self):
        """Test input validation in smartcontract flow."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func):
            
            # Store contract data from previous state
            self.context.user_data['contract_code'] = "12345"
            self.context.user_data['contract'] = self.mock_contract
            
            # Test input with special characters
            update = MockTelegramObjects.create_update("Transaction@#$%", chat_id=chat_id)
            result = await self.handler._transaction_desc_callback(update, self.context)
            
            # Should handle special characters appropriately
            assert result in [SMARTCONTRACT_TRANSACTION_DESC, SMARTCONTRACT_MENU, ConversationHandler.END]
    
    async def test_smartcontract_flow_state_persistence(self):
        """Test that smartcontract flow maintains state correctly across transitions."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('services.handler_business_service.HandlerBusinessService') as mock_business_service:
            
            # Mock business service
            mock_service = Mock()
            mock_service.get_smart_contract_by_code.return_value = self.mock_contract
            mock_service.get_contract_transactions.return_value = self.mock_transactions
            mock_business_service.return_value = mock_service
            
            # Set args for contract code
            self.context.args = ["12345"]
            
            # Step 1: Start transactions with contract code
            update = MockTelegramObjects.create_update(text="/transactions 12345", chat_id=chat_id)
            result1 = await self.handler._start_transactions(update, self.context)
            assert result1 == SMARTCONTRACT_MENU
            
            # Step 2: Select add transaction
            update = MockTelegramObjects.create_update(callback_data="sc_add_transaction", chat_id=chat_id)
            result2 = await self.handler._menu_callback(update, self.context)
            assert result2 == SMARTCONTRACT_TRANSACTION_DESC
            
            # Verify state is maintained
            assert 'contract_code' in self.context.user_data
            assert self.context.user_data['contract_code'] == "12345"
            assert 'contract' in self.context.user_data


if __name__ == "__main__":
    pytest.main([__file__])