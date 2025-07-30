import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

# Import all your handlers
from handlers.start_handler import start, protect
from handlers.global_handlers import cancel, cancel_callback
from handlers.login_handler import login_handler
from handlers.product_handler import get_product_conversation_handler
from handlers.relatorios_handler import (
    get_relatorios_conversation_handler,
    exportar_csv_handler,
    exportar_csv_detalhes_handler,
    fechar_handler,
)
from handlers.buy_handler import get_buy_conversation_handler 
from handlers.user_handler import get_user_conversation_handler
from handlers.smartcontract_handler import (
    criar_smart_contract,
    get_smartcontract_conversation_handler,
    confirmar_transacao_prompt,
    confirmar_transacao_exec
)
from handlers.estoque_handler import get_estoque_conversation_handler 
from handlers.lista_produtos_handler import lista_produtos
from handlers.commands_handler import commands_handler
from handlers.pagamento_handler import (
    pagar_vendas,
    get_pagamento_conversation_handler,
)

logger = logging.getLogger(__name__)


class HandlerRegistry:
    """
    Clean handler registration system.
    Organizes all telegram handlers in one place.
    """
    
    @staticmethod
    def register_all_handlers(app_bot: Application):
        """Register all handlers in the correct order."""
        try:
            logger.info("🔄 Registering telegram handlers...")
            
            # Register conversation handlers first (they have priority)
            HandlerRegistry._register_conversation_handlers(app_bot)
            
            # Register command handlers
            HandlerRegistry._register_command_handlers(app_bot)
            
            # Register callback query handlers
            HandlerRegistry._register_callback_handlers(app_bot)
            
            logger.info("✅ All telegram handlers registered successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to register handlers: {e}", exc_info=True)
            raise
    
    @staticmethod
    def _register_conversation_handlers(app_bot: Application):
        """Register conversation handlers (highest priority)."""
        conversation_handlers = [
            ("user_handler", get_user_conversation_handler),
            ("login_handler", lambda: login_handler),
            ("product_handler", get_product_conversation_handler),
            ("estoque_handler", get_estoque_conversation_handler),
            ("relatorios_handler", get_relatorios_conversation_handler),
            ("smartcontract_handler", get_smartcontract_conversation_handler),
            ("buy_handler", get_buy_conversation_handler),
            ("pagamento_handler", get_pagamento_conversation_handler),
        ]
        
        for name, handler_factory in conversation_handlers:
            try:
                handler = handler_factory()
                app_bot.add_handler(handler)
                logger.debug(f"✅ Registered conversation handler: {name}")
            except Exception as e:
                logger.error(f"❌ Failed to register {name}: {e}")
                raise
    
    @staticmethod
    def _register_command_handlers(app_bot: Application):
        """Register command handlers."""
        command_handlers = [
            ("start", start),
            ("commands", commands_handler),
            ("protect", protect),
            ("cancel", cancel),
            ("pagar", pagar_vendas),
            ("lista_produtos", lista_produtos),
            ("smartcontract", criar_smart_contract),
        ]
        
        for command, handler_func in command_handlers:
            try:
                app_bot.add_handler(CommandHandler(command, handler_func))
                logger.debug(f"✅ Registered command handler: /{command}")
            except Exception as e:
                logger.error(f"❌ Failed to register command {command}: {e}")
                raise
    
    @staticmethod
    def _register_callback_handlers(app_bot: Application):
        """Register callback query handlers."""
        callback_handlers = [
            ("exportar_csv", exportar_csv_handler),
            ("exportar_csv_detalhes", exportar_csv_detalhes_handler),
            ("fechar", fechar_handler),
            ("confirmar_transacao", confirmar_transacao_prompt, "^confirma_transacao:"),
            ("confirmar_exec", confirmar_transacao_exec, "^confirmar_"),
        ]
        
        for name, handler_func, *pattern in callback_handlers:
            try:
                if pattern:
                    app_bot.add_handler(CallbackQueryHandler(handler_func, pattern=pattern[0]))
                    logger.debug(f"✅ Registered callback handler: {name} (pattern: {pattern[0]})")
                else:
                    app_bot.add_handler(CallbackQueryHandler(handler_func))
                    logger.debug(f"✅ Registered callback handler: {name}")
            except Exception as e:
                logger.error(f"❌ Failed to register callback {name}: {e}")
                raise


def configure_handlers(app_bot: Application):
    """Main function to configure all handlers."""
    HandlerRegistry.register_all_handlers(app_bot)