# pagamento_handler.py
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, CallbackQueryHandler,
    CommandHandler, MessageHandler, filters
)
from utils.message_cleaner import send_and_delete, delete_protected_message, send_menu_with_delete
from services import produto_service_pg as produto_service
from handlers.global_handlers import cancel, cancel_callback
from utils.permissions import require_permission

logger = logging.getLogger(__name__)

PAGAMENTO_VALOR = range(1)

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
    await send_menu_with_delete(texto, update, context, InlineKeyboardMarkup(keyboard), delay=15, protected=False)

async def iniciar_pagamento_parcial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("→ Entrando em iniciar_pagamento_parcial()")
    query = update.callback_query
    await query.answer()
    await delete_protected_message(update, context)

    venda_id = query.data.split(":")[1]
    context.user_data["venda_a_pagar"] = venda_id

    total = produto_service.valor_total_venda(venda_id)
    pago = produto_service.valor_pago_venda(venda_id)
    restante = total - pago

    await send_and_delete(
        f"💸 Total: R${total:.2f}\nPago: R${pago:.2f}\n🔹 Restante: R${restante:.2f}\n\nDigite o valor a pagar:",
        update, context
    )
    return PAGAMENTO_VALOR

async def receber_pagamento_parcial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("→ Entrando em receber_pagamento_parcial()")
    texto = update.message.text.replace(",", ".").strip()

    try:
        valor = float(texto)
        if valor <= 0:
            raise ValueError()
    except:
        await send_and_delete("❌ Valor inválido. Tente novamente com um número válido.", update, context)
        return PAGAMENTO_VALOR

    venda_id = context.user_data.get("venda_a_pagar")
    produto_service.registrar_pagamento(venda_id, valor)

    total = produto_service.valor_total_venda(venda_id)
    pago = produto_service.valor_pago_venda(venda_id)

    if pago >= total:
        produto_service.atualizar_status_pago(venda_id, True)
        await send_and_delete(f"✅ Pagamento de R${valor:.2f} registrado.\n💰 Venda quitada!", update, context)
    else:
        await send_and_delete(
            f"✅ Pagamento de R${valor:.2f} registrado.\n💸 Total pago até agora: R${pago:.2f} / R${total:.2f}",
            update, context
        )

    return ConversationHandler.END

def get_pagamento_conversation_handler():
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(iniciar_pagamento_parcial, pattern="^pagar:"),
        ],
        states={
            PAGAMENTO_VALOR: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receber_pagamento_parcial)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(cancel_callback, pattern="^buy_cancelar$"),
        ],
        allow_reentry=True
    )
