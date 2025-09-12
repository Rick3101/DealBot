from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from handlers.base_handler import BaseHandler, HandlerRequest, HandlerResponse
from handlers.error_handler import with_error_boundary
from core.modern_service_container import get_user_service
from utils.message_cleaner import send_and_delete


class ModernCommandsHandler(BaseHandler):
    def __init__(self):
        super().__init__("commands")
    
    async def handle(self, request: HandlerRequest) -> HandlerResponse:
        """Show available commands based on user level."""
        user_service = get_user_service(request.context)
        user = user_service.get_user_by_chat_id(request.chat_id)
        
        if not user:
            commands = [
                "🤖 **Comandos Universais** (Sem Login):",
                "/start - Inicializar bot com frase de proteção",
                "/login - Autenticação com limpeza automática",
                "",
                "💡 Faça /login primeiro para ver mais comandos!"
            ]
            return HandlerResponse(
                message="\n".join(commands)
            )
        
        level = user.level.value
        username = user.username
        
        commands = [
            f"📋 **Comandos para {username}** ({level.upper()}):\n"
        ]
        
        # Universal commands (always shown)
        commands.extend([
            "🎯 **Universais:**",
            "/start - Inicializar bot",
            "/login - Autenticação",
            "/commands - Lista de comandos dinâmica",
            ""
        ])
        
        # User level commands (logged in users)
        commands.extend([
            "👤 **Usuário:**",
            "/cancel - Cancelar operação atual",
            "/delete_my_data - Deletar seus dados",
            ""
        ])
        
        # Admin level commands
        if level in ["admin", "owner"]:
            commands.extend([
                "👮 **Admin - Operações Principais:**",
                "/buy - Fluxo de compras com validação FIFO",
                "/estoque - Gerenciamento de inventário",
                "/pagar - Processamento de pagamentos",
                "",
                "📊 **Relatórios & Informações:**",
                "/lista_produtos - Catálogo com mídia",
                "/relatorios - Relatórios vendas/dívidas + CSV",
                "/dividas - Relatório pessoal de dívidas",
                "/detalhes - Informações detalhadas de vendas",
                ""
            ])
        
        # Owner level commands
        if level == "owner":
            commands.extend([
                "👑 **Owner - Gerenciamento:**",
                "/user - Sistema completo de usuários",
                "/product - CRUD de produtos + mídia",
                "/smartcontract - Contratos inteligentes",
                "/transactions - Menu de transações",
                ""
            ])
        
        # Special features info
        if level in ["admin", "owner"]:
            commands.extend([
                "🎯 **Recursos Especiais:**",
                "• Menu Secreto: Palavras especiais no /buy",
                "• Auto-deleção: Mensagens sensíveis",
                "• CSV Export: Todos os relatórios",
                "• FIFO: Processamento automático de estoque",
                ""
            ])
        
        commands.extend([
            "💡 **Dicas:**",
            "• Use /cancel em qualquer fluxo",
            "• Relatórios têm limpeza automática",
            "• Login é lembrado automaticamente"
        ])
        
        return HandlerResponse(
            message="\n".join(commands)
        )
    
    @with_error_boundary("commands")
    async def show_commands(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        request = self.create_request(update, context)
        response = await self.handle(request)
        
        await send_and_delete(response.message, update, context, delay=30)


def get_modern_commands_handler():
    """Get the modern commands handler."""
    handler = ModernCommandsHandler()
    return CommandHandler("commands", handler.show_commands)