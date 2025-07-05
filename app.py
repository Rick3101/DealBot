from flask import Flask, request
from telegram.ext import MessageHandler, filters, Application, CommandHandler , ConversationHandler , CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import services.produto_service as produto_service
from handlers.start_handler import start
from handlers.login_handler import login_handler
import services.produto_service as produto_service
from handlers.user_handler import get_user_conversation_handler
from handlers.global_handlers import cancel
from handlers.product_handler import get_product_conversation_handler
from handlers.estoque_handler import get_estoque_conversation_handler 
from handlers.buy_handler import get_buy_conversation_handler ,listar_debitos,selecionar_debito,marcar_pagamento ,  pagar_vendas, confirmar_pagamento, executar_pagamento
from handlers.relatorios_handler import exportar_csv_handler, exportar_csv_detalhes_handler, fechar_handler , get_relatorios_conversation_handler
from handlers.lista_produtos_handler import lista_produtos
from handlers.smartcontract_handler import (
    criar_smart_contract,
    get_smartcontract_conversation_handler,
    confirmar_transacao_prompt,
    confirmar_transacao_exec
)

import logging
import os
import sys

TOKEN = os.getenv("BOT_TOKEN")

# 🗄️ Inicializa o banco
produto_service.init_db()

# 🤖 Inicializa o bot
app_bot = Application.builder().token(TOKEN).build()

# Adiciona handlers
app_bot.add_handler(CommandHandler("start", start))
app_bot.add_handler(CommandHandler("start", start))
app_bot.add_handler(CommandHandler("cancel", cancel))
app_bot.add_handler(get_user_conversation_handler())
app_bot.add_handler(login_handler)
app_bot.add_handler(get_product_conversation_handler())
app_bot.add_handler(get_estoque_conversation_handler()) 
app_bot.add_handler(get_buy_conversation_handler()) 
app_bot.add_handler(CommandHandler("debitos", listar_debitos))
app_bot.add_handler(CallbackQueryHandler(selecionar_debito, pattern="^debito:"))
app_bot.add_handler(CallbackQueryHandler(marcar_pagamento, pattern="^pagar_"))
app_bot.add_handler(CommandHandler("pagar", pagar_vendas))
app_bot.add_handler(CallbackQueryHandler(confirmar_pagamento, pattern="^pagar:"))
app_bot.add_handler(CallbackQueryHandler(executar_pagamento, pattern="^confirmar_pagamento_"))
app_bot.add_handler(get_relatorios_conversation_handler())
app_bot.add_handler(exportar_csv_handler)
app_bot.add_handler(exportar_csv_detalhes_handler)
app_bot.add_handler(fechar_handler)
app_bot.add_handler(CommandHandler("lista_produtos", lista_produtos))
app_bot.add_handler(CommandHandler("smartcontract", criar_smart_contract))
app_bot.add_handler(get_smartcontract_conversation_handler())
app_bot.add_handler(CallbackQueryHandler(confirmar_transacao_prompt, pattern="^confirma_transacao:"))
app_bot.add_handler(CallbackQueryHandler(confirmar_transacao_exec, pattern="^confirmar_"))


# Flask App
flask_app = Flask(__name__)

@flask_app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), app_bot.bot)
    app_bot.update_queue.put_nowait(update)
    return "OK"

# Inicializa o webhook quando o app é iniciado
@flask_app.before_first_request
def setup():
    webhook_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{TOKEN}"
    app_bot.bot.set_webhook(url=webhook_url)

if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
