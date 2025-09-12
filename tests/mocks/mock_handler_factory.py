"""
Mock handler factory for creating real handler instances with mocked dependencies.
Provides clean, reusable handler mocks for all tests.
"""

from unittest.mock import patch, Mock
from contextlib import contextmanager
from typing import Dict, Any, Optional

from .mock_services import MockServiceContainer, create_mock_services


class MockHandlerFactory:
    """Factory for creating real handler instances with mocked services."""
    
    def __init__(self):
        self._active_patches = []
    
    @contextmanager
    def create_login_handler(self, mock_services: MockServiceContainer = None):
        """Create a real ModernLoginHandler with mocked services."""
        if mock_services is None:
            mock_services = create_mock_services()
        
        # Import here to avoid circular imports
        from handlers.login_handler import ModernLoginHandler
        
        with patch('handlers.login_handler.HandlerBusinessService') as mock_business:
            mock_business.return_value = mock_services.handler_business_service
            
            handler = ModernLoginHandler()
            yield handler, mock_services
    
    @contextmanager
    def create_buy_handler(self, mock_services: MockServiceContainer = None):
        """Create a real ModernBuyHandler with mocked services."""
        if mock_services is None:
            mock_services = create_mock_services()
        
        from handlers.buy_handler import ModernBuyHandler
        
        patches = [
            patch('handlers.buy_handler.HandlerBusinessService', return_value=mock_services.handler_business_service),
            patch('handlers.buy_handler.get_user_service', return_value=mock_services.user_service),
            patch('handlers.buy_handler.get_product_service', return_value=mock_services.product_service),
        ]
        
        with patches[0], patches[1], patches[2]:
            handler = ModernBuyHandler()
            yield handler, mock_services
    
    @contextmanager
    def create_product_handler(self, mock_services: MockServiceContainer = None):
        """Create a real ModernProductHandler with mocked services."""
        if mock_services is None:
            mock_services = create_mock_services()
        
        from handlers.product_handler import ModernProductHandler
        
        with patch('handlers.product_handler.HandlerBusinessService') as mock_business:
            mock_business.return_value = mock_services.handler_business_service
            
            handler = ModernProductHandler()
            yield handler, mock_services
    
    @contextmanager
    def create_user_handler(self, mock_services: MockServiceContainer = None):
        """Create a real ModernUserHandler with mocked services."""
        if mock_services is None:
            mock_services = create_mock_services()
        
        from handlers.user_handler import ModernUserHandler
        
        with patch('handlers.user_handler.HandlerBusinessService') as mock_business:
            mock_business.return_value = mock_services.handler_business_service
            
            handler = ModernUserHandler()
            yield handler, mock_services
    
    @contextmanager
    def create_start_handler(self, mock_services: MockServiceContainer = None):
        """Create a real ModernStartHandler with mocked services."""
        if mock_services is None:
            mock_services = create_mock_services()
        
        from handlers.start_handler import ModernStartHandler
        
        with patch('handlers.start_handler.get_user_service') as mock_user_service:
            mock_user_service.return_value = mock_services.user_service
            
            handler = ModernStartHandler()
            yield handler, mock_services
    
    @contextmanager
    def create_estoque_handler(self, mock_services: MockServiceContainer = None):
        """Create a real ModernEstoqueHandler with mocked services."""
        if mock_services is None:
            mock_services = create_mock_services()
        
        from handlers.estoque_handler import ModernEstoqueHandler
        
        with patch('handlers.estoque_handler.HandlerBusinessService') as mock_business:
            mock_business.return_value = mock_services.handler_business_service
            
            handler = ModernEstoqueHandler()
            yield handler, mock_services
    
    @contextmanager
    def create_commands_handler(self, mock_services: MockServiceContainer = None):
        """Create a real ModernCommandsHandler with mocked services."""
        if mock_services is None:
            mock_services = create_mock_services()
        
        from handlers.commands_handler import ModernCommandsHandler
        
        with patch('handlers.commands_handler.get_user_service') as mock_user_service:
            mock_user_service.return_value = mock_services.user_service
            
            handler = ModernCommandsHandler()
            yield handler, mock_services
    
    def create_handler(self, handler_type: str, mock_services: MockServiceContainer = None):
        """Create any handler by type name."""
        handler_map = {
            'login': self.create_login_handler,
            'buy': self.create_buy_handler,
            'product': self.create_product_handler,
            'user': self.create_user_handler,
            'start': self.create_start_handler,
            'estoque': self.create_estoque_handler,
            'commands': self.create_commands_handler,
        }
        
        if handler_type not in handler_map:
            raise ValueError(f"Unknown handler type: {handler_type}")
        
        return handler_map[handler_type](mock_services)


class HandlerTestMixin:
    """Mixin class to provide easy handler creation in test classes."""
    
    def __init__(self):
        self.handler_factory = MockHandlerFactory()
    
    def create_login_handler(self, **service_configs):
        """Create login handler with optional service configurations."""
        mock_services = create_mock_services()
        
        # Apply configurations
        if 'user_level' in service_configs:
            mock_services.configure_user(level=service_configs['user_level'])
        if 'auth_success' in service_configs:
            mock_services.configure_authentication(success=service_configs['auth_success'])
        
        return self.handler_factory.create_login_handler(mock_services)
    
    def create_buy_handler(self, **service_configs):
        """Create buy handler with optional service configurations."""
        mock_services = create_mock_services()
        
        # Apply configurations
        if 'user_level' in service_configs:
            mock_services.configure_user(level=service_configs['user_level'])
        if 'products' in service_configs:
            mock_services.configure_products(service_configs['products'])
        if 'purchase_success' in service_configs:
            mock_services.configure_purchase_flow(success=service_configs['purchase_success'])
        
        return self.handler_factory.create_buy_handler(mock_services)
    
    def create_product_handler(self, **service_configs):
        """Create product handler with optional service configurations."""
        mock_services = create_mock_services()
        
        if 'user_level' in service_configs:
            mock_services.configure_user(level=service_configs['user_level'])
        
        return self.handler_factory.create_product_handler(mock_services)


# Global factory instance for convenience
mock_handler_factory = MockHandlerFactory()