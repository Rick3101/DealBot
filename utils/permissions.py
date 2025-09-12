from telegram import Update
from telegram.ext import ContextTypes
from core.modern_service_container import get_user_service
from models.user import UserLevel
from services.base_service import ServiceError
from utils.message_cleaner import send_and_delete
from functools import wraps


def require_permission(required_level_str: str):
    """
    Decorator to protect commands based on permission level.
    Levels: 'user', 'admin', 'owner'
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Handle both function calls and method calls
            if len(args) >= 3 and hasattr(args[1], 'effective_chat'):
                # Instance method call: (self, update, context, ...)
                self, update, context = args[0], args[1], args[2]
                remaining_args = args[3:]
            elif len(args) >= 2 and hasattr(args[0], 'effective_chat'):
                # Function call: (update, context, ...)
                update, context = args[0], args[1]
                remaining_args = args[2:]
            else:
                raise ValueError("Invalid arguments for permission decorator")
            
            chat_id = update.effective_chat.id
            
            try:
                user_service = get_user_service(context)
                user_level = user_service.get_user_permission_level(chat_id)
                required_level = UserLevel.from_string(required_level_str)

                if user_level is None:
                    await send_and_delete(
                        "❌ Você não está logado. Use /login para acessar.",
                        update,
                        context
                    )
                    return

                if not user_level.can_access(required_level):
                    await send_and_delete(
                        f"⛔ Permissão insuficiente. Este comando exige nível '{required_level_str}'.",
                        update,
                        context
                    )
                    return

                # Call the function with the appropriate arguments
                if 'self' in locals():
                    return await func(self, update, context, *remaining_args, **kwargs)
                else:
                    return await func(update, context, *remaining_args, **kwargs)
                
            except ServiceError:
                await send_and_delete(
                    "❌ Erro interno. Tente novamente.",
                    update,
                    context
                )
                return

        return wrapper
    return decorator
