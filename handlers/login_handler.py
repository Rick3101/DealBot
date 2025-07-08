from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)
from utils.message_cleaner import send_and_delete, delayed_delete
import asyncio
import services.produto_service_pg as produto_service

# 🔸 Estados
LOGIN_USERNAME, LOGIN_PASSWORD = range(2)

# 🔸 Entradas
async def start_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_and_delete("📝 Por favor, envie seu nome de usuário:", update, context)
    return LOGIN_USERNAME

async def received_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["username_login"] = update.message.text

    asyncio.create_task(delayed_delete(update.message, context, delay=10))
    await send_and_delete("🔒 Agora envie sua senha:", update, context)
    return LOGIN_PASSWORD

async def received_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = context.user_data.get("username_login")
    password = update.message.text
    chat_id = update.effective_chat.id

    asyncio.create_task(delayed_delete(update.message, context, delay=10))

    if produto_service.verificar_login(username, password, chat_id):
        await send_and_delete("✅ Login realizado com sucesso!", update, context)
    else:
        await send_and_delete("❌ Usuário ou senha inválidos.", update, context)

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_and_delete("🚫 Login cancelado.", update, context)
    return ConversationHandler.END

login_handler = ConversationHandler(
    entry_points=[CommandHandler("login", start_login)],
    states={
        LOGIN_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_username)],
        LOGIN_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_password)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    allow_reentry=True
)
