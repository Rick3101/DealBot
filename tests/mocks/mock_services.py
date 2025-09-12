"""
Mock services for testing handlers.
Provides standardized mocks for all service dependencies.
"""

from unittest.mock import Mock, AsyncMock
from typing import Dict, Any, Optional


class MockUser:
    """Mock user object with configurable properties."""
    
    def __init__(self, username: str = "testuser", level: str = "admin", chat_id: int = 12345):
        self.username = username
        self.chat_id = chat_id
        self.level = Mock()
        self.level.value = level


class MockProduct:
    """Mock product object for testing."""
    
    def __init__(self, id: int = 1, name: str = "Test Product", emoji: str = "🧪"):
        self.id = id
        self.name = name
        self.emoji = emoji
        self.media_file_id = None


class MockProductWithStock:
    """Mock product with stock information."""
    
    def __init__(self, product: MockProduct = None, available_quantity: int = 10):
        self.product = product or MockProduct()
        self.available_quantity = available_quantity


class MockUserService:
    """Mock user service with common methods."""
    
    def __init__(self):
        self.authenticate_user = AsyncMock(return_value=True)
        self.get_user_permission_level = Mock(return_value="admin")
        self.get_user_by_chat_id = Mock(return_value=MockUser())
        self.create_user = AsyncMock(return_value=1)
        self.update_user = AsyncMock(return_value=True)
        self.delete_user = AsyncMock(return_value=True)
        self.get_all_users = AsyncMock(return_value=[])


class MockProductService:
    """Mock product service with CRUD operations."""
    
    def __init__(self):
        self.get_all_products = AsyncMock(return_value=[])
        self.get_product_by_id = AsyncMock(return_value=MockProduct())
        self.create_product = AsyncMock(return_value=1)
        self.update_product = AsyncMock(return_value=True)
        self.delete_product = AsyncMock(return_value=True)
        self.get_products_with_stock = AsyncMock(return_value=[MockProductWithStock()])


class MockSalesService:
    """Mock sales service for purchase operations."""
    
    def __init__(self):
        self.create_sale = AsyncMock(return_value=1)
        self.get_sales = AsyncMock(return_value=[])
        self.process_payment = AsyncMock(return_value=True)
        self.get_debt_report = AsyncMock(return_value=[])
        self.calculate_total = Mock(return_value=100.0)


class MockSmartContractService:
    """Mock smart contract service."""
    
    def __init__(self):
        self.create_contract = AsyncMock(return_value=1)
        self.add_transaction = AsyncMock(return_value=1)
        self.confirm_transaction = AsyncMock(return_value=True)
        self.get_contract_transactions = AsyncMock(return_value=[])


class MockHandlerBusinessService:
    """Mock high-level business service that handlers use."""
    
    def __init__(self):
        self.handle_login = AsyncMock(return_value={"success": True, "message": "Login successful"})
        self.handle_product_creation = AsyncMock(return_value={"success": True, "product_id": 1})
        self.handle_purchase = AsyncMock(return_value={"success": True, "sale_id": 1})
        self.handle_inventory_update = AsyncMock(return_value={"success": True})
        self.handle_user_creation = AsyncMock(return_value={"success": True, "user_id": 1})
        
        # Product management
        self.get_products_for_purchase = Mock(return_value=[MockProductWithStock()])
        self.process_purchase = AsyncMock(return_value={"success": True, "sale_id": 1})
        
        # User management  
        self.get_users_for_management = Mock(return_value=[MockUser()])
        self.validate_user_permissions = Mock(return_value=True)


class MockServiceContainer:
    """Container for all mock services with easy configuration."""
    
    def __init__(self, **custom_services):
        # Initialize default services
        self.user_service = custom_services.get('user_service', MockUserService())
        self.product_service = custom_services.get('product_service', MockProductService())
        self.sales_service = custom_services.get('sales_service', MockSalesService())
        self.smartcontract_service = custom_services.get('smartcontract_service', MockSmartContractService())
        self.handler_business_service = custom_services.get('handler_business_service', MockHandlerBusinessService())
        
        self._services = {
            'user_service': self.user_service,
            'product_service': self.product_service,
            'sales_service': self.sales_service,
            'smartcontract_service': self.smartcontract_service,
            'handler_business_service': self.handler_business_service,
        }
    
    def get_service(self, service_name: str):
        """Get a service by name."""
        return self._services.get(service_name)
    
    def configure_user(self, username: str = "testuser", level: str = "admin", chat_id: int = 12345):
        """Configure the mock user for testing."""
        mock_user = MockUser(username, level, chat_id)
        self.user_service.get_user_by_chat_id.return_value = mock_user
        self.user_service.get_user_permission_level.return_value = level
        return mock_user
    
    def configure_products(self, products: list = None):
        """Configure mock products for testing."""
        if products is None:
            products = [MockProductWithStock()]
        
        self.product_service.get_products_with_stock.return_value = products
        self.handler_business_service.get_products_for_purchase.return_value = products
        return products
    
    def configure_authentication(self, success: bool = True, message: str = "Login successful"):
        """Configure authentication behavior."""
        self.user_service.authenticate_user.return_value = success
        self.handler_business_service.handle_login.return_value = {
            "success": success,
            "message": message
        }
    
    def configure_purchase_flow(self, success: bool = True, sale_id: int = 1):
        """Configure purchase flow behavior."""
        self.sales_service.create_sale.return_value = sale_id if success else None
        self.handler_business_service.process_purchase.return_value = {
            "success": success,
            "sale_id": sale_id if success else None
        }


def create_mock_services(**kwargs) -> MockServiceContainer:
    """Factory function to create configured mock services."""
    return MockServiceContainer(**kwargs)