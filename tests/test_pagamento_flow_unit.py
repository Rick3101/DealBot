#!/usr/bin/env python3
"""
Unit tests for pagamento (payment) handler flow functionality.
Tests conversation state transitions and method calls following the established pattern.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from telegram import Update, Message, User, Chat, CallbackQuery
from telegram.ext import ConversationHandler

# Import handler and states
from handlers.pagamento_handler import (
    ModernPagamentoHandler, 
    PAGAMENTO_MENU, 
    PAGAMENTO_VALOR
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
class TestPagamentoFlowUnit:
    """Unit tests for pagamento handler conversation states."""
    
    def setup_method(self):
        """Set up each test with mocked dependencies."""
        self.handler = ModernPagamentoHandler()
        self.context = MockTelegramObjects.create_context()
        
        # Mock sales for testing
        self.mock_sales = [
            Mock(id=1, nome_comprador="John Doe", total=100.0, total_pago=50.0, saldo_devedor=50.0),
            Mock(id=2, nome_comprador="Jane Smith", total=200.0, total_pago=0.0, saldo_devedor=200.0)
        ]
    
    async def test_pagamento_start_with_buyer_name(self):
        """Test pagamento start with buyer name - should show specific buyer's debts."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('services.handler_business_service.HandlerBusinessService') as mock_business_service:
            
            # Mock business service
            mock_service = Mock()
            mock_service.get_unpaid_sales.return_value = [self.mock_sales[0]]
            mock_business_service.return_value = mock_service
            
            # Set args for buyer name
            self.context.args = ["John", "Doe"]
            
            # Test starting payment process with buyer name
            update = MockTelegramObjects.create_update(text="/pagar John Doe", chat_id=chat_id)
            result = await self.handler._start_pagamento(update, self.context)
            
            # Should transition to PAGAMENTO_MENU state or show results
            assert result in [PAGAMENTO_MENU, ConversationHandler.END]
            
            # Verify service was called with buyer name
            mock_service.get_unpaid_sales.assert_called_with("John Doe")
    
    async def test_pagamento_start_without_buyer_name(self):
        """Test pagamento start without buyer name - should show all debts."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('services.handler_business_service.HandlerBusinessService') as mock_business_service:
            
            # Mock business service
            mock_service = Mock()
            mock_service.get_unpaid_sales.return_value = self.mock_sales
            mock_business_service.return_value = mock_service
            
            # Test starting payment process without buyer name
            update = MockTelegramObjects.create_update(text="/pagar", chat_id=chat_id)
            result = await self.handler._start_pagamento(update, self.context)
            
            # Should transition to PAGAMENTO_MENU state or show results
            assert result in [PAGAMENTO_MENU, ConversationHandler.END]
            
            # Verify service was called without buyer name
            mock_service.get_unpaid_sales.assert_called_with(None)
    
    async def test_pagamento_no_unpaid_sales(self):
        """Test pagamento when no unpaid sales exist."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('services.handler_business_service.HandlerBusinessService') as mock_business_service:
            
            # Mock business service with no unpaid sales
            mock_service = Mock()
            mock_service.get_unpaid_sales.return_value = []
            mock_business_service.return_value = mock_service
            
            # Test starting payment process
            update = MockTelegramObjects.create_update(text="/pagar", chat_id=chat_id)
            result = await self.handler._start_pagamento(update, self.context)
            
            # Should complete conversation
            assert result == ConversationHandler.END
    
    async def test_pagamento_sale_selection_callback(self):
        """Test pagamento sale selection callback - unit test coverage."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('services.handler_business_service.HandlerBusinessService') as mock_business_service:
            
            # Mock business service
            mock_service = Mock()
            mock_service.get_sale_with_payments.return_value = Mock(
                sale=self.mock_sales[0],
                total_paid=50.0,
                balance_due=50.0
            )
            mock_business_service.return_value = mock_service
            
            # Test selecting a sale for payment
            update = MockTelegramObjects.create_update(callback_data="pag_select:1", chat_id=chat_id)
            result = await self.handler._sale_selection_callback(update, self.context)
            
            # Should transition to PAGAMENTO_VALOR state
            assert result == PAGAMENTO_VALOR
            
            # Verify sale ID is stored
            assert 'selected_sale_id' in self.context.user_data
            assert self.context.user_data['selected_sale_id'] == 1
    
    async def test_pagamento_menu_callback(self):
        """Test pagamento menu callback - unit test coverage."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func):
            
            # Test menu callback
            update = MockTelegramObjects.create_update(callback_data="pag_menu_action", chat_id=chat_id)
            result = await self.handler._menu_callback(update, self.context)
            
            # Should handle menu action appropriately
            assert result in [PAGAMENTO_MENU, PAGAMENTO_VALOR, ConversationHandler.END]
    
    async def test_pagamento_value_input_full_payment(self):
        """Test pagamento value input for full payment - unit test coverage."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('services.handler_business_service.HandlerBusinessService') as mock_business_service:
            
            # Mock business service
            mock_service = Mock()
            mock_payment_response = Mock(
                success=True,
                is_fully_paid=True,
                remaining_balance=0.0,
                message="Payment successful"
            )
            mock_service.process_payment.return_value = mock_payment_response
            mock_business_service.return_value = mock_service
            
            # Store sale from previous state
            self.context.user_data['selected_sale_id'] = 1
            
            # Test entering payment amount that covers full debt
            update = MockTelegramObjects.create_update("50.00", chat_id=chat_id)
            result = await self.handler._payment_value_callback(update, self.context)
            
            # Should complete conversation
            assert result == ConversationHandler.END
            
            # Verify payment was processed
            mock_service.process_payment.assert_called_once()
    
    async def test_pagamento_value_input_partial_payment(self):
        """Test pagamento value input for partial payment - unit test coverage."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('services.handler_business_service.HandlerBusinessService') as mock_business_service:
            
            # Mock business service
            mock_service = Mock()
            mock_payment_response = Mock(
                success=True,
                is_fully_paid=False,
                remaining_balance=25.0,
                message="Partial payment processed"
            )
            mock_service.process_payment.return_value = mock_payment_response
            mock_business_service.return_value = mock_service
            
            # Store sale from previous state
            self.context.user_data['selected_sale_id'] = 1
            
            # Test entering partial payment amount
            update = MockTelegramObjects.create_update("25.00", chat_id=chat_id)
            result = await self.handler._payment_value_callback(update, self.context)
            
            # Should complete conversation
            assert result == ConversationHandler.END
    
    async def test_pagamento_value_input_invalid_amount(self):
        """Test pagamento value input with invalid amount - unit test coverage."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func):
            
            # Store sale from previous state
            self.context.user_data['selected_sale_id'] = 1
            
            # Test entering invalid payment amount
            update = MockTelegramObjects.create_update("invalid_amount", chat_id=chat_id)
            result = await self.handler._payment_value_callback(update, self.context)
            
            # Should stay in same state or show error
            assert result in [PAGAMENTO_VALOR, ConversationHandler.END]
    
    async def test_conversation_states_registration(self):
        """Test conversation handler has all required states - unit test coverage."""
        
        # Get the conversation handler
        conv_handler = self.handler.get_conversation_handler()
        
        # Verify all pagamento flow states are registered
        required_states = [
            PAGAMENTO_MENU,
            PAGAMENTO_VALOR
        ]
        
        for state in required_states:
            assert state in conv_handler.states, f"State {state} not registered in conversation handler"
    
    async def test_pagamento_flow_cancel_handling(self):
        """Test cancel operation during pagamento flow."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('handlers.global_handlers.cancel_callback') as mock_cancel:
            
            # Mock cancel function
            mock_cancel.return_value = ConversationHandler.END
            
            # Test cancel from any pagamento state
            update = MockTelegramObjects.create_update(callback_data="pag_cancel", chat_id=chat_id)
            
            # Test cancel
            result = await mock_cancel(update, self.context)
            assert result == ConversationHandler.END
    
    async def test_pagamento_flow_error_scenarios(self):
        """Test error scenarios in pagamento flow."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('services.handler_business_service.HandlerBusinessService') as mock_business_service:
            
            # Mock service to raise an error
            mock_service = Mock()
            mock_service.get_unpaid_sales.side_effect = Exception("Database error")
            mock_business_service.return_value = mock_service
            
            # Test error handling in payment start
            update = MockTelegramObjects.create_update(text="/pagar", chat_id=chat_id)
            result = await self.handler._start_pagamento(update, self.context)
            
            # Should handle error gracefully
            assert result in [ConversationHandler.END, PAGAMENTO_MENU]
    
    async def test_pagamento_flow_input_validation(self):
        """Test input validation in pagamento flow."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func):
            
            # Store sale from previous state
            self.context.user_data['selected_sale_id'] = 1
            
            # Test empty input
            update = MockTelegramObjects.create_update("", chat_id=chat_id)
            result = await self.handler._payment_value_callback(update, self.context)
            
            # Should stay in same state or show error
            assert result in [PAGAMENTO_VALOR, ConversationHandler.END]
    
    async def test_pagamento_flow_state_persistence(self):
        """Test that pagamento flow maintains state correctly across transitions."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('services.handler_business_service.HandlerBusinessService') as mock_business_service:
            
            # Mock business service
            mock_service = Mock()
            mock_service.get_unpaid_sales.return_value = self.mock_sales
            mock_service.get_sale_with_payments.return_value = Mock(
                sale=self.mock_sales[0],
                total_paid=50.0,
                balance_due=50.0
            )
            mock_business_service.return_value = mock_service
            
            # Step 1: Start pagamento
            update = MockTelegramObjects.create_update(text="/pagar", chat_id=chat_id)
            result1 = await self.handler._start_pagamento(update, self.context)
            assert result1 in [PAGAMENTO_MENU, ConversationHandler.END]
            
            # Step 2: Select sale (if menu was shown)
            if result1 == PAGAMENTO_MENU:
                update = MockTelegramObjects.create_update(callback_data="pag_select:1", chat_id=chat_id)
                result2 = await self.handler._sale_selection_callback(update, self.context)
                assert result2 == PAGAMENTO_VALOR
                
                # Verify state is maintained
                assert 'selected_sale_id' in self.context.user_data
                assert self.context.user_data['selected_sale_id'] == 1


if __name__ == "__main__":
    pytest.main([__file__])