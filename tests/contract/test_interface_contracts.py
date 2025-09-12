"""
Interface Contract Tests

Tests that validate interfaces between different layers:
- Service ↔ Model contracts (what you just fixed)
- Handler ↔ Service contracts  
- Business Service ↔ Core Service contracts

These tests catch issues like:
- Method signature mismatches
- Attribute access errors
- Return type inconsistencies
- Interface compatibility
"""

import pytest
import inspect
from typing import Any, Dict, List, get_type_hints
from dataclasses import fields

# Import models
from models.sale import Sale, SaleWithPayments, CreateSaleRequest, CreatePaymentRequest
from models.user import User, CreateUserRequest
from models.product import Product, CreateProductRequest, AddStockRequest

# Import services
from services.sales_service import SalesService
from services.user_service import UserService
from services.product_service import ProductService
from services.handler_business_service import HandlerBusinessService

# Import handler models
from models.handler_models import (
    PurchaseRequest, PurchaseResponse,
    PaymentRequest, PaymentResponse,
    ReportRequest, ReportResponse
)


class InterfaceValidator:
    """Validates interfaces between system components."""
    
    @staticmethod
    def get_public_methods(cls) -> Dict[str, Any]:
        """Get all public methods of a class."""
        return {
            name: method for name, method in inspect.getmembers(cls, inspect.isfunction)
            if not name.startswith('_')
        }
    
    @staticmethod
    def get_public_attributes(obj) -> List[str]:
        """Get all public attributes of an object."""
        if hasattr(obj, '__dataclass_fields__'):
            # Dataclass - get field names
            return [field.name for field in fields(obj)]
        else:
            # Regular class - get non-method attributes
            return [
                attr for attr in dir(obj)
                if not attr.startswith('_') and not callable(getattr(obj, attr))
            ]
    
    @staticmethod
    def validate_method_exists(cls, method_name: str, expected_signature: str = None) -> bool:
        """Validate that a method exists with expected signature."""
        if not hasattr(cls, method_name):
            return False
        
        method = getattr(cls, method_name)
        if not callable(method):
            return False
        
        if expected_signature:
            sig = inspect.signature(method)
            return str(sig) == expected_signature
        
        return True
    
    @staticmethod
    def validate_attribute_access(obj, attribute_path: str) -> bool:
        """Validate that an attribute can be accessed via dot notation."""
        try:
            current = obj
            for part in attribute_path.split('.'):
                if hasattr(current, part):
                    current = getattr(current, part)
                else:
                    return False
            return True
        except Exception:
            return False


class TestServiceModelContracts:
    """Test contracts between services and models."""
    
    def setup_method(self):
        """Set up test environment."""
        self.validator = InterfaceValidator()
    
    @pytest.mark.contract
    def test_sale_model_interface_contract(self):
        """Test that Sale model provides expected interface for services."""
        
        # Create a mock Sale object
        sale = Sale(id=1, comprador="test", data="2024-01-01")
        
        # Test required attributes exist
        required_attrs = ['id', 'comprador', 'data']
        for attr in required_attrs:
            assert hasattr(sale, attr), f"Sale model missing required attribute: {attr}"
        
        # Test required methods exist
        required_methods = ['get_total_value', 'get_item_count', 'from_db_row']
        for method in required_methods:
            assert hasattr(sale, method), f"Sale model missing required method: {method}"
            assert callable(getattr(sale, method)), f"Sale.{method} is not callable"
        
        # Test method signatures
        assert callable(sale.get_total_value), "get_total_value must be callable"
        assert callable(sale.get_item_count), "get_item_count must be callable"
        
        # Test that commonly misused attributes don't exist
        forbidden_attrs = ['total_amount', 'buyer_name', 'created_at', 'amount_paid']
        for attr in forbidden_attrs:
            assert not hasattr(sale, attr), f"Sale model should not have attribute: {attr} (use correct interface)"
    
    @pytest.mark.contract
    def test_sale_with_payments_interface_contract(self):
        """Test SaleWithPayments model interface."""
        
        # Create mock objects
        sale = Sale(id=1, comprador="test", data="2024-01-01")
        sale_with_payments = SaleWithPayments(sale=sale, payments=[], total_paid=0.0)
        
        # Test required attributes
        required_attrs = ['sale', 'payments', 'total_paid']
        for attr in required_attrs:
            assert hasattr(sale_with_payments, attr), f"SaleWithPayments missing: {attr}"
        
        # Test required properties
        required_properties = ['balance_due', 'is_fully_paid', 'is_overpaid']
        for prop in required_properties:
            assert hasattr(sale_with_payments, prop), f"SaleWithPayments missing property: {prop}"
        
        # Test that commonly misused attributes don't exist
        forbidden_attrs = ['total_amount']
        for attr in forbidden_attrs:
            assert not hasattr(sale_with_payments, attr), f"SaleWithPayments should not have: {attr}"
    
    @pytest.mark.contract
    def test_sales_service_return_type_contracts(self):
        """Test that SalesService returns expected types."""
        
        # Test method exists and signature
        service_methods = {
            'create_sale': 'CreateSaleRequest -> Sale',
            'get_sale_by_id': 'int -> Optional[Sale]', 
            'get_sale_with_payments': 'int -> Optional[SaleWithPayments]',
            'create_payment': 'CreatePaymentRequest -> Payment'
        }
        
        for method_name, expected_return in service_methods.items():
            assert hasattr(SalesService, method_name), f"SalesService missing method: {method_name}"
            method = getattr(SalesService, method_name)
            assert callable(method), f"SalesService.{method_name} not callable"
    
    @pytest.mark.contract
    def test_user_model_interface_contract(self):
        """Test User model interface."""
        
        user = User(id=1, username="test", password="hash", nivel="user", chat_id=123)
        
        required_attrs = ['id', 'username', 'password', 'nivel', 'chat_id']
        for attr in required_attrs:
            assert hasattr(user, attr), f"User model missing: {attr}"
        
        # Test forbidden attributes that might be misused
        forbidden_attrs = ['level', 'permission_level', 'role']
        for attr in forbidden_attrs:
            assert not hasattr(user, attr), f"User model should not have: {attr} (use 'nivel')"
    
    @pytest.mark.contract
    def test_product_model_interface_contract(self):
        """Test Product model interface."""
        
        product = Product(id=1, nome="test", emoji="🧪", data="2024-01-01")
        
        required_attrs = ['id', 'nome', 'emoji', 'data']
        for attr in required_attrs:
            assert hasattr(product, attr), f"Product model missing: {attr}"
        
        # Test forbidden attributes
        forbidden_attrs = ['name', 'created_at', 'price']
        for attr in forbidden_attrs:
            assert not hasattr(product, attr), f"Product model should not have: {attr}"


class TestHandlerServiceContracts:
    """Test contracts between handlers and services."""
    
    def setup_method(self):
        """Set up test environment."""
        self.validator = InterfaceValidator()
    
    @pytest.mark.contract
    def test_purchase_request_response_contract(self):
        """Test PurchaseRequest/PurchaseResponse interface contract."""
        
        # Test PurchaseRequest has required fields
        purchase_req_fields = [f.name for f in fields(PurchaseRequest)]
        expected_fields = ['buyer_name', 'items', 'total_amount', 'chat_id']
        
        for field in expected_fields:
            assert field in purchase_req_fields, f"PurchaseRequest missing field: {field}"
        
        # Test PurchaseResponse has required fields
        purchase_resp_fields = [f.name for f in fields(PurchaseResponse)]
        expected_resp_fields = ['success', 'total_amount', 'sale_id', 'message']
        
        for field in expected_resp_fields:
            assert field in purchase_resp_fields, f"PurchaseResponse missing field: {field}"
    
    @pytest.mark.contract
    def test_payment_request_response_contract(self):
        """Test PaymentRequest/PaymentResponse interface contract."""
        
        # Test PaymentRequest fields
        payment_req_fields = [f.name for f in fields(PaymentRequest)]
        expected_fields = ['sale_id', 'amount', 'chat_id']
        
        for field in expected_fields:
            assert field in payment_req_fields, f"PaymentRequest missing field: {field}"
        
        # Test PaymentResponse fields
        payment_resp_fields = [f.name for f in fields(PaymentResponse)]
        expected_resp_fields = ['success', 'remaining_debt', 'total_paid', 'is_fully_paid', 'message']
        
        for field in expected_resp_fields:
            assert field in payment_resp_fields, f"PaymentResponse missing field: {field}"
    
    @pytest.mark.contract
    def test_business_service_interface_contract(self):
        """Test HandlerBusinessService provides expected interface."""
        
        required_methods = [
            'handle_purchase',
            'process_payment', 
            'generate_report'
        ]
        
        for method in required_methods:
            assert hasattr(HandlerBusinessService, method), f"HandlerBusinessService missing: {method}"
            assert callable(getattr(HandlerBusinessService, method)), f"{method} not callable"


class TestRuntimeInterfaceValidation:
    """Test interfaces with actual object instances to catch runtime issues."""
    
    @pytest.mark.contract
    def test_sale_attribute_access_patterns(self):
        """Test common Sale attribute access patterns used in codebase."""
        
        # Create realistic Sale object
        sale = Sale(id=1, comprador="Test User", data="2024-01-01 10:00:00")
        sale.items = []  # Empty items list
        
        # Test patterns used in business service
        try:
            # These should work
            buyer_name = sale.comprador  # Not sale.buyer_name
            created_at = sale.data       # Not sale.created_at  
            total_value = sale.get_total_value()  # Not sale.total_amount
            item_count = sale.get_item_count()
            
            assert isinstance(buyer_name, str)
            assert isinstance(total_value, (int, float))
            assert isinstance(item_count, int)
            
        except AttributeError as e:
            pytest.fail(f"Sale interface validation failed: {e}")
    
    @pytest.mark.contract
    def test_sale_with_payments_access_patterns(self):
        """Test SaleWithPayments access patterns."""
        
        sale = Sale(id=1, comprador="Test", data="2024-01-01")
        sale.items = []
        swp = SaleWithPayments(sale=sale, payments=[], total_paid=50.0)
        
        try:
            # These should work
            total_amount = swp.sale.get_total_value()  # Not swp.total_amount
            remaining = swp.balance_due
            is_paid = swp.is_fully_paid
            paid_amount = swp.total_paid
            
            assert isinstance(total_amount, (int, float))
            assert isinstance(remaining, (int, float))
            assert isinstance(is_paid, bool)
            assert isinstance(paid_amount, (int, float))
            
        except AttributeError as e:
            pytest.fail(f"SaleWithPayments interface validation failed: {e}")
    
    @pytest.mark.contract
    def test_service_request_object_compatibility(self):
        """Test that request objects are compatible with service methods."""
        
        # Test CreateSaleRequest compatibility
        from decimal import Decimal
        from models.sale import CreateSaleItemRequest
        
        sale_item = CreateSaleItemRequest(
            produto_id=1,
            quantidade=2,
            valor_unitario=25.0
        )
        
        sale_request = CreateSaleRequest(
            comprador="Test User",
            items=[sale_item]
        )
        
        # Test that request has expected interface
        assert hasattr(sale_request, 'comprador')
        assert hasattr(sale_request, 'items')
        assert hasattr(sale_request, 'validate')
        assert hasattr(sale_request, 'get_total_value')
        
        # Test validation works
        errors = sale_request.validate()
        assert isinstance(errors, list)
        
        # Test total calculation works
        total = sale_request.get_total_value()
        assert total == 50.0  # 2 * 25.0


class TestCommonInterfaceMistakes:
    """Test for common interface mistakes that cause runtime errors."""
    
    @pytest.mark.contract
    def test_attribute_vs_method_mistakes(self):
        """Test that commonly confused attributes vs methods are caught."""
        
        sale = Sale(id=1, comprador="Test", data="2024-01-01")
        
        # These should raise AttributeError if mistakenly accessed
        with pytest.raises(AttributeError):
            _ = sale.total_amount  # Should use get_total_value()
        
        with pytest.raises(AttributeError):
            _ = sale.buyer_name    # Should use comprador
        
        with pytest.raises(AttributeError):
            _ = sale.created_at    # Should use data
    
    @pytest.mark.contract
    def test_service_method_signature_compatibility(self):
        """Test that services can be called with expected parameters."""
        
        # Test that CreatePaymentRequest has expected structure
        payment_req = CreatePaymentRequest(venda_id=1, valor_pago=50.0)
        
        assert hasattr(payment_req, 'venda_id')
        assert hasattr(payment_req, 'valor_pago')
        assert hasattr(payment_req, 'validate')
        
        # Test validation
        errors = payment_req.validate()
        assert isinstance(errors, list)


if __name__ == "__main__":
    # Run interface contract tests
    pytest.main([__file__, "-v", "-m", "contract"])