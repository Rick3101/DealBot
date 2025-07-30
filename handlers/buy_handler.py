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
from telegram.constants import ParseMode
from utils.message_cleaner import (
    send_menu_with_delete,
    delete_protected_message,
    send_and_delete,
)
from utils.input_sanitizer import InputSanitizer
import services.produto_service_pg as produto_service
from handlers.global_handlers import cancel, cancel_callback
from utils.permissions import require_permission
from datetime import datetime

BUY_NAME, BUY_SELECT_PRODUCT, BUY_QUANTITY, BUY_PRICE = range(4)

# 🔘 Teclado com produtos + finalizar compra
def gerar_keyboard_comprar(nivel):
    produtos = produto_service.listar_produtos_com_estoque()
    keyboard = []

    for pid, nome, emoji, quantidade in produtos:
        if emoji in {"🧪", "💀"}:
            continue  # ⛔️ Pula itens secretos

        if nivel == "owner":
            display_text = f"{emoji} {nome} — {quantidade} unidades"
        else:
            display_text = f"{emoji} {nome}"

        keyboard.append([InlineKeyboardButton(display_text, callback_data=f"buyproduct:{pid}")])

    keyboard.append([
        InlineKeyboardButton("✅ Finalizar Compra", callback_data="buy_finalizar"),
        InlineKeyboardButton("❌ Cancelar", callback_data="buy_cancelar")
    ])
    return InlineKeyboardMarkup(keyboard)

@require_permission("admin")
async def start_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    logger.info("→ Entrando em start_buy()")

    context.user_data.clear()
    context.chat_data.clear()
    context.user_data["itens_venda"] = []

    chat_id = update.effective_chat.id
    nivel = produto_service.obter_nivel(chat_id)
    context.user_data["nivel"] = nivel

    if nivel == "owner":
        await send_and_delete(
            "📟 Qual o nome do comprador?",
            update,
            context,
            delay=10,
            protected=False
        )
        return BUY_NAME

    elif nivel == "admin":
        nome = produto_service.obter_username_por_chat_id(chat_id)
        context.user_data["nome_comprador"] = nome

        logger.info(f"🤪 chat_id={chat_id} → nome={nome}")

        await send_menu_with_delete(
            f"🛒 Compra registrada em nome de: *{nome}*\nEscolha o produto:",
            update,
            context,
            gerar_keyboard_comprar(nivel),
            delay=10,
            protected=False
        )
        return BUY_SELECT_PRODUCT

    else:
        await send_and_delete("⛔ Permissão insuficiente para realizar compras.", update, context)
        return ConversationHandler.END

async def buy_set_name(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    logger.info("→ Entrando em buy_set_name()")

    try:
        nome_comprador = InputSanitizer.sanitize_buyer_name(update.message.text)
        context.user_data["nome_comprador"] = nome_comprador
        
        nivel = context.user_data.get("nivel")
        await send_menu_with_delete(
            "🛒 Escolha o produto:",
            update,
            context,
            gerar_keyboard_comprar(nivel),
            delay=10,
            protected=False
        )
        return BUY_SELECT_PRODUCT
        
    except ValueError as e:
        await send_and_delete(f"❌ {str(e)}\n\nDigite um nome válido:", update, context)
        return BUY_NAME

async def buy_select_product(update: Update, context: ContextTypes.DEFAULT_TYPE):  
    logger.info("→ Entrando em buy_select_product()")

    query = update.callback_query
    await query.answer()

    await delete_protected_message(update, context)

    if query.data == "buy_finalizar":
        return await finalizar_compra(update, context)

    produto_id = query.data.split(":")[1]
    context.user_data["produto_atual"] = produto_id

    await send_and_delete(
        "✍️ Quantidade desse produto:",
        update,
        context,
        delay=10,
        protected=False
    )
    return BUY_QUANTITY

async def buy_set_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):   
    logger.info("→ Entrando em buy_set_quantity()")

    try:
        quantidade = InputSanitizer.sanitize_quantity(update.message.text)
        context.user_data["quantidade_atual"] = quantidade

        await send_and_delete(
            "💰 Qual o preço do lote?",
            update,
            context,
            delay=10,
            protected=False
        )
        return BUY_PRICE
        
    except ValueError as e:
        await send_and_delete(f"❌ {str(e)}\n\nDigite uma quantidade válida:", update, context)
        return BUY_QUANTITY

async def buy_set_price(update: Update, context: ContextTypes.DEFAULT_TYPE):  
    logger.info("→ Entrando em buy_set_price()")

    try:
        await update.message.delete()
    except:
        pass

    try:
        preco = InputSanitizer.sanitize_price(update.message.text)
    except ValueError as e:
        await send_and_delete(f"❌ {str(e)}\n\nDigite um preço válido:", update, context)
        return BUY_PRICE

    item = {
        "produto_id": context.user_data["produto_atual"],
        "quantidade": context.user_data["quantidade_atual"],
        "preco": preco
    }

    context.user_data["itens_venda"].append(item)

    nivel = context.user_data.get("nivel")
    await send_menu_with_delete(
        "🛒 Produto adicionado! Escolha outro ou finalize a compra.",
        update,
        context,
        gerar_keyboard_comprar(nivel)
    )

    return BUY_SELECT_PRODUCT

async def finalizar_compra(update: Update, context: ContextTypes.DEFAULT_TYPE):  
    logger.info("→ Entrando em finalizar_compra()")

    query = update.callback_query
    await query.answer()

    await delete_protected_message(update, context)

    nome = context.user_data.get("nome_comprador")
    itens = context.user_data.get("itens_venda", [])

    if not itens:
        await send_and_delete("❌ Nenhum item adicionado na compra.", update, context)
        return ConversationHandler.END

    dados = [(int(i["produto_id"]), int(i["quantidade"]), float(i["preco"])) for i in itens]

    valido, problema_id, disponivel = produto_service.validar_estoque_suficiente(dados)

    if not valido:
        nome_prod = produto_service.obter_nome_produto(problema_id)
        await send_and_delete(
            f"❌ Estoque insuficiente para *{nome_prod}*\nDisponível: {disponivel}",
            update,
            context,
            delay=10,
            protected=False
        )
        return ConversationHandler.END

    venda_id = produto_service.registrar_venda(nome, datetime.now(), pago=False)

    for produto_id, quantidade, preco in dados:
        produto_service.registrar_item_venda(venda_id, produto_id, quantidade, preco)
        produto_service.consumir_estoque_fifo(produto_id, quantidade)

    context.user_data.pop("modo_secreto", None)
    await send_and_delete("✅ Compra finalizada e estoque atualizado!", update, context)
    return ConversationHandler.END

async def checar_menu_secreto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    logger.info(f"🤪 Recebido no BUY_SELECT_PRODUCT: {texto}")

    if texto.lower() == "wubba lubba dub dub":
        nivel = context.user_data.get("nivel")

        produtos_secretos = [
            (pid, nome, emoji, qtd)
            for pid, nome, emoji, qtd in produto_service.listar_produtos_com_estoque()
            if emoji in {"🧪", "💀"}
        ]

        if not produtos_secretos:
            await send_and_delete("🧙‍♂️ Nenhum item secreto disponível.", update, context)
            return BUY_SELECT_PRODUCT

        teclado = [
            [InlineKeyboardButton(f"{emoji} {nome}", callback_data=f"buyproduct:{pid}")]
            for pid, nome, emoji, qtd in produtos_secretos
        ]

        teclado.append([
            InlineKeyboardButton("✅ Finalizar Compra", callback_data="buy_finalizar"),
            InlineKeyboardButton("❌ Cancelar", callback_data="buy_cancelar")
        ])

        await send_menu_with_delete(
            "🤪 Itens secretos desbloqueados! Escolha um:",
            update,
            context,
            InlineKeyboardMarkup(teclado),
            delay=10,
            protected=False
        )
        return BUY_SELECT_PRODUCT

    await send_and_delete("❓ Comando não reconhecido. Use os botões para selecionar.", update, context)
    return BUY_SELECT_PRODUCT


def get_buy_conversation_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("buy", start_buy)],
        states={
            BUY_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, buy_set_name)
            ],
            BUY_SELECT_PRODUCT: [
                CallbackQueryHandler(buy_select_product, pattern="^buyproduct:"),
                CallbackQueryHandler(finalizar_compra, pattern="^buy_finalizar$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, checar_menu_secreto),
            ],
            BUY_QUANTITY: [
                MessageHandler(filters.Regex(r"^\d+$"), buy_set_quantity)
            ],
            BUY_PRICE: [
                MessageHandler(filters.Regex(r"^\d+(\.\d{1,2})?$"), buy_set_price)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(cancel_callback, pattern="^buy_cancelar$")
        ],
        allow_reentry=True
    )
