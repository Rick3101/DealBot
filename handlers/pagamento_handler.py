import logging
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters
)
from handlers.base_handler import FormHandlerBase, HandlerRequest, HandlerResponse
from handlers.error_handler import with_error_boundary
from models.handler_models import PaymentRequest, PaymentResponse
from services.handler_business_service import HandlerBusinessService
from utils.input_sanitizer import InputSanitizer
from utils.permissions import require_permission
from handlers.global_handlers import cancel, cancel_callback

logger = logging.getLogger(__name__)

# States
PAGAMENTO_MENU, PAGAMENTO_VALOR = range(2)


class ModernPagamentoHandler(FormHandlerBase):
    def __init__(self):
        super().__init__("pagamento")
        
    def get_form_fields(self) -> list:
        return ["valor_pagamento"]
    
    def get_retry_state(self) -> Optional[int]:
        return PAGAMENTO_VALOR
        
    async def handle(self, request: HandlerRequest) -> HandlerResponse:
        return await self._show_unpaid_sales(request)
    
    async def _show_unpaid_sales(self, request: HandlerRequest) -> HandlerResponse:
        business_service = HandlerBusinessService(request.context)
        
        # Get buyer name from args if provided
        nome = None
        if hasattr(request, 'args') and request.args:
            nome = " ".join(request.args).strip()
        
        # Get unpaid sales
        unpaid_sales = business_service.get_unpaid_sales(nome)
        
        if not unpaid_sales:
            msg = f"✅ Nenhuma venda pendente para *{nome}*." if nome else "✅ Nenhuma venda pendente."
            return HandlerResponse(
                message=msg,
                end_conversation=True
            )
        
        texto = "*💰 Vendas pendentes:*\n\n"
        keyboard = []
        ids_adicionados = set()
        
        for sale_with_payments in unpaid_sales:
            sale = sale_with_payments.sale
            venda_id = sale.id
            
            if venda_id not in ids_adicionados:
                # Get first item for display
                primeiro_item = sale.items[0] if sale.items else None
                produto_nome = "N/A"
                if primeiro_item:
                    # Handle both old and new SaleItem format
                    if hasattr(primeiro_item, 'produto_nome') and primeiro_item.produto_nome:
                        produto_nome = primeiro_item.produto_nome
                    else:
                        # Fallback: get product name from service if produto_nome not available
                        try:
                            from core.modern_service_container import get_product_service
                            product_service = get_product_service()
                            product = product_service.get_product_by_id(primeiro_item.produto_id)
                            produto_nome = product.nome if product else f"Produto #{primeiro_item.produto_id}"
                        except Exception:
                            produto_nome = f"Produto #{primeiro_item.produto_id}"
                total_items = len(sale.items)
                
                display_total = sale_with_payments.balance_due
                display = f"#{venda_id} — {sale.comprador} ({produto_nome}"
                if total_items > 1:
                    display += f" +{total_items-1} itens"
                display += f", R${display_total:.0f})"
                
                keyboard.append([InlineKeyboardButton(display, callback_data=f"pag_select:{venda_id}")])
                ids_adicionados.add(venda_id)
        
        keyboard.append([InlineKeyboardButton("🚫 Fechar", callback_data="pag_cancel")])
        
        return HandlerResponse(
            message=texto,
            keyboard=InlineKeyboardMarkup(keyboard),
            next_state=PAGAMENTO_MENU,
            delay=15
        )
    
    async def _handle_sale_selection(self, request: HandlerRequest, venda_id: int) -> HandlerResponse:
        business_service = HandlerBusinessService(request.context)
        request.user_data["venda_a_pagar"] = venda_id
        
        # Get sale details with payments
        sale_with_payments = business_service.get_sale_with_payments(venda_id)
        
        if not sale_with_payments:
            return HandlerResponse(
                message="❌ Venda não encontrada.",
                end_conversation=True
            )
        
        total = sale_with_payments.sale.get_total_value()
        pago = sale_with_payments.total_paid
        restante = sale_with_payments.balance_due
        
        message = (
            f"💸 Total: R${total:.2f}\n"
            f"Pago: R${pago:.2f}\n"
            f"🔹 Restante: R${restante:.2f}\n\n"
            f"Digite o valor a pagar:"
        )
        
        return HandlerResponse(
            message=message,
            next_state=PAGAMENTO_VALOR
        )
    
    async def validate_field(self, field_name: str, value: str) -> float:
        if field_name == "valor_pagamento":
            return InputSanitizer.sanitize_price(value)
        raise ValueError(f"Campo desconhecido: {field_name}")
    
    def get_field_prompt(self, field_name: str) -> str:
        if field_name == "valor_pagamento":
            return "Digite o valor a pagar:"
        return "Campo desconhecido"
    
    def get_field_state(self, field_name: str) -> int:
        if field_name == "valor_pagamento":
            return PAGAMENTO_VALOR
        return PAGAMENTO_VALOR
    
    def get_next_field(self, current_field: str) -> Optional[str]:
        return None  # Only one field
    
    async def process_form_data(self, request: HandlerRequest, form_data: dict) -> HandlerResponse:
        business_service = HandlerBusinessService(request.context)
        venda_id = request.user_data.get("venda_a_pagar")
        valor = form_data.get("valor_pagamento")
        
        if not venda_id or not valor:
            return HandlerResponse(
                message="❌ Dados de pagamento incompletos.",
                end_conversation=True
            )
        
        # Create payment request
        payment_request = PaymentRequest(
            sale_id=venda_id,
            amount=valor,
            chat_id=request.chat_id
        )
        
        # Process payment
        payment_response = business_service.process_payment(payment_request)
        
        if not payment_response.success:
            return HandlerResponse(
                message=f"❌ {payment_response.message}",
                end_conversation=True
            )
        
        # Build success message
        if payment_response.is_fully_paid:
            message = f"✅ Pagamento de R${valor:.2f} registrado.\n💰 Venda quitada!"
        else:
            message = (
                f"✅ Pagamento de R${valor:.2f} registrado.\n"
                f"💸 Total pago até agora: R${payment_response.total_paid:.2f} / "
                f"R${payment_response.total_paid + payment_response.remaining_debt:.2f}"
            )
        
        return HandlerResponse(
            message=message,
            end_conversation=True
        )
    
    def get_conversation_handler(self) -> ConversationHandler:
        return ConversationHandler(
            entry_points=[
                CommandHandler("pagar", self._start_pagamento),
                CallbackQueryHandler(self._sale_selection_callback, pattern="^pag_select:")
            ],
            states={
                PAGAMENTO_MENU: [
                    CallbackQueryHandler(self._menu_callback, pattern="^pag_")
                ],
                PAGAMENTO_VALOR: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._payment_value_callback)
                ]
            },
            fallbacks=[
                CommandHandler("cancel", cancel),
                CallbackQueryHandler(cancel_callback, pattern="^pag_cancel$"),
            ],
            allow_reentry=True
        )
    
    @require_permission("admin")
    @with_error_boundary
    async def _start_pagamento(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        request = self.create_request(update, context)
        
        # Store args for buyer name filtering
        if context.args:
            request.args = context.args
        
        response = await self.handle(request)
        return await self.send_response(response, request)
    
    @with_error_boundary
    async def _sale_selection_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        request = self.create_request(update, context)
        venda_id = int(update.callback_query.data.split(":")[1])
        
        response = await self._handle_sale_selection(request, venda_id)
        return await self.send_response(response, request)
    
    @with_error_boundary
    async def _menu_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        request = self.create_request(update, context)
        selection = update.callback_query.data
        
        if selection == "pag_cancel":
            response = HandlerResponse(
                message="🚫 Operação cancelada.",
                end_conversation=True
            )
        else:
            response = HandlerResponse(
                message="❌ Operação inválida.",
                end_conversation=True
            )
        
        return await self.send_response(response, request)
    
    @with_error_boundary
    async def _payment_value_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        request = self.create_request(update, context)
        response = await self.handle_form_input(request, "valor_pagamento", request.update.message.text)
        return await self.send_response(response, request)


# Factory function for the pagamento conversation handler
def get_pagamento_conversation_handler() -> ConversationHandler:
    handler = ModernPagamentoHandler()
    return handler.get_conversation_handler()


# Legacy callback handler for compatibility with existing menu integrations
@with_error_boundary
async def iniciar_pagamento_parcial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Legacy callback handler for starting partial payment"""
    logger.info("→ Entrando em iniciar_pagamento_parcial()")
    
    query = update.callback_query
    await query.answer()
    
    from utils.message_cleaner import delete_protected_message
    await delete_protected_message(update, context)

    venda_id = int(query.data.split(":")[1])
    context.user_data["venda_a_pagar"] = venda_id

    business_service = HandlerBusinessService(context)
    sale_with_payments = business_service.get_sale_with_payments(venda_id)
    
    if not sale_with_payments:
        from utils.message_cleaner import send_and_delete
        await send_and_delete("❌ Venda não encontrada.", update, context)
        return ConversationHandler.END
    
    total = sale_with_payments.sale.get_total_value()
    pago = sale_with_payments.total_paid
    restante = sale_with_payments.balance_due

    from utils.message_cleaner import send_and_delete
    await send_and_delete(
        f"💸 Total: R${total:.2f}\nPago: R${pago:.2f}\n🔹 Restante: R${restante:.2f}\n\nDigite o valor a pagar:",
        update, context
    )
    return PAGAMENTO_VALOR


@with_error_boundary
async def receber_pagamento_parcial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Legacy message handler for receiving payment amount"""
    logger.info("→ Entrando em receber_pagamento_parcial()")

    try:
        valor = InputSanitizer.sanitize_price(update.message.text)
    except ValueError as e:
        from utils.message_cleaner import send_and_delete
        await send_and_delete(f"❌ {str(e)}\n\nDigite um valor válido:", update, context)
        return PAGAMENTO_VALOR

    venda_id = context.user_data.get("venda_a_pagar")
    business_service = HandlerBusinessService(context)
    
    # Create payment request
    payment_request = PaymentRequest(
        sale_id=venda_id,
        amount=valor,
        chat_id=update.effective_chat.id
    )
    
    payment_response = business_service.process_payment(payment_request)
    
    if not payment_response.success:
        from utils.message_cleaner import send_and_delete
        await send_and_delete(f"❌ {payment_response.message}", update, context)
        return ConversationHandler.END
    
    # Build success message
    if payment_response.is_fully_paid:
        message = f"✅ Pagamento de R${valor:.2f} registrado.\n💰 Venda quitada!"
    else:
        message = (
            f"✅ Pagamento de R${valor:.2f} registrado.\n"
            f"💸 Total pago até agora: R${payment_response.total_paid:.2f} / "
            f"R${payment_response.total_paid + payment_response.remaining_debt:.2f}"
        )

    from utils.message_cleaner import send_and_delete
    await send_and_delete(message, update, context)
    return ConversationHandler.END


# Legacy conversation handler for backward compatibility
def get_pagamento_legacy_conversation_handler():
    """Legacy conversation handler for existing integrations"""
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


# Command handler registrations
pagamento_command_handler = CommandHandler("pagar", ModernPagamentoHandler()._start_pagamento)
pagar_callback_handler = CallbackQueryHandler(iniciar_pagamento_parcial, pattern="^pagar:")