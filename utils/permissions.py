from telegram import Update
from telegram.ext import ContextTypes
import services.produto_service as produto_service
from utils.message_cleaner import send_and_delete
from functools import wraps


def require_permission(required_level):
    """
    Decorador para proteger comandos baseado no nível de permissão.
    Níveis: 'user', 'admin', 'owner'
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            chat_id = update.effective_chat.id
            user_level = produto_service.obter_nivel(chat_id)

            levels = {"user": 1, "admin": 2, "owner": 3}

            if user_level is None:
                await send_and_delete(
                    "❌ Você não está logado. Use /login para acessar.",
                    update,
                    context
                )
                return

            if levels.get(user_level, 0) < levels.get(required_level, 0):
                await send_and_delete(
                    f"⛔ Permissão insuficiente. Este comando exige nível '{required_level}'.",
                    update,
                    context
                )
                return

            return await func(update, context, *args, **kwargs)

        return wrapper
    return decorator
