"""
Integration Contract Tests

Tests actual integration between components with real objects and method calls.
These tests would have caught your recent issues like:
- sale.total_amount attribute errors
- Method signature mismatches
- Return type incompatibilities
"""

import pytest
import os
from unittest.mock import Mock

# Initialize services before importing
os.environ['CONTRACT_TESTING'] = 'true'

from services.sales_service import SalesService
from services.user_service import UserService
from services.product_service import ProductService
from services.handler_business_service import HandlerBusinessService

from models.sale import CreateSaleRequest, CreateSaleItemRequest, CreatePaymentRequest
from models.user import CreateUserRequest
from models.product import CreateProductRequest, AddStockRequest
from models.handler_models import PurchaseRequest, PaymentRequest, ProductSelectionRequest


class TestServiceIntegrationContracts:
    """Test actual service integration with real method calls."""
    
    def setup_method(self):
        """Set up with mock services to test interfaces without database."""
        
        # Create mock services that return realistic objects
        self.sales_service = Mock(spec=SalesService)
        self.user_service = Mock(spec=UserService) 
        self.product_service = Mock(spec=ProductService)
        
        # Configure mocks to return objects with correct interfaces
        self._setup_realistic_mocks()
    
    def _setup_realistic_mocks(self):
        """Configure mocks to return realistic objects."""
        from models.sale import Sale
        from models.user import User
        from models.product import Product
        
        # Mock sale with realistic interface
        mock_sale = Sale(id=1, comprador="Test User", data="2024-01-01")
        mock_sale.items = []
        self.sales_service.create_sale.return_value = mock_sale
        self.sales_service.get_sale_by_id.return_value = mock_sale
        
        # Mock user
        mock_user = User(id=1, username="test", password="hash", nivel="user", chat_id=123)
        self.user_service.create_user.return_value = mock_user
        
        # Mock product
        mock_product = Product(id=1, nome="Test Product", emoji="🧪", data="2024-01-01")
        self.product_service.create_product.return_value = mock_product
    
    @pytest.mark.contract
    def test_business_service_purchase_integration_contract(self):
        """Test that business service can handle purchase workflow with correct interfaces."""
        
        # Create realistic business service with mocked dependencies
        business_service = HandlerBusinessService()
        business_service.sales_service = self.sales_service
        business_service.product_service = self.product_service
        business_service.user_service = self.user_service
        
        # Create purchase request with correct interface
        purchase_request = PurchaseRequest(
            buyer_name="Test User",
            items=[
                ProductSelectionRequest(
                    product_id=1,
                    quantity=2,
                    custom_price=25.0
                )
            ],
            total_amount=50.0,
            chat_id=123
        )
        
        # Mock the create_sale to return realistic Sale object
        from models.sale import Sale
        mock_sale = Sale(id=1, comprador="Test User", data="2024-01-01")
        mock_sale.items = []
        self.sales_service.create_sale.return_value = mock_sale
        
        try:
            # This should work with correct interfaces
            response = business_service.handle_purchase(purchase_request)
            
            # Verify response has expected interface
            assert hasattr(response, 'success')
            assert hasattr(response, 'total_amount')
            assert hasattr(response, 'sale_id')
            assert hasattr(response, 'message')
            
            # Verify the response uses correct Sale interface
            assert response.total_amount == mock_sale.get_total_value()
            
        except AttributeError as e:
            pytest.fail(f"Purchase integration failed due to interface mismatch: {e}")
    
    @pytest.mark.contract
    def test_payment_integration_contract(self):
        """Test payment workflow integration."""
        
        from models.sale import SaleWithPayments
        
        # Setup business service
        business_service = HandlerBusinessService()
        business_service.sales_service = self.sales_service
        
        # Mock get_sale_with_payments to return realistic object
        mock_sale = Sale(id=1, comprador="Test User", data="2024-01-01")
        mock_sale.items = []
        mock_swp = SaleWithPayments(sale=mock_sale, payments=[], total_paid=0.0)
        
        self.sales_service.get_sale_by_id.return_value = mock_sale
        self.sales_service.get_sale_with_payments.return_value = mock_swp
        self.sales_service.create_payment.return_value = Mock()  # Payment object
        
        # Create payment request
        payment_request = PaymentRequest(
            sale_id=1,
            amount=25.0,
            chat_id=123
        )
        
        try:
            # This should work with correct interfaces
            response = business_service.process_payment(payment_request)
            
            # Verify response interface
            assert hasattr(response, 'success')
            assert hasattr(response, 'remaining_debt')
            assert hasattr(response, 'total_paid')
            assert hasattr(response, 'is_fully_paid')
            
        except AttributeError as e:
            pytest.fail(f"Payment integration failed due to interface mismatch: {e}")
    
    @pytest.mark.contract
    def test_sale_creation_integration_contract(self):
        """Test that sale creation works with correct request/response interfaces."""
        
        # Test CreateSaleRequest interface
        sale_item = CreateSaleItemRequest(
            produto_id=1,
            quantidade=2,
            valor_unitario=25.0
        )
        
        sale_request = CreateSaleRequest(
            comprador="Test User",
            items=[sale_item]
        )
        
        # Verify request interface
        assert hasattr(sale_request, 'comprador')  # Not buyer_name
        assert hasattr(sale_request, 'items')
        assert hasattr(sale_request, 'validate')
        assert hasattr(sale_request, 'get_total_value')  # Not total_amount
        
        # Test that validation works
        errors = sale_request.validate()
        assert isinstance(errors, list)
        
        # Test that total calculation works
        total = sale_request.get_total_value()
        assert total == 50.0


class TestRealObjectInterfaceCompatibility:
    """Test interface compatibility with real objects."""
    
    @pytest.mark.contract
    def test_sale_object_interface_in_business_logic(self):
        """Test that Sale objects work correctly in business logic contexts."""
        
        from models.sale import Sale, SaleItem
        
        # Create realistic Sale with items
        sale = Sale(id=1, comprador="Test User", data="2024-01-01 10:30:00")
        
        # Add realistic items
        item1 = SaleItem(id=1, venda_id=1, produto_id=1, quantidade=2, valor_unitario=25.0)
        item2 = SaleItem(id=2, venda_id=1, produto_id=2, quantidade=1, valor_unitario=50.0)
        sale.items = [item1, item2]
        
        # Test interface usage patterns from business service
        try:
            # These are the patterns used in your codebase
            buyer_name = sale.comprador           # ✓ Correct
            created_at = sale.data               # ✓ Correct  
            total_value = sale.get_total_value()  # ✓ Correct
            item_count = sale.get_item_count()   # ✓ Correct
            
            # Verify calculations work
            assert total_value == 100.0  # (2*25) + (1*50)
            assert item_count == 3       # 2 + 1
            assert buyer_name == "Test User"
            
        except Exception as e:
            pytest.fail(f"Sale interface compatibility failed: {e}")
    
    @pytest.mark.contract
    def test_payment_request_creation_compatibility(self):
        """Test CreatePaymentRequest compatibility with services."""
        
        payment_request = CreatePaymentRequest(
            venda_id=1,
            valor_pago=50.0
        )
        
        # Test interface
        assert hasattr(payment_request, 'venda_id')    # ✓ Correct
        assert hasattr(payment_request, 'valor_pago')  # ✓ Correct
        assert hasattr(payment_request, 'validate')
        
        # Test validation
        errors = payment_request.validate()
        assert isinstance(errors, list)
        assert len(errors) == 0  # Valid request
        
        # Test invalid request
        invalid_request = CreatePaymentRequest(venda_id=1, valor_pago=-10.0)
        errors = invalid_request.validate()
        assert len(errors) > 0  # Should have validation errors


class TestInterfaceErrorPrevention:
    """Test that common interface errors are prevented."""
    
    @pytest.mark.contract
    def test_prevents_total_amount_attribute_error(self):
        """Test that the total_amount attribute error is prevented."""
        
        from models.sale import Sale
        
        sale = Sale(id=1, comprador="Test", data="2024-01-01")
        
        # This should raise AttributeError (preventing accidental use)
        with pytest.raises(AttributeError):
            _ = sale.total_amount  # Wrong - should use get_total_value()
        
        # This should work
        total = sale.get_total_value()  # Correct
        assert isinstance(total, (int, float))
    
    @pytest.mark.contract
    def test_prevents_buyer_name_attribute_error(self):
        """Test that buyer_name attribute error is prevented."""
        
        from models.sale import Sale
        
        sale = Sale(id=1, comprador="Test User", data="2024-01-01")
        
        # This should raise AttributeError
        with pytest.raises(AttributeError):
            _ = sale.buyer_name  # Wrong - should use comprador
        
        # This should work
        buyer = sale.comprador  # Correct
        assert buyer == "Test User"
    
    @pytest.mark.contract
    def test_prevents_payment_interface_errors(self):
        """Test that payment interface errors are prevented."""
        
        from models.sale import Sale, SaleWithPayments
        
        sale = Sale(id=1, comprador="Test", data="2024-01-01")
        swp = SaleWithPayments(sale=sale, payments=[], total_paid=50.0)
        
        # This should raise AttributeError
        with pytest.raises(AttributeError):
            _ = swp.total_amount  # Wrong - should use sale.get_total_value()
        
        # This should work
        total = swp.sale.get_total_value()  # Correct
        balance = swp.balance_due           # Correct
        paid = swp.total_paid              # Correct
        
        assert isinstance(total, (int, float))
        assert isinstance(balance, (int, float))
        assert isinstance(paid, (int, float))


if __name__ == "__main__":
    # Run integration contract tests
    pytest.main([__file__, "-v", "-m", "contract"])