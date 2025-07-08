import logging
logger = logging.getLogger(__name__)

import services.produto_service_pg as produto_service
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters
)
from utils.message_cleaner import send_and_delete, delete_protected_message
from handlers.global_handlers import cancel, cancel_callback

TRANSACTION_MENU, TRANSACTION_DESCRICAO = range(2)

async def criar_smart_contract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("→ Entrando em criar_smart_contract()")
    chat_id = update.effective_chat.id

    if not context.args:
        logger.warning(f"Chat {chat_id} não enviou código do contrato.")
        await send_and_delete("❗ Envie o código do contrato. Ex: /smartcontract 12345", update, context)
        return ConversationHandler.END

    codigo = " ".join(context.args).strip()
    produto_service.criar_smart_contract(chat_id, codigo)
    logger.info(f"Contrato '{codigo}' criado para chat_id={chat_id}")
    await send_and_delete(f"✅ Contrato `{codigo}` criado com sucesso!", update, context)
    return ConversationHandler.END

async def start_transactions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("→ Entrando em start_transactions()")
    chat_id = update.effective_chat.id

    if not context.args:
        await send_and_delete("❗ Envie o código do contrato. Ex: /transactions 12345", update, context)
        return ConversationHandler.END

    codigo = " ".join(context.args).strip()
    contrato = produto_service.obter_smart_contract(chat_id, codigo)

    if not contrato:
        await send_and_delete(f"❌ Contrato `{codigo}` não encontrado.", update, context)
        return ConversationHandler.END

    context.user_data["contrato_id"] = contrato[0]
    context.user_data["codigo_contrato"] = contrato[1]

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🤝 Shakehands", callback_data="shakehands")],
        [InlineKeyboardButton("➕ Adicionar Transação", callback_data="add_transaction")],
        [InlineKeyboardButton("🚫 Cancelar", callback_data="cancelar")]
    ])

    await send_and_delete(f"📄 Contrato `{codigo}` encontrado. O que deseja fazer?", update, context, reply_markup=keyboard)
    return TRANSACTION_MENU

async def transacao_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("→ Entrando em transacao_menu()")
    query = update.callback_query
    await query.answer()
    await delete_protected_message(update, context)

    contrato_id = context.user_data.get("contrato_id")

    if query.data == "shakehands":
        transacoes = produto_service.listar_transacoes_contrato(contrato_id)

        if not transacoes:
            await send_and_delete("📭 Nenhuma transação registrada.", update, context)
            return ConversationHandler.END

        keyboard = []
        for tid, descricao in transacoes:
            label = f"🧾 {descricao[:40]}"
            keyboard.append([InlineKeyboardButton(label, callback_data=f"confirma_transacao:{tid}")])

        keyboard.append([InlineKeyboardButton("🚫 Cancelar", callback_data="cancelar")])
        markup = InlineKeyboardMarkup(keyboard)

        await query.message.reply_text("📜 Transações registradas:", reply_markup=markup)
        return ConversationHandler.END

    elif query.data == "add_transaction":
        await send_and_delete("✍️ Envie a descrição da transação:", update, context)
        return TRANSACTION_DESCRICAO

async def receber_descricao_transacao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("→ Entrando em receber_descricao_transacao()")
    contrato_id = context.user_data.get("contrato_id")
    descricao = update.message.text.strip()

    if not descricao:
        await send_and_delete("❌ Descrição vazia. Tente novamente.", update, context)
        return TRANSACTION_DESCRICAO

    produto_service.adicionar_transacao_contrato(contrato_id, descricao)
    logger.info(f"Transação adicionada no contrato {contrato_id}: {descricao}")
    await send_and_delete("✅ Transação adicionada com sucesso!", update, context)
    return ConversationHandler.END

async def confirmar_transacao_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("→ Entrando em confirmar_transacao_prompt()")
    query = update.callback_query
    await query.answer()
    await delete_protected_message(update, context)

    tid = query.data.split(":")[1]
    context.user_data["transacao_a_confirmar"] = tid

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Sim", callback_data="confirmar_sim")],
        [InlineKeyboardButton("❌ Não", callback_data="confirmar_nao")]
    ])
    await query.message.reply_text("✅ Confirmar esta transação?", reply_markup=keyboard)

async def confirmar_transacao_exec(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("→ Entrando em confirmar_transacao_exec()")
    query = update.callback_query
    await query.answer()
    await delete_protected_message(update, context)

    tid = context.user_data.get("transacao_a_confirmar")

    if query.data == "confirmar_sim":
        logger.info(f"Transação {tid} confirmada.")
        await query.message.reply_text(f"🔐 Transação #{tid} confirmada com sucesso!")
    else:
        logger.info(f"Transação {tid} cancelada.")
        await query.message.reply_text("❌ Confirmação cancelada.")

def get_smartcontract_conversation_handler():
    logger.info("→ Entrando em get_smartcontract_conversation_handler()")
    return ConversationHandler(
        entry_points=[CommandHandler("transactions", start_transactions)],
        states={
            TRANSACTION_MENU: [CallbackQueryHandler(transacao_menu)],
            TRANSACTION_DESCRICAO: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_descricao_transacao)],
        },
        fallbacks=[CommandHandler("cancel", cancel), CallbackQueryHandler(cancel_callback, pattern="^cancelar$")]
    )
