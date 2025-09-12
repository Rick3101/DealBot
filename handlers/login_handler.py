from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)
from handlers.base_handler import FormHandlerBase, HandlerRequest, HandlerResponse, InteractionType, ContentType
from handlers.error_handler import with_error_boundary
from models.handler_models import LoginRequest, ValidationResult
from services.handler_business_service import HandlerBusinessService
from core.modern_service_container import get_context
from utils.input_sanitizer import InputSanitizer
from services.base_service import ValidationError
import asyncio


# States
LOGIN_USERNAME, LOGIN_PASSWORD = range(2)


class ModernLoginHandler(FormHandlerBase):
    def __init__(self):
        super().__init__("login")
        self.form_fields = ["username", "password"]
    
    def get_form_fields(self) -> list:
        return self.form_fields
    
    async def process_form_data(self, request: HandlerRequest, form_data: dict) -> HandlerResponse:
        """Process complete login form data."""
        try:
            business_service = HandlerBusinessService()
        except RuntimeError as e:
            if "not initialized" in str(e):
                # Try to initialize services if they haven't been initialized yet
                try:
                    from core.modern_service_container import initialize_services
                    from database import initialize_database
                    from database.schema import initialize_schema
                    
                    initialize_database()
                    initialize_schema()
                    initialize_services({})
                    
                    business_service = HandlerBusinessService()
                except Exception as init_error:
                    self.logger.error(f"Failed to initialize services: {init_error}")
                    return self.create_smart_response(
                        message="❌ Erro de inicialização do sistema. Tente novamente em alguns momentos.",
                        keyboard=None,
                        interaction_type=InteractionType.ERROR_DISPLAY,
                        content_type=ContentType.ERROR,
                        end_conversation=True
                    )
            else:
                raise
        
        login_request = LoginRequest(
            username=form_data["username"],
            password=form_data["password"],
            chat_id=request.chat_id
        )
        
        response = business_service.process_login(login_request)
        
        # Clean up sensitive data
        asyncio.create_task(self._cleanup_sensitive_messages(request))
        
        return self.create_smart_response(
            message=response.message,
            keyboard=None,
            interaction_type=InteractionType.SECURITY if response.success else InteractionType.ERROR_DISPLAY,
            content_type=ContentType.SUCCESS if response.success else ContentType.ERROR,
            end_conversation=True
        )
    
    async def validate_field(self, field_name: str, value: str) -> str:
        """Validate individual form fields."""
        if field_name == "username":
            return InputSanitizer.sanitize_username(value)
        elif field_name == "password":
            return InputSanitizer.sanitize_password(value)
        else:
            raise ValidationError(f"Unknown field: {field_name}")
    
    def get_field_prompt(self, field_name: str) -> str:
        """Get prompt message for each field."""
        prompts = {
            "username": "📝 Por favor, envie seu nome de usuário:",
            "password": "🔒 Agora envie sua senha:"
        }
        return prompts.get(field_name, "Envie o valor:")
    
    def get_field_state(self, field_name: str) -> int:
        """Get conversation state for each field."""
        states = {
            "username": LOGIN_USERNAME,
            "password": LOGIN_PASSWORD
        }
        return states.get(field_name, LOGIN_USERNAME)
    
    def get_next_field(self, current_field: str) -> str:
        """Get next field in the form sequence."""
        field_sequence = {
            "username": "password",
            "password": None
        }
        return field_sequence.get(current_field)
    
    def get_retry_state(self) -> int:
        """Return state to retry on validation error."""
        return LOGIN_USERNAME
    
    async def handle(self, request: HandlerRequest) -> HandlerResponse:
        """Handle initial login command."""
        return self.create_smart_response(
            message=self.get_field_prompt("username"),
            keyboard=None,
            interaction_type=InteractionType.FORM_INPUT,
            content_type=ContentType.INFO,
            next_state=LOGIN_USERNAME
        )
    
    async def _cleanup_sensitive_messages(self, request: HandlerRequest):
        """Clean up sensitive messages after delay."""
        await asyncio.sleep(10)
        # Implementation would clean up password messages
        pass
    
    # Wrapper methods for conversation handler
    @with_error_boundary("login_start")
    async def start_login(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        request = self.create_request(update, context)
        response = await self.handle(request)
        return await self.send_response(response, request)
    
    @with_error_boundary("login_username")
    async def received_username(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        request = self.create_request(update, context)
        response = await self.handle_form_input(request, "username", update.message.text)
        
        # Schedule message deletion using batch cleanup
        asyncio.create_task(self.batch_cleanup_messages([update.message], strategy="delayed"))
        
        return await self.send_response(response, request)
    
    @with_error_boundary("login_password")
    async def received_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        request = self.create_request(update, context)
        response = await self.handle_form_input(request, "password", update.message.text)
        
        # Schedule message deletion immediately for security using batch cleanup
        asyncio.create_task(self.batch_cleanup_messages([update.message], strategy="instant"))
        
        return await self.send_response(response, request)
    
    @with_error_boundary("login_cancel")
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        request = self.create_request(update, context)
        response = self.create_smart_response(
            message="🚫 Login cancelado.",
            keyboard=None,
            interaction_type=InteractionType.CONFIRMATION,
            content_type=ContentType.INFO,
            end_conversation=True
        )
        return await self.send_response(response, request)
    
    
    def get_conversation_handler(self) -> ConversationHandler:
        """Create the conversation handler."""
        return ConversationHandler(
            entry_points=[CommandHandler("login", self.start_login)],
            states={
                LOGIN_USERNAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.received_username)
                ],
                LOGIN_PASSWORD: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.received_password)
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            allow_reentry=True
        )


# Factory function for easy integration
def get_modern_login_handler():
    """Get the modern login conversation handler."""
    handler = ModernLoginHandler()
    return handler.get_conversation_handler()