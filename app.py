import os
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application
from telegram.ext import MessageHandler, filters, Application, CommandHandler , ConversationHandler , CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
# Handlers do seu projeto
from handlers.start_handler import start
from handlers.login_handler import login_handler
from handlers.user_handler import get_user_conversation_handler
from handlers.product_handler import get_product_conversation_handler
from handlers.estoque_handler import get_estoque_conversation_handler
from handlers.buy_handler import (
    get_buy_conversation_handler,
    listar_debitos, selecionar_debito, marcar_pagamento,
    pagar_vendas, confirmar_pagamento, executar_pagamento
)
from handlers.relatorios_handler import (
    get_relatorios_conversation_handler,
    exportar_csv_handler, exportar_csv_detalhes_handler, fechar_handler
)
from handlers.lista_produtos_handler import lista_produtos
from handlers.global_handlers import cancel


# ENV
TOKEN = os.getenv("BOT_TOKEN") or "7593794682:AAEqzdMTtkzGcJLdI_SGFjRSF50q4ntlIjo"
RAILWAY_URL = os.getenv("RAILWAY_URL") or "web-production-32b2.up.railway.app"
WEBHOOK_PATH = f"/{TOKEN}"
WEBHOOK_URL = f"https://{RAILWAY_URL}{WEBHOOK_PATH}"
app_bot = Application.builder().token(TOKEN).build()
app = Flask(__name__)

# === ADICIONA OS HANDLERS COMO FAZIA NO main.py
def configurar_handlers():
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("cancel", cancel))
    app_bot.add_handler(login_handler)
    app_bot.add_handler(get_user_conversation_handler())
    app_bot.add_handler(get_product_conversation_handler())
    app_bot.add_handler(get_estoque_conversation_handler())
    app_bot.add_handler(get_buy_conversation_handler())
    app_bot.add_handler(get_relatorios_conversation_handler())
    app_bot.add_handler(CommandHandler("debitos", listar_debitos))
    app_bot.add_handler(CallbackQueryHandler(selecionar_debito, pattern="^debito:"))
    app_bot.add_handler(CallbackQueryHandler(marcar_pagamento, pattern="^pagar_"))
    app_bot.add_handler(CommandHandler("pagar", pagar_vendas))
    app_bot.add_handler(CallbackQueryHandler(confirmar_pagamento, pattern="^pagar:"))
    app_bot.add_handler(CallbackQueryHandler(executar_pagamento, pattern="^confirmar_pagamento_"))
    app_bot.add_handler(exportar_csv_handler)
    app_bot.add_handler(exportar_csv_detalhes_handler)
    app_bot.add_handler(fechar_handler)
    app_bot.add_handler(CommandHandler("lista_produtos", lista_produtos))

# SETUP FLASK
app = Flask(__name__)

# SETUP BOT: initialize, set webhook, start
async def setup_bot():
    await app_bot.initialize()
    await app_bot.bot.set_webhook(url=WEBHOOK_URL)
    await app_bot.start()

asyncio.run(setup_bot())

# WEBHOOK ENDPOINT
@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), app_bot.bot)
    asyncio.run(app_bot.process_update(update))
    return "OK", 200

# SAÚDE (opcional)
@app.route("/")
def health():
    return "Bot online ✔️", 200

# FLASK START
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
