"""
Test for /dividas command in relatorios handler.
Tests the new dividas_usuario function with proper mocking.
"""

import pytest
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from telegram import Update, User, Chat, Message
from telegram.ext import ContextTypes

from handlers.relatorios_handler import dividas_usuario
from models.user import User as UserModel, UserLevel
from models.handler_models import ReportRequest, ReportResponse


class TestDividasCommand:
    """Test the /dividas command functionality."""
    
    @pytest.fixture(autouse=True)
    def setup_environment(self):
        """Setup test environment variables."""
        os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/test_db"
        os.environ["BOT_TOKEN"] = "test_token"
        yield
        # Cleanup
        if "DATABASE_URL" in os.environ:
            del os.environ["DATABASE_URL"]
        if "BOT_TOKEN" in os.environ:
            del os.environ["BOT_TOKEN"]
    
    @pytest.fixture
    def mock_telegram_objects(self):
        """Create mock telegram objects."""
        # Mock user
        user = Mock(spec=User)
        user.id = 123456789
        user.first_name = "Test"
        user.username = "testuser"
        
        # Mock chat
        chat = Mock(spec=Chat)
        chat.id = 123456789
        chat.type = "private"
        
        # Mock message
        message = Mock(spec=Message)
        message.message_id = 1
        message.from_user = user
        message.chat = chat
        message.text = "/dividas"
        message.reply_text = AsyncMock()
        
        # Mock update
        update = Mock(spec=Update)
        update.update_id = 1
        update.message = message
        update.effective_user = user
        update.effective_chat = chat
        
        # Mock context
        context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {}
        context.chat_data = {}
        
        return {
            'update': update,
            'context': context,
            'user': user,
            'chat': chat,
            'message': message
        }
    
    @pytest.fixture
    def mock_authenticated_user(self):
        """Create a mock authenticated user."""
        user = UserModel(
            id=1,
            username="testuser",
            password="hashedpassword",
            level=UserLevel.ADMIN,
            chat_id=123456789
        )
        return user
    
    @pytest.fixture 
    def mock_debt_data(self):
        """Create mock debt/report data."""
        return [
            {
                'id': 1,
                'produto_nome': 'Test Product 1',
                'quantidade': 2,
                'valor_total': 100.0,
                'data_venda': '2024-01-01'
            },
            {
                'id': 2,
                'produto_nome': 'Test Product 2',
                'quantidade': 1,
                'valor_total': 50.0,
                'data_venda': '2024-01-02'
            }
        ]
    
    @pytest.mark.asyncio
    async def test_dividas_comando_success(self, mock_telegram_objects, mock_authenticated_user, mock_debt_data):
        """Test successful /dividas command execution."""
        update = mock_telegram_objects['update']
        context = mock_telegram_objects['context']
        
        # Mock the user service to return authenticated user
        mock_user_service = Mock()
        mock_user_service.get_user_by_chat_id = Mock(return_value=mock_authenticated_user)
        mock_user_service.get_user_permission_level = Mock(return_value=UserLevel.ADMIN)
        
        # Mock the business service to return debt data
        mock_business_service = Mock()
        mock_report_response = ReportResponse(
            success=True,
            report_data=mock_debt_data,
            message="Success"
        )
        mock_business_service.generate_report = Mock(return_value=mock_report_response)
        
        with patch('core.modern_service_container.get_user_service', return_value=mock_user_service), \
             patch('services.handler_business_service.HandlerBusinessService', return_value=mock_business_service), \
             patch('utils.message_cleaner.delayed_delete', new_callable=AsyncMock) as mock_delayed_delete:
            
            # Execute the command
            result = await dividas_usuario(update, context)
            
            # Verify user service was called correctly
            mock_user_service.get_user_by_chat_id.assert_called_once_with(123456789)
            
            # Verify business service was called correctly
            mock_business_service.generate_report.assert_called_once()
            call_args = mock_business_service.generate_report.call_args[0][0]
            assert call_args.report_type == "debts"
            assert call_args.buyer_name == "testuser"
            
            # Verify message was sent with correct content
            update.message.reply_text.assert_called_once()
            call_args = update.message.reply_text.call_args[1]
            message_text = call_args['text']
            assert "💸 Suas Dívidas:" in message_text
            assert "testuser" in message_text
            assert "Test Product 1" in message_text
            assert "Test Product 2" in message_text
            assert "R$150" in message_text  # Total should be calculated
            
            # Verify delayed delete was called
            mock_delayed_delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_dividas_comando_user_not_authenticated(self, mock_telegram_objects):
        """Test /dividas command when user is not authenticated."""
        update = mock_telegram_objects['update']
        context = mock_telegram_objects['context']
        
        # Mock user service to return None (not authenticated)
        mock_user_service = Mock()
        mock_user_service.get_user_by_chat_id = Mock(return_value=None)
        
        with patch('handlers.relatorios_handler.get_user_service', return_value=mock_user_service), \
             patch('handlers.relatorios_handler.send_and_delete', new_callable=AsyncMock) as mock_send_and_delete:
            
            # Execute the command
            result = await dividas_usuario(update, context)
            
            # Verify user service was called
            mock_user_service.get_user_by_chat_id.assert_called_once_with(123456789)
            
            # Verify error message was sent
            mock_send_and_delete.assert_called_once_with(
                "❌ Usuário não autenticado. Use /login primeiro.", 
                update, 
                context
            )
    
    @pytest.mark.asyncio
    async def test_dividas_comando_no_debts_found(self, mock_telegram_objects, mock_authenticated_user):
        """Test /dividas command when user has no debts."""
        update = mock_telegram_objects['update']
        context = mock_telegram_objects['context']
        
        # Mock services
        mock_user_service = Mock()
        mock_user_service.get_user_by_chat_id = Mock(return_value=mock_authenticated_user)
        
        mock_business_service = Mock()
        mock_report_response = ReportResponse(
            success=False,
            report_data=None,
            message="No data found"
        )
        mock_business_service.generate_report = Mock(return_value=mock_report_response)
        
        with patch('handlers.relatorios_handler.get_user_service', return_value=mock_user_service), \
             patch('handlers.relatorios_handler.HandlerBusinessService', return_value=mock_business_service), \
             patch('handlers.relatorios_handler.send_and_delete', new_callable=AsyncMock) as mock_send_and_delete:
            
            # Execute the command
            result = await dividas_usuario(update, context)
            
            # Verify "no debts" message was sent
            mock_send_and_delete.assert_called_once()
            call_args = mock_send_and_delete.call_args[0]
            assert "📭 Nenhuma compra pendente encontrada" in call_args[0]
            assert "testuser" in call_args[0]
    
    @pytest.mark.asyncio
    async def test_dividas_comando_service_error(self, mock_telegram_objects):
        """Test /dividas command when service throws an error."""
        update = mock_telegram_objects['update']
        context = mock_telegram_objects['context']
        
        # Mock user service to throw an exception
        mock_user_service = Mock()
        mock_user_service.get_user_by_chat_id = Mock(side_effect=Exception("Service error"))
        
        with patch('handlers.relatorios_handler.get_user_service', return_value=mock_user_service), \
             patch('handlers.relatorios_handler.send_and_delete', new_callable=AsyncMock) as mock_send_and_delete:
            
            # Execute the command
            result = await dividas_usuario(update, context)
            
            # Verify error message was sent
            mock_send_and_delete.assert_called_once_with(
                "❌ Erro interno. Tente novamente.", 
                update, 
                context
            )
    
    @pytest.mark.asyncio
    async def test_dividas_comando_get_user_service_error(self, mock_telegram_objects):
        """Test /dividas command when get_user_service fails."""
        update = mock_telegram_objects['update']
        context = mock_telegram_objects['context']
        
        with patch('handlers.relatorios_handler.get_user_service', side_effect=Exception("Container not initialized")), \
             patch('handlers.relatorios_handler.send_and_delete', new_callable=AsyncMock) as mock_send_and_delete:
            
            # Execute the command
            result = await dividas_usuario(update, context)
            
            # Verify error message was sent
            mock_send_and_delete.assert_called_once_with(
                "❌ Erro interno. Tente novamente.",
                update,
                context
            )