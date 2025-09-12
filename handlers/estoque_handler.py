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
from models.handler_models import InventoryAddRequest, InventoryResponse
from services.handler_business_service import HandlerBusinessService
from core.modern_service_container import get_context, get_product_service
from utils.input_sanitizer import InputSanitizer
from utils.permissions import require_permission
from utils.product_list_generator import ProductListGenerator, ProductListFormat
from services.base_service import ValidationError


# States
ESTOQUE_MENU, ESTOQUE_ADD_SELECT, ESTOQUE_ADD_VALUES, ESTOQUE_VIEW = range(4)


class ModernEstoqueHandler(MenuHandlerBase):
    def __init__(self):
        super().__init__("estoque")
    
    def create_main_menu_keyboard(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("➕ Adicionar ao estoque", callback_data="add_estoque"),
                InlineKeyboardButton("📦 Verificar estoque", callback_data="verificar_estoque")
            ],
            [
                InlineKeyboardButton("🚫 Cancelar", callback_data="cancel")
            ]
        ])
    
    def get_menu_text(self) -> str:
        return "📦 O que deseja fazer?"
    
    def get_menu_state(self) -> int:
        return ESTOQUE_MENU
    
    def create_products_keyboard(self, request: HandlerRequest, action_prefix: str) -> InlineKeyboardMarkup:
        """Create keyboard with products list using the utility method."""
        try:
            self.logger.info(f"Creating products keyboard with action_prefix: {action_prefix}")
            product_service = get_product_service(request.context)
            self.logger.info("Product service obtained successfully")
            
            products_with_stock = product_service.get_products_with_stock()
            self.logger.info(f"Found {len(products_with_stock)} products with stock")
            
            # Use the utility to generate keyboard (include secret products for inventory management)
            keyboard = ProductListGenerator.generate_product_list(
                products=products_with_stock,
                format_type=ProductListFormat.KEYBOARD,
                user_level="owner",  # Show stock quantities
                callback_prefix=action_prefix,
                include_actions=True
            )
            
            self.logger.info(f"Products keyboard created using utility")
            return keyboard
            
        except Exception as e:
            self.logger.error(f"Error creating products keyboard: {e}", exc_info=True)
            raise
    
    async def handle_menu_selection(self, request: HandlerRequest, selection: str) -> HandlerResponse:
        """Handle main menu selections."""
        if selection == "add_estoque":
            return HandlerResponse(
                message="📦 Escolha o produto para adicionar estoque:",
                keyboard=self.create_products_keyboard(request, "add_stock"),
                next_state=ESTOQUE_ADD_SELECT,
                edit_message=True
            )
        elif selection == "verificar_estoque":
            return await self.show_stock_info(request)
        elif selection == "cancel":
            return HandlerResponse(
                message="🚫 Operação cancelada.",
                end_conversation=True,
                edit_message=True
            )
        else:
            return HandlerResponse(
                message="❌ Opção inválida.",
                keyboard=self.create_main_menu_keyboard(),
                next_state=ESTOQUE_MENU,
                edit_message=True
            )
    
    async def handle(self, request: HandlerRequest) -> HandlerResponse:
        """Handle initial estoque command - show main menu."""
        return await self.show_main_menu(request)
    
    async def handle_product_selection(self, request: HandlerRequest, product_id: int) -> HandlerResponse:
        """Handle product selection for stock addition."""
        product_service = get_product_service(request.context)
        product = product_service.get_product_by_id(product_id)
        
        if not product:
            return HandlerResponse(
                message="❌ Produto não encontrado.",
                end_conversation=True
            )
        
        request.user_data["selected_product_id"] = product_id
        request.user_data["selected_product_name"] = product.nome
        
        return HandlerResponse(
            message=f"📦 Adicionando estoque para: {product.emoji} {product.nome}\n\n"
                   f"Envie os valores no formato:\n"
                   f"**quantidade / preço / custo**\n\n"
                   f"Exemplo: `10 / 5.50 / 3.00`",
            next_state=ESTOQUE_ADD_VALUES,
            edit_message=True
        )
    
    async def handle_stock_values(self, request: HandlerRequest) -> HandlerResponse:
        """Handle stock values input (quantity/price/cost)."""
        try:
            text = request.update.message.text.strip()
            self.logger.info(f"Processing stock values input: {text}")
            
            # Parse format: quantity / price / cost
            parts = [part.strip() for part in text.split('/')]
            
            if len(parts) != 3:
                return HandlerResponse(
                    message="❌ Formato inválido. Use: `quantidade / preço / custo`\n"
                           "Exemplo: `10 / 5.50 / 3.00`",
                    next_state=ESTOQUE_ADD_VALUES
                )
            
            quantity = InputSanitizer.sanitize_quantity(parts[0])
            unit_price = InputSanitizer.sanitize_price(parts[1])
            unit_cost = InputSanitizer.sanitize_price(parts[2])
            
            product_id = request.user_data["selected_product_id"]
            self.logger.info(f"Adding stock: product_id={product_id}, quantity={quantity}, unit_price={unit_price}, unit_cost={unit_cost}")
            
            # Add stock through business service
            try:
                business_service = self.ensure_services_initialized()
                self.logger.info("Business service initialized successfully")
                
                inventory_request = InventoryAddRequest(
                    product_id=product_id,
                    quantity=quantity,
                    unit_price=unit_price,
                    unit_cost=unit_cost
                )
                
                self.logger.info("Calling business_service.add_inventory...")
                response = business_service.add_inventory(inventory_request)
                self.logger.info(f"add_inventory successful: {response.message}")
                
                # Continue adding more stock to same or different products
                return HandlerResponse(
                    message=f"{response.message}\n\n📦 Deseja adicionar mais estoque?",
                    keyboard=self.create_main_menu_keyboard(),
                    next_state=ESTOQUE_MENU
                )
                
            except Exception as service_error:
                self.logger.error(f"Service error in add_inventory: {service_error}", exc_info=True)
                raise
            
        except ValueError as e:
            self.logger.error(f"Value error in handle_stock_values: {e}")
            return HandlerResponse(
                message=f"❌ {str(e)}\n\nTente novamente no formato: `quantidade / preço / custo`",
                next_state=ESTOQUE_ADD_VALUES
            )
        except Exception as e:
            self.logger.error(f"Unexpected error in handle_stock_values: {e}", exc_info=True)
            raise
    
    async def show_stock_info(self, request: HandlerRequest) -> HandlerResponse:
        """Show current stock information for all products."""
        try:
            product_service = get_product_service(request.context)
            products_with_stock = product_service.get_products_with_stock()
            
            if not products_with_stock:
                return HandlerResponse(
                    message="📦 Nenhum produto com estoque encontrado.",
                    end_conversation=True
                )
            
            # Use the utility to generate table with detailed stock info (include secret products for inventory)
            stock_text = ProductListGenerator.generate_product_list(
                products=products_with_stock,
                format_type=ProductListFormat.TABLE,
                user_level="owner"  # Show detailed stock info in table format
            )
            
            message = f"📦 <b>Estoque Atual:</b>\n\n{stock_text}"
            
            return HandlerResponse(
                message=message,
                keyboard=self.create_main_menu_keyboard(),
                next_state=ESTOQUE_MENU,
                edit_message=True,
                parse_mode="HTML"
            )
            
        except Exception as e:
            return HandlerResponse(
                message="❌ Erro ao carregar informações de estoque.",
                end_conversation=True
            )
    
    # Wrapper methods for conversation handler
    @require_permission("admin")
    @with_error_boundary("estoque_start")
    async def start_estoque(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.logger.info(f"start_estoque called for user {update.effective_user.id} in chat {update.effective_chat.id}")
        try:
            return await self.safe_handle(self.handle, update, context)
        except Exception as e:
            self.logger.error(f"Error in start_estoque: {e}", exc_info=True)
            raise
    
    @with_error_boundary("estoque_menu")
    async def estoque_menu_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        # Delete menu message using safe deletion
        await self.safe_delete_message(query)
        
        request = self.create_request(update, context)
        response = await self.handle_menu_selection(request, query.data)
        return await self.send_response(response, request)
    
    @with_error_boundary("estoque_select")
    async def estoque_select_product(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        product_id = int(query.data.split(":")[1])
        
        # Use safe deletion method
        await self.safe_delete_message(query)
        
        request = self.create_request(update, context)
        response = await self.handle_product_selection(request, product_id)
        return await self.send_response(response, request)
    
    @with_error_boundary("estoque_values")
    async def estoque_add_values(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        request = self.create_request(update, context)
        response = await self.handle_stock_values(request)
        return await self.send_response(response, request)
    
    @with_error_boundary("estoque_cancel")
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        request = self.create_request(update, context)
        response = HandlerResponse(
            message="🚫 Operação cancelada.",
            end_conversation=True
        )
        return await self.send_response(response, request)
    
    def get_conversation_handler(self) -> ConversationHandler:
        """Create the conversation handler."""
        return ConversationHandler(
            entry_points=[CommandHandler("estoque", self.start_estoque)],
            states={
                ESTOQUE_MENU: [
                    CallbackQueryHandler(self.estoque_menu_selection)
                ],
                ESTOQUE_ADD_SELECT: [
                    CallbackQueryHandler(self.estoque_select_product, pattern="^add_stock:")
                ],
                ESTOQUE_ADD_VALUES: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.estoque_add_values)
                ],
            },
            fallbacks=[
                CommandHandler("cancel", self.cancel),
                CallbackQueryHandler(self.cancel, pattern="^cancel$")
            ],
            allow_reentry=True
        )


# Factory function
def get_modern_estoque_handler():
    """Get the modern estoque conversation handler."""
    handler = ModernEstoqueHandler()
    return handler.get_conversation_handler()