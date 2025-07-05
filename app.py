from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
import os
import services.produto_service as produto_service

# Handlers
from handlers.start_handler import start
from handlers.login_handler import login_handler
from handlers.user_handler import get_user_conversation_handler
from handlers.global_handlers import cancel
from handlers.product_handler import get_product_conversation_handler
from handlers.estoque_handler import get_estoque_conversation_handler
from handlers.buy_handler import (
    get_buy_conversation_handler, listar_debitos, selecionar_debito,
    marcar_pagamento, pagar_vendas, confirmar_pagamento, executar_pagamento
)
from handlers.relatorios_handler import (
    exportar_csv_handler, exportar_csv_detalhes_handler,
    fechar_handler, get_relatorios_conversation_handler
)
from handlers.lista_produtos_handler import lista_produtos
from handlers.smartcontract_handler import (
    criar_smart_contract,
    get_smartcontract_conversation_handler,
    confirmar_transacao_prompt,
    confirmar_transacao_exec
)
import os
import asyncio

# Token do bot
TOKEN = os.environ.get("BOT_TOKEN")



# # 🗄️ Banco
# produto_service.init_db()

# # 🤖 Telegram bot
# app_bot = Application.builder().token(TOKEN).build()

# # Handlers
# app_bot.add_handler(CommandHandler("start", start))
# app_bot.add_handler(CommandHandler("cancel", cancel))
# app_bot.add_handler(login_handler)
# app_bot.add_handler(get_user_conversation_handler())
# app_bot.add_handler(get_product_conversation_handler())
# app_bot.add_handler(get_estoque_conversation_handler())
# app_bot.add_handler(get_buy_conversation_handler())
# app_bot.add_handler(CommandHandler("debitos", listar_debitos))
# app_bot.add_handler(CallbackQueryHandler(selecionar_debito, pattern="^debito:"))
# app_bot.add_handler(CallbackQueryHandler(marcar_pagamento, pattern="^pagar_"))
# app_bot.add_handler(CommandHandler("pagar", pagar_vendas))
# app_bot.add_handler(CallbackQueryHandler(confirmar_pagamento, pattern="^pagar:"))
# app_bot.add_handler(CallbackQueryHandler(executar_pagamento, pattern="^confirmar_pagamento_"))
# app_bot.add_handler(get_relatorios_conversation_handler())
# app_bot.add_handler(exportar_csv_handler)
# app_bot.add_handler(exportar_csv_detalhes_handler)
# app_bot.add_handler(fechar_handler)
# app_bot.add_handler(CommandHandler("lista_produtos", lista_produtos))
# app_bot.add_handler(CommandHandler("smartcontract", criar_smart_contract))
# app_bot.add_handler(get_smartcontract_conversation_handler())
# app_bot.add_handler(CallbackQueryHandler(confirmar_transacao_prompt, pattern="^confirma_transacao:"))
# app_bot.add_handler(CallbackQueryHandler(confirmar_transacao_exec, pattern="^confirmar_"))
# Cria Application sem Updater
app_bot = Application.builder().token(TOKEN).build()

# Handler de exemplo
async def start(update: Update, context):
    await update.message.reply_text("🤖 Bot online e funcionando!")

app_bot.add_handler(CommandHandler("start", start))

# Flask App
flask_app = Flask(__name__)

@flask_app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), app_bot.bot)
    asyncio.create_task(app_bot.process_update(update))
    return "ok"

@flask_app.before_first_request
def setup():
    url = f"https://{os.environ['RENDER_EXTERNAL_HOSTNAME']}/{TOKEN}"
    asyncio.create_task(app_bot.bot.set_webhook(url))

if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
