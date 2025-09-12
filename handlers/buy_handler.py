from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from handlers.base_handler import MenuHandlerBase, HandlerRequest, HandlerResponse, InteractionType, ContentType
from handlers.error_handler import with_error_boundary
from models.handler_models import PurchaseRequest, ProductSelectionRequest
from services.handler_business_service import HandlerBusinessService
from core.modern_service_container import get_context, get_user_service, get_product_service
from core.config import get_config
from utils.input_sanitizer import InputSanitizer
from utils.permissions import require_permission
from utils.product_list_generator import create_product_keyboard
from services.base_service import ValidationError


# States
BUY_NAME, BUY_SELECT_PRODUCT, BUY_QUANTITY, BUY_PRICE = range(4)


class ModernBuyHandler(MenuHandlerBase):
    def __init__(self):
        super().__init__("buy")
        self.secret_phrase = get_config().services.secret_menu_phrase
    
    def create_main_menu_keyboard(self) -> InlineKeyboardMarkup:
        # This handler doesn't use a traditional main menu
        return None
    
    def get_menu_text(self) -> str:
        return "🛒 Escolha o produto:"
    
    def get_menu_state(self) -> int:
        return BUY_SELECT_PRODUCT
    
    def create_products_keyboard(self, request: HandlerRequest, include_secret: bool = False) -> InlineKeyboardMarkup:
        """Create keyboard with available products using the utility method."""
        user_level = request.user_data.get("nivel", "user")
        business_service = self.ensure_services_initialized()
        
        return create_product_keyboard(
            business_service=business_service,
            user_level=user_level,
            include_secret=include_secret,
            callback_prefix="buyproduct",
            include_actions=True
        )
    
    async def handle_menu_selection(self, request: HandlerRequest, selection: str) -> HandlerResponse:
        """Handle product selection or finalize purchase."""
        if selection == "buy_finalizar":
            return await self.finalize_purchase(request)
        elif selection == "buy_cancelar":
            return self.create_smart_response(
                message="❌ Compra cancelada.",
                keyboard=None,
                interaction_type=InteractionType.CONFIRMATION,
                content_type=ContentType.INFO,
                end_conversation=True
            )
        elif selection.startswith("buyproduct:"):
            product_id = int(selection.split(":")[1])
            request.user_data["produto_atual"] = product_id
            
            return self.create_smart_response(
                message="✍️ Quantidade desse produto:",
                keyboard=None,
                interaction_type=InteractionType.FORM_INPUT,
                content_type=ContentType.INFO,
                next_state=BUY_QUANTITY
            )
        else:
            return self.create_smart_response(
                message="❌ Opção inválida.",
                keyboard=self.create_products_keyboard(request, include_secret=False),
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.VALIDATION_ERROR,
                next_state=BUY_SELECT_PRODUCT
            )
    
    async def handle(self, request: HandlerRequest) -> HandlerResponse:
        """Handle initial buy command - determine user level and flow."""
        # Clear previous data
        request.user_data.clear()
        request.context.chat_data.clear()
        request.user_data["itens_venda"] = []
        
        # Get user information
        user_service = get_user_service(request.context)
        user = user_service.get_user_by_chat_id(request.chat_id)
        
        if not user:
            return self.create_smart_response(
                message="❌ Usuário não encontrado. Execute /login primeiro.",
                keyboard=None,
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.ERROR,
                end_conversation=True
            )
        
        request.user_data["nivel"] = user.level.value
        
        if user.level.value == "owner":
            return self.create_smart_response(
                message="📟 Qual o nome do comprador?",
                keyboard=None,
                interaction_type=InteractionType.FORM_INPUT,
                content_type=ContentType.INFO,
                next_state=BUY_NAME
            )
        elif user.level.value == "admin":
            request.user_data["nome_comprador"] = user.username
            
            return self.create_smart_response(
                message=f"🛒 Compra registrada em nome de: *{user.username}*\nEscolha o produto:",
                keyboard=self.create_products_keyboard(request, include_secret=False),
                interaction_type=InteractionType.MENU_NAVIGATION,
                content_type=ContentType.SELECTION,
                next_state=BUY_SELECT_PRODUCT
            )
        else:
            return self.create_smart_response(
                message="⛔ Permissão insuficiente para realizar compras.",
                keyboard=None,
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.ERROR,
                end_conversation=True
            )
    
    async def handle_buyer_name(self, request: HandlerRequest) -> HandlerResponse:
        """Handle buyer name input (owner only)."""
        try:
            buyer_name = InputSanitizer.sanitize_buyer_name(request.update.message.text)
            request.user_data["nome_comprador"] = buyer_name
            
            return HandlerResponse(
                message="🛒 Escolha o produto:",
                keyboard=self.create_products_keyboard(request, include_secret=False),
                next_state=BUY_SELECT_PRODUCT,
                edit_message=True
            )
            
        except ValueError as e:
            return HandlerResponse(
                message=f"❌ {str(e)}\n\nDigite um nome válido:",
                next_state=BUY_NAME,
                edit_message=True
            )
    
    async def handle_quantity(self, request: HandlerRequest) -> HandlerResponse:
        """Handle quantity input."""
        try:
            quantity = InputSanitizer.sanitize_quantity(request.update.message.text)
            request.user_data["quantidade_atual"] = quantity
            
            return HandlerResponse(
                message="💰 Qual o preço da unidade?",
                next_state=BUY_PRICE,
                edit_message=True
            )
            
        except ValueError as e:
            return HandlerResponse(
                message=f"❌ {str(e)}\n\nDigite uma quantidade válida:",
                next_state=BUY_QUANTITY,
                edit_message=True
            )
    
    async def handle_price(self, request: HandlerRequest) -> HandlerResponse:
        """Handle price input and add item to cart."""
        try:
            # Delete the price message for privacy using safe deletion
            await self.batch_cleanup_messages([request.update.message], strategy="instant")
            
            price = InputSanitizer.sanitize_price(request.update.message.text)
            
            # Add item to cart
            item = {
                "produto_id": request.user_data["produto_atual"],
                "quantidade": request.user_data["quantidade_atual"],
                "preco": price
            }
            
            request.user_data["itens_venda"].append(item)
            
            return HandlerResponse(
                message="🛒 Produto adicionado! Escolha outro ou finalize a compra.",
                keyboard=self.create_products_keyboard(request, include_secret=False),
                next_state=BUY_SELECT_PRODUCT,
                edit_message=True
            )
            
        except ValueError as e:
            return HandlerResponse(
                message=f"❌ {str(e)}\n\nDigite um preço válido:",
                next_state=BUY_PRICE,
                edit_message=True
            )
    
    async def handle_secret_menu_check(self, request: HandlerRequest) -> HandlerResponse:
        """Handle secret menu activation."""
        text = request.update.message.text.strip()
        
        if text.lower() == self.secret_phrase:
            # Show secret products
            return HandlerResponse(
                message="🤪 Itens secretos desbloqueados! Escolha um:",
                keyboard=self.create_products_keyboard(request, include_secret=True),
                next_state=BUY_SELECT_PRODUCT,
                edit_message=True
            )
        else:
            return HandlerResponse(
                message="❓ Comando não reconhecido. Use os botões para selecionar.",
                next_state=BUY_SELECT_PRODUCT,
                edit_message=True
            )
    
    async def finalize_purchase(self, request: HandlerRequest) -> HandlerResponse:
        """Finalize the purchase using business service."""
        buyer_name = request.user_data.get("nome_comprador")
        items = request.user_data.get("itens_venda", [])
        
        if not items:
            return HandlerResponse(
                message="❌ Nenhum item adicionado na compra.",
                end_conversation=True
            )
        
        # Convert items to purchase request format
        purchase_items = []
        total_amount = 0
        
        for item in items:
            product_id = int(item["produto_id"])
            quantity = int(item["quantidade"])
            price = float(item["preco"])
            
            purchase_items.append(ProductSelectionRequest(
                product_id=product_id,
                quantity=quantity,
                custom_price=price
            ))
            
            total_amount += price
        
        # Create purchase request
        purchase_request = PurchaseRequest(
            buyer_name=buyer_name,
            items=purchase_items,
            total_amount=total_amount,
            chat_id=request.chat_id
        )
        
        # Process purchase through business service
        business_service = self.ensure_services_initialized()
        response = business_service.process_purchase(purchase_request)
        
        if response.success:
            return HandlerResponse(
                message="✅ Compra finalizada e estoque atualizado!",
                end_conversation=True
            )
        else:
            error_message = response.message
            if response.warnings:
                error_message += "\n\n" + "\n".join(response.warnings)
            
            return HandlerResponse(
                message=error_message,
                end_conversation=True
            )
    
    # Wrapper methods for conversation handler
    @with_error_boundary("buy_start")
    @require_permission("admin")
    async def start_buy(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return await self.safe_handle(self.handle, update, context)
    
    @with_error_boundary("buy_name")
    async def buy_set_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        request = self.create_request(update, context)
        response = await self.handle_buyer_name(request)
        return await self.send_response(response, request)
    
    @with_error_boundary("buy_select")
    async def buy_select_product(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        # Delete protected message
        # Use safe deletion method
        await self.batch_cleanup_messages([query], strategy="instant")
        
        request = self.create_request(update, context)
        response = await self.handle_menu_selection(request, query.data)
        return await self.send_response(response, request)
    
    @with_error_boundary("buy_quantity")
    async def buy_set_quantity(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        request = self.create_request(update, context)
        response = await self.handle_quantity(request)
        return await self.send_response(response, request)
    
    @with_error_boundary("buy_price")
    async def buy_set_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        request = self.create_request(update, context)
        response = await self.handle_price(request)
        return await self.send_response(response, request)
    
    @with_error_boundary("buy_secret")
    async def check_secret_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        request = self.create_request(update, context)
        response = await self.handle_secret_menu_check(request)
        return await self.send_response(response, request)
    
    @with_error_boundary("buy_cancel")
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        request = self.create_request(update, context)
        response = HandlerResponse(
            message="🚫 Compra cancelada.",
            end_conversation=True
        )
        return await self.send_response(response, request)
    
    def get_conversation_handler(self) -> ConversationHandler:
        """Create the conversation handler."""
        return ConversationHandler(
            entry_points=[CommandHandler("buy", self.start_buy)],
            states={
                BUY_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.buy_set_name)
                ],
                BUY_SELECT_PRODUCT: [
                    CallbackQueryHandler(self.buy_select_product, pattern="^buyproduct:"),
                    CallbackQueryHandler(self.buy_select_product, pattern="^buy_finalizar$"),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.check_secret_menu),
                ],
                BUY_QUANTITY: [
                    MessageHandler(filters.Regex(r"^\d+$"), self.buy_set_quantity)
                ],
                BUY_PRICE: [
                    MessageHandler(filters.Regex(r"^\d+(\.\d{1,2})?$"), self.buy_set_price)
                ],
            },
            fallbacks=[
                CommandHandler("cancel", self.cancel),
                CallbackQueryHandler(self.cancel, pattern="^buy_cancelar$")
            ],
            allow_reentry=True
        )


# Factory function
def get_modern_buy_handler():
    """Get the modern buy conversation handler."""
    handler = ModernBuyHandler()
    return handler.get_conversation_handler()