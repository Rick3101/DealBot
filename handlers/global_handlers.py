from telegram import Update
from telegram.ext import ContextTypes ,ConversationHandler
from utils.message_cleaner import send_and_delete , delete_protected_message


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message or (update.callback_query.message if update.callback_query else None)

    if msg:
        try:
            await msg.delete()
        except:
            pass

    context.user_data.clear()
    context.chat_data.clear()

    await msg.reply_text("🚫 Operação cancelada.")
    return ConversationHandler.END

async def cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # 🔥 Limpa mensagens protegidas
    context.chat_data["protected_messages"] = set()

    # 🔥 Limpa dados temporários
    context.user_data.clear()
    context.chat_data.clear()

    await query.message.delete()
    await query.message.reply_text("🚫 Operação cancelada.")

    return ConversationHandler.END
