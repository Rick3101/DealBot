"""
Handler Migration Utility

This module provides utilities to gradually migrate from legacy handlers to modern handlers.
It allows for easy switching between old and new implementations.
"""

from telegram.ext import Application
from handlers.login_handler import get_modern_login_handler
from handlers.product_handler import get_modern_product_handler
from handlers.buy_handler import get_modern_buy_handler
from handlers.user_handler import get_modern_user_handler
from handlers.estoque_handler import get_modern_estoque_handler
from handlers.commands_handler import get_modern_commands_handler
from handlers.start_handler import get_modern_start_handler
from handlers.smartcontract_handler import get_smartcontract_conversation_handler, smartcontract_command_handler
from handlers.relatorios_handler import (
    get_relatorios_conversation_handler, detalhes_vendas_handler, exportar_csv_detalhes_handler,
    dividas_usuario_handler, exportar_csv_dividas_usuario_handler, fechar_relatorio_handler
)
from handlers.pagamento_handler import get_pagamento_conversation_handler, pagamento_command_handler, pagar_callback_handler
from handlers.global_handlers import delete_user_data_handler, confirm_delete_user_handler
from handlers.lista_produtos_handler import get_lista_produtos_handler
from handlers.broadcast_handler import get_modern_broadcast_handler
from handlers.poll_interaction_handler import get_poll_interaction_handler
from handlers.poll_answer_handler import create_poll_answer_handler
from handlers.cash_balance_handler import get_cash_balance_handler
from handlers.expedition_handler import get_expedition_handler
from handlers.brambler_handler import get_brambler_handler
from handlers.item_naming_handler import get_item_naming_handler
from handlers.miniapp_handler import MiniAppHandler

# Legacy handlers have been removed - all modern handlers are now active


class HandlerMigrationManager:
    """
    Manages handler registration for the modern architecture.
    
    Features:
    - Centralized handler registration
    - Status tracking for migrated vs unmigrated handlers
    - Migration support for remaining legacy handlers
    """
    
    def __init__(self):
        # Modern handlers are now always enabled (legacy handlers removed)
        self.use_modern_handlers = {
            'login': True,      # Modern handler active
            'product': True,    # Modern handler active
            'buy': True,        # Modern handler active
            'user': True,       # Modern handler active
            'estoque': True,    # Modern handler active
            'commands': True,   # Modern handler active
            'start': True,      # Modern handler active
            'relatorios': True, # Modern handler active (migrated)
            'pagamento': True,  # Modern handler active (migrated)
            'smartcontract': True, # Modern handler active (migrated)
            'global_handlers': True, # Modern handler active (migrated)
            'lista_produtos': True, # Modern handler active (migrated)
            'broadcast': True,  # Modern handler active (broadcast messaging)
            'expedition': True, # Modern handler active (expedition management)
            'brambler': True,   # Modern handler active (pirate name management)
            'item_naming': True, # Modern handler active (item name management)
        }
    
    def register_handlers(self, application: Application):
        """
        Register handlers with the application.
        
        Args:
            application: The Telegram bot application instance
        """
        # Register all handlers
        application.add_handler(get_modern_login_handler())
        print("[OK] Registered login handler")
        
        application.add_handler(get_modern_product_handler())
        print("[OK] Registered product handler")
        
        application.add_handler(get_modern_buy_handler())
        print("[OK] Registered buy handler")
        
        application.add_handler(get_modern_user_handler())
        print("[OK] Registered user handler")
        
        application.add_handler(get_modern_estoque_handler())
        print("[OK] Registered estoque handler")
        
        application.add_handler(get_modern_commands_handler())
        print("[OK] Registered commands handler")
        
        application.add_handler(get_modern_start_handler())
        print("[OK] Registered start handler")
        
        # Register migrated handlers
        application.add_handler(get_smartcontract_conversation_handler())
        application.add_handler(smartcontract_command_handler)
        print("[OK] Registered smartcontract handler")
        
        application.add_handler(get_relatorios_conversation_handler())
        application.add_handler(detalhes_vendas_handler)
        application.add_handler(exportar_csv_detalhes_handler)
        application.add_handler(dividas_usuario_handler)
        application.add_handler(exportar_csv_dividas_usuario_handler)
        application.add_handler(fechar_relatorio_handler)
        print("[OK] Registered relatorios handler (including /dividas command and fechar button)")
        
        application.add_handler(get_pagamento_conversation_handler())
        application.add_handler(pagamento_command_handler)
        application.add_handler(pagar_callback_handler)
        print("[OK] Registered pagamento handler")
        
        # Register global handlers
        application.add_handler(delete_user_data_handler)
        application.add_handler(confirm_delete_user_handler)
        print("[OK] Registered global handlers")
        
        # Register lista produtos handler
        application.add_handler(get_lista_produtos_handler())
        print("[OK] Registered lista produtos handler")
        
        # Register Broadcast handler
        application.add_handler(get_modern_broadcast_handler())
        application.add_handler(get_poll_interaction_handler())
        application.add_handler(create_poll_answer_handler())
        print("[OK] Registered broadcast handler (with poll interaction and answer tracking)")

        # Register Cash Balance handler
        application.add_handler(get_cash_balance_handler())
        print("[OK] Registered cash balance handler")

        # Register Expedition handler
        application.add_handler(get_expedition_handler())
        print("[OK] Registered expedition handler")

        # Register Brambler handler
        application.add_handler(get_brambler_handler())
        print("[OK] Registered brambler handler")

        # Register Item Naming handler
        application.add_handler(get_item_naming_handler())
        print("[OK] Registered item naming handler")

        # Register Mini App handler
        from core.modern_service_container import get_user_service
        user_service = get_user_service(None)
        miniapp_handler = MiniAppHandler(user_service)
        for handler in miniapp_handler.get_handlers():
            application.add_handler(handler)
        print("[OK] Registered mini app handler")

        print(f"\nHandler Status:")
        print(f"[OK] Active handlers: {sum(self.use_modern_handlers.values()) + 2}")
        print(f"[INFO] All handlers using modern architecture")
    
    def enable_modern_handler(self, handler_name: str):
        """Enable modern handler for a specific feature (only applies to unmigrated handlers)."""
        if handler_name in self.use_modern_handlers:
            if handler_name in ['login', 'product', 'buy', 'user', 'estoque', 'commands', 'start', 'broadcast']:
                print(f"[INFO] Handler {handler_name} is already using modern implementation")
            else:
                self.use_modern_handlers[handler_name] = True
                print(f"[OK] Enabled modern {handler_name} handler")
        else:
            print(f"[ERROR] Unknown handler: {handler_name}")
    
    def disable_modern_handler(self, handler_name: str):
        """Disable modern handler (only available for unmigrated handlers)."""
        if handler_name in self.use_modern_handlers:
            if handler_name in ['login', 'product', 'buy', 'user', 'estoque', 'commands', 'start', 'broadcast']:
                print(f"[WARN] Cannot disable {handler_name} - legacy version has been removed")
            else:
                self.use_modern_handlers[handler_name] = False
                print(f"[WARN] Disabled modern {handler_name} handler (using legacy)")
        else:
            print(f"[ERROR] Unknown handler: {handler_name}")
    
    def get_migration_status(self) -> dict:
        """Get current migration status."""
        return {
            'modern_count': sum(self.use_modern_handlers.values()),
            'legacy_count': len(self.use_modern_handlers) - sum(self.use_modern_handlers.values()),
            'total_handlers': len(self.use_modern_handlers),
            'handlers': self.use_modern_handlers.copy()
        }
    
    def enable_all_modern_handlers(self):
        """Enable all available modern handlers."""
        available_modern = ['login', 'product', 'buy', 'user', 'estoque', 'commands', 'start', 'broadcast']
        print("[INFO] All available modern handlers are already enabled")
        print(f"[OK] Modern handlers active: {', '.join(available_modern)}")
    
    def rollback_all_to_legacy(self):
        """Rollback capability is no longer available (legacy handlers removed)."""
        print("[WARN] Cannot rollback - legacy handlers have been removed from the codebase")
        print("[INFO] Modern handlers are now the only implementation available")


# Global instance for easy access
migration_manager = HandlerMigrationManager()


def register_all_handlers(application: Application):
    """
    Convenience function to register all handlers with migration support.
    
    Args:
        application: The Telegram bot application instance
    """
    migration_manager.register_handlers(application)


def get_migration_status():
    """Get current migration status."""
    return migration_manager.get_migration_status()


def enable_modern_handler(handler_name: str):
    """Enable modern handler for a specific feature."""
    migration_manager.enable_modern_handler(handler_name)


def disable_modern_handler(handler_name: str):
    """Disable modern handler for a specific feature."""
    migration_manager.disable_modern_handler(handler_name)