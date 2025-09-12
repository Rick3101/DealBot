from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes, CommandHandler
from handlers.base_handler import BaseHandler, HandlerRequest, HandlerResponse
from handlers.error_handler import with_error_boundary
from utils.permissions import require_permission
from utils.message_cleaner import send_and_delete


class ModernMiniAppHandler(BaseHandler):
    def __init__(self):
        super().__init__("miniapp")
    
    async def handle(self, request: HandlerRequest) -> HandlerResponse:
        """Handle the /miniapp command."""
        try:
            # Get the current configuration to determine the webhook URL
            from core.config import get_config
            config = get_config()
            
            # Build the MiniApp URL
            base_url = config.telegram.webhook_url or "https://your-app.render.com"
            miniapp_url = f"{base_url}/miniapp"
            
            # Create WebApp keyboard
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "🚀 Abrir Dashboard", 
                    web_app=WebAppInfo(url=miniapp_url)
                )],
                [InlineKeyboardButton("❌ Cancelar", callback_data="cancel")]
            ])
            
            message = (
                "📱 *MiniApp Dashboard*\n\n"
                "Clique no botão abaixo para abrir o dashboard interativo do bot.\n\n"
                "O MiniApp permite visualizar:\n"
                "• 📊 Estatísticas em tempo real\n"
                "• 📋 Tabelas de dados\n"
                "• 🔄 Atualizações dinâmicas\n"
                "• 🎨 Interface nativa do Telegram\n\n"
                "💡 *Dica:* O MiniApp abrirá dentro do próprio Telegram!"
            )
            
            return HandlerResponse(
                message=message,
                keyboard=keyboard,
                protected=True,
                delay=30
            )
            
        except Exception as e:
            self.logger.error(f"Error in miniapp handler: {e}", exc_info=True)
            return HandlerResponse(
                message="❌ Erro ao carregar o MiniApp. Tente novamente mais tarde.",
                delay=10
            )
    
    @require_permission("user")
    @with_error_boundary("miniapp")
    async def miniapp_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /miniapp command with permission check."""
        request = self.create_request(update, context)
        response = await self.handle(request)
        
        if response.keyboard:
            await send_and_delete(
                response.message,
                update,
                context,
                reply_markup=response.keyboard,
                delay=response.delay,
                protected=response.protected,
                parse_mode="Markdown"
            )
        else:
            await send_and_delete(
                response.message,
                update,
                context,
                delay=response.delay,
                parse_mode="Markdown"
            )


def get_modern_miniapp_handler():
    """Get the modern MiniApp handler."""
    handler = ModernMiniAppHandler()
    return CommandHandler("miniapp", handler.miniapp_command)