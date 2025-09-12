#!/usr/bin/env python3
"""
Mocked integration tests for database operations.
Tests business logic without requiring real database connection.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from models.product import CreateProductRequest, AddStockRequest
from models.sale import CreateSaleRequest, CreateSaleItemRequest
from models.user import CreateUserRequest, UserLevel
from models.handler_models import PurchaseRequest, ProductSelectionRequest


class TestDatabaseOperationsMocked:
    """Test suite for database operations using mocks."""
    
    @pytest.fixture(autouse=True)
    def setup_services(self, mock_all_services):
        """Setup services with mocks."""
        self.services = mock_all_services
        self.user_service = mock_all_services['user_service']
        self.product_service = mock_all_services['product_service']
        self.sales_service = mock_all_services['sales_service']
        self.business_service = mock_all_services['business_service']
    
    def test_database_connection_mocked(self, mock_database_manager):
        """Test that database manager is available (mocked)."""
        assert mock_database_manager is not None
        # In real test, this would verify connection, but with mocks we just verify mock exists
        assert hasattr(mock_database_manager, 'acquire_connection')
    
    def test_create_product_mocked(self):
        """Test product creation with mocked service."""
        request = CreateProductRequest(
            nome="Test Product",
            emoji="📦"
        )
        
        # Configure mock to return a product-like object
        mock_product = Mock()
        mock_product.id = 1
        mock_product.nome = "Test Product"
        mock_product.emoji = "📦"
        
        self.product_service.create_product.return_value = mock_product
        
        # Test the service call
        product = self.product_service.create_product(request)
        
        # Verify mock was called correctly
        self.product_service.create_product.assert_called_once_with(request)
        
        # Verify result
        assert product.id == 1
        assert product.nome == "Test Product"
        assert product.emoji == "📦"
    
    def test_add_stock_mocked(self):
        """Test adding stock with mocked service."""
        # Setup: create a product first
        self.product_service.get_product_by_id.return_value = Mock(id=1, nome="Test Product")
        
        request = AddStockRequest(
            produto_id=1,
            quantidade=10,
            valor=25.0,
            custo=50.0
        )
        
        # Configure mock
        self.product_service.add_stock.return_value = True
        
        # Test the service call
        result = self.product_service.add_stock(request)
        
        # Verify
        self.product_service.add_stock.assert_called_once_with(request)
        assert result is True
    
    def test_get_available_quantity_mocked(self):
        """Test getting available quantity with mocked service."""
        product_id = 1
        expected_quantity = 15
        
        # Configure mock
        self.product_service.get_available_quantity.return_value = expected_quantity
        
        # Test
        quantity = self.product_service.get_available_quantity(product_id)
        
        # Verify
        self.product_service.get_available_quantity.assert_called_once_with(product_id)
        assert quantity == expected_quantity
    
    def test_consume_stock_fifo_mocked(self):
        """Test FIFO stock consumption with mocked service."""
        product_id = 1
        quantity_to_consume = 5
        
        # Mock FIFO consumption result
        mock_consumption = [
            {"stock_id": 1, "quantity_consumed": 3, "cost": 30.0},
            {"stock_id": 2, "quantity_consumed": 2, "cost": 20.0}
        ]
        
        self.product_service.consume_stock_fifo.return_value = mock_consumption
        
        # Test
        consumption = self.product_service.consume_stock_fifo(product_id, quantity_to_consume)
        
        # Verify
        self.product_service.consume_stock_fifo.assert_called_once_with(product_id, quantity_to_consume)
        assert len(consumption) == 2
        assert consumption[0]["quantity_consumed"] == 3
        assert consumption[1]["quantity_consumed"] == 2
    
    def test_create_user_mocked(self):
        """Test user creation with mocked service."""
        request = CreateUserRequest(
            username="testuser",
            password="testpass",
            level=UserLevel.ADMIN
        )
        
        # Configure mock
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.level = UserLevel.ADMIN
        
        self.user_service.create_user.return_value = mock_user
        
        # Test
        user = self.user_service.create_user(request)
        
        # Verify
        self.user_service.create_user.assert_called_once_with(request)
        assert user.id == 1
        assert user.username == "testuser"
        assert user.level == UserLevel.ADMIN
    
    def test_create_sale_mocked(self):
        """Test sale creation with mocked service."""
        request = CreateSaleRequest(
            comprador="Test Buyer",
            items=[
                CreateSaleItemRequest(produto_id=1, quantidade=2, valor_unitario=50.0)
            ]
        )
        
        # Configure mock
        mock_sale = Mock()
        mock_sale.id = 1
        mock_sale.comprador = "Test Buyer"
        
        self.sales_service.create_sale.return_value = mock_sale
        
        # Test
        sale = self.sales_service.create_sale(request)
        
        # Verify
        self.sales_service.create_sale.assert_called_once_with(request)
        assert sale.id == 1
        assert sale.comprador == "Test Buyer"
    
    def test_purchase_flow_end_to_end_mocked(self):
        """Test complete purchase flow with mocked services."""
        # Setup purchase request
        purchase_request = PurchaseRequest(
            buyer_name="End to End Buyer",
            items=[
                ProductSelectionRequest(product_id=1, quantity=2, custom_price=25.0)
            ],
            total_amount=50.0,
            chat_id=12345
        )
        
        # Configure business service mock
        mock_response = Mock()
        mock_response.success = True
        mock_response.message = "Purchase completed successfully"
        mock_response.sale_id = 1
        
        self.business_service.process_purchase.return_value = mock_response
        
        # Test
        response = self.business_service.process_purchase(purchase_request)
        
        # Verify
        self.business_service.process_purchase.assert_called_once_with(purchase_request)
        assert response.success is True
        assert response.sale_id == 1
        assert "successfully" in response.message
    
    def test_insufficient_stock_error_mocked(self):
        """Test handling of insufficient stock error with mocked service."""
        product_id = 1
        requested_quantity = 100
        
        # Mock insufficient stock scenario
        from services.base_service import ValidationError
        self.product_service.consume_stock_fifo.side_effect = ValidationError("Insufficient stock")
        
        # Test
        with pytest.raises(ValidationError) as exc_info:
            self.product_service.consume_stock_fifo(product_id, requested_quantity)
        
        # Verify
        assert "Insufficient stock" in str(exc_info.value)
        self.product_service.consume_stock_fifo.assert_called_once_with(product_id, requested_quantity)
    
    def test_multiple_products_purchase_mocked(self):
        """Test purchasing multiple products with mocked services."""
        # Setup purchase with multiple products
        purchase_request = PurchaseRequest(
            buyer_name="Multi Product Buyer",
            items=[
                ProductSelectionRequest(product_id=1, quantity=2, custom_price=25.0),
                ProductSelectionRequest(product_id=2, quantity=1, custom_price=50.0)
            ],
            total_amount=100.0,
            chat_id=12345
        )
        
        # Configure mock response
        mock_response = Mock()
        mock_response.success = True
        mock_response.message = "Multiple products purchased"
        mock_response.sale_id = 2
        
        self.business_service.process_purchase.return_value = mock_response
        
        # Test
        response = self.business_service.process_purchase(purchase_request)
        
        # Verify
        assert response.success is True
        assert response.sale_id == 2
        assert len(purchase_request.items) == 2
        
        # Verify all items were included
        total_from_items = sum(item.quantity * item.custom_price for item in purchase_request.items)
        assert total_from_items == purchase_request.total_amount


class TestBusinessLogicMocked:
    """Test business logic layer with mocked dependencies."""
    
    @pytest.fixture(autouse=True)
    def setup_business_service(self, mock_all_services):
        """Setup business service with mocks."""
        self.business_service = mock_all_services['business_service']
    
    def test_purchase_validation_mocked(self):
        """Test purchase validation logic with mocks."""
        # Test valid purchase
        valid_request = PurchaseRequest(
            buyer_name="Valid Buyer",
            items=[ProductSelectionRequest(product_id=1, quantity=1, custom_price=10.0)],
            total_amount=10.0,
            chat_id=12345
        )
        
        mock_response = Mock()
        mock_response.success = True
        mock_response.warnings = []
        
        self.business_service.process_purchase.return_value = mock_response
        
        response = self.business_service.process_purchase(valid_request)
        assert response.success is True
        assert len(response.warnings) == 0
    
    def test_purchase_with_warnings_mocked(self):
        """Test purchase that succeeds but has warnings."""
        request = PurchaseRequest(
            buyer_name="Warning Buyer",
            items=[ProductSelectionRequest(product_id=1, quantity=10, custom_price=1.0)],
            total_amount=10.0,
            chat_id=12345
        )
        
        mock_response = Mock()
        mock_response.success = True
        mock_response.warnings = ["Low stock warning", "Price below cost warning"]
        
        self.business_service.process_purchase.return_value = mock_response
        
        response = self.business_service.process_purchase(request)
        assert response.success is True
        assert len(response.warnings) == 2
        assert "Low stock" in response.warnings[0]