"""
Dependency Injection Container.
A robust service container with proper lifecycle management, configuration, and registration.
"""

import logging
from typing import Any, Dict, Type, TypeVar, Generic, Optional, Callable
from enum import Enum
import threading
from functools import wraps

T = TypeVar('T')


class ServiceLifetime(Enum):
    """Service lifetime management options."""
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


class ServiceDescriptor(Generic[T]):
    """Describes how a service should be created and managed."""
    
    def __init__(
        self,
        interface_type: Type[T],
        implementation_type: Type[T] = None,
        factory: Callable[[], T] = None,
        instance: T = None,
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
        dependencies: Optional[Dict[str, Type]] = None
    ):
        self.interface_type = interface_type
        self.implementation_type = implementation_type
        self.factory = factory
        self.instance = instance
        self.lifetime = lifetime
        self.dependencies = dependencies or {}
        
        # Validation
        if not any([implementation_type, factory, instance]):
            raise ValueError("Must provide either implementation_type, factory, or instance")


class DIContainer:
    """
    Dependency Injection Container.
    Manages service registration, creation, and lifecycle.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger(__name__)
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._singletons: Dict[Type, Any] = {}
        self._scoped_instances: Dict[str, Dict[Type, Any]] = {}
        self._lock = threading.RLock()
        self._config = config or {}
        
        self.logger.info("Dependency Injection Container initialized")
    
    def register_singleton(
        self, 
        interface_type: Type[T], 
        implementation_type: Type[T] = None,
        factory: Callable[[], T] = None,
        instance: T = None
    ) -> 'DIContainer':
        """Register a service as singleton (one instance for entire application)."""
        return self._register_service(
            interface_type, implementation_type, factory, instance, ServiceLifetime.SINGLETON
        )
    
    def register_transient(
        self, 
        interface_type: Type[T], 
        implementation_type: Type[T] = None,
        factory: Callable[[], T] = None
    ) -> 'DIContainer':
        """Register a service as transient (new instance every time)."""
        return self._register_service(
            interface_type, implementation_type, factory, None, ServiceLifetime.TRANSIENT
        )
    
    def register_scoped(
        self, 
        interface_type: Type[T], 
        implementation_type: Type[T] = None,
        factory: Callable[[], T] = None
    ) -> 'DIContainer':
        """Register a service as scoped (one instance per scope/context)."""
        return self._register_service(
            interface_type, implementation_type, factory, None, ServiceLifetime.SCOPED
        )
    
    def _register_service(
        self,
        interface_type: Type[T],
        implementation_type: Type[T] = None,
        factory: Callable[[], T] = None,
        instance: T = None,
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON
    ) -> 'DIContainer':
        """Internal method to register services."""
        with self._lock:
            descriptor = ServiceDescriptor(
                interface_type=interface_type,
                implementation_type=implementation_type,
                factory=factory,
                instance=instance,
                lifetime=lifetime
            )
            
            self._services[interface_type] = descriptor
            
            # If instance provided, store it as singleton
            if instance is not None:
                self._singletons[interface_type] = instance
            
            self.logger.debug(f"Registered {interface_type.__name__} as {lifetime.value}")
            
        return self
    
    def get_service(self, interface_type: Type[T], scope_id: Optional[str] = None) -> T:
        """
        Get service instance.
        
        Args:
            interface_type: The interface/service type to get
            scope_id: Optional scope identifier for scoped services
            
        Returns:
            Service instance
            
        Raises:
            ValueError: If service not registered
        """
        if interface_type not in self._services:
            raise ValueError(f"Service {interface_type.__name__} is not registered")
        
        descriptor = self._services[interface_type]
        
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            return self._get_singleton(interface_type, descriptor)
        elif descriptor.lifetime == ServiceLifetime.TRANSIENT:
            return self._create_instance(descriptor)
        elif descriptor.lifetime == ServiceLifetime.SCOPED:
            return self._get_scoped(interface_type, descriptor, scope_id)
        else:
            raise ValueError(f"Unknown service lifetime: {descriptor.lifetime}")
    
    def _get_singleton(self, interface_type: Type[T], descriptor: ServiceDescriptor[T]) -> T:
        """Get singleton instance."""
        with self._lock:
            if interface_type not in self._singletons:
                self._singletons[interface_type] = self._create_instance(descriptor)
            return self._singletons[interface_type]
    
    def _get_scoped(self, interface_type: Type[T], descriptor: ServiceDescriptor[T], scope_id: str) -> T:
        """Get scoped instance."""
        if scope_id is None:
            scope_id = "default"
        
        with self._lock:
            if scope_id not in self._scoped_instances:
                self._scoped_instances[scope_id] = {}
            
            scoped_services = self._scoped_instances[scope_id]
            
            if interface_type not in scoped_services:
                scoped_services[interface_type] = self._create_instance(descriptor)
            
            return scoped_services[interface_type]
    
    def _create_instance(self, descriptor: ServiceDescriptor[T]) -> T:
        """Create new service instance."""
        try:
            if descriptor.instance is not None:
                return descriptor.instance
            elif descriptor.factory is not None:
                return descriptor.factory()
            elif descriptor.implementation_type is not None:
                # Simple constructor injection - look for dependencies
                return self._create_with_dependencies(descriptor.implementation_type)
            else:
                raise ValueError("No way to create instance")
                
        except Exception as e:
            self.logger.error(f"Failed to create instance of {descriptor.interface_type.__name__}: {e}")
            raise
    
    def _create_with_dependencies(self, implementation_type: Type[T]) -> T:
        """Create instance with constructor dependency injection."""
        try:
            # For now, simple creation without constructor inspection
            # This can be enhanced to inspect __init__ parameters and inject dependencies
            return implementation_type()
        except Exception as e:
            self.logger.error(f"Failed to create {implementation_type.__name__}: {e}")
            raise
    
    def clear_scope(self, scope_id: str):
        """Clear all scoped services for a specific scope."""
        with self._lock:
            if scope_id in self._scoped_instances:
                # Cleanup scoped instances
                scoped_services = self._scoped_instances[scope_id]
                for service in scoped_services.values():
                    if hasattr(service, 'dispose'):
                        try:
                            service.dispose()
                        except Exception as e:
                            self.logger.warning(f"Error disposing service: {e}")
                
                del self._scoped_instances[scope_id]
                self.logger.debug(f"Cleared scope: {scope_id}")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on all registered services."""
        health_status = {
            "container": {"healthy": True, "registered_services": len(self._services)},
            "services": {}
        }
        
        for interface_type, descriptor in self._services.items():
            service_name = interface_type.__name__
            try:
                # Try to get service instance
                service = self.get_service(interface_type)
                
                # Check if service has health_check method
                if hasattr(service, 'health_check'):
                    service_health = service.health_check()
                    health_status["services"][service_name] = service_health
                else:
                    health_status["services"][service_name] = {
                        "healthy": True, 
                        "message": "Service accessible"
                    }
                    
            except Exception as e:
                health_status["services"][service_name] = {
                    "healthy": False, 
                    "message": str(e)
                }
                health_status["container"]["healthy"] = False
        
        return health_status
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get information about registered services."""
        return {
            "registered_services": {
                service_type.__name__: {
                    "interface": service_type.__name__,
                    "implementation": descriptor.implementation_type.__name__ if descriptor.implementation_type else "Factory/Instance",
                    "lifetime": descriptor.lifetime.value,
                    "is_singleton_created": service_type in self._singletons
                }
                for service_type, descriptor in self._services.items()
            },
            "active_singletons": len(self._singletons),
            "active_scopes": len(self._scoped_instances)
        }
    
    def dispose(self):
        """Dispose container and cleanup resources."""
        with self._lock:
            # Dispose all singletons
            for service in self._singletons.values():
                if hasattr(service, 'dispose'):
                    try:
                        service.dispose()
                    except Exception as e:
                        self.logger.warning(f"Error disposing singleton service: {e}")
            
            # Clear all scoped services
            for scope_id in list(self._scoped_instances.keys()):
                self.clear_scope(scope_id)
            
            self._singletons.clear()
            self._services.clear()
            
            self.logger.info("Dependency Injection Container disposed")


# Decorators for easier service injection
def inject(service_type: Type[T]):
    """Decorator to inject services into methods."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # This would require a global container reference
            # Implementation depends on how container is made available
            return func(*args, **kwargs)
        return wrapper
    return decorator


def service_method(container_getter: Callable[[], DIContainer]):
    """Decorator to make methods service-aware."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            container = container_getter()
            kwargs['container'] = container
            return func(*args, **kwargs)
        return wrapper
    return decorator