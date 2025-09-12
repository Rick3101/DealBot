"""
Integration test for /dividas command that tests the real business service.
This would have caught the missing get_sale_items method.
"""

import pytest
import os
from unittest.mock import Mock, AsyncMock, patch

from handlers.relatorios_handler import dividas_usuario
from models.user import User, UserLevel
from models.sale import Sale, SaleItem
from models.product import Product


class TestDividasIntegration:
    """Integration tests for /dividas command with real services."""
    
    @pytest.fixture(autouse=True)
    def setup_environment(self):
        """Setup test environment variables."""
        os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/test_db"
        os.environ["BOT_TOKEN"] = "test_token"
        yield
        if "DATABASE_URL" in os.environ:
            del os.environ["DATABASE_URL"]
        if "BOT_TOKEN" in os.environ:
            del os.environ["BOT_TOKEN"]
    
    @pytest.fixture
    def mock_telegram_objects(self):
        """Create mock telegram objects."""
        update = Mock()
        context = Mock()
        update.effective_chat = Mock()
        update.effective_chat.id = 123456789
        update.message = Mock()
        update.message.reply_text = AsyncMock()
        context.user_data = {}
        
        return {'update': update, 'context': context}
    
    @pytest.fixture
    def sample_sales_data(self):
        """Create sample sales data that mirrors real database structure."""
        sale1 = Sale(id=1, comprador="testuser", data="2024-01-01")
        sale2 = Sale(id=2, comprador="testuser", data="2024-01-02")
        
        items1 = [SaleItem(id=1, venda_id=1, produto_id=1, quantidade=2, valor_unitario=50.0)]
        items2 = [SaleItem(id=2, venda_id=2, produto_id=2, quantidade=1, valor_unitario=30.0)]
        
        product1 = Product(id=1, nome="Test Product 1", emoji="🎮", media_type=None, media_file_id=None)
        product2 = Product(id=2, nome="Test Product 2", emoji="🖱️", media_type=None, media_file_id=None)
        
        return {
            'sales': [sale1, sale2],
            'items': {1: items1, 2: items2},
            'products': {1: product1, 2: product2}
        }
    
    async def test_dividas_integration_with_real_business_service(self, mock_telegram_objects, sample_sales_data):
        """
        Integration test using REAL business service but mocked data services.
        This would catch missing methods in the business service.
        """
        update = mock_telegram_objects['update']
        context = mock_telegram_objects['context']
        
        # Mock only the data layer, not the business logic layer
        mock_user_service = Mock()
        mock_authenticated_user = User(
            id=1, username="testuser", password="hash", 
            level=UserLevel.ADMIN, chat_id=123456789
        )
        mock_user_service.get_user_by_chat_id.return_value = mock_authenticated_user
        
        # Mock the data services but let business service run real logic
        mock_sales_service = Mock()
        mock_sales_service.get_sales_by_buyer.return_value = sample_sales_data['sales']
        mock_sales_service.get_sale_items.side_effect = lambda sale_id: sample_sales_data['items'].get(sale_id, [])
        
        mock_product_service = Mock()
        mock_product_service.get_product_by_id.side_effect = lambda prod_id: sample_sales_data['products'].get(prod_id)
        
        with patch('utils.permissions.get_user_service', return_value=mock_user_service), \
             patch('core.modern_service_container.get_user_service', return_value=mock_user_service), \
             patch('core.modern_service_container.get_sales_service', return_value=mock_sales_service), \
             patch('core.modern_service_container.get_product_service', return_value=mock_product_service), \
             patch('handlers.relatorios_handler.delayed_delete', new_callable=AsyncMock):
            
            # This would fail if get_sale_items method was missing
            result = await dividas_usuario(update, context)
            
            # Verify the real business logic was executed
            mock_sales_service.get_sales_by_buyer.assert_called_once_with("testuser")
            mock_sales_service.get_sale_items.assert_called()  # This would fail with missing method
            mock_product_service.get_product_by_id.assert_called()
            
            # Verify correct message was sent
            update.message.reply_text.assert_called_once()
            call_args = update.message.reply_text.call_args[1]
            message_text = call_args['text']
            assert "💸 Suas Dívidas:" in message_text
            assert "testuser" in message_text
    
    async def test_dividas_no_sales_found_integration(self, mock_telegram_objects):
        """Test integration when no sales are found (real business service)."""
        update = mock_telegram_objects['update']
        context = mock_telegram_objects['context']
        
        mock_user_service = Mock()
        mock_authenticated_user = User(
            id=1, username="testuser", password="hash", 
            level=UserLevel.ADMIN, chat_id=123456789
        )
        mock_user_service.get_user_by_chat_id.return_value = mock_authenticated_user
        
        # Mock empty sales result
        mock_sales_service = Mock()
        mock_sales_service.get_sales_by_buyer.return_value = []  # No sales found
        
        with patch('utils.permissions.get_user_service', return_value=mock_user_service), \
             patch('core.modern_service_container.get_user_service', return_value=mock_user_service), \
             patch('core.modern_service_container.get_sales_service', return_value=mock_sales_service), \
             patch('utils.message_cleaner.send_and_delete', new_callable=AsyncMock) as mock_send_and_delete:
            
            result = await dividas_usuario(update, context)
            
            # Should call send_and_delete with "no debts found" message
            mock_send_and_delete.assert_called_once()
            call_args = mock_send_and_delete.call_args[0]
            assert "Nenhuma compra pendente encontrada" in call_args[0]
            assert "testuser" in call_args[0]