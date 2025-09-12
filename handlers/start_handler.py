from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from handlers.base_handler import BaseHandler, HandlerRequest, HandlerResponse
from handlers.error_handler import with_error_boundary
from utils.message_cleaner import send_and_delete
from services.config_service import get_config_service


class ModernStartHandler(BaseHandler):
    def __init__(self):
        super().__init__("start")
    
    async def handle(self, request: HandlerRequest) -> HandlerResponse:
        """Handle the /start command."""
        try:
            # Get random start message from configuration database
            config_service = get_config_service()
            welcome_message = config_service.get_random_start_message()
            
            # Return only the database message
            return HandlerResponse(message=welcome_message)
            
        except Exception as e:
            # Fallback to hardcoded message if config service fails
            fallback_message = (
                "Bot inicializado com sucesso!\n\n"
                "Para começar, você precisa fazer login:\n"
                "👉 Use /login para acessar o sistema\n\n"
                "Após o login, use /commands para ver os comandos disponíveis.\n\n"
                "💡 Dica: Use /cancel para cancelar qualquer operação."
            )
            
            return HandlerResponse(message=fallback_message)
    
    @with_error_boundary("start")
    async def start_bot(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        request = self.create_request(update, context)
        response = await self.handle(request)
        
        await send_and_delete(response.message, update, context, delay=20, protected=True)


def get_modern_start_handler():
    """Get the modern start handler."""
    handler = ModernStartHandler()
    return CommandHandler("start", handler.start_bot)