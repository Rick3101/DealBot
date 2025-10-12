"""
Item Naming Handler - Custom Item/Product Name Management System
Handles custom display names/aliases for products, similar to brambler but for items.
"""

import logging
from typing import Optional, List
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, filters

from handlers.base_handler import MenuHandlerBase, HandlerRequest, HandlerResponse, InteractionType, ContentType
from services.item_naming_service import ItemNamingService
from utils.permissions import require_permission


# Conversation states
ITEM_NAMING_MENU = 0
ITEM_NAMING_CUSTOM_PRODUCT_SELECT = 1
ITEM_NAMING_CUSTOM_NAME_INPUT = 2


class ItemNamingHandler(MenuHandlerBase):
    """Handler for item/product custom name management."""

    def __init__(self):
        super().__init__("item_naming")
        self.logger = logging.getLogger(__name__)

    def get_conversation_handler(self) -> ConversationHandler:
        """Get the conversation handler for item naming management."""
        return ConversationHandler(
            entry_points=[
                CommandHandler("items", self.start_item_naming, filters.ChatType.PRIVATE),
            ],
            states={
                ITEM_NAMING_MENU: [
                    CallbackQueryHandler(self.item_naming_menu_handler, pattern=r"^item_"),
                ],
                ITEM_NAMING_CUSTOM_PRODUCT_SELECT: [
                    CallbackQueryHandler(self.handle_product_selection, pattern=r"^item_product:"),
                    CallbackQueryHandler(self.item_naming_menu_handler, pattern=r"^item_back$"),
                    CallbackQueryHandler(self.cancel_item_naming, pattern=r"^item_cancel$"),
                ],
                ITEM_NAMING_CUSTOM_NAME_INPUT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_custom_name_input),
                    CallbackQueryHandler(self.item_naming_menu_handler, pattern=r"^item_back$"),
                    CallbackQueryHandler(self.cancel_item_naming, pattern=r"^item_cancel$"),
                ],
            },
            fallbacks=[
                CallbackQueryHandler(self.cancel_item_naming, pattern=r"^item_cancel$"),
                CommandHandler("cancel", self.cancel_item_naming),
            ],
            per_message=False,
        )

    @require_permission('admin')
    async def start_item_naming(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start item naming management."""
        request = self.create_request(update, context)

        message_text = (
            "📦 **Sistema de Nomes de Itens - Gerenciamento de Nomes Personalizados**\n\n"
            "Aqui você pode gerenciar nomes personalizados para seus produtos:\n\n"
            "🎲 **Gerar Nomes Personalizados**: Cria nomes fantasia para todos os produtos\n"
            "✏️ **Atribuir Nome**: Define um nome específico para um produto\n"
            "👁️ **Ver Mapeamentos**: Lista todos os nomes personalizados existentes\n\n"
            "Escolha uma opção:"
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎲 Gerar Nomes Personalizados", callback_data="item_generate_custom")],
            [InlineKeyboardButton("✏️ Atribuir Nome", callback_data="item_assign_custom")],
            [InlineKeyboardButton("👁️ Ver Mapeamentos", callback_data="item_view_mappings")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="item_cancel")]
        ])

        await update.message.reply_text(
            message_text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )

        return ITEM_NAMING_MENU

    async def item_naming_menu_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle item naming menu callbacks."""
        query = update.callback_query

        # Handle cancel first before answering query
        if query.data == "item_cancel":
            return await self.cancel_item_naming(update, context)

        await query.answer()

        request = self.create_request(update, context)

        if query.data == "item_generate_custom":
            return await self.handle_generate_custom_names(request)
        elif query.data == "item_assign_custom":
            return await self.show_product_selection(request)
        elif query.data == "item_view_mappings":
            return await self.show_item_mappings(request)
        elif query.data == "item_back":
            return await self.show_main_menu(request)

        return ITEM_NAMING_MENU

    async def handle_generate_custom_names(self, request: HandlerRequest) -> int:
        """Generate custom fantasy names for all products."""
        try:
            item_service = ItemNamingService()

            # Get all available products
            available_products = item_service.get_available_products()

            if not available_products:
                message_text = (
                    "❌ **Nenhum produto encontrado**\n\n"
                    "Não há produtos cadastrados.\n"
                    "Cadastre alguns produtos primeiro para ter itens disponíveis."
                )
            else:
                # Generate custom fantasy names
                results = []
                new_count = 0
                existing_count = 0

                for product_name in available_products:
                    # Check if product already has a custom name
                    existing_custom = item_service.get_custom_name_for_product(product_name)

                    if existing_custom:
                        results.append(f"   📦 {product_name} → {existing_custom} *(existente)*")
                        existing_count += 1
                    else:
                        # Generate new fantasy name
                        custom_name = item_service._generate_deterministic_fantasy_name(product_name)
                        # Store the mapping
                        chat_id = request.update.effective_chat.id if request.update.effective_chat else None
                        item_service.create_global_item_mapping(product_name, custom_name, chat_id)
                        results.append(f"   📦 {product_name} → {custom_name} *(novo)*")
                        new_count += 1

                message_text = (
                    f"🎲 **Nomes Personalizados Processados!**\n\n"
                    f"✅ **{len(available_products)}** produtos processados:\n"
                    f"🆕 **{new_count}** novos nomes gerados\n"
                    f"📋 **{existing_count}** nomes existentes\n\n"
                    "**Mapeamentos:**\n" + "\n".join(results)
                )

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="item_back")]
            ])

            await request.update.callback_query.edit_message_text(
                message_text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )

        except Exception as e:
            self.logger.error(f"Error generating custom names: {e}", exc_info=True)
            await request.update.callback_query.edit_message_text(
                "❌ Erro ao gerar nomes personalizados. Tente novamente.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Voltar", callback_data="item_back")]
                ])
            )

        return ITEM_NAMING_MENU

    async def show_product_selection(self, request: HandlerRequest) -> int:
        """Show product selection for custom name assignment."""
        try:
            item_service = ItemNamingService()
            available_products = item_service.get_available_products()

            if not available_products:
                message_text = (
                    "❌ **Nenhum produto encontrado**\n\n"
                    "Não há produtos cadastrados para atribuir nomes personalizados."
                )
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Voltar", callback_data="item_back")]
                ])
            else:
                message_text = (
                    "✏️ **Atribuir Nome Personalizado**\n\n"
                    "Selecione um produto para definir um nome personalizado:"
                )

                # Create buttons for products (max 15 for readability)
                buttons = []
                for product in available_products[:15]:  # Limit to first 15 for UI
                    current_custom = item_service.get_custom_name_for_product(product)
                    display_text = f"{product}"
                    if current_custom:
                        display_text += f" → {current_custom}"
                    buttons.append([InlineKeyboardButton(display_text, callback_data=f"item_product:{product}")])

                buttons.append([InlineKeyboardButton("🔙 Voltar", callback_data="item_back")])
                keyboard = InlineKeyboardMarkup(buttons)

            await request.update.callback_query.edit_message_text(
                message_text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )

            return ITEM_NAMING_CUSTOM_PRODUCT_SELECT

        except Exception as e:
            self.logger.error(f"Error showing product selection: {e}", exc_info=True)
            await request.update.callback_query.edit_message_text(
                "❌ Erro ao carregar produtos. Tente novamente.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Voltar", callback_data="item_back")]
                ])
            )
            return ITEM_NAMING_MENU

    async def handle_product_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle product selection for custom name assignment."""
        query = update.callback_query
        await query.answer()

        product_name = query.data.split(":", 1)[1]
        context.user_data['selected_product'] = product_name

        try:
            item_service = ItemNamingService()
            current_custom = item_service.get_custom_name_for_product(product_name)

            current_text = f" (atual: **{current_custom}**)" if current_custom else ""

            message_text = (
                f"✏️ **Definir Nome Personalizado**\n\n"
                f"Produto selecionado: **{product_name}**{current_text}\n\n"
                f"Digite o nome personalizado que deseja atribuir a este produto:\n\n"
                f"💡 *Exemplo: Poção Mágica da Força, Espada Lendária do Dragão, etc.*"
            )

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Voltar", callback_data="item_back")]
            ])

            await query.edit_message_text(
                message_text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )

            return ITEM_NAMING_CUSTOM_NAME_INPUT

        except Exception as e:
            self.logger.error(f"Error handling product selection: {e}", exc_info=True)
            await query.edit_message_text(
                "❌ Erro ao processar seleção. Tente novamente.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Voltar", callback_data="item_back")]
                ])
            )
            return ITEM_NAMING_CUSTOM_PRODUCT_SELECT

    async def handle_custom_name_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle custom item name input."""
        # Delete user's input message immediately
        try:
            await update.message.delete()
        except Exception as e:
            self.logger.warning(f"Could not delete user input message: {e}")

        request = self.create_request(update, context)
        product_name = context.user_data.get('selected_product')
        custom_name = update.message.text.strip()

        if not product_name:
            await request.context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ Erro: Nenhum produto selecionado. Use /items para começar novamente."
            )
            return ConversationHandler.END

        if not custom_name or len(custom_name) < 2:
            # Send error message with auto-deletion
            message = await request.context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ Nome muito curto. Digite um nome personalizado válido (mínimo 2 caracteres)."
            )
            # Auto-delete error message after 8 seconds
            request.context.job_queue.run_once(
                lambda context: context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message.message_id),
                when=8
            )
            return ITEM_NAMING_CUSTOM_NAME_INPUT

        try:
            item_service = ItemNamingService()

            # Check if name already exists for another product
            existing_product = item_service.get_product_for_custom_name(custom_name)
            if existing_product and existing_product != product_name:
                # Send error message with auto-deletion
                message = await request.context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"❌ O nome **{custom_name}** já está sendo usado por **{existing_product}**.\n"
                         "Escolha um nome diferente.",
                    parse_mode='Markdown'
                )
                # Auto-delete error message after 8 seconds
                request.context.job_queue.run_once(
                    lambda context: context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message.message_id),
                    when=8
                )
                return ITEM_NAMING_CUSTOM_NAME_INPUT

            # Create or update the mapping
            chat_id = update.effective_chat.id if update.effective_chat else None
            item_service.create_or_update_global_item_mapping(product_name, custom_name, chat_id)

            message_text = (
                f"✅ **Nome Personalizado Atribuído!**\n\n"
                f"📦 **{product_name}** → **{custom_name}**\n\n"
                f"O produto agora será conhecido como **{custom_name}** em exibições personalizadas."
            )

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✏️ Atribuir Outro Nome", callback_data="item_assign_custom")],
                [InlineKeyboardButton("🔙 Menu Principal", callback_data="item_back")]
            ])

            # Success message
            await request.context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=message_text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )

            return ITEM_NAMING_MENU

        except Exception as e:
            self.logger.error(f"Error assigning custom name: {e}", exc_info=True)
            await request.context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ Erro ao atribuir nome personalizado. Tente novamente."
            )
            return ITEM_NAMING_CUSTOM_NAME_INPUT

    async def show_item_mappings(self, request: HandlerRequest) -> int:
        """Show all existing item name mappings with detailed information."""
        try:
            item_service = ItemNamingService()
            all_mappings = item_service.get_all_mapping_details()

            if not all_mappings:
                message_text = (
                    "📋 **Mapeamentos de Nomes**\n\n"
                    "Nenhum mapeamento de nome personalizado encontrado.\n"
                    "Use 'Gerar Nomes Personalizados' para criar mapeamentos."
                )
            else:
                mappings_text = []
                fantasy_count = 0
                manual_count = 0

                for mapping in all_mappings:
                    product_name = mapping['product_name']
                    custom_name = mapping['custom_name']
                    is_fantasy = mapping['is_fantasy_generated']
                    created_at = mapping['created_at']

                    if is_fantasy:
                        fantasy_count += 1
                        status_icon = "🎲"
                    else:
                        manual_count += 1
                        status_icon = "✏️"

                    # Format creation date
                    date_str = created_at.strftime("%d/%m") if created_at else "N/A"

                    mappings_text.append(f"   {status_icon} {product_name} → {custom_name} *({date_str})*")

                message_text = (
                    f"📋 **Mapeamentos de Nomes ({len(all_mappings)})**\n\n"
                    f"🎲 **{fantasy_count}** gerados automaticamente\n"
                    f"✏️ **{manual_count}** definidos manualmente\n\n"
                    "**Lista completa:**\n" + "\n".join(mappings_text)
                )

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="item_back")]
            ])

            await request.update.callback_query.edit_message_text(
                message_text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )

        except Exception as e:
            self.logger.error(f"Error showing mappings: {e}", exc_info=True)
            await request.update.callback_query.edit_message_text(
                "❌ Erro ao carregar mapeamentos. Tente novamente.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Voltar", callback_data="item_back")]
                ])
            )

        return ITEM_NAMING_MENU

    async def show_main_menu(self, request: HandlerRequest) -> int:
        """Show the main item naming menu."""
        message_text = (
            "📦 **Sistema de Nomes de Itens - Gerenciamento de Nomes Personalizados**\n\n"
            "Aqui você pode gerenciar nomes personalizados para seus produtos:\n\n"
            "🎲 **Gerar Nomes Personalizados**: Cria nomes fantasia para todos os produtos\n"
            "✏️ **Atribuir Nome**: Define um nome específico para um produto\n"
            "👁️ **Ver Mapeamentos**: Lista todos os nomes personalizados existentes\n\n"
            "Escolha uma opção:"
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎲 Gerar Nomes Personalizados", callback_data="item_generate_custom")],
            [InlineKeyboardButton("✏️ Atribuir Nome", callback_data="item_assign_custom")],
            [InlineKeyboardButton("👁️ Ver Mapeamentos", callback_data="item_view_mappings")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="item_cancel")]
        ])

        await request.update.callback_query.edit_message_text(
            message_text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )

        return ITEM_NAMING_MENU

    async def cancel_item_naming(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel item naming conversation."""
        if update.callback_query:
            try:
                # Answer callback query first
                await update.callback_query.answer()
                # Delete message immediately
                await update.callback_query.message.delete()
            except Exception as e:
                self.logger.error(f"Failed to delete item naming menu message: {e}")

        # Clean up user data
        context.user_data.pop('selected_product', None)

        return ConversationHandler.END

    # Required abstract method implementations for MenuHandlerBase
    def create_main_menu_keyboard(self) -> InlineKeyboardMarkup:
        """Create the main item naming menu keyboard."""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🎲 Gerar Nomes Personalizados", callback_data="item_generate_custom")],
            [InlineKeyboardButton("✏️ Atribuir Nome", callback_data="item_assign_custom")],
            [InlineKeyboardButton("👁️ Ver Mapeamentos", callback_data="item_view_mappings")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="item_cancel")]
        ])

    async def handle_menu_selection(self, request: HandlerRequest, selection: str) -> HandlerResponse:
        """Handle menu selection (not used in our implementation)."""
        return HandlerResponse(
            message="Menu selection not implemented for item naming",
            next_state=ITEM_NAMING_MENU
        )

    def get_menu_text(self) -> str:
        """Get the main menu text."""
        return (
            "📦 **Sistema de Nomes de Itens - Gerenciamento de Nomes Personalizados**\n\n"
            "Aqui você pode gerenciar nomes personalizados para seus produtos:\n\n"
            "🎲 **Gerar Nomes Personalizados**: Cria nomes fantasia para todos os produtos\n"
            "✏️ **Atribuir Nome**: Define um nome específico para um produto\n"
            "👁️ **Ver Mapeamentos**: Lista todos os nomes personalizados existentes\n\n"
            "Escolha uma opção:"
        )

    def get_menu_state(self) -> int:
        """Get the menu state."""
        return ITEM_NAMING_MENU

    async def handle(self, request: HandlerRequest) -> HandlerResponse:
        """Handle item naming requests (not used in conversation handler implementation)."""
        return HandlerResponse(
            message="Item naming handle method called - not implemented for conversation handlers",
            next_state=ITEM_NAMING_MENU
        )


def get_item_naming_handler() -> ConversationHandler:
    """Get the item naming conversation handler."""
    handler = ItemNamingHandler()
    return handler.get_conversation_handler()