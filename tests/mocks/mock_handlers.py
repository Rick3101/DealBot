"""
Specialized mock handler configurations for different testing scenarios.
Provides pre-configured handlers for common test cases.
"""

from unittest.mock import Mock
from .mock_services import MockServiceContainer, create_mock_services, MockUser, MockProduct, MockProductWithStock
from .mock_handler_factory import MockHandlerFactory


class LoginHandlerMocks:
    """Pre-configured login handler scenarios."""
    
    @staticmethod
    def successful_login():
        """Handler configured for successful login flow."""
        mock_services = create_mock_services()
        mock_services.configure_authentication(success=True, message="Login successful")
        mock_services.configure_user(username="testuser", level="admin")
        return mock_services
    
    @staticmethod
    def failed_authentication():
        """Handler configured for failed authentication."""
        mock_services = create_mock_services()
        mock_services.configure_authentication(success=False, message="Invalid credentials")
        return mock_services


class BuyHandlerMocks:
    """Pre-configured buy handler scenarios."""
    
    @staticmethod
    def admin_user_purchase():
        """Handler configured for admin user making a purchase."""
        mock_services = create_mock_services()
        mock_services.configure_user(username="admin", level="admin")
        mock_services.configure_products([
            MockProductWithStock(MockProduct(1, "Product A", "🧪"), 10),
            MockProductWithStock(MockProduct(2, "Product B", "🔬"), 5)
        ])
        mock_services.configure_purchase_flow(success=True, sale_id=1)
        return mock_services
    
    @staticmethod
    def owner_user_purchase():
        """Handler configured for owner user making a purchase."""
        mock_services = create_mock_services()
        mock_services.configure_user(username="owner", level="owner")
        mock_services.configure_products([
            MockProductWithStock(MockProduct(1, "Secret Product", "💀"), 3)
        ])
        mock_services.configure_purchase_flow(success=True, sale_id=2)
        return mock_services
    
    @staticmethod
    def insufficient_stock():
        """Handler configured for insufficient stock scenario."""
        mock_services = create_mock_services()
        mock_services.configure_user(level="admin")
        mock_services.configure_products([
            MockProductWithStock(MockProduct(1, "Low Stock", "⚠️"), 0)
        ])
        mock_services.configure_purchase_flow(success=False)
        return mock_services


class ProductHandlerMocks:
    """Pre-configured product handler scenarios."""
    
    @staticmethod
    def owner_create_product():
        """Handler configured for owner creating products."""
        mock_services = create_mock_services()
        mock_services.configure_user(level="owner")
        mock_services.handler_business_service.handle_product_creation.return_value = {
            "success": True,
            "product_id": 1,
            "message": "Product created successfully"
        }
        return mock_services
    
    @staticmethod
    def insufficient_permissions():
        """Handler configured for insufficient permissions."""
        mock_services = create_mock_services()
        mock_services.configure_user(level="user")  # Regular user can't create products
        return mock_services


class UserHandlerMocks:
    """Pre-configured user handler scenarios."""
    
    @staticmethod
    def owner_manage_users():
        """Handler configured for owner managing users."""
        mock_services = create_mock_services()
        mock_services.configure_user(level="owner")
        mock_services.handler_business_service.get_users_for_management.return_value = [
            MockUser("user1", "user", 111),
            MockUser("admin1", "admin", 222),
            MockUser("owner1", "owner", 333)
        ]
        return mock_services


class HandlerScenarios:
    """Collection of all handler scenarios for easy access."""
    
    login = LoginHandlerMocks
    buy = BuyHandlerMocks
    product = ProductHandlerMocks
    user = UserHandlerMocks


class MockHandlerBuilder:
    """Builder pattern for creating complex handler scenarios."""
    
    def __init__(self):
        self.factory = MockHandlerFactory()
        self.mock_services = create_mock_services()
    
    def with_user(self, username: str = "testuser", level: str = "admin", chat_id: int = 12345):
        """Configure the user for this handler."""
        self.mock_services.configure_user(username, level, chat_id)
        return self
    
    def with_products(self, products: list):
        """Configure products for this handler."""
        self.mock_services.configure_products(products)
        return self
    
    def with_authentication(self, success: bool = True, message: str = "Success"):
        """Configure authentication behavior."""
        self.mock_services.configure_authentication(success, message)
        return self
    
    def with_purchase_flow(self, success: bool = True, sale_id: int = 1):
        """Configure purchase flow behavior."""
        self.mock_services.configure_purchase_flow(success, sale_id)
        return self
    
    def build_login_handler(self):
        """Build a login handler with current configuration."""
        return self.factory.create_login_handler(self.mock_services)
    
    def build_buy_handler(self):
        """Build a buy handler with current configuration."""
        return self.factory.create_buy_handler(self.mock_services)
    
    def build_product_handler(self):
        """Build a product handler with current configuration."""
        return self.factory.create_product_handler(self.mock_services)
    
    def build_user_handler(self):
        """Build a user handler with current configuration."""
        return self.factory.create_user_handler(self.mock_services)


def create_handler_scenario(scenario_name: str):
    """Factory function to create handlers from predefined scenarios."""
    scenarios = {
        'login_success': HandlerScenarios.login.successful_login,
        'login_failed': HandlerScenarios.login.failed_authentication,
        'buy_admin': HandlerScenarios.buy.admin_user_purchase,
        'buy_owner': HandlerScenarios.buy.owner_user_purchase,
        'buy_no_stock': HandlerScenarios.buy.insufficient_stock,
        'product_owner': HandlerScenarios.product.owner_create_product,
        'product_no_perm': HandlerScenarios.product.insufficient_permissions,
        'user_owner': HandlerScenarios.user.owner_manage_users,
    }
    
    if scenario_name not in scenarios:
        raise ValueError(f"Unknown scenario: {scenario_name}")
    
    return scenarios[scenario_name]()


# Convenience function for tests
def mock_handler(handler_type: str, scenario: str = None):
    """Quick handler creation for tests."""
    builder = MockHandlerBuilder()
    
    if scenario:
        mock_services = create_handler_scenario(scenario)
        builder.mock_services = mock_services
    
    return getattr(builder, f'build_{handler_type}_handler')()