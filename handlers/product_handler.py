from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message
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
from models.product import CreateProductRequest, UpdateProductRequest
from core.modern_service_container import get_product_service, get_context
from utils.input_sanitizer import InputSanitizer
from services.base_service import ValidationError, DuplicateError
from utils.permissions import require_permission
from utils.product_list_generator import create_simple_product_keyboard


# States
(PRODUCT_MENU, 
 PRODUCT_ADD_NAME, PRODUCT_ADD_EMOJI, PRODUCT_ADD_MEDIA_CONFIRM, PRODUCT_ADD_MEDIA,
 PRODUCT_EDIT_SELECT, PRODUCT_EDIT_PROPERTY, PRODUCT_EDIT_NEW_VALUE) = range(8)


class ModernProductHandler(MenuHandlerBase):
    def __init__(self):
        super().__init__("product")
    
    def create_main_menu_keyboard(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("➕ Inserir Produto", callback_data="add_product"),
                InlineKeyboardButton("✏️ Editar Produto", callback_data="edit_product"),
            ],
            [
                InlineKeyboardButton("🚫 Cancelar", callback_data="cancel")
            ],
        ])
    
    def get_menu_text(self) -> str:
        return "📦 O que deseja fazer?"
    
    def get_menu_state(self) -> int:
        return PRODUCT_MENU
    
    async def handle_menu_selection(self, request: HandlerRequest, selection: str) -> HandlerResponse:
        if selection == "add_product":
            return HandlerResponse(
                message="📝 Envie o nome do produto:",
                next_state=PRODUCT_ADD_NAME,
                edit_message=True
            )
        elif selection == "edit_product":
            return await self._start_edit_product(request)
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
                next_state=PRODUCT_MENU,
                edit_message=True
            )
    
    async def handle(self, request: HandlerRequest) -> HandlerResponse:
        """Handle initial product command - show main menu."""
        return await self.show_main_menu(request)
    
    async def handle_add_name(self, request: HandlerRequest) -> HandlerResponse:
        """Handle product name input."""
        try:
            name = InputSanitizer.sanitize_product_name(request.update.message.text)
            product_service = get_product_service(request.context)
            
            if product_service.product_name_exists(name):
                return HandlerResponse(
                    message="❌ Já existe um produto com esse nome. Por favor, envie outro nome:",
                    next_state=PRODUCT_ADD_NAME,
                    edit_message=True
                )
            
            request.user_data["product_name"] = name
            
            return HandlerResponse(
                message="😊 Agora envie o emoji para este produto:",
                next_state=PRODUCT_ADD_EMOJI
            )
            
        except ValueError as e:
            return HandlerResponse(
                message=f"❌ {str(e)}\n\nEnvie um nome válido:",
                next_state=PRODUCT_ADD_NAME,
                edit_message=True
            )
    
    async def handle_add_emoji(self, request: HandlerRequest) -> HandlerResponse:
        """Handle product emoji input."""
        try:
            emoji = InputSanitizer.sanitize_emoji(request.update.message.text)
            request.user_data["product_emoji"] = emoji
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📷 Sim", callback_data="add_media_yes"),
                    InlineKeyboardButton("❌ Não", callback_data="add_media_no")
                ]
            ])
            
            return HandlerResponse(
                message="Deseja adicionar uma mídia ao produto?",
                keyboard=keyboard,
                next_state=PRODUCT_ADD_MEDIA_CONFIRM,
                protected=False
            )
            
        except ValueError as e:
            return HandlerResponse(
                message=f"❌ {str(e)}\n\nEnvie um emoji válido:",
                next_state=PRODUCT_ADD_EMOJI,
                edit_message=True
            )
    
    async def handle_media_confirm(self, request: HandlerRequest) -> HandlerResponse:
        """Handle media confirmation."""
        query = request.update.callback_query
        await query.answer()
        
        if query.data == "add_media_yes":
            return HandlerResponse(
                message="📥 Envie a mídia (foto, vídeo ou documento):",
                next_state=PRODUCT_ADD_MEDIA,
                edit_message=True
            )
        elif query.data == "add_media_no":
            return await self._create_product_without_media(request)
        else:
            return HandlerResponse(
                message="❌ Opção inválida.",
                end_conversation=True,
                edit_message=True
            )
    
    async def handle_media_upload(self, request: HandlerRequest) -> HandlerResponse:
        """Handle media file upload."""
        message: Message = request.update.message
        file_id = None
        
        if message.photo:
            file_id = message.photo[-1].file_id
        elif message.document:
            file_id = message.document.file_id
        elif message.video:
            file_id = message.video.file_id
        
        if not file_id:
            return HandlerResponse(
                message="❌ Mídia inválida. Envie uma foto, vídeo ou documento.",
                next_state=PRODUCT_ADD_MEDIA,
                edit_message=True
            )
        
        return await self._create_product_with_media(request, file_id)
    
    async def _create_product_without_media(self, request: HandlerRequest) -> HandlerResponse:
        """Create product without media."""
        try:
            product_service = get_product_service(request.context)
            product_request = CreateProductRequest(
                nome=request.user_data["product_name"],
                emoji=request.user_data["product_emoji"],
                media_file_id=None
            )
            
            product = product_service.create_product(product_request)
            
            return HandlerResponse(
                message="✅ Produto adicionado com sucesso sem mídia.",
                end_conversation=True
            )
            
        except (ValidationError, DuplicateError) as e:
            return HandlerResponse(
                message=f"❌ {str(e)}",
                end_conversation=True
            )
    
    async def _create_product_with_media(self, request: HandlerRequest, file_id: str) -> HandlerResponse:
        """Create product with media."""
        try:
            product_service = get_product_service(request.context)
            product_request = CreateProductRequest(
                nome=request.user_data["product_name"],
                emoji=request.user_data["product_emoji"],
                media_file_id=file_id
            )
            
            product = product_service.create_product(product_request)
            
            # Mark media as protected
            message = request.update.message
            protected_messages = request.context.chat_data.setdefault("protected_messages", set())
            protected_messages.add(message.message_id)
            
            return HandlerResponse(
                message="✅ Produto adicionado com sucesso com mídia.",
                end_conversation=True
            )
            
        except (ValidationError, DuplicateError) as e:
            return HandlerResponse(
                message=f"❌ {str(e)}",
                end_conversation=True
            )
    
    async def _start_edit_product(self, request: HandlerRequest) -> HandlerResponse:
        """Start product editing process."""
        product_service = get_product_service(request.context)
        products = product_service.get_all_products()
        
        if not products:
            return HandlerResponse(
                message="🚫 Nenhum produto cadastrado.",
                end_conversation=True
            )
        
        keyboard = self._create_products_keyboard("edit_product", products)
        
        return HandlerResponse(
            message="👀 Escolha o produto que deseja editar:",
            keyboard=keyboard,
            next_state=PRODUCT_EDIT_SELECT,
            edit_message=True
        )
    
    def _create_products_keyboard(self, prefix: str, products) -> InlineKeyboardMarkup:
        """Create keyboard with product list using the utility method."""
        return create_simple_product_keyboard(
            products=products,
            callback_prefix=prefix,
            include_secret=True,  # For product management, show all products including secret ones
            include_actions=True
        )
    
    # Wrapper methods for conversation handler
    @require_permission("owner")
    @with_error_boundary("product_start")
    async def start_product(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return await self.safe_handle(self.handle, update, context)
    
    @with_error_boundary("product_menu")
    async def product_menu_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        request = self.create_request(update, context)
        response = await self.handle_menu_selection(request, query.data)
        return await self.send_response(response, request)
    
    @with_error_boundary("product_add_name")
    async def product_add_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        request = self.create_request(update, context)
        response = await self.handle_add_name(request)
        return await self.send_response(response, request)
    
    @with_error_boundary("product_add_emoji")
    async def product_add_emoji(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        request = self.create_request(update, context)
        response = await self.handle_add_emoji(request)
        return await self.send_response(response, request)
    
    @with_error_boundary("product_media_confirm")
    async def product_media_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        request = self.create_request(update, context)
        response = await self.handle_media_confirm(request)
        return await self.send_response(response, request)
    
    @with_error_boundary("product_media_upload")
    async def product_receive_media(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        request = self.create_request(update, context)
        response = await self.handle_media_upload(request)
        return await self.send_response(response, request)
    
    @with_error_boundary("product_edit_select")
    async def product_edit_select(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle product selection for editing."""
        query = update.callback_query
        await query.answer()
        
        if query.data == "cancel":
            request = self.create_request(update, context)
            response = HandlerResponse(
                message="🚫 Operação cancelada.",
                end_conversation=True
            )
            return await self.send_response(response, request)
        
        if query.data.startswith("edit_product:"):
            product_id = int(query.data.split(":")[1])
            context.user_data["editing_product_id"] = product_id
            
            # Show edit options
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📝 Nome", callback_data="edit_name"),
                    InlineKeyboardButton("😊 Emoji", callback_data="edit_emoji")
                ],
                [
                    InlineKeyboardButton("📷 Mídia", callback_data="edit_media"),
                    InlineKeyboardButton("🗑️ Remover Produto", callback_data="delete_product")
                ],
                [
                    InlineKeyboardButton("🚫 Cancelar", callback_data="cancel")
                ]
            ])
            
            request = self.create_request(update, context)
            response = HandlerResponse(
                message="✏️ O que deseja editar?",
                keyboard=keyboard,
                next_state=PRODUCT_EDIT_PROPERTY,
                edit_message=True
            )
            return await self.send_response(response, request)
        
        # Invalid selection
        request = self.create_request(update, context)
        response = HandlerResponse(
            message="❌ Seleção inválida.",
            end_conversation=True
        )
        return await self.send_response(response, request)
    
    @with_error_boundary("product_edit_property")
    async def product_edit_property(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle edit property selection."""
        query = update.callback_query
        await query.answer()
        
        if query.data == "cancel":
            request = self.create_request(update, context)
            response = HandlerResponse(
                message="🚫 Operação cancelada.",
                end_conversation=True
            )
            return await self.send_response(response, request)
        
        context.user_data["edit_property"] = query.data
        
        request = self.create_request(update, context)
        
        if query.data == "edit_name":
            response = HandlerResponse(
                message="📝 Envie o novo nome do produto:",
                next_state=PRODUCT_EDIT_NEW_VALUE,
                edit_message=True
            )
        elif query.data == "edit_emoji":
            response = HandlerResponse(
                message="😊 Envie o novo emoji do produto:",
                next_state=PRODUCT_EDIT_NEW_VALUE,
                edit_message=True
            )
        elif query.data == "edit_media":
            response = HandlerResponse(
                message="📷 Envie a nova mídia do produto (foto, vídeo ou documento):",
                next_state=PRODUCT_EDIT_NEW_VALUE,
                edit_message=True
            )
        elif query.data == "delete_product":
            # Delete product immediately
            return await self._delete_product(request)
        else:
            response = HandlerResponse(
                message="❌ Opção inválida.",
                end_conversation=True
            )
        
        return await self.send_response(response, request)
    
    @with_error_boundary("product_edit_new_value")
    async def product_edit_new_value(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle new value input for editing."""
        request = self.create_request(update, context)
        edit_property = context.user_data.get("edit_property")
        product_id = context.user_data.get("editing_product_id")
        
        if not edit_property or not product_id:
            response = HandlerResponse(
                message="❌ Erro no processo de edição.",
                end_conversation=True
            )
            return await self.send_response(response, request)
        
        try:
            product_service = get_product_service(request.context)
            
            if edit_property == "edit_name":
                new_name = InputSanitizer.sanitize_product_name(update.message.text)
                if product_service.product_name_exists(new_name, exclude_product_id=product_id):
                    response = HandlerResponse(
                        message="❌ Já existe um produto com esse nome. Envie outro nome:",
                        next_state=PRODUCT_EDIT_NEW_VALUE,
                        edit_message=True
                    )
                    return await self.send_response(response, request)
                
                update_request = UpdateProductRequest(product_id=product_id, nome=new_name)
                product_service.update_product(update_request)
                response = HandlerResponse(
                    message="✅ Nome do produto atualizado com sucesso!",
                    end_conversation=True
                )
                
            elif edit_property == "edit_emoji":
                new_emoji = InputSanitizer.sanitize_emoji(update.message.text)
                update_request = UpdateProductRequest(product_id=product_id, emoji=new_emoji)
                product_service.update_product(update_request)
                response = HandlerResponse(
                    message="✅ Emoji do produto atualizado com sucesso!",
                    end_conversation=True
                )
                
            elif edit_property == "edit_media":
                message = update.message
                file_id = None
                
                if message.photo:
                    file_id = message.photo[-1].file_id
                elif message.document:
                    file_id = message.document.file_id
                elif message.video:
                    file_id = message.video.file_id
                
                if not file_id:
                    response = HandlerResponse(
                        message="❌ Mídia inválida. Envie uma foto, vídeo ou documento:",
                        next_state=PRODUCT_EDIT_NEW_VALUE,
                        edit_message=True
                    )
                    return await self.send_response(response, request)
                
                update_request = UpdateProductRequest(product_id=product_id, media_file_id=file_id)
                product_service.update_product(update_request)
                
                # Mark new media as protected
                protected_messages = request.context.chat_data.setdefault("protected_messages", set())
                protected_messages.add(message.message_id)
                
                response = HandlerResponse(
                    message="✅ Mídia do produto atualizada com sucesso!",
                    end_conversation=True
                )
            else:
                response = HandlerResponse(
                    message="❌ Propriedade inválida.",
                    end_conversation=True
                )
            
        except ValueError as e:
            response = HandlerResponse(
                message=f"❌ {str(e)}\n\nTente novamente:",
                next_state=PRODUCT_EDIT_NEW_VALUE,
                edit_message=True
            )
        except Exception as e:
            response = HandlerResponse(
                message=f"❌ Erro ao atualizar produto: {str(e)}",
                end_conversation=True
            )
        
        return await self.send_response(response, request)
    
    async def _delete_product(self, request: HandlerRequest) -> int:
        """Delete a product."""
        try:
            product_id = request.context.user_data.get("editing_product_id")
            if not product_id:
                response = HandlerResponse(
                    message="❌ Produto não encontrado.",
                    end_conversation=True
                )
                return await self.send_response(response, request)
            
            product_service = get_product_service(request.context)
            product_service.delete_product(product_id)
            
            response = HandlerResponse(
                message="🗑️ Produto removido com sucesso!",
                end_conversation=True
            )
            return await self.send_response(response, request)
            
        except Exception as e:
            response = HandlerResponse(
                message=f"❌ Erro ao remover produto: {str(e)}",
                end_conversation=True
            )
            return await self.send_response(response, request)
    
    @with_error_boundary("product_cancel")
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
            entry_points=[CommandHandler("product", self.start_product)],
            states={
                PRODUCT_MENU: [
                    CallbackQueryHandler(self.product_menu_selection)
                ],
                PRODUCT_ADD_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.product_add_name)
                ],
                PRODUCT_ADD_EMOJI: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.product_add_emoji)
                ],
                PRODUCT_ADD_MEDIA_CONFIRM: [
                    CallbackQueryHandler(self.product_media_confirm)
                ],
                PRODUCT_ADD_MEDIA: [
                    MessageHandler(filters.ALL & ~filters.COMMAND, self.product_receive_media)
                ],
                PRODUCT_EDIT_SELECT: [
                    CallbackQueryHandler(self.product_edit_select)
                ],
                PRODUCT_EDIT_PROPERTY: [
                    CallbackQueryHandler(self.product_edit_property)
                ],
                PRODUCT_EDIT_NEW_VALUE: [
                    MessageHandler(filters.ALL & ~filters.COMMAND, self.product_edit_new_value)
                ]
            },
            fallbacks=[
                CommandHandler("cancel", self.cancel),
                CallbackQueryHandler(self.cancel, pattern="^cancel$")
            ],
            allow_reentry=True
        )


# Factory function
def get_modern_product_handler():
    """Get the modern product conversation handler."""
    handler = ModernProductHandler()
    return handler.get_conversation_handler()