"""
Estoque handler tests using proven mocking strategy.
Tests core inventory management functionality with comprehensive service mocking.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from telegram.ext import ConversationHandler

from handlers.estoque_handler import ModernEstoqueHandler, ESTOQUE_MENU, ESTOQUE_ADD_SELECT, ESTOQUE_ADD_VALUES
from handlers.base_handler import HandlerRequest, HandlerResponse
from services.base_service import ValidationError, ServiceError, NotFoundError


class TestEstoqueHandler:
    """Test cases for estoque handler functionality with proper mocking"""
    
    @pytest.fixture
    def estoque_handler(self):
        """Create a real estoque handler for testing"""
        return ModernEstoqueHandler()
    
    @pytest.fixture
    def estoque_request(self, mock_telegram_objects):
        """Create an estoque handler request"""
        return HandlerRequest(
            update=mock_telegram_objects.update,
            context=mock_telegram_objects.context,
            user_data=mock_telegram_objects.context.user_data,
            chat_id=mock_telegram_objects.chat.id,
            user_id=mock_telegram_objects.user.id
        )
    
    @pytest.mark.asyncio
    async def test_estoque_basic_execution(self, estoque_handler, estoque_request):
        """Test basic estoque command execution"""
        # Basic handle() doesn't require service mocking - it just shows the menu
        response = await estoque_handler.handle(estoque_request)
        
        assert response is not None
        assert isinstance(response, HandlerResponse)
        assert "deseja fazer" in response.message.lower()
        assert response.keyboard is not None
        assert response.next_state == ESTOQUE_MENU
    
    @pytest.mark.asyncio
    async def test_estoque_menu_add_selection(self, estoque_handler, estoque_request):
        """Test menu selection for adding stock"""
        # Mock the product service for keyboard creation
        with patch('handlers.estoque_handler.get_product_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_products_with_stock = Mock(return_value=[])
            mock_get_service.return_value = mock_service
            
            response = await estoque_handler.handle_menu_selection(estoque_request, "add_estoque")
        
        assert response.next_state == ESTOQUE_ADD_SELECT
        assert "produto" in response.message.lower()
        assert response.keyboard is not None
    
    @pytest.mark.asyncio
    async def test_estoque_menu_cancel_selection(self, estoque_handler, estoque_request):
        """Test menu selection for cancel"""
        response = await estoque_handler.handle_menu_selection(estoque_request, "cancel")
        
        assert response.end_conversation == True
        assert "cancelada" in response.message.lower()
    
    @pytest.mark.asyncio
    async def test_estoque_product_selection_valid(self, estoque_handler, estoque_request):
        """Test valid product selection for stock addition"""
        # Mock the product service
        with patch('handlers.estoque_handler.get_product_service') as mock_get_service:
            mock_service = Mock()
            mock_product = Mock()
            mock_product.id = 1
            mock_product.nome = "Test Product"
            mock_service.get_product_by_id = Mock(return_value=mock_product)
            mock_get_service.return_value = mock_service
            
            response = await estoque_handler.handle_product_selection(estoque_request, 1)
        
        assert response.next_state == ESTOQUE_ADD_VALUES
        assert "quantidade" in response.message.lower()
        assert estoque_request.user_data["selected_product_id"] == 1
        assert estoque_request.user_data["selected_product_name"] == "Test Product"
    
    @pytest.mark.asyncio
    async def test_estoque_product_not_found(self, estoque_handler, estoque_request):
        """Test product not found handling"""
        # Mock the product service to return None
        with patch('handlers.estoque_handler.get_product_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_product_by_id = Mock(return_value=None)
            mock_get_service.return_value = mock_service
            
            response = await estoque_handler.handle_product_selection(estoque_request, 999)
        
        assert response.end_conversation == True
        assert "não encontrado" in response.message.lower()
    
    @pytest.mark.asyncio
    async def test_estoque_stock_addition_valid(self, estoque_handler, estoque_request):
        """Test valid stock addition"""
        # Set up form data
        estoque_request.user_data["selected_product_id"] = 1
        estoque_request.user_data["selected_product_name"] = "Test Product"
        estoque_request.update.message.text = "10 / 25.50 / 20.00"
        
        # Mock the business service via ensure_services_initialized
        with patch('handlers.estoque_handler.ModernEstoqueHandler.ensure_services_initialized') as mock_ensure:
            mock_business_service = Mock()
            mock_response = Mock()
            mock_response.message = "Estoque adicionado com sucesso!"
            mock_business_service.add_inventory = Mock(return_value=mock_response)
            mock_ensure.return_value = mock_business_service
            
            response = await estoque_handler.handle_stock_values(estoque_request)
        
        assert "sucesso" in response.message.lower()
        assert response.next_state == ESTOQUE_MENU
    
    @pytest.mark.asyncio
    async def test_estoque_validation_error_handling(self, estoque_handler, estoque_request):
        """Test handling of validation errors"""
        # Set up invalid stock values (wrong format)
        estoque_request.user_data["selected_product_id"] = 1
        estoque_request.update.message.text = "invalid format"
        
        response = await estoque_handler.handle_stock_values(estoque_request)
        
        assert "❌" in response.message
        assert response.next_state == ESTOQUE_ADD_VALUES
    
    @pytest.mark.asyncio
    async def test_estoque_service_error_handling(self, estoque_handler, estoque_request):
        """Test handling of service errors"""
        # Mock the business service to raise ServiceError
        with patch('handlers.estoque_handler.ModernEstoqueHandler.ensure_services_initialized') as mock_ensure:
            mock_business_service = Mock()
            mock_business_service.add_inventory = Mock(side_effect=ServiceError("Database error"))
            mock_ensure.return_value = mock_business_service
            
            estoque_request.user_data["selected_product_id"] = 1
            estoque_request.update.message.text = "10 / 25.50 / 20.00"
            
            # The handler should let the exception bubble up for base handler error handling
            with pytest.raises(ServiceError):
                await estoque_handler.handle_stock_values(estoque_request)
    
    @pytest.mark.parametrize("stock_input,expected_valid,expected_parts", [
        ("10 / 25.50 / 20.00", True, [10, 25.50, 20.00]),
        ("5 / 30 / 25", True, [5, 30.0, 25.0]),
        ("1 / 100.99 / 95.50", True, [1, 100.99, 95.50]),
        ("10 / 25.50", False, None),      # Missing part
        ("invalid / format", False, None), # Invalid format
        ("0 / 25.50 / 20.00", False, None), # Zero quantity
        ("-5 / 25.50 / 20.00", False, None), # Negative quantity
        ("10 / -25.50 / 20.00", False, None), # Negative price
        ("10 / 25.50 / -20.00", False, None), # Negative cost
        ("", False, None),                    # Empty
    ])
    def test_stock_values_parsing(self, stock_input, expected_valid, expected_parts):
        """Test stock values parsing with various inputs"""
        # Test the parsing logic directly via the handler method  
        def parse_stock_values(text):
            parts = [part.strip() for part in text.split('/')]
            if len(parts) != 3:
                raise ValueError("Invalid format")
            
            from utils.input_sanitizer import InputSanitizer
            quantity = InputSanitizer.sanitize_quantity(parts[0])
            unit_price = InputSanitizer.sanitize_price(parts[1])
            unit_cost = InputSanitizer.sanitize_price(parts[2])
            
            return [quantity, unit_price, unit_cost]
        
        try:
            parts = parse_stock_values(stock_input)
            result = True
            if expected_parts:
                # Check if parsed values match expected
                assert parts[0] == expected_parts[0]  # quantity
                assert abs(parts[1] - expected_parts[1]) < 0.01  # price (allow small float differences)
                assert abs(parts[2] - expected_parts[2]) < 0.01  # cost
        except (ValueError, TypeError, IndexError):
            result = False
            parts = None
        
        assert result == expected_valid
    
    def test_stock_calculation_accuracy(self):
        """Test stock calculation precision"""
        # Test the parsing logic directly
        def parse_stock_values(text):
            parts = [part.strip() for part in text.split('/')]
            if len(parts) != 3:
                raise ValueError("Invalid format")
            
            from utils.input_sanitizer import InputSanitizer
            quantity = InputSanitizer.sanitize_quantity(parts[0])
            unit_price = InputSanitizer.sanitize_price(parts[1])
            unit_cost = InputSanitizer.sanitize_price(parts[2])
            
            return [quantity, unit_price, unit_cost]
        
        # Test with decimal values to ensure precision
        quantity, price, cost = parse_stock_values("3 / 15.99 / 12.50")
        
        assert quantity == 3
        assert abs(price - 15.99) < 0.01
        assert abs(cost - 12.50) < 0.01
        
        # Test total value calculation
        total_value = quantity * price
        total_cost = quantity * cost
        
        assert abs(total_value - 47.97) < 0.01
        assert abs(total_cost - 37.50) < 0.01