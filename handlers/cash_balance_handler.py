"""
Modern Telegram handler for cash balance and revenue management.
Provides commands for viewing balance, managing expenses, and generating reports.
Follows UX Flow Guide patterns for professional user experience.
"""

import logging
import tempfile
import os
import csv
import asyncio
from decimal import Decimal, InvalidOperation
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler

from handlers.base_handler import BaseHandler, HandlerRequest, HandlerResponse, DelayConstants
from handlers.error_handler import with_error_boundary_standalone
from core.modern_service_container import get_service_registry
from core.interfaces import ICashBalanceService
from utils.permissions import require_permission
from utils.input_sanitizer import InputSanitizer


# Conversation states
BALANCE_MENU, REVENUE_REPORT, TRANSACTION_HISTORY = range(3)
EXPENSE_VALUE, EXPENSE_DESCRIPTION = range(3, 5)
ADJUST_VALUE, ADJUST_DESCRIPTION = range(5, 7)

logger = logging.getLogger(__name__)


class ModernCashBalanceHandler(BaseHandler):
    """Modern handler for cash balance management following UX Flow Guide."""

    def __init__(self):
        super().__init__("cash_balance")

    async def handle(self, request: HandlerRequest) -> HandlerResponse:
        """Route requests to appropriate handlers based on callback data."""
        # Get callback data from update
        callback_data = None
        if request.update.callback_query:
            callback_data = request.update.callback_query.data

        # Route callback queries to their handlers
        if callback_data == "revenue_report":
            return await self._handle_revenue_report(request)
        elif callback_data == "transaction_history":
            return await self._handle_transaction_history(request)
        elif callback_data == "add_expense":
            return await self._handle_add_expense_start(request)
        elif callback_data == "adjust_balance":
            return await self._handle_adjust_balance_start(request)
        elif callback_data == "back_to_balance":
            return await self._handle_back_to_balance(request)
        elif callback_data == "close_balance":
            return await self._handle_close_balance(request)
        elif callback_data == "export_revenue_csv":
            return await self._handle_export_revenue_csv(request)
        elif callback_data == "export_history_csv":
            return await self._handle_export_history_csv(request)
        else:
            # Default: Show balance menu
            return await self._handle_balance_menu(request)

    async def _handle_balance_menu(self, request: HandlerRequest) -> HandlerResponse:
        """Show main balance menu."""
        # 🔑 CRITICAL: Delete user's command message immediately (UX Flow Guide requirement)
        if request.update.message:
            try:
                await self.safe_delete_message(request.update.message, self.logger)
            except:
                pass  # Don't fail if deletion doesn't work

        try:
            from core.modern_service_container import get_cash_balance_service
            cash_service = get_cash_balance_service()
            current_balance = cash_service.get_current_balance()

            keyboard = [
                [InlineKeyboardButton("📊 Relatório de Receita", callback_data="revenue_report")],
                [InlineKeyboardButton("📈 Histórico de Transações", callback_data="transaction_history")],
                [InlineKeyboardButton("💸 Adicionar Despesa", callback_data="add_expense")],
                [InlineKeyboardButton("⚖️ Ajustar Saldo", callback_data="adjust_balance")],
                [InlineKeyboardButton("❌ Fechar", callback_data="close_balance")]
            ]

            message = f"""💰 **SALDO ATUAL**

**Saldo:** R$ {current_balance.saldo_atual:.2f}
**Última atualização:** {current_balance.data_atualizacao.strftime('%d/%m/%Y %H:%M')}

Escolha uma opção:"""

            return HandlerResponse(
                message=message,
                keyboard=InlineKeyboardMarkup(keyboard),
                next_state=BALANCE_MENU,
                parse_mode='Markdown',
                edit_message=True,
                protected=True,  # Protect balance menu from auto-deletion
                delay=DelayConstants.MANUAL_ONLY  # Only delete manually via close button
            )

        except Exception as e:
            self.logger.error(f"Error getting cash balance: {e}", exc_info=True)
            return HandlerResponse(
                message="❌ Erro ao buscar saldo. Tente novamente.",
                end_conversation=True,
                delay=DelayConstants.ERROR
            )

    async def _handle_revenue_report(self, request: HandlerRequest) -> HandlerResponse:
        """Generate and show revenue report with edit-in-place pattern."""
        try:
            # Get report for last 30 days
            from core.modern_service_container import get_cash_balance_service
            cash_service = get_cash_balance_service()
            report = cash_service.get_revenue_report(days=30)

            message = f"""📊 **RELATÓRIO DE RECEITA (30 dias)**

**Período:** {report.periodo_inicio.strftime('%d/%m/%Y')} a {report.periodo_fim.strftime('%d/%m/%Y')}

💰 **VENDAS**
Total de vendas: R$ {report.total_vendas:.2f}
Vendas realizadas: {report.vendas_count}
Pagamentos recebidos: R$ {report.total_pagamentos:.2f}

📈 **LUCRO**
Custos dos produtos: R$ {report.total_custos:.2f}
Lucro bruto: R$ {report.lucro_bruto:.2f}
Despesas: R$ {report.total_despesas:.2f}
Lucro líquido: R$ {report.lucro_liquido:.2f}

💳 **SALDO ATUAL**
Saldo em caixa: R$ {report.saldo_atual:.2f}

Transações registradas: {report.transacoes_count}"""

            keyboard = [
                [InlineKeyboardButton("📄 Exportar CSV", callback_data="export_revenue_csv")],
                [InlineKeyboardButton("🔙 Voltar", callback_data="back_to_balance")]
            ]

            # Edit message in-place following UX Flow Guide
            return HandlerResponse(
                message=message,
                keyboard=InlineKeyboardMarkup(keyboard),
                next_state=REVENUE_REPORT,
                edit_message=True,
                parse_mode='Markdown',
                protected=True,  # Protect report from auto-deletion
                delay=DelayConstants.MANUAL_ONLY
            )

        except Exception as e:
            self.logger.error(f"Error generating revenue report: {e}")
            return HandlerResponse(
                message="❌ Erro ao gerar relatório. Tente novamente.",
                edit_message=True,
                delay=DelayConstants.ERROR
            )

    async def _handle_transaction_history(self, request: HandlerRequest) -> HandlerResponse:
        """Show transaction history with edit-in-place pattern."""
        try:
            from core.modern_service_container import get_cash_balance_service
            cash_service = get_cash_balance_service()
            transactions = cash_service.get_transactions_history(limit=10)

            if not transactions:
                message = "📈 **HISTÓRICO DE TRANSAÇÕES**\n\nNenhuma transação encontrada."
            else:
                message = "📈 **HISTÓRICO DE TRANSAÇÕES (últimas 10)**\n\n"

                for t in transactions:
                    tipo_emoji = {"receita": "💰", "despesa": "💸", "ajuste": "⚖️"}.get(t.tipo, "📝")
                    valor_display = f"+R$ {t.valor:.2f}" if t.tipo == 'receita' else f"-R$ {t.valor:.2f}"
                    if t.tipo == 'ajuste':
                        valor_display = f"R$ {t.saldo_novo - t.saldo_anterior:+.2f}"

                    message += f"{tipo_emoji} **{valor_display}**\n"
                    if t.descricao:
                        message += f"   {t.descricao[:50]}...\n" if len(t.descricao) > 50 else f"   {t.descricao}\n"
                    message += f"   {t.data_transacao.strftime('%d/%m %H:%M')} | Saldo: R$ {t.saldo_novo:.2f}\n\n"

            keyboard = [
                [InlineKeyboardButton("📄 Exportar Histórico", callback_data="export_history_csv")],
                [InlineKeyboardButton("🔙 Voltar", callback_data="back_to_balance")]
            ]

            # Edit message in-place following UX Flow Guide
            return HandlerResponse(
                message=message,
                keyboard=InlineKeyboardMarkup(keyboard),
                next_state=TRANSACTION_HISTORY,
                edit_message=True,
                parse_mode='Markdown',
                protected=True,  # Protect transaction history from auto-deletion
                delay=DelayConstants.MANUAL_ONLY
            )

        except Exception as e:
            self.logger.error(f"Error showing transaction history: {e}")
            return HandlerResponse(
                message="❌ Erro ao buscar histórico. Tente novamente.",
                edit_message=True,
                delay=DelayConstants.ERROR
            )

    async def _handle_add_expense_start(self, request: HandlerRequest) -> HandlerResponse:
        """Start expense addition flow - send new message to preserve menu."""
        return HandlerResponse(
            message="💸 **ADICIONAR DESPESA**\n\nDigite o valor da despesa (ex: 150.50):",
            next_state=EXPENSE_VALUE,
            edit_message=False,  # Don't edit the balance menu - send new message instead
            delay=DelayConstants.FILE_TRANSFER,  # Auto-delete after 2 minutes if no response
            protected=True  # Protect expense flow messages
        )

    async def _handle_adjust_balance_start(self, request: HandlerRequest) -> HandlerResponse:
        """Start balance adjustment flow - admin+ only."""
        # TODO: Add permission check for admin+ level
        return HandlerResponse(
            message="""⚖️ **AJUSTAR SALDO**

Digite o valor do ajuste:
• **Positivo** para aumentar o saldo (ex: 100.50)
• **Negativo** para diminuir o saldo (ex: -50.00)""",
            next_state=ADJUST_VALUE,
            parse_mode='Markdown',
            edit_message=False,  # Don't edit the balance menu - send new message instead
            delay=DelayConstants.FILE_TRANSFER,  # Auto-delete after 2 minutes if no response
            protected=True  # Protect adjustment flow messages
        )

    async def _handle_back_to_balance(self, request: HandlerRequest) -> HandlerResponse:
        """Return to main balance menu - edit in place."""
        return await self._handle_balance_menu(request)

    async def _handle_close_balance(self, request: HandlerRequest) -> HandlerResponse:
        """Close balance menu - instant deletion."""
        # Delete the message directly if it's a callback query
        if request.update.callback_query:
            try:
                # Answer the callback query first to prevent "loading" state
                await request.update.callback_query.answer()
                # Delete the message immediately
                await request.update.callback_query.message.delete()
            except Exception as e:
                # Log the error but don't let it bubble up to error boundary
                self.logger.warning(f"Could not delete balance menu message (this is normal): {e}")
                # Still answer the callback query even if deletion failed
                try:
                    await request.update.callback_query.answer()
                except:
                    pass

        # Return a special response that indicates we've already handled everything
        # and don't want any additional message processing
        return HandlerResponse(
            message="",  # Empty message
            end_conversation=True,
            delay=0,
            edit_message=False,
            keyboard=None
        )

    async def _handle_export_revenue_csv(self, request: HandlerRequest) -> HandlerResponse:
        """Export revenue report as CSV."""
        try:
            from core.modern_service_container import get_cash_balance_service
            cash_service = get_cash_balance_service()
            report = cash_service.get_revenue_report(days=30)

            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8') as f:
                writer = csv.writer(f)

                # Headers
                writer.writerow(['Métrica', 'Valor'])

                # Data rows
                writer.writerow(['Período Início', report.periodo_inicio.strftime('%d/%m/%Y')])
                writer.writerow(['Período Fim', report.periodo_fim.strftime('%d/%m/%Y')])
                writer.writerow(['Total Vendas', f'R$ {report.total_vendas:.2f}'])
                writer.writerow(['Total Pagamentos', f'R$ {report.total_pagamentos:.2f}'])
                writer.writerow(['Total Custos', f'R$ {report.total_custos:.2f}'])
                writer.writerow(['Lucro Bruto', f'R$ {report.lucro_bruto:.2f}'])
                writer.writerow(['Total Despesas', f'R$ {report.total_despesas:.2f}'])
                writer.writerow(['Lucro Líquido', f'R$ {report.lucro_liquido:.2f}'])
                writer.writerow(['Saldo Atual', f'R$ {report.saldo_atual:.2f}'])
                writer.writerow(['Número de Vendas', report.vendas_count])
                writer.writerow(['Número de Transações', report.transacoes_count])

                temp_file_path = f.name

            # Send file
            filename = f"relatorio_receita_{report.periodo_inicio.strftime('%Y%m%d')}.csv"

            # Schedule file cleanup after sending
            async def cleanup_file():
                await asyncio.sleep(60)
                try:
                    os.unlink(temp_file_path)
                except:
                    pass

            asyncio.create_task(cleanup_file())

            return HandlerResponse(
                message="✅ Relatório exportado com sucesso!",
                edit_message=True,
                delay=DelayConstants.IMPORTANT
            )

        except Exception as e:
            self.logger.error(f"Error exporting revenue CSV: {e}")
            return HandlerResponse(
                message="❌ Erro ao exportar relatório. Tente novamente.",
                edit_message=True,
                delay=DelayConstants.ERROR
            )

    async def _handle_export_history_csv(self, request: HandlerRequest) -> HandlerResponse:
        """Export transaction history as CSV."""
        try:
            from core.modern_service_container import get_cash_balance_service
            cash_service = get_cash_balance_service()
            transactions = cash_service.get_transactions_history(limit=100)

            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8') as f:
                writer = csv.writer(f)

                # Headers
                writer.writerow(['Data', 'Tipo', 'Valor', 'Descrição', 'Saldo Anterior', 'Saldo Novo'])

                # Data rows
                for t in transactions:
                    writer.writerow([
                        t.data_transacao.strftime('%d/%m/%Y %H:%M'),
                        t.tipo.title(),
                        f'R$ {t.valor:.2f}',
                        t.descricao or '',
                        f'R$ {t.saldo_anterior:.2f}',
                        f'R$ {t.saldo_novo:.2f}'
                    ])

                temp_file_path = f.name

            # Send file
            filename = f"historico_transacoes_{transactions[0].data_transacao.strftime('%Y%m%d') if transactions else 'vazio'}.csv"

            # Schedule file cleanup
            async def cleanup_file():
                await asyncio.sleep(60)
                try:
                    os.unlink(temp_file_path)
                except:
                    pass

            asyncio.create_task(cleanup_file())

            return HandlerResponse(
                message="✅ Histórico exportado com sucesso!",
                edit_message=True,
                delay=DelayConstants.IMPORTANT
            )

        except Exception as e:
            self.logger.error(f"Error exporting history CSV: {e}")
            return HandlerResponse(
                message="❌ Erro ao exportar histórico. Tente novamente.",
                edit_message=True,
                delay=DelayConstants.ERROR
            )

    # Text input handlers for expenses and adjustments
    async def _handle_expense_value(self, request: HandlerRequest) -> HandlerResponse:
        """Handle expense value input."""
        # Delete the user's input message immediately
        try:
            await self.safe_delete_message(request.update.message, self.logger)
        except:
            pass  # Don't fail if deletion doesn't work

        try:
            valor_str = request.update.message.text.strip().replace(',', '.')
            valor = Decimal(valor_str)

            if valor <= 0:
                return HandlerResponse(
                    message="❌ Valor deve ser maior que zero. Digite novamente:",
                    next_state=EXPENSE_VALUE,
                    protected=True,
                    delay=DelayConstants.ERROR
                )

            # Store value and ask for description
            request.user_data['expense_value'] = valor
            return HandlerResponse(
                message="📝 Digite uma descrição para a despesa:",
                next_state=EXPENSE_DESCRIPTION,
                delay=DelayConstants.FILE_TRANSFER,
                protected=True  # Protect description request message
            )

        except (InvalidOperation, ValueError):
            return HandlerResponse(
                message="❌ Valor inválido. Digite um número (ex: 150.50):",
                next_state=EXPENSE_VALUE,
                protected=True,
                delay=DelayConstants.ERROR
            )

    async def _handle_expense_description(self, request: HandlerRequest) -> HandlerResponse:
        """Handle expense description and create expense."""
        # Delete the user's input message immediately
        try:
            await self.safe_delete_message(request.update.message, self.logger)
        except:
            pass  # Don't fail if deletion doesn't work

        try:
            descricao = InputSanitizer.sanitize_text(request.update.message.text.strip())
            valor = request.user_data.get('expense_value')

            if not valor:
                return HandlerResponse(
                    message="❌ Erro: valor não encontrado. Inicie novamente.",
                    end_conversation=True,
                    delay=DelayConstants.ERROR
                )

            from core.modern_service_container import get_cash_balance_service
            cash_service = get_cash_balance_service()
            transaction = cash_service.add_expense(
                valor=valor,
                descricao=descricao,
                usuario_chat_id=request.chat_id
            )

            message = f"""✅ **DESPESA ADICIONADA**

**Valor:** R$ {transaction.valor:.2f}
**Descrição:** {transaction.descricao}
**Saldo anterior:** R$ {transaction.saldo_anterior:.2f}
**Novo saldo:** R$ {transaction.saldo_novo:.2f}"""

            # Clean up user data
            request.user_data.pop('expense_value', None)

            return HandlerResponse(
                message=message,
                end_conversation=True,
                delay=DelayConstants.IMPORTANT,
                parse_mode='Markdown',
                edit_message=True  # Edit the expense message to show success, then auto-delete
            )

        except Exception as e:
            self.logger.error(f"Error adding expense: {e}")
            return HandlerResponse(
                message="❌ Erro ao adicionar despesa. Tente novamente.",
                end_conversation=True,
                delay=DelayConstants.ERROR
            )

    async def _handle_adjust_value(self, request: HandlerRequest) -> HandlerResponse:
        """Handle adjustment value input."""
        # Delete the user's input message immediately
        try:
            await self.safe_delete_message(request.update.message, self.logger)
        except:
            pass  # Don't fail if deletion doesn't work

        try:
            valor_str = request.update.message.text.strip().replace(',', '.')
            valor = Decimal(valor_str)

            # Store value and ask for description
            request.user_data['adjust_value'] = valor
            return HandlerResponse(
                message="📝 Digite uma descrição para o ajuste:",
                next_state=ADJUST_DESCRIPTION,
                delay=DelayConstants.FILE_TRANSFER,
                protected=True  # Protect description request message
            )

        except (InvalidOperation, ValueError):
            return HandlerResponse(
                message="❌ Valor inválido. Digite um número (ex: 150.50 ou -50.00):",
                next_state=ADJUST_VALUE,
                protected=True,
                delay=DelayConstants.ERROR
            )

    async def _handle_adjust_description(self, request: HandlerRequest) -> HandlerResponse:
        """Handle adjustment description and create adjustment."""
        # Delete the user's input message immediately
        try:
            await self.safe_delete_message(request.update.message, self.logger)
        except:
            pass  # Don't fail if deletion doesn't work

        try:
            descricao = InputSanitizer.sanitize_text(request.update.message.text.strip())
            valor = request.user_data.get('adjust_value')

            if valor is None:
                return HandlerResponse(
                    message="❌ Erro: valor não encontrado. Inicie novamente.",
                    end_conversation=True,
                    delay=DelayConstants.ERROR
                )

            from core.modern_service_container import get_cash_balance_service
            cash_service = get_cash_balance_service()
            transaction = cash_service.adjust_balance(
                valor=valor,
                descricao=descricao,
                usuario_chat_id=request.chat_id
            )

            sign = "+" if valor > 0 else ""
            message = f"""✅ **SALDO AJUSTADO**

**Ajuste:** {sign}R$ {valor:.2f}
**Descrição:** {transaction.descricao}
**Saldo anterior:** R$ {transaction.saldo_anterior:.2f}
**Novo saldo:** R$ {transaction.saldo_novo:.2f}"""

            # Clean up user data
            request.user_data.pop('adjust_value', None)

            return HandlerResponse(
                message=message,
                end_conversation=True,
                delay=DelayConstants.IMPORTANT,
                parse_mode='Markdown',
                edit_message=True  # Edit the adjustment message to show success, then auto-delete
            )

        except Exception as e:
            self.logger.error(f"Error adjusting balance: {e}")
            return HandlerResponse(
                message="❌ Erro ao ajustar saldo. Tente novamente.",
                end_conversation=True,
                delay=DelayConstants.ERROR
            )

    async def cancel_conversation(self, request: HandlerRequest) -> HandlerResponse:
        """Cancel ongoing conversation."""
        return HandlerResponse(
            message="❌ Operação cancelada.",
            end_conversation=True,
            delay=DelayConstants.SUCCESS
        )


def get_modern_cash_balance_handler() -> ConversationHandler:
    """Create modern cash balance conversation handler following UX Flow Guide."""
    handler_instance = ModernCashBalanceHandler()

    # Async wrapper functions that properly handle update/context and use HandlerRequest
    async def handle_with_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        request = handler_instance.create_request(update, context)
        response = await handler_instance.handle(request)
        return await handler_instance.send_response(response, request)

    async def handle_expense_value_with_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        request = handler_instance.create_request(update, context)
        response = await handler_instance._handle_expense_value(request)
        return await handler_instance.send_response(response, request)

    async def handle_expense_description_with_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        request = handler_instance.create_request(update, context)
        response = await handler_instance._handle_expense_description(request)
        return await handler_instance.send_response(response, request)

    async def handle_adjust_value_with_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        request = handler_instance.create_request(update, context)
        response = await handler_instance._handle_adjust_value(request)
        return await handler_instance.send_response(response, request)

    async def handle_adjust_description_with_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        request = handler_instance.create_request(update, context)
        response = await handler_instance._handle_adjust_description(request)
        return await handler_instance.send_response(response, request)

    async def handle_cancel_with_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        request = handler_instance.create_request(update, context)
        response = await handler_instance.cancel_conversation(request)
        return await handler_instance.send_response(response, request)

    return ConversationHandler(
        entry_points=[
            CommandHandler('saldo', with_error_boundary_standalone("cash_balance_entry")(handle_with_request), filters.ChatType.PRIVATE)
        ],
        states={
            BALANCE_MENU: [
                CallbackQueryHandler(with_error_boundary_standalone("cash_balance_callback")(handle_with_request), pattern="^(revenue_report|transaction_history|add_expense|adjust_balance|close_balance|back_to_balance|export_revenue_csv|export_history_csv)$")
            ],
            REVENUE_REPORT: [
                CallbackQueryHandler(with_error_boundary_standalone("cash_balance_callback")(handle_with_request), pattern="^(export_revenue_csv|back_to_balance)$")
            ],
            TRANSACTION_HISTORY: [
                CallbackQueryHandler(with_error_boundary_standalone("cash_balance_callback")(handle_with_request), pattern="^(export_history_csv|back_to_balance)$")
            ],
            EXPENSE_VALUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, with_error_boundary_standalone("cash_balance_expense_value")(handle_expense_value_with_request))
            ],
            EXPENSE_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, with_error_boundary_standalone("cash_balance_expense_desc")(handle_expense_description_with_request))
            ],
            ADJUST_VALUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, with_error_boundary_standalone("cash_balance_adjust_value")(handle_adjust_value_with_request))
            ],
            ADJUST_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, with_error_boundary_standalone("cash_balance_adjust_desc")(handle_adjust_description_with_request))
            ]
        },
        fallbacks=[
            CommandHandler('cancel', with_error_boundary_standalone("cash_balance_cancel")(handle_cancel_with_request))
        ],
        per_message=False
    )


# Keep compatibility with old handler name
def get_cash_balance_handler() -> ConversationHandler:
    """Compatibility function - returns modern handler."""
    return get_modern_cash_balance_handler()