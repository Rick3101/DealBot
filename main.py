from telegram.ext import MessageHandler, filters, Application, CommandHandler , ConversationHandler , CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from handlers.start_handler import start
from handlers.login_handler import login_handler
import services.produto_service_pg as produto_service
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
import sys


# 🔑 Token do Bot
TOKEN = "7593794682:AAEqzdMTtkzGcJLdI_SGFjRSF50q4ntlIjo"

# 🌍 URL pública gerada pelo ngrok ou domínio
WEBHOOK_URL = f"https://777b-2804-1b3-a7c0-d599-f9bf-ac44-a52b-8d26.ngrok-free.app/{TOKEN}"


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot.log',            # arquivo de log
    filemode='a',                  # append
)

logger = logging.getLogger(__name__)


def excecao_global(exc_type, exc_value, traceback):
    logger.error("Exceção não tratada", exc_info=(exc_type, exc_value, traceback))

sys.excepthook = excecao_global

# 🗄️ Inicializa o banco
produto_service.init_db()

# 🤖 Inicializa o bot
app = Application.builder().token(TOKEN).build()
print("🔥 App rodando. Handlers carregados.")
# 🔗 Adiciona os handlers


# 🔥 Login Conversation Handler
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("cancel", cancel))
app.add_handler(get_user_conversation_handler())
app.add_handler(login_handler)
app.add_handler(get_product_conversation_handler())
app.add_handler(get_estoque_conversation_handler()) 
app.add_handler(get_buy_conversation_handler()) 
app.add_handler(CommandHandler("debitos", listar_debitos))
app.add_handler(CallbackQueryHandler(selecionar_debito, pattern="^debito:"))
app.add_handler(CallbackQueryHandler(marcar_pagamento, pattern="^pagar_"))
app.add_handler(CommandHandler("pagar", pagar_vendas))
app.add_handler(CallbackQueryHandler(confirmar_pagamento, pattern="^pagar:"))
app.add_handler(CallbackQueryHandler(executar_pagamento, pattern="^confirmar_pagamento_"))
app.add_handler(get_relatorios_conversation_handler())
app.add_handler(exportar_csv_handler)
app.add_handler(exportar_csv_detalhes_handler)
app.add_handler(fechar_handler)
app.add_handler(CommandHandler("lista_produtos", lista_produtos))
app.add_handler(CommandHandler("smartcontract", criar_smart_contract))
app.add_handler(get_smartcontract_conversation_handler())
app.add_handler(CallbackQueryHandler(confirmar_transacao_prompt, pattern="^confirma_transacao:"))
app.add_handler(CallbackQueryHandler(confirmar_transacao_exec, pattern="^confirmar_"))


# 🚀 Webhook
app.run_webhook(
    listen="0.0.0.0",
    port=5000,
    url_path=TOKEN,
    webhook_url=WEBHOOK_URL
)

print("HERE")
