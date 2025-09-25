import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from handlers.error_handler import with_error_boundary_standalone
from utils.message_cleaner import send_and_delete, delete_protected_message
from handlers.base_handler import DelayConstants

logger = logging.getLogger(__name__)


class ModernGlobalHandlers:
    """Modern global handlers with error boundaries and proper cleanup"""
    
    @staticmethod
    @with_error_boundary_standalone("global_cancel")
    async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Modern cancel handler with proper cleanup and error handling"""
        logger.info("→ Executing modern cancel handler")
        
        try:
            msg = update.message or (update.callback_query.message if update.callback_query else None)

            if msg:
                try:
                    await msg.delete()
                except Exception as e:
                    logger.warning(f"Failed to delete message during cancel: {e}")

            # Clear all user and chat data
            context.user_data.clear()
            context.chat_data.clear()
            
            # Clear protected messages if they exist
            if "protected_messages" in context.chat_data:
                context.chat_data["protected_messages"] = set()

            # No confirmation message per UX Flow Guide Pattern 2.1
            
        except Exception as e:
            logger.error(f"Error in cancel handler: {e}", exc_info=True)
            # Fallback response
            if update.message:
                # No confirmation message per UX Flow Guide Pattern 2.1
                pass
        
        return ConversationHandler.END

    @staticmethod  
    @with_error_boundary_standalone("global_cancel_callback")
    async def cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Modern callback cancel handler with proper cleanup and error handling"""
        logger.info("→ Executing modern cancel_callback handler")
        
        try:
            query = update.callback_query
            await query.answer()

            # Clean up protected messages
            context.chat_data["protected_messages"] = set()

            # Clear temporary data
            context.user_data.clear()
            context.chat_data.clear()

            try:
                await query.message.delete()
            except Exception as e:
                logger.warning(f"Failed to delete callback message during cancel: {e}")

            # No confirmation message per UX Flow Guide Pattern 2.1
            
        except Exception as e:
            logger.error(f"Error in cancel_callback handler: {e}", exc_info=True)
            # Fallback response
            try:
                if update.callback_query and update.callback_query.message:
                    # No confirmation message per UX Flow Guide Pattern 2.1
                    pass
            except:
                pass
        
        return ConversationHandler.END

    @staticmethod
    @with_error_boundary_standalone("global_delete_user_data")
    async def delete_user_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Modern user data deletion handler with confirmation"""
        logger.info("→ Executing modern delete_user_data handler")
        
        try:
            chat_id = update.effective_chat.id
            
            # Import here to avoid circular dependency
            from services.handler_business_service import HandlerBusinessService
            business_service = HandlerBusinessService(context)
            
            # Check if user exists and can be deleted
            user_exists = business_service.user_exists(chat_id)
            
            if not user_exists:
                await send_and_delete(
                    "❌ Usuário não encontrado ou já foi removido.", 
                    update, 
                    context
                )
                return
            
            # Confirm deletion
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Sim, deletar", callback_data="confirm_delete_user"),
                    InlineKeyboardButton("❌ Cancelar", callback_data="cancel_delete_user")
                ]
            ])
            
            await send_and_delete(
                "⚠️ Tem certeza que deseja deletar todos os seus dados?\n"
                "Esta ação não pode ser desfeita.",
                update,
                context,
                reply_markup=keyboard,
                delay=DelayConstants.FILE_TRANSFER // 4  # 30 seconds
            )
            
        except Exception as e:
            logger.error(f"Error in delete_user_data handler: {e}", exc_info=True)
            await send_and_delete(
                "❌ Erro ao processar solicitação de deleção.",
                update,
                context
            )

    @staticmethod
    @with_error_boundary_standalone("global_confirm_delete_user")  
    async def confirm_delete_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Confirm and execute user data deletion"""
        logger.info("→ Executing confirm_delete_user handler")
        
        try:
            query = update.callback_query
            await query.answer()
            await delete_protected_message(update, context)
            
            if query.data == "confirm_delete_user":
                chat_id = update.effective_chat.id
                
                # Import here to avoid circular dependency
                from services.handler_business_service import HandlerBusinessService
                business_service = HandlerBusinessService(context)
                
                # Delete user data
                success = business_service.delete_user_data(chat_id)
                
                if success:
                    # Clear all context data
                    context.user_data.clear()
                    context.chat_data.clear()
                    
                    await query.message.reply_text(
                        "✅ Seus dados foram completamente removidos do sistema.\n"
                        "Use /start para começar novamente."
                    )
                else:
                    await query.message.reply_text(
                        "❌ Erro ao deletar dados. Tente novamente mais tarde."
                    )
            else:
                # No confirmation message per UX Flow Guide Pattern 2.1
                pass
                
        except Exception as e:
            logger.error(f"Error in confirm_delete_user handler: {e}", exc_info=True)
            try:
                if update.callback_query and update.callback_query.message:
                    await update.callback_query.message.reply_text(
                        "❌ Erro ao processar deleção."
                    )
            except:
                pass

    @staticmethod
    @with_error_boundary_standalone("global_unauthorized_access")
    async def handle_unauthorized_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle unauthorized access attempts with proper logging"""
        logger.warning(f"Unauthorized access attempt from {update.effective_user.id}")
        
        await send_and_delete(
            "❌ Você não tem permissão para usar este comando.\n"
            "Faça login primeiro com /login",
            update,
            context,
            delay=DelayConstants.SUCCESS
        )

    @staticmethod
    @with_error_boundary_standalone("global_conversation_timeout")
    async def handle_conversation_timeout(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle conversation timeouts gracefully"""
        logger.info("→ Handling conversation timeout")
        
        # Clear any pending data
        context.user_data.clear()
        context.chat_data.clear()
        
        await send_and_delete(
            "⏰ Conversa expirada por inatividade.\n"
            "Use /commands para ver os comandos disponíveis.",
            update,
            context,
            delay=DelayConstants.INFO
        )
        
        return ConversationHandler.END

    @staticmethod
    @with_error_boundary_standalone("global_invalid_state")
    async def handle_invalid_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle invalid conversation states"""
        logger.warning("→ Invalid conversation state detected")
        
        # Reset conversation state
        context.user_data.clear()
        context.chat_data.clear()
        
        await send_and_delete(
            "❌ Estado da conversa inválido.\n"
            "Operação reiniciada. Use /commands para continuar.",
            update,
            context,
            delay=DelayConstants.ERROR
        )
        
        return ConversationHandler.END


# Export the handlers for backward compatibility
cancel = ModernGlobalHandlers.cancel
cancel_callback = ModernGlobalHandlers.cancel_callback
delete_user_data = ModernGlobalHandlers.delete_user_data
confirm_delete_user = ModernGlobalHandlers.confirm_delete_user
handle_unauthorized_access = ModernGlobalHandlers.handle_unauthorized_access
handle_conversation_timeout = ModernGlobalHandlers.handle_conversation_timeout
handle_invalid_state = ModernGlobalHandlers.handle_invalid_state


# Command and callback handler registrations
from telegram.ext import CommandHandler, CallbackQueryHandler

delete_user_data_handler = CommandHandler("delete_my_data", delete_user_data)
confirm_delete_user_handler = CallbackQueryHandler(confirm_delete_user, pattern="^(confirm_delete_user|cancel_delete_user)$")
unauthorized_access_handler = CommandHandler("unauthorized", handle_unauthorized_access)