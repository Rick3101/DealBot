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
from models.handler_models import UserManagementRequest, UserManagementResponse
from models.user import UserLevel
from services.handler_business_service import HandlerBusinessService
from core.modern_service_container import get_context, get_user_service
from utils.input_sanitizer import InputSanitizer
from utils.permissions import require_permission
from services.base_service import ValidationError


# States
(USER_MENU, USER_ADD_USERNAME, USER_ADD_PASSWORD, 
 USER_REMOVE_SELECT, USER_EDIT_SELECT, USER_EDIT_PROPERTY, USER_EDIT_VALUE) = range(7)


class ModernUserHandler(MenuHandlerBase):
    def __init__(self):
        super().__init__("user")
    
    def create_main_menu_keyboard(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("➕ Adicionar", callback_data="add_user"),
                InlineKeyboardButton("➖ Remover", callback_data="remove_user"),
            ],
            [
                InlineKeyboardButton("✏️ Editar", callback_data="edit_user"),
            ],
            [
                InlineKeyboardButton("🚫 Cancelar", callback_data="cancel"),
            ],
        ])
    
    def get_menu_text(self) -> str:
        return "👤 O que deseja fazer?"
    
    def get_menu_state(self) -> int:
        return USER_MENU
    
    def create_users_keyboard(self, action_prefix: str) -> InlineKeyboardMarkup:
        """Create keyboard with user list."""
        user_service = self.ensure_user_service_initialized(self._current_context)
        users = user_service.get_all_users()
        
        keyboard = []
        for user in users:
            keyboard.append([
                InlineKeyboardButton(
                    f"{user.username} ({user.level.value})", 
                    callback_data=f"{action_prefix}:{user.id}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("🚫 Cancelar", callback_data="cancel")])
        return InlineKeyboardMarkup(keyboard)
    
    def create_edit_properties_keyboard(self) -> InlineKeyboardMarkup:
        """Create keyboard for editing user properties."""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📝 Nome", callback_data="edit_username"),
                InlineKeyboardButton("🔒 Senha", callback_data="edit_password"),
            ],
            [
                InlineKeyboardButton("🎭 Nível", callback_data="edit_level"),
            ],
            [
                InlineKeyboardButton("🚫 Cancelar", callback_data="cancel")
            ]
        ])
    
    def create_level_keyboard(self) -> InlineKeyboardMarkup:
        """Create keyboard for selecting user level."""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("👤 User", callback_data="level_user"),
                InlineKeyboardButton("👮 Admin", callback_data="level_admin"),
            ],
            [
                InlineKeyboardButton("👑 Owner", callback_data="level_owner"),
            ],
            [
                InlineKeyboardButton("🚫 Cancelar", callback_data="cancel")
            ]
        ])
    
    async def handle_menu_selection(self, request: HandlerRequest, selection: str) -> HandlerResponse:
        """Handle main menu selections."""
        self._current_context = request.context  # Store context for keyboard creation
        
        if selection == "add_user":
            return self.create_smart_response(
                message="🆕 Envie o nome de usuário que deseja adicionar:",
                keyboard=None,
                interaction_type=InteractionType.FORM_INPUT,
                content_type=ContentType.INFO,
                next_state=USER_ADD_USERNAME
            )
        elif selection == "remove_user":
            user_service = get_user_service(request.context)
            users = user_service.get_all_users()
            
            if not users:
                return self.create_smart_response(
                    message="🚫 Nenhum usuário encontrado.",
                    keyboard=None,
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.INFO,
                    end_conversation=True
                )
            
            return self.create_smart_response(
                message="👥 Escolha o usuário que deseja remover:",
                keyboard=self.create_users_keyboard("remove_user"),
                interaction_type=InteractionType.MENU_NAVIGATION,
                content_type=ContentType.SELECTION,
                next_state=USER_REMOVE_SELECT
            )
        elif selection == "edit_user":
            user_service = get_user_service(request.context)
            users = user_service.get_all_users()
            
            if not users:
                return self.create_smart_response(
                    message="🚫 Nenhum usuário encontrado.",
                    keyboard=None,
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.INFO,
                    end_conversation=True
                )
            
            return self.create_smart_response(
                message="👥 Escolha o usuário que deseja editar:",
                keyboard=self.create_users_keyboard("edit_user"),
                interaction_type=InteractionType.MENU_NAVIGATION,
                content_type=ContentType.SELECTION,
                next_state=USER_EDIT_SELECT
            )
        elif selection == "cancel":
            return self.create_smart_response(
                message="🚫 Operação cancelada.",
                keyboard=None,
                interaction_type=InteractionType.CONFIRMATION,
                content_type=ContentType.INFO,
                end_conversation=True
            )
        else:
            return self.create_smart_response(
                message="❌ Opção inválida.",
                keyboard=self.create_main_menu_keyboard(),
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.VALIDATION_ERROR,
                next_state=USER_MENU
            )
    
    async def handle(self, request: HandlerRequest) -> HandlerResponse:
        """Handle initial user command - show main menu."""
        return await self.show_main_menu(request)
    
    async def handle_add_username(self, request: HandlerRequest) -> HandlerResponse:
        """Handle username input for new user."""
        try:
            username = InputSanitizer.sanitize_username(request.update.message.text)
            
            # Check if username already exists
            user_service = get_user_service(request.context)
            if user_service.username_exists(username):
                return HandlerResponse(
                    message="❌ Este nome de usuário já existe. Escolha outro:",
                    next_state=USER_ADD_USERNAME,
                    edit_message=True
                )
            
            request.user_data["new_username"] = username
            
            return HandlerResponse(
                message="🔒 Agora envie a senha para este usuário:",
                next_state=USER_ADD_PASSWORD
            )
            
        except ValueError as e:
            return HandlerResponse(
                message=f"❌ {str(e)}\n\nEnvie um nome de usuário válido:",
                next_state=USER_ADD_USERNAME,
                edit_message=True
            )
    
    async def handle_add_password(self, request: HandlerRequest) -> HandlerResponse:
        """Handle password input and create user."""
        try:
            password = InputSanitizer.sanitize_password(request.update.message.text)
            username = request.user_data["new_username"]
            
            # Create user through business service
            business_service = self.ensure_services_initialized()
            user_request = UserManagementRequest(
                action="add",
                username=username,
                password=password,
                level=request.user_data.get("new_level", "user")  # Use level from user_data or default to user
            )
            
            response = business_service.manage_user(user_request)
            
            return HandlerResponse(
                message=response.message,
                end_conversation=True
            )
            
        except ValueError as e:
            return HandlerResponse(
                message=f"❌ {str(e)}\n\nEnvie uma senha válida:",
                next_state=USER_ADD_PASSWORD,
                edit_message=True
            )
    
    async def handle_remove_user(self, request: HandlerRequest, user_id: int) -> HandlerResponse:
        """Handle user removal."""
        try:
            user_service = get_user_service(request.context)
            user = user_service.get_user_by_id(user_id)
            
            if not user:
                return HandlerResponse(
                    message="❌ Usuário não encontrado.",
                    end_conversation=True
                )
            
            business_service = self.ensure_services_initialized()
            user_request = UserManagementRequest(
                action="remove",
                username=user.username,
                target_user_id=user_id
            )
            
            response = business_service.manage_user(user_request)
            
            return HandlerResponse(
                message=response.message,
                end_conversation=True
            )
            
        except Exception as e:
            return HandlerResponse(
                message="❌ Erro ao remover usuário.",
                end_conversation=True
            )
    
    async def handle_edit_user_select(self, request: HandlerRequest, user_id: int) -> HandlerResponse:
        """Handle user selection for editing."""
        user_service = get_user_service(request.context)
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            return HandlerResponse(
                message="❌ Usuário não encontrado.",
                end_conversation=True
            )
        
        request.user_data["edit_user_id"] = user_id
        request.user_data["edit_username"] = user.username
        
        return HandlerResponse(
            message=f"✏️ Editando usuário: {user.username}\nO que deseja alterar?",
            keyboard=self.create_edit_properties_keyboard(),
            next_state=USER_EDIT_PROPERTY,
            edit_message=True
        )
    
    async def handle_edit_property_selection(self, request: HandlerRequest, property_type: str) -> HandlerResponse:
        """Handle property selection for editing."""
        request.user_data["edit_property"] = property_type
        
        if property_type == "edit_username":
            return HandlerResponse(
                message="📝 Envie o novo nome de usuário:",
                next_state=USER_EDIT_VALUE,
                edit_message=True
            )
        elif property_type == "edit_password":
            return HandlerResponse(
                message="🔒 Envie a nova senha:",
                next_state=USER_EDIT_VALUE,
                edit_message=True
            )
        elif property_type == "edit_level":
            return HandlerResponse(
                message="🎭 Escolha o novo nível de acesso:",
                keyboard=self.create_level_keyboard(),
                next_state=USER_EDIT_VALUE,
                edit_message=True
            )
        else:
            return HandlerResponse(
                message="❌ Propriedade inválida.",
                end_conversation=True
            )
    
    async def handle_edit_value(self, request: HandlerRequest, new_value: str) -> HandlerResponse:
        """Handle new value input for editing."""
        property_type = request.user_data.get("edit_property")
        user_id = request.user_data.get("edit_user_id")  
        username = request.user_data.get("edit_username")
        
        try:
            business_service = self.ensure_services_initialized()
            
            if property_type == "edit_username":
                new_value = InputSanitizer.sanitize_username(new_value)
                user_request = UserManagementRequest(
                    action="edit",
                    username=new_value,
                    target_user_id=user_id
                )
            elif property_type == "edit_password":
                new_value = InputSanitizer.sanitize_password(new_value)
                user_request = UserManagementRequest(
                    action="edit",
                    username=username,
                    password=new_value,
                    target_user_id=user_id
                )
            elif property_type == "edit_level":
                level_map = {
                    "level_user": "user",
                    "level_admin": "admin", 
                    "level_owner": "owner"
                }
                level = level_map.get(new_value)
                if not level:
                    return HandlerResponse(
                        message="❌ Nível inválido.",
                        end_conversation=True,
                        edit_message=True
                    )
                
                user_request = UserManagementRequest(
                    action="edit",
                    username=username,
                    level=level,
                    target_user_id=user_id
                )
            else:
                return HandlerResponse(
                    message="❌ Tipo de edição inválido.",
                    end_conversation=True
                )
            
            response = business_service.manage_user(user_request)
            
            return HandlerResponse(
                message=response.message,
                end_conversation=True
            )
            
        except ValueError as e:
            return HandlerResponse(
                message=f"❌ {str(e)}\n\nTente novamente:",
                next_state=USER_EDIT_VALUE,
                edit_message=True
            )
    
    # Wrapper methods for conversation handler
    @require_permission("owner")
    @with_error_boundary("user_start")
    async def start_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return await self.safe_handle(self.handle, update, context)
    
    @with_error_boundary("user_menu")
    async def menu_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        # Use edit-in-place instead of deletion for better UX
        # Menu will be updated via edit_message=True in responses
        
        request = self.create_request(update, context)
        response = await self.handle_menu_selection(request, query.data)
        return await self.send_response(response, request)
    
    @with_error_boundary("user_add_username")
    async def add_username(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        request = self.create_request(update, context)
        response = await self.handle_add_username(request)
        return await self.send_response(response, request)
    
    @with_error_boundary("user_add_password")
    async def add_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        request = self.create_request(update, context)
        response = await self.handle_add_password(request)
        return await self.send_response(response, request)
    
    @with_error_boundary("user_remove")  
    async def remove_user_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        user_id = int(query.data.split(":")[1])
        
        # Use edit-in-place instead of deletion for better UX
        
        request = self.create_request(update, context)
        response = await self.handle_remove_user(request, user_id)
        return await self.send_response(response, request)
    
    @with_error_boundary("user_edit_select")
    async def edit_user_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        user_id = int(query.data.split(":")[1])
        
        # Use edit-in-place instead of deletion for better UX
        
        request = self.create_request(update, context)
        response = await self.handle_edit_user_select(request, user_id)
        return await self.send_response(response, request)
    
    @with_error_boundary("user_edit_property")
    async def edit_property_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        # Use edit-in-place instead of deletion for better UX
        
        request = self.create_request(update, context)
        response = await self.handle_edit_property_selection(request, query.data)
        return await self.send_response(response, request)
    
    @with_error_boundary("user_edit_value")
    async def edit_value_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        request = self.create_request(update, context)
        
        # Handle both text input and callback (for level selection)
        if update.callback_query:
            new_value = update.callback_query.data
            await update.callback_query.answer()
            try:
                await self.batch_cleanup_messages([update.callback_query], strategy="instant")
            except:
                pass
        else:
            new_value = update.message.text
        
        response = await self.handle_edit_value(request, new_value)
        return await self.send_response(response, request)
    
    @with_error_boundary("user_cancel")
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
            entry_points=[CommandHandler("user", self.start_user)],
            states={
                USER_MENU: [
                    CallbackQueryHandler(self.menu_selection)
                ],
                USER_ADD_USERNAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.add_username)
                ],
                USER_ADD_PASSWORD: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.add_password)
                ],
                USER_REMOVE_SELECT: [
                    CallbackQueryHandler(self.remove_user_callback, pattern="^remove_user:")
                ],
                USER_EDIT_SELECT: [
                    CallbackQueryHandler(self.edit_user_callback, pattern="^edit_user:")
                ],
                USER_EDIT_PROPERTY: [
                    CallbackQueryHandler(self.edit_property_callback, pattern="^edit_")
                ],
                USER_EDIT_VALUE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.edit_value_input),
                    CallbackQueryHandler(self.edit_value_input, pattern="^level_")
                ],
            },
            fallbacks=[
                CommandHandler("cancel", self.cancel),
                CallbackQueryHandler(self.cancel, pattern="^cancel$")
            ],
            allow_reentry=True
        )


# Factory function
def get_modern_user_handler():
    """Get the modern user conversation handler.""" 
    handler = ModernUserHandler()
    return handler.get_conversation_handler()