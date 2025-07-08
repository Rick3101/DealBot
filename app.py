import os
import asyncio
import logging
import nest_asyncio
import threading
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, ContextTypes
from telegram.request import HTTPXRequest
from queue import Queue

# === CONFIGURAÇÃO ===
TOKEN = os.getenv("BOT_TOKEN") or "7593794682:AAEqzdMTtkzGcJLdI_SGFjRSF50q4ntlIjo"
RAILWAY_URL = os.getenv("RAILWAY_URL") or "https://dealbot.onrender.com"
WEBHOOK_PATH = f"/{TOKEN}"
WEBHOOK_URL = f"{RAILWAY_URL}{WEBHOOK_PATH}"

# === FLASK INIT ===
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
nest_asyncio.apply()

# === UPDATE QUEUE ===
update_queue = Queue()
app_bot = None

# === HANDLERS ===
from handlers.start_handler import start, protect
from handlers.global_handlers import cancel, cancel_callback
from handlers.login_handler import login_handler
from handlers.product_handler import get_product_conversation_handler
from handlers.relatorios_handler import (
    get_relatorios_conversation_handler,
    exportar_csv_handler,
    exportar_csv_detalhes_handler,
    fechar_handler,
)
from handlers.buy_handler import get_buy_conversation_handler, listar_debitos, selecionar_debito, marcar_pagamento, pagar_vendas, confirmar_pagamento, executar_pagamento
from handlers.user_handler import get_user_conversation_handler
from handlers.smartcontract_handler import (
    criar_smart_contract,
    get_smartcontract_conversation_handler,
    confirmar_transacao_prompt,
    confirmar_transacao_exec
)
from handlers.estoque_handler import get_estoque_conversation_handler 
from handlers.lista_produtos_handler import lista_produtos

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    import traceback
    logger.error("❌ Exception caught:", exc_info=context.error)
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = ''.join(tb_list)
    print(f"🔴 Traceback:\n{tb_string}")
    chat_id = update.effective_chat.id if isinstance(update, Update) and update.effective_chat else None
    if chat_id:
        try:
            await context.bot.send_message(chat_id=chat_id, text="⚠️ Ocorreu um erro inesperado.")
        except:
            pass

def configurar_handlers(app_bot):
    app_bot.add_handler(get_user_conversation_handler())
    app_bot.add_handler(login_handler)
    app_bot.add_handler(get_product_conversation_handler())
    app_bot.add_handler(get_estoque_conversation_handler()) 
    app_bot.add_handler(get_relatorios_conversation_handler())
    app_bot.add_handler(exportar_csv_handler)
    app_bot.add_handler(exportar_csv_detalhes_handler)
    app_bot.add_handler(fechar_handler)
    app_bot.add_handler(get_smartcontract_conversation_handler())
    app_bot.add_handler(get_buy_conversation_handler()) 

    from telegram.ext import CommandHandler, CallbackQueryHandler
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("protect", protect))
    app_bot.add_handler(CommandHandler("cancel", cancel))
    app_bot.add_handler(CommandHandler("debitos", listar_debitos))
    app_bot.add_handler(CommandHandler("pagar", pagar_vendas))
    app_bot.add_handler(CallbackQueryHandler(selecionar_debito, pattern="^debito:"))
    app_bot.add_handler(CallbackQueryHandler(marcar_pagamento, pattern="^pagar_(sim|nao)$"))
    app_bot.add_handler(CallbackQueryHandler(confirmar_pagamento, pattern="^pagar:"))
    app_bot.add_handler(CallbackQueryHandler(executar_pagamento, pattern="^confirmar_pagamento_(sim|nao)$"))
    app_bot.add_handler(CallbackQueryHandler(confirmar_transacao_prompt, pattern="^confirma_transacao:"))
    app_bot.add_handler(CallbackQueryHandler(confirmar_transacao_exec, pattern="^confirmar_"))
    app_bot.add_handler(CommandHandler("lista_produtos", lista_produtos))
    app_bot.add_handler(CommandHandler("smartcontract", criar_smart_contract))


# === WORKER QUE PROCESSA A FILA DE UPDATES ===
def start_update_worker():
    global app_bot
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def worker():
        global app_bot

        request_conf = HTTPXRequest(connect_timeout=10, read_timeout=10, write_timeout=10)
        app_bot = Application.builder().token(TOKEN).request(request_conf).build()

        configurar_handlers(app_bot)
        await app_bot.initialize()
        await app_bot.bot.set_webhook(url=WEBHOOK_URL)
        await app_bot.start()
        logger.info("✅ Webhook registrado e bot pronto para processar mensagens.")

        while True:
            update = await loop.run_in_executor(None, update_queue.get)
            try:
                await app_bot.process_update(update)
            except Exception as e:
                logger.error(f"[worker] erro ao processar update: {e}", exc_info=True)

    loop.run_until_complete(worker())

@app.before_first_request
def activate_bot():
    if not hasattr(app, "bot_started"):
        app.bot_started = True
        threading.Thread(target=start_update_worker, daemon=True).start()

# === FLASK ROUTES ===
@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    global app_bot
    if app_bot is None or app_bot.bot is None:
        return "BOT NOT READY", 503

    update = Update.de_json(request.get_json(force=True), app_bot.bot)
    update_queue.put(update)
    return "OK", 200

@app.route("/")
def health():
    return "✅ Bot online (health check)", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))