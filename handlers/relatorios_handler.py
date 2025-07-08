import logging
logger = logging.getLogger(__name__)
import csv
from io import StringIO
from telegram import (
    InputFile,
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.constants import ParseMode
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
    MessageHandler
)

import services.produto_service_pg as produto_service
from utils.message_cleaner import delete_protected_message, send_and_delete, send_menu_with_delete , enviar_documento_temporario
from handlers.global_handlers import cancel_callback
from utils.permissions import require_permission
from utils.files import exportar_para_csv
from telegram.ext import ConversationHandler


RELATORIO_MENU, RELATORIO_DIVIDA_NOME = range(2)


@require_permission("admin")
async def start_relatorios(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    
    logger.info("→ Entrando em start_relatorios()")

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🧾 Vendas", callback_data="relatorio_vendas"),
            InlineKeyboardButton("💸 Dívidas", callback_data="relatorio_dividas")
        ],
        [InlineKeyboardButton("🚫 Cancelar", callback_data="relatorio_cancelar")]
    ])
    await send_menu_with_delete("📊 Relatório de:", update, context, keyboard, delay=15)
    return RELATORIO_MENU

async def relatorio_dividas_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    
    logger.info("→ Entrando em relatorio_dividas_callback()")

    query = update.callback_query
    await query.answer()
    await delete_protected_message(update, context)

    await send_and_delete("✍️ Digite o nome do comprador (ou envie vazio para todos):", update, context)
    return RELATORIO_DIVIDA_NOME

async def relatorio_vendas_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    
    logger.info("→ Entrando em relatorio_vendas_callback()")

    query = update.callback_query
    await query.answer()
    await delete_protected_message(update, context)
    return await listar_vendas(update, context)


async def relatorio_dividas_nome(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    
    logger.info("→ Entrando em relatorio_dividas_nome()")

    nome = update.message.text.strip()
    if nome == "":
        nome = None
    context.args = [nome] if nome else []
    return await detalhes_vendas(update, context)

@require_permission("owner")
async def listar_vendas(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    
    logger.info("→ Entrando em listar_vendas()")

    vendas = produto_service.listar_vendas_detalhadas()
    try:
        await update.message.delete()
    except:
        pass

    if not vendas:
        await send_and_delete("📭 Nenhuma venda registrada.", update, context,delay=10,protected=False)
        return

    # 🔸 Tabela em Markdown
    texto = f"*🧾 Vendas :* \n"

    texto += "```plaintext\n"
    texto += f"{'ID':<5} {'Produto':<20} {'Qtd':<5} {'Valor':<8}\n"
    texto += "-" * 42 + "\n"
    for venda_id, nome, qtd, total in vendas:
        texto += f"{venda_id:<5} {nome[:20]:<20} {qtd:<5} R${int(total):<8}\n"
    texto += "```"

    # 🔸 Botão de exportar
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Exportar CSV", callback_data="csv_relatorio")],
        [InlineKeyboardButton("🚫 Fechar", callback_data="buy_relatorio")]
    ])

    await send_menu_with_delete(
        texto,
        update,
        context,
        keyboard=keyboard,
        delay=15,
        protected=False
)


@require_permission("admin")
async def detalhes_vendas(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    
    logger.info("→ Entrando em detalhes_vendas()")

    if not context.args:
        await send_and_delete("❗ Use: /detalhes <nome_do_comprador> [pagos|pendentes]", update, context)
        return

    args = context.args
    nome = args[0]
    status = args[1].lower() if len(args) > 1 and args[1].lower() in ("pagos", "pendentes") else None

    vendas = produto_service.listar_vendas_por_comprador(nome, status)

    if not vendas:
        msg = f"📭 Nenhuma venda encontrada para *{nome}*"
        if status == "pagos":
            msg += " (pagas)."
        elif status == "pendentes":
            msg += " (pendentes)."
        else:
            msg += "."
        await send_and_delete(msg, update, context)
        return


    texto = f"*🧾 Compras de:* `{nome}`\n"
    texto += "```plaintext\n"
    texto += f"{'ID':<5} {'Produto':<20} {'Qtd':<5} {'Valor':<8} {'PG'}\n"
    texto += "-" * 50 + "\n"

    for venda_id, nome_produto, qtd, total in vendas:
        texto += f"{venda_id:<5} {nome_produto[:20]:<20} {qtd:<5} R${int(total):<8} \n"

    texto += "```"

    # Salvar nome no contexto para exportação
    context.user_data["detalhes_comprador"] = nome

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Exportar CSV", callback_data="exportar_csv_detalhes")],
        [InlineKeyboardButton("🚫 Fechar", callback_data="buy_cancelar")]
    ])

    await update.message.reply_text(texto, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)

async def exportar_csv_detalhes(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    
    logger.info("→ Entrando em exportar_csv_detalhes()")

    query = update.callback_query
    await query.answer()

    nome = context.user_data.get("detalhes_comprador")
    if not nome:
        await query.message.edit_text("❌ Nome do comprador não encontrado.")
        return

    vendas = produto_service.listar_vendas_por_comprador(nome)

    if not vendas:
        await query.message.edit_text("📭 Nenhuma venda registrada.")
        return

    colunas = ["ID", "Produto", "Quantidade", "Valor Lote"]
    dados = [[venda_id, nome, qtd, f"{total:.2f}"] for venda_id, nome, qtd, total in vendas]
    csv_bytes = exportar_para_csv(colunas, dados)

    await enviar_documento_temporario(
    context=context,
    chat_id=query.message.chat_id,
    document_bytes=csv_bytes,
    filename=f"compras_{nome}.csv",
    caption=f"📄 Compras de {nome} exportadas com sucesso! Este arquivo será deletado em 2 minutos.",
    timeout=120
    )

async def exportar_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    
    logger.info("→ Entrando em exportar_csv()")

    query = update.callback_query
    await query.answer()

    vendas = produto_service.listar_vendas_detalhadas()

    if not vendas:
        await query.message.edit_text("📭 Nenhuma venda registrada.")
        return

    # Criar CSV na memória
    colunas = ["ID", "Produto", "Quantidade", "Valor Lote"]
    dados = [[venda_id, nome, qtd, f"{total:.2f}"] for venda_id, nome, qtd, total in vendas]
    csv_bytes = exportar_para_csv(colunas, dados)

    await enviar_documento_temporario(
        context=context,
        chat_id=query.message.chat_id,
        document_bytes=csv_bytes,
        filename="vendas.csv",
        caption="📄 Arquivo exportado com sucesso! Este arquivo será deletado em 2 minutos.",
        timeout=120
    )

def get_relatorios_conversation_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("relatorios", start_relatorios)],
        states={
            RELATORIO_MENU: [
                CallbackQueryHandler(relatorio_vendas_callback, pattern="^relatorio_vendas$"),
                CallbackQueryHandler(relatorio_dividas_callback, pattern="^relatorio_dividas$"),
                CallbackQueryHandler(cancel_callback, pattern="^relatorio_cancelar$")
            ],
            RELATORIO_DIVIDA_NOME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, relatorio_dividas_nome)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_callback),
            CallbackQueryHandler(cancel_callback, pattern="^relatorio_cancelar$")
        ],
        allow_reentry=True
    )

exportar_csv_detalhes_handler = CallbackQueryHandler(exportar_csv_detalhes, pattern="^exportar_csv_detalhes$")
exportar_csv_handler = CallbackQueryHandler(exportar_csv, pattern="^csv_relatorio$")
fechar_handler = CallbackQueryHandler(cancel_callback, pattern="^buy_cancelar$|^buy_relatorio$|^relatorio_cancelar$")

exportar_csv_handler = CallbackQueryHandler(exportar_csv, pattern="^csv_relatorio$")
fechar_tabela_handler = CallbackQueryHandler(cancel_callback, pattern="^buy_relatorio$")
