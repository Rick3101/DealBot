from utils.message_cleaner import send_and_delete
import services.produto_service_pg as produto_service
from telegram.ext import ContextTypes
from telegram import Update

async def commands_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    nivel = produto_service.obter_nivel(chat_id) or "user"

    comandos = {
        "user": [
            "/start",
            "/login",
            "/commands"
        ],
        "admin": [
            "/start",
            "/login",
            "/commands",
            "/buy",
            "/estoque",
            "/debitos",
            "/pagar",
            "/lista_produtos",
            "/relatorios"
        ],
        "owner": [
            "/start",
            "/login",
            "/commands",
            "/buy",
            "/estoque",
            "/user",
            "/debitos",
            "/pagar",
            "/lista_produtos",
            "/relatorios",
            "/smartcontract"
        ]
    }

    texto = f"*🛠 Comandos disponíveis para `{nivel}`:*\n\n"
    for cmd in comandos.get(nivel, []):
        texto += f"• `{cmd}`\n"

    await send_and_delete(texto, update, context)
