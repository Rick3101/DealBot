"""
Modern Service Container with proper dependency injection.
Replaces the old service_container.py with better architecture.
"""

import logging
from typing import Dict, Any, Optional
from core.di_container import DIContainer
from core.interfaces import IUserService, IProductService, ISalesService, IDatabaseManager, ISmartContractService, IBroadcastService, ICashBalanceService, IExpeditionService, IBramblerService, IWebSocketService, IExportService
from services.user_service import UserService
from services.product_service import ProductService
from services.sales_service import SalesService
from services.smartcontract_service import SmartContractService
from services.broadcast_service import BroadcastService
from services.cash_balance_service import CashBalanceService
from services.expedition_service import ExpeditionService
from services.brambler_service import BramblerService
from services.websocket_service import WebSocketService
from services.export_service import ExportService
from database.connection import DatabaseManager


class ServiceRegistry:
    """
    Central registry for service configuration and initialization.
    Manages the dependency injection container and service registration.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        self._container: Optional[DIContainer] = None
        self._initialized = False
        
        self.logger.info("Service Registry initialized")
    
    def initialize(self) -> DIContainer:
        """
        Initialize the DI container and register all services.
        
        Returns:
            Configured DIContainer instance
        """
        if self._initialized:
            return self._container
        
        self.logger.info("Initializing service container...")
        
        # Create DI container
        self._container = DIContainer(self.config)
        
        # Register services with their interfaces
        self._register_core_services()
        self._register_business_services()
        self._register_expedition_services()
        
        self._initialized = True
        self.logger.info("Service container initialized successfully")
        
        return self._container
    
    def _register_core_services(self):
        """Register core infrastructure services."""
        self.logger.debug("Registering core services...")
        
        # Database Manager (singleton - one connection pool)
        self._container.register_singleton(
            IDatabaseManager,
            factory=self._create_database_manager
        )
    
    def _register_business_services(self):
        """Register business logic services."""
        self.logger.debug("Registering business services...")
        
        # User Service (singleton - stateless service)
        self._container.register_singleton(
            IUserService,
            implementation_type=UserService
        )
        
        # Product Service (singleton - stateless service)
        self._container.register_singleton(
            IProductService,
            implementation_type=ProductService
        )
        
        # Sales Service (singleton - stateless service)
        self._container.register_singleton(
            ISalesService,
            implementation_type=SalesService
        )
        
        # SmartContract Service (singleton - stateless service)
        self._container.register_singleton(
            ISmartContractService,
            implementation_type=SmartContractService
        )
        
        # Broadcast Service (singleton - stateless service)
        self._container.register_singleton(
            IBroadcastService,
            implementation_type=BroadcastService
        )

        # Cash Balance Service (singleton - stateless service)
        self._container.register_singleton(
            ICashBalanceService,
            implementation_type=CashBalanceService
        )
        
        self.logger.debug("All business services registered")

    def _register_expedition_services(self):
        """Register expedition-related services."""
        self.logger.debug("Registering expedition services...")

        # Brambler Service (singleton - stateless service)
        self._container.register_singleton(
            IBramblerService,
            implementation_type=BramblerService
        )

        # Expedition Service (singleton - stateless service with product service dependency)
        self._container.register_singleton(
            IExpeditionService,
            factory=self._create_expedition_service
        )

        # WebSocket Service (singleton - real-time updates service)
        self._container.register_singleton(
            IWebSocketService,
            implementation_type=WebSocketService
        )

        # Export Service (singleton - stateless export service)
        self._container.register_singleton(
            IExportService,
            implementation_type=ExportService
        )

        self.logger.debug("All expedition services registered")

    def _create_expedition_service(self) -> ExpeditionService:
        """Factory method for creating expedition service with dependencies."""
        product_service = self._container.get_service(IProductService)
        return ExpeditionService(product_service=product_service)

    def _create_database_manager(self) -> DatabaseManager:
        """Factory method for creating database manager."""
        from database import get_db_manager, initialize_database
        import os

        try:
            # Ensure database is initialized before getting manager
            # This is a safety check in case services are accessed before app initialization
            return get_db_manager()
        except RuntimeError as e:
            if "not initialized" in str(e):
                self.logger.warning("Database manager not initialized, attempting to initialize now...")
                try:
                    # Load environment variables if not already loaded
                    try:
                        from dotenv import load_dotenv
                        load_dotenv()
                    except ImportError:
                        pass

                    # Initialize database with environment URL
                    database_url = os.environ.get('DATABASE_URL')
                    if not database_url:
                        raise RuntimeError("DATABASE_URL environment variable not set. Please check your .env file.")

                    initialize_database(database_url)
                    return get_db_manager()
                except Exception as init_error:
                    self.logger.error(f"Failed to initialize database: {init_error}")
                    raise RuntimeError(f"Database initialization failed: {init_error}")
            else:
                raise
    
    def get_container(self) -> DIContainer:
        """Get the initialized container."""
        if not self._initialized:
            return self.initialize()
        return self._container
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on the service registry and all services."""
        if not self._initialized:
            return {
                "registry": {"healthy": False, "message": "Not initialized"},
                "container": {"healthy": False, "message": "Container not available"}
            }
        
        registry_health = {
            "registry": {
                "healthy": True,
                "initialized": self._initialized,
                "config_loaded": bool(self.config)
            }
        }
        
        container_health = self._container.health_check()
        
        return {**registry_health, **container_health}
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get detailed information about registered services."""
        if not self._initialized:
            return {"error": "Service registry not initialized"}
        
        return self._container.get_service_info()
    
    def dispose(self):
        """Dispose the service registry and cleanup resources."""
        if self._container:
            self._container.dispose()
        
        self._initialized = False
        self._container = None
        
        self.logger.info("Service Registry disposed")


# Global service registry instance
_service_registry: Optional[ServiceRegistry] = None


def initialize_services(config: Optional[Dict[str, Any]] = None) -> ServiceRegistry:
    """
    Initialize global service registry.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        ServiceRegistry instance
    """
    global _service_registry
    
    if _service_registry is None:
        _service_registry = ServiceRegistry(config)
        _service_registry.initialize()
    
    return _service_registry


def get_service_registry() -> ServiceRegistry:
    """
    Get the global service registry.
    
    Returns:
        ServiceRegistry instance
        
    Raises:
        RuntimeError: If services haven't been initialized
    """
    global _service_registry
    
    if _service_registry is None:
        raise RuntimeError("Services not initialized. Call initialize_services() first.")
    
    return _service_registry


def get_container() -> DIContainer:
    """
    Get the global DI container.
    
    Returns:
        DIContainer instance
    """
    return get_service_registry().get_container()


# Enhanced service accessor functions with better error handling
def get_user_service(context=None) -> IUserService:
    """
    Get user service instance.
    
    Args:
        context: Optional telegram context (maintained for backward compatibility)
        
    Returns:
        IUserService implementation
    """
    try:
        container = get_container()
        return container.get_service(IUserService)
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to get user service: {e}")
        raise RuntimeError(f"User service unavailable: {str(e)}")


def get_product_service(context=None) -> IProductService:
    """
    Get product service instance.
    
    Args:
        context: Optional telegram context (maintained for backward compatibility)
        
    Returns:
        IProductService implementation
    """
    try:
        container = get_container()
        return container.get_service(IProductService)
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to get product service: {e}")
        raise RuntimeError(f"Product service unavailable: {str(e)}")


def get_sales_service(context=None) -> ISalesService:
    """
    Get sales service instance.
    
    Args:
        context: Optional telegram context (maintained for backward compatibility)
        
    Returns:
        ISalesService implementation
    """
    try:
        container = get_container()
        return container.get_service(ISalesService)
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to get sales service: {e}")
        raise RuntimeError(f"Sales service unavailable: {str(e)}")


def get_smartcontract_service(context=None) -> ISmartContractService:
    """
    Get smartcontract service instance.
    
    Args:
        context: Optional telegram context (maintained for backward compatibility)
        
    Returns:
        ISmartContractService implementation
    """
    try:
        container = get_container()
        return container.get_service(ISmartContractService)
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to get smartcontract service: {e}")
        raise RuntimeError(f"SmartContract service unavailable: {str(e)}")


def get_broadcast_service(context=None) -> IBroadcastService:
    """
    Get broadcast service instance.

    Args:
        context: Optional telegram context (maintained for backward compatibility)

    Returns:
        IBroadcastService implementation
    """
    try:
        container = get_container()
        return container.get_service(IBroadcastService)
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to get broadcast service: {e}")
        raise RuntimeError(f"Broadcast service unavailable: {str(e)}")


def get_cash_balance_service(context=None) -> ICashBalanceService:
    """
    Get cash balance service instance.

    Args:
        context: Optional telegram context (maintained for backward compatibility)

    Returns:
        ICashBalanceService implementation
    """
    try:
        container = get_container()
        return container.get_service(ICashBalanceService)
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to get cash balance service: {e}")
        raise RuntimeError(f"Cash balance service unavailable: {str(e)}")


def get_expedition_service(context=None) -> IExpeditionService:
    """
    Get expedition service instance.

    Args:
        context: Optional telegram context (maintained for backward compatibility)

    Returns:
        IExpeditionService implementation
    """
    try:
        container = get_container()
        return container.get_service(IExpeditionService)
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to get expedition service: {e}")
        raise RuntimeError(f"Expedition service unavailable: {str(e)}")


def get_brambler_service(context=None) -> IBramblerService:
    """
    Get brambler service instance.

    Args:
        context: Optional telegram context (maintained for backward compatibility)

    Returns:
        IBramblerService implementation
    """
    try:
        container = get_container()
        return container.get_service(IBramblerService)
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to get brambler service: {e}")
        raise RuntimeError(f"Brambler service unavailable: {str(e)}")


def get_websocket_service(context=None) -> IWebSocketService:
    """
    Get WebSocket service instance.

    Args:
        context: Optional telegram context (maintained for backward compatibility)

    Returns:
        IWebSocketService implementation
    """
    try:
        container = get_container()
        return container.get_service(IWebSocketService)
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to get websocket service: {e}")
        raise RuntimeError(f"WebSocket service unavailable: {str(e)}")


def get_export_service(context=None) -> IExportService:
    """
    Get export service instance.

    Args:
        context: Optional telegram context (maintained for backward compatibility)

    Returns:
        IExportService implementation
    """
    try:
        container = get_container()
        return container.get_service(IExportService)
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to get export service: {e}")
        raise RuntimeError(f"Export service unavailable: {str(e)}")


def get_database_manager() -> IDatabaseManager:
    """
    Get database manager instance.

    Returns:
        IDatabaseManager implementation
    """
    try:
        container = get_container()
        return container.get_service(IDatabaseManager)
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to get database manager: {e}")
        raise RuntimeError(f"Database manager unavailable: {str(e)}")


# Service context management for scoped services
class ServiceScope:
    """Context manager for service scopes."""
    
    def __init__(self, scope_id: str):
        self.scope_id = scope_id
        self.container = get_container()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.container.clear_scope(self.scope_id)
    
    def get_service(self, service_type):
        """Get scoped service."""
        return self.container.get_service(service_type, self.scope_id)


def create_service_scope(scope_id: str) -> ServiceScope:
    """
    Create a new service scope for scoped services.
    
    Args:
        scope_id: Unique identifier for the scope
        
    Returns:
        ServiceScope context manager
    """
    return ServiceScope(scope_id)


# Health check utilities
def health_check_services() -> Dict[str, Any]:
    """
    Perform comprehensive health check on all services.
    
    Returns:
        Health status dictionary
    """
    try:
        registry = get_service_registry()
        return registry.health_check()
    except Exception as e:
        return {
            "registry": {"healthy": False, "message": f"Registry error: {str(e)}"},
            "container": {"healthy": False, "message": "Container unavailable"}
        }


def get_service_diagnostics() -> Dict[str, Any]:
    """
    Get detailed service diagnostics information.
    
    Returns:
        Diagnostics dictionary
    """
    try:
        registry = get_service_registry()
        health = registry.health_check()
        info = registry.get_service_info()
        
        return {
            "health": health,
            "service_info": info,
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "error": str(e),
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }


def get_context():
    """
    Get application context.
    For backward compatibility, returns None for now.
    """
    return None