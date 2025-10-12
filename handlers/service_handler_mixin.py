"""
Service Handler Mixin - Eliminates repetitive service access patterns across handlers.
Provides standardized service injection and error handling for all handlers.
"""

from typing import Any, Dict, Optional, Type, TypeVar
from abc import ABC
from telegram.ext import ContextTypes
from core.modern_service_container import (
    get_user_service, get_product_service, get_sales_service,
    get_expedition_service, get_brambler_service, get_cash_balance_service,
    get_smartcontract_service, get_broadcast_service, get_export_service,
    get_websocket_service, get_context
)
from services.base_service import BaseService
import logging

T = TypeVar('T', bound=BaseService)


class ServiceHandlerMixin(ABC):
    """
    Mixin providing standardized service access patterns for handlers.
    Eliminates repetitive service getter calls and provides caching.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._service_cache: Dict[str, Any] = {}
        self.logger = logging.getLogger(self.__class__.__name__)

    def _get_service(self, service_name: str, context: ContextTypes.DEFAULT_TYPE,
                    service_getter: callable) -> Any:
        """
        Generic service getter with caching.

        Args:
            service_name: Name of the service for caching
            context: Telegram context
            service_getter: Function to get the service

        Returns:
            Service instance
        """
        cache_key = f"{service_name}_{id(context)}"

        if cache_key not in self._service_cache:
            try:
                self._service_cache[cache_key] = service_getter(context)
            except Exception as e:
                self.logger.error(f"Failed to get {service_name}: {e}")
                raise

        return self._service_cache[cache_key]

    # Standardized service getters
    def get_user_service(self, context: ContextTypes.DEFAULT_TYPE):
        """Get UserService instance."""
        return self._get_service("user", context, get_user_service)

    def get_product_service(self, context: ContextTypes.DEFAULT_TYPE):
        """Get ProductService instance."""
        return self._get_service("product", context, get_product_service)

    def get_sales_service(self, context: ContextTypes.DEFAULT_TYPE):
        """Get SalesService instance."""
        return self._get_service("sales", context, get_sales_service)

    def get_expedition_service(self, context: ContextTypes.DEFAULT_TYPE):
        """Get ExpeditionService instance."""
        return self._get_service("expedition", context, get_expedition_service)

    def get_brambler_service(self, context: ContextTypes.DEFAULT_TYPE):
        """Get BramblerService instance."""
        return self._get_service("brambler", context, get_brambler_service)

    def get_cash_balance_service(self, context: ContextTypes.DEFAULT_TYPE):
        """Get CashBalanceService instance."""
        return self._get_service("cash_balance", context, get_cash_balance_service)

    def get_smartcontract_service(self, context: ContextTypes.DEFAULT_TYPE):
        """Get SmartContractService instance."""
        return self._get_service("smartcontract", context, get_smartcontract_service)

    def get_broadcast_service(self, context: ContextTypes.DEFAULT_TYPE):
        """Get BroadcastService instance."""
        return self._get_service("broadcast", context, get_broadcast_service)

    def get_export_service(self, context: ContextTypes.DEFAULT_TYPE):
        """Get ExportService instance."""
        return self._get_service("export", context, get_export_service)

    def get_websocket_service(self, context: ContextTypes.DEFAULT_TYPE):
        """Get WebSocketService instance."""
        return self._get_service("websocket", context, get_websocket_service)

    def clear_service_cache(self):
        """Clear the service cache (useful for testing or context changes)."""
        self._service_cache.clear()

    def get_all_services(self, context: ContextTypes.DEFAULT_TYPE) -> Dict[str, Any]:
        """
        Get all services at once for handlers that need multiple services.

        Returns:
            Dictionary mapping service names to service instances
        """
        return {
            'user': self.get_user_service(context),
            'product': self.get_product_service(context),
            'sales': self.get_sales_service(context),
            'expedition': self.get_expedition_service(context),
            'brambler': self.get_brambler_service(context),
            'cash_balance': self.get_cash_balance_service(context),
            'smartcontract': self.get_smartcontract_service(context),
            'broadcast': self.get_broadcast_service(context),
            'export': self.get_export_service(context),
            'websocket': self.get_websocket_service(context)
        }


class StandardErrorHandlerMixin(ABC):
    """
    Mixin providing standardized error handling patterns for handlers.
    Eliminates repetitive try-catch blocks and error response patterns.
    """

    def handle_service_error(self, error: Exception, operation: str = "operation") -> str:
        """
        Standardized service error handling.

        Args:
            error: The exception that occurred
            operation: Description of the operation that failed

        Returns:
            User-friendly error message
        """
        from services.base_service import ValidationError, ServiceError, NotFoundError, DuplicateError

        if isinstance(error, ValidationError):
            return f"❌ Validation error in {operation}: {str(error)}"
        elif isinstance(error, NotFoundError):
            return f"❌ Not found: {str(error)}"
        elif isinstance(error, DuplicateError):
            return f"❌ Duplicate entry: {str(error)}"
        elif isinstance(error, ServiceError):
            self.logger.error(f"Service error in {operation}: {error}")
            return f"❌ System error during {operation}. Please try again."
        else:
            self.logger.error(f"Unexpected error in {operation}: {error}")
            return f"❌ Unexpected error during {operation}. Please contact support."

    async def safe_service_call(self, service_call: callable, operation: str = "operation",
                              success_message: Optional[str] = None) -> tuple[bool, str]:
        """
        Safely execute a service call with standardized error handling.

        Args:
            service_call: Function to execute
            operation: Description of the operation
            success_message: Message to return on success

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            result = await service_call() if asyncio.iscoroutinefunction(service_call) else service_call()
            message = success_message or f"✅ {operation.capitalize()} completed successfully"
            return True, message
        except Exception as e:
            error_message = self.handle_service_error(e, operation)
            return False, error_message


class ConversationStateManager:
    """
    Utility class for managing conversation states consistently across handlers.
    Eliminates repetitive state management patterns.
    """

    @staticmethod
    def clear_conversation_data(context: ContextTypes.DEFAULT_TYPE,
                              keys: Optional[list] = None):
        """Clear conversation data keys."""
        if keys:
            for key in keys:
                context.user_data.pop(key, None)
        else:
            context.user_data.clear()

    @staticmethod
    def get_conversation_data(context: ContextTypes.DEFAULT_TYPE,
                            key: str, default: Any = None) -> Any:
        """Get conversation data with default."""
        return context.user_data.get(key, default)

    @staticmethod
    def set_conversation_data(context: ContextTypes.DEFAULT_TYPE,
                            key: str, value: Any):
        """Set conversation data."""
        context.user_data[key] = value

    @staticmethod
    def has_conversation_data(context: ContextTypes.DEFAULT_TYPE, key: str) -> bool:
        """Check if conversation data exists."""
        return key in context.user_data


# Combined mixin for maximum convenience
class StandardHandlerMixin(ServiceHandlerMixin, StandardErrorHandlerMixin):
    """
    Combined mixin providing both service access and error handling.
    Use this for most handlers to get all standardized patterns.
    """
    pass