from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
import logging

logger = logging.getLogger(__name__)

def lock_conversation(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        try:
            if context.chat_data.get("busy"):
                try:
                    await update.effective_message.reply_text("⏳ Ainda estou processando o comando anterior. Aguarde.")
                except Exception as e:
                    logger.warning(f"Falha ao enviar mensagem de bloqueio: {e}")
                return ConversationHandler.END

            context.chat_data["busy"] = True

            try:
                return await func(update, context, *args, **kwargs)
            finally:
                context.chat_data["busy"] = False

        except Exception as e:
            logger.error(f"[lock_conversation] Erro inesperado em '{func.__name__}': {e}", exc_info=True)
            try:
                await update.effective_message.reply_text("⚠️ Erro ao processar este comando. Tente novamente.")
            except:
                pass
            return ConversationHandler.END

    return wrapper
