import logging
logger = logging.getLogger(__name__)
import csv
from io import StringIO
from telegram import (
    InputFile,
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
    get_effective_message
)
import services.produto_service_pg as produto_service
from handlers.global_handlers import cancel, cancel_callback
from utils.permissions import require_permission
from datetime import datetime

# 🔥 Estados
BUY_NAME, BUY_SELECT_PRODUCT, BUY_QUANTITY, BUY_PRICE = range(4)


# 🔘 Teclado com produtos + finalizar compra
def gerar_keyboard_comprar(nivel):
    produtos = produto_service.listar_produtos_com_estoque()
    keyboard = []

    for pid, nome, emoji, quantidade in produtos:
        if nivel == "owner":
            display_text = f"{emoji} {nome} — {quantidade} unidades"
        else:
            display_text = f"{emoji} {nome}"
        keyboard.append([InlineKeyboardButton(display_text, callback_data=f"buyproduct:{pid}")])

    logger.info(f"Nível: {nivel}")

    keyboard.append([
        InlineKeyboardButton("✅ Finalizar Compra", callback_data="buy_finalizar"),
        InlineKeyboardButton("🚫 Cancelar", callback_data="buy_cancelar")
    ])
    return InlineKeyboardMarkup(keyboard)


# 🚀 Início do /buy
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
            "🧾 Qual o nome do comprador?",
            update,
            context,
            delay=10,
            protected=False
        )
        return BUY_NAME
    
    elif nivel == "admin":
        nome = produto_service.obter_username_por_chat_id(chat_id)
        context.user_data["nome_comprador"] = nome
        
        logger.info(f"🧪 chat_id={chat_id} → nome={nome}")

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

# ▶️ Recebe nome do comprador
async def buy_set_name(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    logger.info("→ Entrando em buy_set_name()")

    context.user_data["nome_comprador"] = update.message.text
    nivel = context.user_data.get("nivel")
    await send_menu_with_delete(
        "🛒 Escolha o produto:",
        update,
        context,
        gerar_keyboard_comprar(nivel),
        delay =10,
        protected=False

    )
    return BUY_SELECT_PRODUCT


# ▶️ Seleciona produto
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
        delay =10,
        protected=False
    )
    return BUY_QUANTITY


# ▶️ Recebe quantidade
async def buy_set_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):   
    logger.info("→ Entrando em buy_set_quantity()")

    quantidade = int(update.message.text)
    context.user_data["quantidade_atual"] = quantidade

    await send_and_delete(
        "💰 Qual o preço do lote?",
        update,
        context,
        delay = 10,
        protected=False
    )
    return BUY_PRICE


# ▶️ Recebe preço e salva o item temporariamente
async def buy_set_price(update: Update, context: ContextTypes.DEFAULT_TYPE):  
    logger.info("→ Entrando em buy_set_price()")

    try:
        await update.message.delete()
    except:
        pass

    preco = float(update.message.text)

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


# ✔️ Finaliza compra
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
        nome = produto_service.obter_nome_produto(problema_id)
        await send_and_delete(
            f"❌ Estoque insuficiente para *{nome}*.\nDisponível: {disponivel}",
            update,
            context,
            delay=10,
            protected=False
        )
        return ConversationHandler.END

    # ✅ Registrar venda e itens corretamente
    venda_id = produto_service.registrar_venda(nome, datetime.now(), pago=False)

    for produto_id, quantidade, preco in dados:
        produto_service.registrar_item_venda(venda_id, produto_id, quantidade, preco)
        produto_service.consumir_estoque_fifo(produto_id, quantidade)

    await send_and_delete("✅ Compra finalizada e estoque atualizado!", update, context)
    return ConversationHandler.END

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

@require_permission("admin")
async def listar_debitos(update: Update, context: ContextTypes.DEFAULT_TYPE):   
    logger.info("→ Entrando em listar_debitos()")

    nome = " ".join(context.args).strip() if context.args else None
    vendas = produto_service.listar_vendas_em_aberto(nome)

    if not vendas:
        msg = f"✅ Nenhum débito encontrado para *{nome}*." if nome else "✅ Nenhum débito pendente."
        await send_and_delete(msg, update, context)
        return

    texto = "*📋 Débitos Pendentes:*\n\n"
    keyboard = []

    for venda_id, cliente, total, pago in vendas:
        pendente = total - pago
        label = f"#{venda_id} — {cliente}: R${pago:.2f} / R${total:.2f}"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"debito:{venda_id}")])

    keyboard.append([InlineKeyboardButton("🚫 Fechar", callback_data="fechar")])
    await send_menu_with_delete(texto, update, context, InlineKeyboardMarkup(keyboard), delay=15)


async def selecionar_debito(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    logger.info("→ Entrando em selecionar_debito()")

    query = update.callback_query
    await query.answer()
    
    await delete_protected_message(update, context)  

    venda_id = query.data.split(":")[1]
    context.user_data["debito_venda_id"] = venda_id

    botoes = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Sim", callback_data="pagar_sim"),
            InlineKeyboardButton("❌ Não", callback_data="pagar_nao")
        ]
    ])
    await send_and_delete(f"Deseja marcar a venda #{venda_id} como paga?", reply_markup=botoes)

async def marcar_pagamento(update: Update, context: ContextTypes.DEFAULT_TYPE):  
    logger.info("→ Entrando em marcar_pagamento()")

    query = update.callback_query
    await query.answer()
    venda_id = context.user_data.get("debito_venda_id")

    await delete_protected_message(update, context)  

    if not venda_id:
        await query.message.reply_text("⚠️ Venda não identificada.")
        return

    if query.data == "pagar_sim":
        produto_service.atualizar_status_pago(venda_id, True)
        await send_and_delete(f"✅ Venda #{venda_id} marcada como paga." ,update, context)
    else:
        await send_and_delete("🚫 Operação cancelada." , update, context)

@require_permission("admin")
async def pagar_vendas(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    logger.info("→ Entrando em pagar_vendas()")

    nome = " ".join(context.args).strip() if context.args else None
    vendas = produto_service.listar_vendas_nao_pagas(nome)

    if not vendas:
        msg = f"✅ Nenhuma venda pendente para *{nome}*." if nome else "✅ Nenhuma venda pendente."
        await send_and_delete(msg, update, context)
        return

    texto = "*💰 Vendas pendentes:*\n\n"
    keyboard = []
    ids_adicionados = set()

    for venda_id, cliente, produto, qtd, total in vendas:
        if venda_id not in ids_adicionados:
            display = f"#{venda_id} — {cliente} ({produto}, {qtd} un., R${int(total)})"
            keyboard.append([InlineKeyboardButton(display, callback_data=f"pagar:{venda_id}")])
            ids_adicionados.add(venda_id)

    keyboard.append([InlineKeyboardButton("🚫 Fechar", callback_data="buy_cancelar")])
    await send_menu_with_delete(
        texto,
        update,
        context,
        keyboard=InlineKeyboardMarkup(keyboard),
        delay=15,         # ou o tempo que quiser
        protected=False   # ou True, se quiser que não seja apagado
    )

async def confirmar_pagamento(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    logger.info("→ Entrando em confirmar_pagamento()")

    query = update.callback_query
    await query.answer()

    await delete_protected_message(update, context)  

    venda_id = query.data.split(":")[1]
    context.user_data["venda_a_pagar"] = venda_id

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Sim", callback_data="confirmar_pagamento_sim"),
            InlineKeyboardButton("❌ Não", callback_data="confirmar_pagamento_nao")
        ]
    ])
    await send_menu_with_delete(
        f"Deseja marcar a venda #{venda_id} como paga?",
        update,
        context,
        keyboard=keyboard,
        delay=15,
        protected=False
    )

async def executar_pagamento(update: Update, context: ContextTypes.DEFAULT_TYPE):  
    logger.info("→ Entrando em executar_pagamento()")

    query = update.callback_query
    await query.answer()
    
    await delete_protected_message(update, context)  

    venda_id = context.user_data.get("venda_a_pagar")

    if not venda_id:
        await send_and_delete("⚠️ Venda não identificada." , update , context)
        return

    if query.data == "confirmar_pagamento_sim":
        produto_service.atualizar_status_pago(venda_id, True)
        await send_and_delete(f"✅ Venda #{venda_id} marcada como paga.",update,context)
    else:
        await send_and_delete("❌ Pagamento cancelado.",update,context)
