from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from handlers.base_handler import MenuHandlerBase, HandlerRequest, HandlerResponse, InteractionType, ContentType, DelayConstants
from handlers.error_handler import with_error_boundary
from models.handler_models import PurchaseRequest, ProductSelectionRequest
from services.handler_business_service import HandlerBusinessService
from core.modern_service_container import get_context, get_user_service, get_product_service, get_expedition_service
from core.config import get_config
from utils.input_sanitizer import InputSanitizer
from utils.permissions import require_permission
from utils.product_list_generator import create_product_keyboard
from services.base_service import ValidationError, ServiceError
import logging


# Enhanced States - supporting expedition integration
BUY_NAME, BUY_TYPE_SELECT, BUY_EXPEDITION_SELECT, BUY_SELECT_PRODUCT, BUY_QUANTITY, BUY_PRICE = range(6)


class ModernBuyHandler(MenuHandlerBase):
    def __init__(self):
        super().__init__("buy")
        self.secret_phrase = get_config().services.secret_menu_phrase
        self.logger = logging.getLogger("handlers.buy")
    
    def create_main_menu_keyboard(self) -> InlineKeyboardMarkup:
        # This handler doesn't use a traditional main menu
        return None

    def create_buy_type_keyboard(self) -> InlineKeyboardMarkup:
        """Create buy type selection keyboard for users with expeditions."""
        keyboard = [
            [InlineKeyboardButton("🛒 Compra Normal", callback_data="buy_normal")],
            [InlineKeyboardButton("🏴‍☠️ Compra para Expedição", callback_data="buy_expedition")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="buy_cancelar")]
        ]
        return InlineKeyboardMarkup(keyboard)

    def create_expedition_selection_keyboard(self, expeditions: list) -> InlineKeyboardMarkup:
        """Create keyboard for expedition selection."""
        keyboard = []

        for expedition in expeditions:
            status_emoji = self._get_status_emoji(expedition.status)
            days_left = (expedition.deadline.date() - expedition.created_at.date()).days

            button_text = f"{status_emoji} {expedition.name[:20]}{'...' if len(expedition.name) > 20 else ''}"
            if days_left <= 3:
                button_text += " 🔥"

            keyboard.append([
                InlineKeyboardButton(
                    button_text,
                    callback_data=f"buy_exp_select:{expedition.id}"
                )
            ])

        keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data="buy_back")])
        keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="buy_cancelar")])

        return InlineKeyboardMarkup(keyboard)
    
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
                end_conversation=True,
                delay=DelayConstants.INFO  # Auto-delete cancel message after 10 seconds
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
        """Handle initial buy command - determine user level and flow with expedition support."""
        # Clear previous data
        request.user_data.clear()
        request.context.chat_data.clear()
        request.user_data["itens_venda"] = []
        request.user_data["expedition_mode"] = False

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

        # Check if user has expeditions for expedition mode
        has_expeditions = False
        try:
            expedition_service = get_expedition_service(request.context)
            expeditions = expedition_service.get_expeditions(
                owner_chat_id=request.chat_id,
                status_filter=['planning', 'active']
            )
            has_expeditions = len(expeditions) > 0
        except Exception as e:
            self.logger.warning(f"Could not check expeditions: {e}")

        request.user_data["has_expeditions"] = has_expeditions

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

            # Show buy type selection if user has expeditions
            if has_expeditions:
                return self.create_smart_response(
                    message=f"🛒 Compra registrada em nome de: *{user.username}*\n\n**Tipo de Compra**\nEscolha o tipo:",
                    keyboard=self.create_buy_type_keyboard(),
                    interaction_type=InteractionType.MENU_NAVIGATION,
                    content_type=ContentType.SELECTION,
                    next_state=BUY_TYPE_SELECT
                )
            else:
                # No expeditions, proceed with normal buy
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
            # Delete user input message immediately
            await self.batch_cleanup_messages([request.update.message], strategy="instant")
            
            buyer_name = InputSanitizer.sanitize_buyer_name(request.update.message.text)
            request.user_data["nome_comprador"] = buyer_name

            # Show buy type selection if user has expeditions
            if request.user_data.get("has_expeditions", False):
                return HandlerResponse(
                    message=f"📟 Compra registrada em nome de: *{buyer_name}*\n\n**Tipo de Compra**\nEscolha o tipo:",
                    keyboard=self.create_buy_type_keyboard(),
                    next_state=BUY_TYPE_SELECT,
                    edit_message=True
                )
            else:
                # No expeditions, proceed with normal buy
                return HandlerResponse(
                    message=f"📟 Compra registrada em nome de: *{buyer_name}*\nEscolha o produto:",
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
            # Delete user input message immediately
            await self.batch_cleanup_messages([request.update.message], strategy="instant")
            
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
            
            # Send new product selection message instead of editing the existing one
            # This preserves the product menu visibility
            return HandlerResponse(
                message="✅ Produto adicionado ao carrinho!\n\n🛒 Escolha outro produto ou finalize a compra:",
                keyboard=self.create_products_keyboard(request, include_secret=False),
                next_state=BUY_SELECT_PRODUCT,
                edit_message=False  # Don't edit, send new message
            )
            
        except ValueError as e:
            return HandlerResponse(
                message=f"❌ {str(e)}\n\nDigite um preço válido:",
                next_state=BUY_PRICE,
                edit_message=True
            )
    
    async def handle_secret_menu_check(self, request: HandlerRequest) -> HandlerResponse:
        """Handle secret menu activation."""
        # Delete user input message immediately
        await self.batch_cleanup_messages([request.update.message], strategy="instant")
        
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

    async def handle_buy_type_selection(self, request: HandlerRequest, selection: str) -> HandlerResponse:
        """Handle buy type selection (normal vs expedition)."""
        if selection == "buy_normal":
            request.user_data["expedition_mode"] = False
            return self.create_smart_response(
                message="🛒 **Compra Normal**\n\nEscolha o produto:",
                keyboard=self.create_products_keyboard(request, include_secret=False),
                interaction_type=InteractionType.MENU_NAVIGATION,
                content_type=ContentType.SELECTION,
                next_state=BUY_SELECT_PRODUCT
            )
        elif selection == "buy_expedition":
            return await self.show_expedition_selection(request)
        else:
            return self.create_smart_response(
                message="❌ Opção inválida. Escolha o tipo de compra:",
                keyboard=self.create_buy_type_keyboard(),
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.VALIDATION_ERROR,
                next_state=BUY_TYPE_SELECT
            )

    async def show_expedition_selection(self, request: HandlerRequest) -> HandlerResponse:
        """Show available expeditions for selection."""
        try:
            expedition_service = get_expedition_service(request.context)
            expeditions = expedition_service.get_expeditions(
                owner_chat_id=request.chat_id,
                status_filter=['planning', 'active']
            )

            if not expeditions:
                return self.create_smart_response(
                    message="🏴‍☠️ Nenhuma expedição ativa encontrada.\n\nCrie uma expedição primeiro usando /expedition",
                    keyboard=self.create_buy_type_keyboard(),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.INFO,
                    next_state=BUY_TYPE_SELECT
                )

            return self.create_smart_response(
                message="🏴‍☠️ **Compra para Expedição**\n\nEscolha a expedição:",
                keyboard=self.create_expedition_selection_keyboard(expeditions),
                interaction_type=InteractionType.MENU_NAVIGATION,
                content_type=ContentType.SELECTION,
                next_state=BUY_EXPEDITION_SELECT
            )

        except ServiceError as e:
            self.logger.error(f"Error loading expeditions: {e}")
            return self.create_smart_response(
                message="❌ Erro ao carregar expedições. Tente novamente.",
                keyboard=self.create_buy_type_keyboard(),
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.ERROR,
                next_state=BUY_TYPE_SELECT
            )

    async def handle_expedition_selection(self, request: HandlerRequest, expedition_id: int) -> HandlerResponse:
        """Handle expedition selection and setup expedition mode."""
        try:
            expedition_service = get_expedition_service(request.context)
            expedition = expedition_service.get_expedition_by_id(expedition_id)

            if not expedition:
                return self.create_smart_response(
                    message="❌ Expedição não encontrada.",
                    keyboard=self.create_buy_type_keyboard(),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.ERROR,
                    next_state=BUY_TYPE_SELECT
                )

            # Verify ownership
            if expedition.owner_chat_id != request.chat_id:
                return self.create_smart_response(
                    message="⛔ Você não tem permissão para usar esta expedição.",
                    keyboard=self.create_buy_type_keyboard(),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.ERROR,
                    next_state=BUY_TYPE_SELECT
                )

            # Set expedition mode
            request.user_data["expedition_mode"] = True
            request.user_data["expedition_id"] = expedition_id
            request.user_data["expedition_name"] = expedition.name

            return self.create_smart_response(
                message=f"🏴‍☠️ **Expedição: {expedition.name}**\n\nEscolha o produto para a expedição:",
                keyboard=self.create_products_keyboard(request, include_secret=False),
                interaction_type=InteractionType.MENU_NAVIGATION,
                content_type=ContentType.SELECTION,
                next_state=BUY_SELECT_PRODUCT
            )

        except ServiceError as e:
            self.logger.error(f"Error selecting expedition: {e}")
            return self.create_smart_response(
                message="❌ Erro ao selecionar expedição. Tente novamente.",
                keyboard=self.create_buy_type_keyboard(),
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.ERROR,
                next_state=BUY_TYPE_SELECT
            )

    def _get_status_emoji(self, status: str) -> str:
        """Get emoji for expedition status."""
        status_emojis = {
            "planning": "📋",
            "active": "🏴‍☠️",
            "completed": "✅",
            "failed": "💀",
            "cancelled": "❌"
        }
        return status_emojis.get(status, "🏴‍☠️")

    async def finalize_purchase(self, request: HandlerRequest) -> HandlerResponse:
        """Finalize the purchase with expedition integration."""
        buyer_name = request.user_data.get("nome_comprador")
        items = request.user_data.get("itens_venda", [])
        expedition_mode = request.user_data.get("expedition_mode", False)
        expedition_id = request.user_data.get("expedition_id")

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

        # Create purchase request with expedition support
        purchase_request = PurchaseRequest(
            buyer_name=buyer_name,
            items=purchase_items,
            total_amount=total_amount,
            chat_id=request.chat_id,
            expedition_id=expedition_id if expedition_mode else None
        )

        # Process purchase through business service
        business_service = self.ensure_services_initialized()
        response = business_service.process_purchase(purchase_request)

        if response.success:
            success_message = "✅ Compra finalizada e estoque atualizado!"

            if expedition_mode:
                expedition_name = request.user_data.get("expedition_name", "N/A")
                success_message += f"\n🏴‍☠️ Itens registrados na expedição: {expedition_name}"

                # Record item consumption for expedition
                try:
                    await self._record_expedition_consumption(request, purchase_items)
                    success_message += "\n📦 Consumo registrado na expedição!"
                except Exception as e:
                    self.logger.error(f"Error recording expedition consumption: {e}")
                    success_message += "\n⚠️ Erro ao registrar consumo na expedição."

            return HandlerResponse(
                message=success_message,
                keyboard=None,
                end_conversation=True,
                delay=DelayConstants.SUCCESS
            )
        else:
            error_message = response.message
            if response.warnings:
                error_message += "\n\n" + "\n".join(response.warnings)

            return HandlerResponse(
                message=error_message,
                keyboard=None,
                end_conversation=True,
                delay=DelayConstants.ERROR
            )

    async def _record_expedition_consumption(self, request: HandlerRequest, purchase_items: list):
        """Record item consumption for expedition."""
        try:
            expedition_service = get_expedition_service(request.context)
            expedition_id = request.user_data.get("expedition_id")

            for item in purchase_items:
                consumption_data = {
                    "expedition_id": expedition_id,
                    "product_id": item.product_id,
                    "quantity_consumed": item.quantity,
                    "consumed_by_chat_id": request.chat_id,
                    "consumption_date": None  # Service will set current timestamp
                }

                expedition_service.consume_item(consumption_data)

        except ServiceError as e:
            self.logger.error(f"Failed to record expedition consumption: {e}")
            raise
    
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
    
    @with_error_boundary("buy_type_select")
    async def buy_type_select(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        request = self.create_request(update, context)
        response = await self.handle_buy_type_selection(request, query.data)
        return await self.send_response(response, request)

    @with_error_boundary("buy_expedition_select")
    async def buy_expedition_select(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        request = self.create_request(update, context)

        if query.data == "buy_back":
            # Return to buy type selection
            response = self.create_smart_response(
                message="**Tipo de Compra**\nEscolha o tipo:",
                keyboard=self.create_buy_type_keyboard(),
                interaction_type=InteractionType.MENU_NAVIGATION,
                content_type=ContentType.SELECTION,
                next_state=BUY_TYPE_SELECT
            )
        elif query.data.startswith("buy_exp_select:"):
            expedition_id = int(query.data.split(":")[1])
            response = await self.handle_expedition_selection(request, expedition_id)
        else:
            response = await self.show_expedition_selection(request)

        return await self.send_response(response, request)

    @with_error_boundary("buy_select")
    async def buy_select_product(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        # Don't delete the product menu immediately - let it persist for better UX
        # Only delete when finalizing or canceling the purchase

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
            keyboard=None,
            end_conversation=True,
            delay=DelayConstants.INFO  # Auto-delete cancel message after 10 seconds
        )
        return await self.send_response(response, request)
    
    def get_conversation_handler(self) -> ConversationHandler:
        """Create the conversation handler with expedition support."""
        return ConversationHandler(
            entry_points=[CommandHandler("buy", self.start_buy)],
            states={
                BUY_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.buy_set_name)
                ],
                BUY_TYPE_SELECT: [
                    CallbackQueryHandler(self.buy_type_select, pattern="^(buy_normal|buy_expedition|buy_cancelar)$"),
                ],
                BUY_EXPEDITION_SELECT: [
                    CallbackQueryHandler(self.buy_expedition_select, pattern="^(buy_back|buy_cancelar)$"),
                    CallbackQueryHandler(self.buy_expedition_select, pattern=r"^buy_exp_select:\d+$"),
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