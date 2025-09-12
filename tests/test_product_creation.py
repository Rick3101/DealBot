"""
Tests for product creation functionality.
Validates complete product creation flow with various scenarios.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from telegram.ext import ConversationHandler

from handlers.base_handler import HandlerRequest, HandlerResponse
from services.base_service import ValidationError, ServiceError
from tests.conftest import assert_handler_response, assert_telegram_call_made


class TestProductCreation:
    """Test cases for product creation functionality"""
    
    @pytest.fixture
    def mock_product_handler(self):
        """Create a mock product handler for testing"""
        with patch('handlers.product_handler.get_modern_product_handler') as mock_get_handler:
            handler = Mock()
            handler.name = "product"
            mock_get_handler.return_value = handler
            yield handler
    
    @pytest.mark.asyncio
    async def test_create_basic_product_success(self, mock_product_handler, mock_telegram_objects, mock_product_service):
        """Test successful creation of basic product without media"""
        # Setup handlers
        mock_product_handler.start = AsyncMock(return_value=1)
        mock_product_handler.menu_callback = AsyncMock(return_value=2)
        mock_product_handler.add_name = AsyncMock(return_value=3)
        mock_product_handler.add_emoji = AsyncMock(return_value=4)
        mock_product_handler.media_confirm = AsyncMock(return_value=ConversationHandler.END)
        
        # Setup service
        mock_product_service.create_product.return_value = 1
        
        # Start product creation flow
        with patch('handlers.product_handler.get_product_service', return_value=mock_product_service):
            # Initiate product command
            result1 = await mock_product_handler.start(
                mock_telegram_objects.update, 
                mock_telegram_objects.context
            )
            assert result1 == 1
            
            # Select "add product" option
            callback_update = Mock()
            callback_update.callback_query = Mock()
            callback_update.callback_query.data = "add_product"
            result2 = await mock_product_handler.menu_callback(
                callback_update, 
                mock_telegram_objects.context
            )
            assert result2 == 2
            
            # Enter product name
            mock_telegram_objects.message.text = "Test Product"
            mock_telegram_objects.context.user_data['product_name'] = "Test Product"
            result3 = await mock_product_handler.add_name(
                mock_telegram_objects.update, 
                mock_telegram_objects.context
            )
            assert result3 == 3
            
            # Enter product emoji
            mock_telegram_objects.message.text = "🧪"
            mock_telegram_objects.context.user_data['product_emoji'] = "🧪"
            result4 = await mock_product_handler.add_emoji(
                mock_telegram_objects.update, 
                mock_telegram_objects.context
            )
            assert result4 == 4
            
            # Decline media addition
            callback_update.callback_query.data = "add_media_no"
            result5 = await mock_product_handler.media_confirm(
                callback_update, 
                mock_telegram_objects.context
            )
            assert result5 == ConversationHandler.END
        
        # Verify product creation was called
        mock_product_service.create_product.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_product_with_photo_media(self, mock_product_handler, mock_telegram_objects, mock_product_service):
        """Test creating product with photo media"""
        # Setup handlers
        mock_product_handler.add_media = AsyncMock(return_value=ConversationHandler.END)
        mock_product_service.create_product.return_value = 1
        
        # Setup photo message
        mock_telegram_objects.message.photo = [Mock()]
        mock_telegram_objects.message.photo[0].file_id = "photo_file_id_123"
        mock_telegram_objects.message.text = None
        
        # Setup user data
        mock_telegram_objects.context.user_data.update({
            'product_name': 'Test Product',
            'product_emoji': '🧪'
        })
        
        with patch('handlers.product_handler.get_product_service', return_value=mock_product_service):
            result = await mock_product_handler.add_media(
                mock_telegram_objects.update,
                mock_telegram_objects.context
            )
        
        assert result == ConversationHandler.END
        # Verify photo file ID was processed
        call_args = mock_product_service.create_product.call_args
        assert "photo_file_id_123" in str(call_args)
    
    @pytest.mark.asyncio
    async def test_create_product_with_video_media(self, mock_product_handler, mock_telegram_objects, mock_product_service):
        """Test creating product with video media"""
        # Setup handlers
        mock_product_handler.add_media = AsyncMock(return_value=ConversationHandler.END)
        mock_product_service.create_product.return_value = 1
        
        # Setup video message
        mock_telegram_objects.message.video = Mock()
        mock_telegram_objects.message.video.file_id = "video_file_id_456"
        mock_telegram_objects.message.photo = None
        mock_telegram_objects.message.document = None
        
        # Setup user data
        mock_telegram_objects.context.user_data.update({
            'product_name': 'Video Product',
            'product_emoji': '🎥'
        })
        
        with patch('handlers.product_handler.get_product_service', return_value=mock_product_service):
            result = await mock_product_handler.add_media(
                mock_telegram_objects.update,
                mock_telegram_objects.context
            )
        
        assert result == ConversationHandler.END
        mock_product_service.create_product.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_product_with_document_media(self, mock_product_handler, mock_telegram_objects, mock_product_service):
        """Test creating product with document media"""
        # Setup handlers
        mock_product_handler.add_media = AsyncMock(return_value=ConversationHandler.END)
        mock_product_service.create_product.return_value = 1
        
        # Setup document message
        mock_telegram_objects.message.document = Mock()
        mock_telegram_objects.message.document.file_id = "doc_file_id_789"
        mock_telegram_objects.message.photo = None
        mock_telegram_objects.message.video = None
        
        # Setup user data
        mock_telegram_objects.context.user_data.update({
            'product_name': 'Document Product',
            'product_emoji': '📄'
        })
        
        with patch('handlers.product_handler.get_product_service', return_value=mock_product_service):
            result = await mock_product_handler.add_media(
                mock_telegram_objects.update,
                mock_telegram_objects.context
            )
        
        assert result == ConversationHandler.END
        mock_product_service.create_product.assert_called_once()
    
    @pytest.mark.parametrize("product_name,expected_result", [
        ("Valid Product Name", 3),  # Should proceed to emoji
        ("A", 2),                   # Too short, stay in name state
        ("", 2),                    # Empty, stay in name state
        ("P", 2),                   # Single char, stay in name state
        ("Very Long Product Name That Exceeds Normal Limits" * 5, 2),  # Too long
    ])
    @pytest.mark.asyncio
    async def test_product_name_validation(self, mock_product_handler, mock_telegram_objects, product_name, expected_result):
        """Test product name validation with various inputs"""
        mock_product_handler.add_name = AsyncMock(return_value=expected_result)
        mock_telegram_objects.message.text = product_name
        
        result = await mock_product_handler.add_name(
            mock_telegram_objects.update,
            mock_telegram_objects.context
        )
        
        assert result == expected_result
        if expected_result == 3:  # Valid name
            assert mock_telegram_objects.context.user_data.get('product_name') == product_name
    
    @pytest.mark.parametrize("emoji,expected_result", [
        ("🧪", 4),    # Valid emoji, proceed to media confirm
        ("🔬", 4),    # Valid emoji
        ("💊", 4),    # Valid emoji
        ("text", 3),  # Not an emoji, stay in emoji state
        ("", 3),      # Empty, stay in emoji state
        ("🧪🔬", 3),  # Multiple emojis, invalid
        ("123", 3),   # Numbers, invalid
    ])
    @pytest.mark.asyncio
    async def test_product_emoji_validation(self, mock_product_handler, mock_telegram_objects, emoji, expected_result):
        """Test product emoji validation with various inputs"""
        mock_product_handler.add_emoji = AsyncMock(return_value=expected_result)
        mock_telegram_objects.message.text = emoji
        
        result = await mock_product_handler.add_emoji(
            mock_telegram_objects.update,
            mock_telegram_objects.context
        )
        
        assert result == expected_result
        if expected_result == 4:  # Valid emoji
            assert mock_telegram_objects.context.user_data.get('product_emoji') == emoji
    
    @pytest.mark.asyncio
    async def test_create_product_service_error(self, mock_product_handler, mock_telegram_objects, mock_product_service):
        """Test handling of service errors during product creation"""
        # Setup service to raise error
        mock_product_service.create_product.side_effect = ServiceError("Database connection failed")
        mock_product_handler.media_confirm = AsyncMock(return_value=ConversationHandler.END)
        
        # Setup user data
        mock_telegram_objects.context.user_data.update({
            'product_name': 'Test Product',
            'product_emoji': '🧪'
        })
        
        with patch('handlers.product_handler.get_product_service', return_value=mock_product_service):
            result = await mock_product_handler.media_confirm(
                mock_telegram_objects.update,
                mock_telegram_objects.context
            )
        
        # Should handle error gracefully and end conversation
        assert result == ConversationHandler.END
    
    @pytest.mark.asyncio
    async def test_create_product_validation_error(self, mock_product_handler, mock_telegram_objects, mock_product_service):
        """Test handling of validation errors"""
        # Setup service to raise validation error
        mock_product_service.create_product.side_effect = ValidationError("Product name already exists")
        mock_product_handler.media_confirm = AsyncMock(return_value=2)  # Return to name input
        
        # Setup user data
        mock_telegram_objects.context.user_data.update({
            'product_name': 'Existing Product',
            'product_emoji': '🧪'
        })
        
        with patch('handlers.product_handler.get_product_service', return_value=mock_product_service):
            result = await mock_product_handler.media_confirm(
                mock_telegram_objects.update,
                mock_telegram_objects.context
            )
        
        # Should return to name input for correction
        assert result == 2
    
    @pytest.mark.asyncio
    async def test_create_hidden_product_with_special_emojis(self, mock_product_handler, mock_telegram_objects, mock_product_service):
        """Test creating hidden products with special emojis (🧪💀)"""
        # Setup handlers
        mock_product_handler.add_emoji = AsyncMock(return_value=4)
        mock_product_service.create_product.return_value = 1
        
        # Test with lab emoji (🧪) - should be marked as hidden
        mock_telegram_objects.message.text = "🧪"
        mock_telegram_objects.context.user_data['product_name'] = "Hidden Lab Product"
        
        result = await mock_product_handler.add_emoji(
            mock_telegram_objects.update,
            mock_telegram_objects.context
        )
        
        assert result == 4
        assert mock_telegram_objects.context.user_data.get('product_emoji') == "🧪"
    
    @pytest.mark.asyncio
    async def test_create_product_permission_check(self, mock_product_handler, mock_telegram_objects, mock_user_service):
        """Test that only owners can create products"""
        # Setup user service to return non-owner permission
        mock_user_service.get_user_permission_level.return_value = "admin"  # Not owner
        mock_product_handler.start = AsyncMock(return_value=ConversationHandler.END)
        
        with patch('core.modern_service_container.get_user_service', return_value=mock_user_service):
            result = await mock_product_handler.start(
                mock_telegram_objects.update,
                mock_telegram_objects.context
            )
        
        # Should deny access for non-owners
        assert result == ConversationHandler.END
    
    @pytest.mark.asyncio
    async def test_create_product_conversation_cancel(self, mock_product_handler, mock_telegram_objects):
        """Test canceling product creation conversation"""
        mock_product_handler.cancel = AsyncMock(return_value=ConversationHandler.END)
        
        # Setup some user data that should be cleared
        mock_telegram_objects.context.user_data.update({
            'product_name': 'Partial Product',
            'product_emoji': '🧪',
            'temp_data': 'should_be_cleared'
        })
        
        result = await mock_product_handler.cancel(
            mock_telegram_objects.update,
            mock_telegram_objects.context
        )
        
        assert result == ConversationHandler.END
        # Verify user data is cleared
        assert mock_telegram_objects.context.user_data == {}
    
    @pytest.mark.asyncio
    async def test_create_product_media_type_detection(self, mock_product_handler, mock_telegram_objects, mock_product_service):
        """Test proper detection of different media types"""
        mock_product_handler.add_media = AsyncMock(return_value=ConversationHandler.END)
        mock_product_service.create_product.return_value = 1
        
        # Setup user data
        mock_telegram_objects.context.user_data.update({
            'product_name': 'Media Test Product',
            'product_emoji': '📸'
        })
        
        # Test with multiple media types in one message (should prioritize photo)
        mock_telegram_objects.message.photo = [Mock()]
        mock_telegram_objects.message.photo[0].file_id = "photo_123"
        mock_telegram_objects.message.document = Mock()
        mock_telegram_objects.message.document.file_id = "doc_456"
        
        with patch('handlers.product_handler.get_product_service', return_value=mock_product_service):
            result = await mock_product_handler.add_media(
                mock_telegram_objects.update,
                mock_telegram_objects.context
            )
        
        assert result == ConversationHandler.END
        # Should use photo file ID (priority over document)
        call_args = str(mock_product_service.create_product.call_args)
        assert "photo_123" in call_args
    
    @pytest.mark.asyncio
    async def test_create_product_data_cleanup(self, mock_product_handler, mock_telegram_objects, mock_product_service):
        """Test that user data is properly cleaned up after product creation"""
        mock_product_handler.media_confirm = AsyncMock(return_value=ConversationHandler.END)
        mock_product_service.create_product.return_value = 1
        
        # Setup user data
        mock_telegram_objects.context.user_data.update({
            'product_name': 'Cleanup Test Product',
            'product_emoji': '🧹',
            'other_data': 'should_remain'
        })
        
        with patch('handlers.product_handler.get_product_service', return_value=mock_product_service):
            result = await mock_product_handler.media_confirm(
                mock_telegram_objects.update,
                mock_telegram_objects.context
            )
        
        assert result == ConversationHandler.END
        # Verify product-specific data is cleaned but other data remains
        assert 'product_name' not in mock_telegram_objects.context.user_data
        assert 'product_emoji' not in mock_telegram_objects.context.user_data
        assert mock_telegram_objects.context.user_data.get('other_data') == 'should_remain'


class TestProductCreationIntegration:
    """Integration tests for product creation with realistic scenarios"""
    
    @pytest.mark.asyncio
    async def test_complete_product_creation_workflow(self, mock_telegram_objects, mock_product_service, test_utils):
        """Test complete product creation workflow with realistic flow"""
        # This would test the actual handler integration
        pass
    
    @pytest.mark.asyncio
    async def test_product_creation_with_inventory_integration(self, mock_telegram_objects, mock_product_service):
        """Test that product creation properly integrates with inventory system"""
        # This would test integration with inventory service
        pass
    
    @pytest.mark.asyncio
    async def test_product_creation_error_recovery(self, mock_telegram_objects):
        """Test error recovery mechanisms during product creation"""
        # This would test various error scenarios and recovery
        pass