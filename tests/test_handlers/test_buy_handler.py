"""
Buy handler tests using real services with proper setup.
Tests the ModernBuyHandler with actual service integration.
"""

import pytest
import os
from unittest.mock import Mock, AsyncMock, patch
from telegram.ext import ConversationHandler

from handlers.buy_handler import ModernBuyHandler, BUY_NAME, BUY_SELECT_PRODUCT, BUY_QUANTITY, BUY_PRICE
from handlers.base_handler import HandlerRequest, HandlerResponse
from services.base_service import ValidationError, ServiceError
from core.config import get_config


class TestBuyHandler:
    """Buy handler tests with real services."""
    
    @pytest.fixture(autouse=True)
    def setup_environment(self):
        """Setup test environment variables."""
        # Set a test database URL
        os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/test_db"
        yield
        # Cleanup
        if "DATABASE_URL" in os.environ:
            del os.environ["DATABASE_URL"]
    
    @pytest.fixture
    def buy_handler(self):
        """Create a buy handler instance."""
        return ModernBuyHandler()
    
    @pytest.fixture
    def mock_telegram_objects(self):
        """Create mock telegram objects."""
        update = Mock()
        context = Mock()
        context.user_data = {}
        context.chat_data = {}
        
        # Mock message
        message = Mock()
        message.text = ""
        message.delete = AsyncMock()
        update.message = message
        
        # Mock callback query
        callback_query = Mock()
        callback_query.answer = AsyncMock()
        callback_query.message = Mock()
        callback_query.message.delete = AsyncMock()
        callback_query.data = ""
        update.callback_query = callback_query
        
        # Mock chat and user
        chat = Mock()
        chat.id = 12345
        update.effective_chat = chat
        
        user = Mock()
        user.id = 67890
        update.effective_user = user
        
        return type('MockObjects', (), {
            'update': update,
            'context': context,
            'message': message,
            'chat': chat,
            'user': user,
            'callback_query': callback_query
        })()
    
    def test_buy_handler_creation(self, buy_handler):
        """Test that buy handler can be created."""
        assert buy_handler.name == "buy"
        assert buy_handler.secret_phrase == get_config().services.secret_menu_phrase
    
    def test_conversation_handler_creation(self, buy_handler):
        """Test that conversation handler can be created."""
        with patch('handlers.buy_handler.get_user_service'), \
             patch('handlers.buy_handler.get_product_service'), \
             patch('services.handler_business_service.HandlerBusinessService'):
            
            conv_handler = buy_handler.get_conversation_handler()
            assert isinstance(conv_handler, ConversationHandler)
            assert len(conv_handler.states) == 4  # BUY_NAME, BUY_SELECT_PRODUCT, BUY_QUANTITY, BUY_PRICE
    
    @pytest.mark.asyncio
    async def test_handle_buyer_name_valid(self, buy_handler, mock_telegram_objects):
        """Test valid buyer name input."""
        mock_telegram_objects.message.text = "John Doe"
        
        request = HandlerRequest(
            update=mock_telegram_objects.update,
            context=mock_telegram_objects.context,
            user_data=mock_telegram_objects.context.user_data,
            chat_id=mock_telegram_objects.chat.id,
            user_id=mock_telegram_objects.user.id
        )
        
        with patch.object(buy_handler, 'create_products_keyboard', return_value=Mock()):
            response = await buy_handler.handle_buyer_name(request)
            
            assert response.next_state == BUY_SELECT_PRODUCT
            assert request.user_data.get('nome_comprador') == "John Doe"
    
    @pytest.mark.asyncio
    async def test_handle_buyer_name_invalid(self, buy_handler, mock_telegram_objects):
        """Test invalid buyer name input."""
        mock_telegram_objects.message.text = ""  # Empty name
        
        request = HandlerRequest(
            update=mock_telegram_objects.update,
            context=mock_telegram_objects.context,
            user_data=mock_telegram_objects.context.user_data,
            chat_id=mock_telegram_objects.chat.id,
            user_id=mock_telegram_objects.user.id
        )
        
        response = await buy_handler.handle_buyer_name(request)
        
        assert response.next_state == BUY_NAME
        assert "❌" in response.message
    
    @pytest.mark.asyncio
    async def test_handle_quantity_valid(self, buy_handler, mock_telegram_objects):
        """Test valid quantity input."""
        mock_telegram_objects.message.text = "5"
        
        request = HandlerRequest(
            update=mock_telegram_objects.update,
            context=mock_telegram_objects.context,
            user_data=mock_telegram_objects.context.user_data,
            chat_id=mock_telegram_objects.chat.id,
            user_id=mock_telegram_objects.user.id
        )
        
        request.user_data['produto_atual'] = 1
        
        response = await buy_handler.handle_quantity(request)
        
        assert response.next_state == BUY_PRICE
        assert request.user_data.get('quantidade_atual') == 5
    
    @pytest.mark.asyncio
    async def test_handle_quantity_invalid(self, buy_handler, mock_telegram_objects):
        """Test invalid quantity input."""
        mock_telegram_objects.message.text = "invalid"
        
        request = HandlerRequest(
            update=mock_telegram_objects.update,
            context=mock_telegram_objects.context,
            user_data=mock_telegram_objects.context.user_data,
            chat_id=mock_telegram_objects.chat.id,
            user_id=mock_telegram_objects.user.id
        )
        
        request.user_data['produto_atual'] = 1
        
        response = await buy_handler.handle_quantity(request)
        
        assert response.next_state == BUY_QUANTITY
        assert "❌" in response.message
    
    @pytest.mark.asyncio
    async def test_handle_price_valid(self, buy_handler, mock_telegram_objects):
        """Test valid price input."""
        mock_telegram_objects.message.text = "15.50"
        
        request = HandlerRequest(
            update=mock_telegram_objects.update,
            context=mock_telegram_objects.context,
            user_data=mock_telegram_objects.context.user_data,
            chat_id=mock_telegram_objects.chat.id,
            user_id=mock_telegram_objects.user.id
        )
        
        request.user_data['produto_atual'] = 1
        request.user_data['quantidade_atual'] = 3
        request.user_data['itens_venda'] = []
        
        with patch.object(buy_handler, 'create_products_keyboard', return_value=Mock()):
            response = await buy_handler.handle_price(request)
            
            assert response.next_state == BUY_SELECT_PRODUCT
            
            # Check item was added to cart
            items = request.user_data.get('itens_venda', [])
            assert len(items) == 1
            assert items[0]['preco'] == 15.50
            assert items[0]['quantidade'] == 3
    
    @pytest.mark.asyncio
    async def test_handle_price_invalid(self, buy_handler, mock_telegram_objects):
        """Test invalid price input."""
        mock_telegram_objects.message.text = "invalid_price"
        
        request = HandlerRequest(
            update=mock_telegram_objects.update,
            context=mock_telegram_objects.context,
            user_data=mock_telegram_objects.context.user_data,
            chat_id=mock_telegram_objects.chat.id,
            user_id=mock_telegram_objects.user.id
        )
        
        request.user_data['produto_atual'] = 1
        request.user_data['quantidade_atual'] = 3
        
        response = await buy_handler.handle_price(request)
        
        assert response.next_state == BUY_PRICE
        assert "❌" in response.message
    
    @pytest.mark.asyncio
    async def test_secret_menu_activation(self, buy_handler, mock_telegram_objects):
        """Test secret menu activation."""
        mock_telegram_objects.message.text = "wubba lubba dub dub"
        
        request = HandlerRequest(
            update=mock_telegram_objects.update,
            context=mock_telegram_objects.context,
            user_data=mock_telegram_objects.context.user_data,
            chat_id=mock_telegram_objects.chat.id,
            user_id=mock_telegram_objects.user.id
        )
        
        with patch.object(buy_handler, 'create_products_keyboard', return_value=Mock()):
            response = await buy_handler.handle_secret_menu_check(request)
            
            assert response.next_state == BUY_SELECT_PRODUCT
            assert "secretos" in response.message.lower()
    
    @pytest.mark.asyncio  
    async def test_menu_selection_product(self, buy_handler, mock_telegram_objects):
        """Test product selection from menu."""
        request = HandlerRequest(
            update=mock_telegram_objects.update,
            context=mock_telegram_objects.context,
            user_data=mock_telegram_objects.context.user_data,
            chat_id=mock_telegram_objects.chat.id,
            user_id=mock_telegram_objects.user.id
        )
        
        response = await buy_handler.handle_menu_selection(request, "buyproduct:1")
        
        assert response.next_state == BUY_QUANTITY
        assert request.user_data.get('produto_atual') == 1
    
    @pytest.mark.asyncio
    async def test_menu_selection_cancel(self, buy_handler, mock_telegram_objects):
        """Test cancel selection from menu."""
        request = HandlerRequest(
            update=mock_telegram_objects.update,
            context=mock_telegram_objects.context,
            user_data=mock_telegram_objects.context.user_data,
            chat_id=mock_telegram_objects.chat.id,
            user_id=mock_telegram_objects.user.id
        )
        
        response = await buy_handler.handle_menu_selection(request, "buy_cancelar")
        
        assert response.end_conversation == True
        assert "cancelada" in response.message.lower()
    
    @pytest.mark.asyncio
    async def test_finalize_purchase_no_items(self, buy_handler, mock_telegram_objects):
        """Test finalizing purchase with no items."""
        request = HandlerRequest(
            update=mock_telegram_objects.update,
            context=mock_telegram_objects.context,
            user_data=mock_telegram_objects.context.user_data,
            chat_id=mock_telegram_objects.chat.id,
            user_id=mock_telegram_objects.user.id
        )
        
        request.user_data['nome_comprador'] = "Test Buyer"
        request.user_data['itens_venda'] = []
        
        response = await buy_handler.finalize_purchase(request)
        
        assert response.end_conversation == True
        assert "Nenhum item" in response.message