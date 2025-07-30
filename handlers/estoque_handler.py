import logging
logger = logging.getLogger(__name__)
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from utils.message_cleaner import (
    send_menu_with_delete,
    delete_protected_message,
    send_and_delete,
    get_effective_message
)
from handlers.global_handlers import cancel, cancel_callback
from utils.input_sanitizer import InputSanitizer
import services.produto_service_pg as produto_service


# 🔥 Estados
ESTOQUE_MENU, ESTOQUE_ADD_SELECT, ESTOQUE_ADD_VALUES = range(3)


# 🔘 Teclado do menu de estoque
def estoque_menu_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Adicionar ao estoque", callback_data="add_estoque"),
            InlineKeyboardButton("📦 Verificar estoque", callback_data="verificar_estoque")
        ],
        [
            InlineKeyboardButton("🚫 Cancelar", callback_data="cancelar")
        ]
    ])


# 🔘 Gera teclado com lista de produtos
def gerar_keyboard_estoque(callback_prefix):
    produtos = produto_service.listar_produtos_com_estoque()
    keyboard = []

    for pid, nome, emoji, quantidade in produtos:
        display_text = f"{emoji} {nome} — {quantidade} unidades"
        keyboard.append([InlineKeyboardButton(display_text, callback_data=f"{callback_prefix}:{pid}")])

    keyboard.append([InlineKeyboardButton("🚫 Cancelar", callback_data="cancelar")])
    return InlineKeyboardMarkup(keyboard)


# 🚀 Início do /estoque
async def start_estoque(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    logger.info("→ Entrando em start_estoque()")

    print("🔥 start_estoque chamado")

    await send_menu_with_delete(
        "📦 O que deseja fazer?",
        update,
        context,
        estoque_menu_keyboard(),
        delay=10,          # 🔥 Tempo para deletar
        protected=False    # 🔥 Não proteger
    )
    return ESTOQUE_MENU


# ▶️ Seleção do menu estoque
async def estoque_menu_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    logger.info("→ Entrando em estoque_menu_selection()")

    query = update.callback_query
    await query.answer()

    await delete_protected_message(update, context)

    if query.data == "add_estoque":
        return await start_add_estoque(update, context)

    if query.data == "verificar_estoque":
        await send_and_delete("🔍 Você escolheu 📦 Verificar estoque (em construção).", update, context)
        return ConversationHandler.END


# ▶️ Ao clicar em "Adicionar ao estoque"
async def start_add_estoque(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    logger.info("→ Entrando em start_add_estoque()")

    query = update.callback_query
    if query:
        await query.answer()
        await delete_protected_message(update, context)

    return await exibir_lista_produtos(update, context)

async def exibir_lista_produtos(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    logger.info("→ Entrando em exibir_lista_produtos()")

    produtos = produto_service.listar_produtos_com_estoque()

    if not produtos:
        await send_and_delete("🚫 Nenhum produto cadastrado.", update, context)
        return ConversationHandler.END

    await send_menu_with_delete(
        "👀 Escolha o produto para adicionar mais estoque:",
        update,
        context,
        gerar_keyboard_estoque("addestoque")
    )
    return ESTOQUE_ADD_SELECT


# ▶️ Seleciona o produto
async def estoque_select_product(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    logger.info("→ Entrando em estoque_select_product()")

    query = update.callback_query
    await query.answer()

    await delete_protected_message(update, context)

    produto_id = query.data.split(":")[1]
    context.user_data["estoque_produto_id"] = produto_id

    await send_and_delete(
        "✍️ Qual a quantidade / valor / custo deste produto?\n\nExemplo:\n10 / 25.90 / 15.00",
        update,
        context
    )
    return ESTOQUE_ADD_VALUES


# ▶️ Recebe os valores e salva no banco
async def estoque_receive_values(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    logger.info("→ Entrando em estoque_receive_values()")

    produto_id = context.user_data["estoque_produto_id"]

    try:
        quantidade, valor, custo = InputSanitizer.sanitize_stock_input(update.message.text)
        produto_service.adicionar_estoque(produto_id, quantidade, valor, custo)

        await send_menu_with_delete(
            f"✅ Estoque adicionado com sucesso!\n\nQuantidade: {quantidade}\nValor: {valor}\nCusto: {custo}\n\nDeseja continuar?",
            update,
            context,
            keyboard=menu_apos_adicionar(),
            delay=15,
            protected=False
        )
        return ConversationHandler.END

    except ValueError as ve:
        await send_and_delete(
            f"{ve}\n\nExemplo válido:\n10 / 25.90 / 15.00",
            update,
            context
        )
        return ESTOQUE_ADD_VALUES

    except Exception as e:
        await send_and_delete(
            f"❌ Erro inesperado: {e}",
            update,
            context
        )
        return ESTOQUE_ADD_VALUES

async def finalizar_estoque(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    logger.info("→ Entrando em finalizar_estoque()")

    await delete_protected_message(update, context)
    await send_and_delete("✅ Edição de estoque finalizada.", update, context)
    return ConversationHandler.END

async def adicionar_mais_estoque(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    logger.info("→ Entrando em adicionar_mais_estoque()")

    await delete_protected_message(update, context)
    return await exibir_lista_produtos(update, context)  # ✅ Essa é segura para chamadas internas

def menu_apos_adicionar():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Adicionar outro", callback_data="add_mais"),
            InlineKeyboardButton("✅ Finalizar", callback_data="finalizar_estoque")
        ]
    ])

# 🔥 ConversationHandler completo
def get_estoque_conversation_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("estoque", start_estoque)],
        states={
            ESTOQUE_MENU: [
                CallbackQueryHandler(estoque_menu_selection),
                CallbackQueryHandler(cancel_callback, pattern="^cancelar$"),
                CallbackQueryHandler(adicionar_mais_estoque, pattern="^add_mais$"),
                CallbackQueryHandler(finalizar_estoque, pattern="^finalizar_estoque$"),
            ],
            ESTOQUE_ADD_SELECT: [
                CallbackQueryHandler(estoque_select_product)
            ],
            ESTOQUE_ADD_VALUES: [
                MessageHandler(filters.Regex(r"^\s*\d+\s*/\s*\d+(\.\d+)?\s*/\s*\d+(\.\d+)?\s*$"), estoque_receive_values),
                CallbackQueryHandler(finalizar_estoque, pattern="^finalizar_estoque$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(cancel_callback, pattern="^cancelar$")
        ],
        allow_reentry=True
    )
