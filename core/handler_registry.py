import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

# Import modern handler migration system
from handlers.handler_migration import register_all_handlers as register_modern_handlers

# Import remaining legacy handlers (for features not yet migrated)
from handlers.global_handlers import cancel, cancel_callback

logger = logging.getLogger(__name__)


class HandlerRegistry:
    """
    Clean handler registration system.
    Organizes all telegram handlers in one place.
    """
    
    @staticmethod
    def register_all_handlers(app_bot: Application):
        """Register all handlers using the modern migration system."""
        try:
            logger.info("Registering telegram handlers with migration support...")
            
            # Use the modern migration system for core handlers
            register_modern_handlers(app_bot)
            
            # Register remaining legacy handlers for unmigrated features
            HandlerRegistry._register_legacy_handlers(app_bot)
            
            logger.info("All telegram handlers registered successfully")
            
        except Exception as e:
            logger.error(f"Failed to register handlers: {e}", exc_info=True)
            raise
    
    @staticmethod
    def _register_legacy_handlers(app_bot: Application):
        """Register legacy handlers for features not yet migrated."""
        logger.info("Registering legacy handlers for unmigrated features...")
        
        # Legacy conversation handlers (not yet migrated)
        legacy_conversation_handlers = [
            # All major conversation handlers have been migrated to modern architecture
        ]
        
        for name, handler_factory in legacy_conversation_handlers:
            try:
                handler = handler_factory()
                app_bot.add_handler(handler)
                logger.debug(f"Registered legacy conversation handler: {name}")
            except Exception as e:
                logger.error(f"Failed to register legacy {name}: {e}")
                raise
        
        # Legacy command handlers
        legacy_command_handlers = [
            ("cancel", cancel),
        ]
        
        for command, handler_func in legacy_command_handlers:
            try:
                app_bot.add_handler(CommandHandler(command, handler_func))
                logger.debug(f"Registered legacy command handler: /{command}")
            except Exception as e:
                logger.error(f"Failed to register legacy command {command}: {e}")
                raise
        
        # Legacy callback query handlers
        legacy_callback_handlers = [
            # Most callback handlers have been migrated to modern architecture
            # Any remaining will be handled by the modern handlers
        ]
        
        for name, handler_func, *pattern in legacy_callback_handlers:
            try:
                if pattern:
                    app_bot.add_handler(CallbackQueryHandler(handler_func, pattern=pattern[0]))
                    logger.debug(f"Registered legacy callback handler: {name} (pattern: {pattern[0]})")
                else:
                    app_bot.add_handler(CallbackQueryHandler(handler_func))
                    logger.debug(f"Registered legacy callback handler: {name}")
            except Exception as e:
                logger.error(f"Failed to register legacy callback {name}: {e}")
                raise


def configure_handlers(app_bot: Application):
    """Main function to configure all handlers."""
    HandlerRegistry.register_all_handlers(app_bot)