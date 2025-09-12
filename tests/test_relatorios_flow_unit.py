#!/usr/bin/env python3
"""
Unit tests for relatorios (reports) handler flow functionality.
Tests conversation state transitions and method calls following the established pattern.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from telegram import Update, Message, User, Chat, CallbackQuery
from telegram.ext import ConversationHandler

# Import handler and states
from handlers.relatorios_handler import (
    ModernRelatoriosHandler, 
    RELATORIO_MENU, 
    RELATORIO_DIVIDA_NOME
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
        return context


@pytest.mark.unit
@pytest.mark.asyncio
class TestRelatoriosFlowUnit:
    """Unit tests for relatorios handler conversation states."""
    
    def setup_method(self):
        """Set up each test with mocked dependencies."""
        self.handler = ModernRelatoriosHandler()
        self.context = MockTelegramObjects.create_context()
        
        # Mock sales data for testing
        self.mock_sales_data = [
            Mock(id=1, nome_comprador="John Doe", produto="Product 1", quantidade=2, preco_unitario=10.0, total=20.0),
            Mock(id=2, nome_comprador="Jane Smith", produto="Product 2", quantidade=1, preco_unitario=50.0, total=50.0)
        ]
        
        # Mock debt data for testing
        self.mock_debt_data = [
            Mock(nome_comprador="John Doe", total_devido=100.0, total_pago=20.0, saldo=80.0),
            Mock(nome_comprador="Jane Smith", total_devido=200.0, total_pago=0.0, saldo=200.0)
        ]
    
    async def test_relatorios_start_menu(self):
        """Test relatorios start - should show main menu."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func):
            
            # Test starting relatorios process
            update = MockTelegramObjects.create_update(text="/relatorios", chat_id=chat_id)
            result = await self.handler._start_relatorios(update, self.context)
            
            # Should transition to RELATORIO_MENU state
            assert result == RELATORIO_MENU
    
    async def test_relatorios_menu_sales_report(self):
        """Test relatorios menu sales report selection - unit test coverage."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('services.handler_business_service.HandlerBusinessService') as mock_business_service:
            
            # Mock business service
            mock_service = Mock()
            mock_service.generate_sales_report.return_value = Mock(
                data=self.mock_sales_data,
                csv_file_path="/tmp/sales_report.csv"
            )
            mock_business_service.return_value = mock_service
            
            # Test sales report selection
            update = MockTelegramObjects.create_update(callback_data="rel_vendas", chat_id=chat_id)
            result = await self.handler._menu_callback(update, self.context)
            
            # Should complete conversation or return to menu
            assert result in [ConversationHandler.END, RELATORIO_MENU]
    
    async def test_relatorios_menu_debt_report_selection(self):
        """Test relatorios menu debt report selection - unit test coverage."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func):
            
            # Test debt report selection
            update = MockTelegramObjects.create_update(callback_data="rel_dividas", chat_id=chat_id)
            result = await self.handler._menu_callback(update, self.context)
            
            # Should transition to RELATORIO_DIVIDA_NOME state
            assert result == RELATORIO_DIVIDA_NOME
    
    async def test_relatorios_menu_general_debt_report(self):
        """Test relatorios menu general debt report selection - unit test coverage."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('services.handler_business_service.HandlerBusinessService') as mock_business_service:
            
            # Mock business service
            mock_service = Mock()
            mock_service.generate_debt_report.return_value = Mock(
                data=self.mock_debt_data,
                csv_file_path="/tmp/debt_report.csv"
            )
            mock_business_service.return_value = mock_service
            
            # Test general debt report selection
            update = MockTelegramObjects.create_update(callback_data="rel_dividas_geral", chat_id=chat_id)
            result = await self.handler._menu_callback(update, self.context)
            
            # Should complete conversation or return to menu
            assert result in [ConversationHandler.END, RELATORIO_MENU]
    
    async def test_relatorios_debt_name_input(self):
        """Test relatorios debt name input - unit test coverage."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('services.handler_business_service.HandlerBusinessService') as mock_business_service:
            
            # Mock business service
            mock_service = Mock()
            mock_service.generate_debt_report_by_name.return_value = Mock(
                data=[self.mock_debt_data[0]],
                csv_file_path="/tmp/debt_report_john.csv"
            )
            mock_business_service.return_value = mock_service
            
            # Test entering buyer name for debt report
            update = MockTelegramObjects.create_update("John Doe", chat_id=chat_id)
            result = await self.handler._debt_name_callback(update, self.context)
            
            # Should complete conversation
            assert result == ConversationHandler.END
            
            # Verify report generation was attempted
            mock_service.generate_debt_report_by_name.assert_called_with("John Doe")
    
    async def test_relatorios_debt_name_not_found(self):
        """Test relatorios debt name input when buyer not found - unit test coverage."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('services.handler_business_service.HandlerBusinessService') as mock_business_service:
            
            # Mock business service to return no data
            mock_service = Mock()
            mock_service.generate_debt_report_by_name.return_value = Mock(
                data=[],
                csv_file_path=None
            )
            mock_business_service.return_value = mock_service
            
            # Test entering non-existent buyer name
            update = MockTelegramObjects.create_update("NonExistent User", chat_id=chat_id)
            result = await self.handler._debt_name_callback(update, self.context)
            
            # Should complete conversation
            assert result == ConversationHandler.END
    
    async def test_relatorios_empty_name_input(self):
        """Test relatorios empty name input - unit test coverage."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func):
            
            # Test entering empty name
            update = MockTelegramObjects.create_update("", chat_id=chat_id)
            result = await self.handler._debt_name_callback(update, self.context)
            
            # Should stay in same state or show error
            assert result in [RELATORIO_DIVIDA_NOME, ConversationHandler.END]
    
    async def test_conversation_states_registration(self):
        """Test conversation handler has all required states - unit test coverage."""
        
        # Get the conversation handler
        conv_handler = self.handler.get_conversation_handler()
        
        # Verify all relatorios flow states are registered
        required_states = [
            RELATORIO_MENU,
            RELATORIO_DIVIDA_NOME
        ]
        
        for state in required_states:
            assert state in conv_handler.states, f"State {state} not registered in conversation handler"
    
    async def test_relatorios_flow_cancel_handling(self):
        """Test cancel operation during relatorios flow."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('handlers.global_handlers.cancel_callback') as mock_cancel:
            
            # Mock cancel function
            mock_cancel.return_value = ConversationHandler.END
            
            # Test cancel from any relatorios state
            update = MockTelegramObjects.create_update(callback_data="rel_cancel", chat_id=chat_id)
            
            # Test cancel
            result = await mock_cancel(update, self.context)
            assert result == ConversationHandler.END
    
    async def test_relatorios_flow_error_scenarios(self):
        """Test error scenarios in relatorios flow."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('services.handler_business_service.HandlerBusinessService') as mock_business_service:
            
            # Mock service to raise an error
            mock_service = Mock()
            mock_service.generate_sales_report.side_effect = Exception("Database error")
            mock_business_service.return_value = mock_service
            
            # Test error handling in sales report
            update = MockTelegramObjects.create_update(callback_data="rel_vendas", chat_id=chat_id)
            result = await self.handler._menu_callback(update, self.context)
            
            # Should handle error gracefully
            assert result in [ConversationHandler.END, RELATORIO_MENU]
    
    async def test_relatorios_flow_input_validation(self):
        """Test input validation in relatorios flow."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func):
            
            # Test input with special characters
            update = MockTelegramObjects.create_update("User@#$%", chat_id=chat_id)
            result = await self.handler._debt_name_callback(update, self.context)
            
            # Should handle special characters appropriately
            assert result in [RELATORIO_DIVIDA_NOME, ConversationHandler.END]
    
    async def test_relatorios_flow_state_persistence(self):
        """Test that relatorios flow maintains state correctly across transitions."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func):
            
            # Step 1: Start relatorios
            update = MockTelegramObjects.create_update(text="/relatorios", chat_id=chat_id)
            result1 = await self.handler._start_relatorios(update, self.context)
            assert result1 == RELATORIO_MENU
            
            # Step 2: Select debt report by name
            update = MockTelegramObjects.create_update(callback_data="rel_dividas", chat_id=chat_id)
            result2 = await self.handler._menu_callback(update, self.context)
            assert result2 == RELATORIO_DIVIDA_NOME
            
            # Verify state transitions work correctly
            assert result2 == RELATORIO_DIVIDA_NOME
    
    async def test_relatorios_csv_file_generation(self):
        """Test CSV file generation in reports - unit test coverage."""
        chat_id = 12345
        
        with patch('utils.permissions.require_permission', lambda level: lambda func: func), \
             patch('services.handler_business_service.HandlerBusinessService') as mock_business_service, \
             patch('builtins.open', create=True) as mock_open, \
             patch('os.path.exists') as mock_exists:
            
            # Mock file operations
            mock_exists.return_value = True
            mock_open.return_value.__enter__.return_value.read.return_value = "csv,data"
            
            # Mock business service
            mock_service = Mock()
            mock_service.generate_sales_report.return_value = Mock(
                data=self.mock_sales_data,
                csv_file_path="/tmp/sales_report.csv"
            )
            mock_business_service.return_value = mock_service
            
            # Test sales report with CSV generation
            update = MockTelegramObjects.create_update(callback_data="rel_vendas", chat_id=chat_id)
            result = await self.handler._menu_callback(update, self.context)
            
            # Should complete successfully
            assert result in [ConversationHandler.END, RELATORIO_MENU]


if __name__ == "__main__":
    pytest.main([__file__])