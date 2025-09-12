"""
Modern Lista Produtos Handler - Displays product catalog with media and pricing.
Implements modern architecture patterns with error boundaries and type safety.
"""
import logging
import asyncio
from typing import List
import telegram
from telegram import Update, Message
from telegram.ext import ContextTypes, CommandHandler

from handlers.base_handler import BaseHandler, HandlerRequest, HandlerResponse
from handlers.error_handler import with_error_boundary
from core.modern_service_container import get_product_service
from core.config import get_secret_menu_emojis
from utils.permissions import require_permission
from utils.product_list_generator import ProductListGenerator

logger = logging.getLogger(__name__)


class ModernListaProdutosHandler(BaseHandler):
    """Modern product listing handler with error boundaries and concurrent safety."""

    def __init__(self):
        super().__init__("lista_produtos")

    async def handle(self, request: HandlerRequest) -> HandlerResponse:
        """Implementation of the abstract handle method."""
        return await self._handle_lista_produtos_request(request)

    async def _handle_lista_produtos_request(self, request: HandlerRequest) -> HandlerResponse:
        """Handle the lista produtos request using the new architecture."""
        try:
            # Validate permissions
            if not await self.validate_user_permission(request, "admin"):
                return HandlerResponse(
                    message="❌ Você não tem permissão para usar este comando.",
                    end_conversation=True
                )

            # Call the main lista produtos logic
            await self.lista_produtos(request.update, request.context)
            
            return HandlerResponse(
                message="✅ Catálogo de produtos exibido com sucesso.",
                end_conversation=True
            )
        except Exception as e:
            logger.error(f"Error in lista produtos handler: {e}")
            return HandlerResponse(
                message="❌ Erro ao exibir catálogo de produtos.",
                end_conversation=True
            )

    @require_permission("admin")
    @with_error_boundary("lista_produtos")
    async def lista_produtos(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Display product catalog with media and pricing."""
        logger.info("→ Displaying product catalog")
        chat_id = update.effective_chat.id

        # Delete the user's command message
        await self._delete_command_message(update)

        # Prevent parallel execution using conversation locks
        lock = await self._get_or_create_lock(context, "lista_lock")
        
        if lock.locked():
            await context.bot.send_message(
                chat_id=chat_id,
                text="⏳ A lista de produtos ainda está sendo exibida. Aguarde um momento..."
            )
            return

        async with lock:
            await self._display_product_catalog(chat_id, context)

    async def _delete_command_message(self, update: Update):
        """Delete the command message sent by the user."""
        msg = update.message or (update.callback_query.message if update.callback_query else None)
        if msg:
            try:
                await msg.delete()
            except Exception:
                pass  # Ignore if message can't be deleted

    async def _get_or_create_lock(self, context: ContextTypes.DEFAULT_TYPE, lock_name: str) -> asyncio.Lock:
        """Get or create a conversation lock for preventing parallel execution."""
        if lock_name not in context.chat_data:
            context.chat_data[lock_name] = asyncio.Lock()
        return context.chat_data[lock_name]

    async def _display_product_catalog(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        """Display the complete product catalog with media and pricing."""
        try:
            product_service = get_product_service(context)
            produtos_with_stock = product_service.get_products_with_stock()
            
            # Filter out secret products using the utility method
            public_products = ProductListGenerator.filter_secret_products(
                produtos_with_stock, include_secret=False
            )
            
            if not public_products:
                await context.bot.send_message(
                    chat_id=chat_id, 
                    text="🚫 Nenhum produto com estoque."
                )
                return

            messages_to_delete = []

            for product_with_stock in public_products:
                product = product_with_stock.product
                price = product_with_stock.average_price
                
                # Send product text message
                text = f"*{product.emoji} {product.nome} - R$ {price:.2f}*"
                msg_txt = await context.bot.send_message(
                    chat_id=chat_id, 
                    text=text, 
                    parse_mode="Markdown"
                )
                messages_to_delete.append(msg_txt)

                # Send product media if available
                if product.media_file_id:
                    media_msg = await self._send_product_media(
                        chat_id, context, product.media_file_id
                    )
                    if media_msg:
                        messages_to_delete.append(media_msg)

            # Auto-delete all messages after 15 seconds
            await self._auto_delete_messages(messages_to_delete)

        except Exception as e:
            logger.error(f"Error displaying product catalog: {e}")
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ Erro ao exibir catálogo de produtos."
            )

    async def _send_product_media(
        self, 
        chat_id: int, 
        context: ContextTypes.DEFAULT_TYPE, 
        media_file_id: str
    ) -> Message:
        """Send product media based on file type."""
        try:
            if media_file_id.startswith("AgAC"):
                return await context.bot.send_photo(chat_id=chat_id, photo=media_file_id)
            elif media_file_id.startswith("BAAC"):
                return await context.bot.send_document(chat_id=chat_id, document=media_file_id)
            elif media_file_id.startswith("BAAD"):
                return await context.bot.send_video(chat_id=chat_id, video=media_file_id)
            else:
                return await context.bot.send_message(
                    chat_id=chat_id, 
                    text="❓ Mídia desconhecida."
                )
        except telegram.error.BadRequest as e:
            logger.warning(f"Failed to send media {media_file_id}: {e}")
            return await context.bot.send_message(
                chat_id=chat_id, 
                text=f"❌ Erro ao carregar mídia: {e}"
            )

    async def _auto_delete_messages(self, messages: List[Message]):
        """Auto-delete messages after a delay."""
        await asyncio.sleep(15)
        for message in messages:
            try:
                await message.delete()
            except Exception:
                pass  # Ignore deletion errors


def get_lista_produtos_handler():
    """Get the lista produtos command handler."""
    handler = ModernListaProdutosHandler()
    return CommandHandler("lista_produtos", handler.lista_produtos)