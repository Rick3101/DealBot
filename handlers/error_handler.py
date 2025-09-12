import logging
from typing import Dict, Any, Optional, Callable
from telegram import Update
from telegram.ext import ContextTypes
from services.base_service import ServiceError, ValidationError, NotFoundError, DuplicateError
from utils.message_cleaner import send_and_delete


logger = logging.getLogger(__name__)


class ErrorBoundary:
    def __init__(self, handler_name: str):
        self.handler_name = handler_name
        self.logger = logging.getLogger(f"error_boundary.{handler_name}")
    
    async def wrap_handler(
        self, 
        handler_func: Callable,
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE,
        **kwargs
    ) -> Any:
        try:
            return await handler_func(update, context, **kwargs)
        except Exception as e:
            return await self.handle_error(e, update, context)
    
    async def handle_error(
        self, 
        error: Exception, 
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[int]:
        self.logger.error(f"Error in {self.handler_name}: {error}", exc_info=True)
        
        error_response = self.create_error_response(error)
        await send_and_delete(error_response.message, update, context, delay=error_response.delay)
        
        return error_response.next_state
    
    def create_error_response(self, error: Exception) -> 'ErrorResponse':
        if isinstance(error, ValidationError):
            return ErrorResponse(
                message=f"❌ {str(error)}\n\nTente novamente:",
                next_state=None,  # Stay in current state
                delay=5,
                error_type="validation"
            )
        elif isinstance(error, NotFoundError):
            return ErrorResponse(
                message="❌ Item não encontrado.",
                next_state=-1,  # End conversation
                delay=5,
                error_type="not_found"
            )
        elif isinstance(error, DuplicateError):
            return ErrorResponse(
                message=f"❌ {str(error)}\n\nTente novamente:",
                next_state=None,  # Stay in current state
                delay=5,
                error_type="duplicate"
            )
        elif isinstance(error, ServiceError):
            return ErrorResponse(
                message="❌ Erro interno do sistema. Tente novamente em alguns momentos.",
                next_state=-1,  # End conversation
                delay=10,
                error_type="service"
            )
        elif isinstance(error, PermissionError):
            return ErrorResponse(
                message="❌ Você não tem permissão para executar esta ação.",
                next_state=-1,  # End conversation
                delay=5,
                error_type="permission"
            )
        else:
            return ErrorResponse(
                message="❌ Erro inesperado. A operação foi cancelada.",
                next_state=-1,  # End conversation
                delay=10,
                error_type="unexpected"
            )


class ErrorResponse:
    def __init__(
        self, 
        message: str, 
        next_state: Optional[int], 
        delay: int = 10,
        error_type: str = "unknown"
    ):
        self.message = message
        self.next_state = next_state
        self.delay = delay
        self.error_type = error_type


class HandlerErrorManager:
    _instances: Dict[str, ErrorBoundary] = {}
    
    @classmethod
    def get_error_boundary(cls, handler_name: str) -> ErrorBoundary:
        if handler_name not in cls._instances:
            cls._instances[handler_name] = ErrorBoundary(handler_name)
        return cls._instances[handler_name]
    
    @classmethod
    def wrap_handler(cls, handler_name_or_func):
        # Support both @with_error_boundary("handler_name") and @with_error_boundary
        if isinstance(handler_name_or_func, str):
            # Called with handler name: @with_error_boundary("handler_name")
            def decorator(handler_func):
                async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs):
                    error_boundary = cls.get_error_boundary(handler_name_or_func)
                    return await error_boundary.wrap_handler(lambda u, c, **kw: handler_func(self, u, c, **kw), update, context, **kwargs)
                return wrapper
            return decorator
        else:
            # Called without arguments: @with_error_boundary
            handler_func = handler_name_or_func
            handler_name = handler_func.__name__
            async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs):
                error_boundary = cls.get_error_boundary(handler_name)
                return await error_boundary.wrap_handler(lambda u, c, **kw: handler_func(self, u, c, **kw), update, context, **kwargs)
            return wrapper


# Convenience decorators for different handler types
def with_error_boundary(handler_name_or_func=None):
    if handler_name_or_func is None:
        # Called without arguments: @with_error_boundary
        def decorator(handler_func):
            return HandlerErrorManager.wrap_handler(handler_func)
        return decorator
    elif isinstance(handler_name_or_func, str):
        # Called with handler name: @with_error_boundary("handler_name")
        return HandlerErrorManager.wrap_handler(handler_name_or_func)
    else:
        # Called directly on function: @with_error_boundary
        return HandlerErrorManager.wrap_handler(handler_name_or_func)


def with_error_boundary_standalone(handler_name: str):
    """Error boundary decorator for standalone functions (not methods)."""
    def decorator(handler_func):
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs):
            error_boundary = HandlerErrorManager.get_error_boundary(handler_name)
            return await error_boundary.wrap_handler(lambda u, c, **kw: handler_func(u, c, **kw), update, context, **kwargs)
        return wrapper
    return decorator


def with_validation_error_boundary(handler_name: str):
    def decorator(handler_func):
        async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs):
            try:
                return await handler_func(self, update, context, **kwargs)
            except ValidationError as e:
                await send_and_delete(f"❌ {str(e)}\n\nTente novamente:", update, context, delay=5)
                return None  # Stay in current state
            except Exception as e:
                error_boundary = HandlerErrorManager.get_error_boundary(handler_name)
                return await error_boundary.handle_error(e, update, context)
        return wrapper
    return decorator


def with_service_error_boundary(handler_name: str):
    def decorator(handler_func):
        async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs):
            try:
                return await handler_func(self, update, context, **kwargs)
            except ServiceError as e:
                await send_and_delete("❌ Erro interno. Tente novamente.", update, context, delay=5) 
                return -1  # End conversation
            except Exception as e:
                error_boundary = HandlerErrorManager.get_error_boundary(handler_name)
                return await error_boundary.handle_error(e, update, context)
        return wrapper
    return decorator