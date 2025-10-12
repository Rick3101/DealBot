"""
Brambler Handler - Pirate Name Management System
Handles consistent pirate name generation and custom assignment for buyers.
"""

import logging
from typing import Optional, List
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, filters

from handlers.base_handler import MenuHandlerBase, HandlerRequest, HandlerResponse, InteractionType, ContentType
from core.modern_service_container import get_brambler_service
from utils.permissions import require_permission


# Conversation states
BRAMBLER_MENU = 0
BRAMBLER_CUSTOM_BUYER_SELECT = 1
BRAMBLER_CUSTOM_NAME_INPUT = 2


class BramblerHandler(MenuHandlerBase):
    """Handler for pirate name management (Brambler system)."""

    def __init__(self):
        super().__init__("brambler")
        self.logger = logging.getLogger(__name__)

    def get_conversation_handler(self) -> ConversationHandler:
        """Get the conversation handler for brambler management."""
        return ConversationHandler(
            entry_points=[
                CommandHandler("brambler", self.start_brambler, filters.ChatType.PRIVATE),
            ],
            states={
                BRAMBLER_MENU: [
                    CallbackQueryHandler(self.brambler_menu_handler, pattern=r"^brambler_"),
                ],
                BRAMBLER_CUSTOM_BUYER_SELECT: [
                    CallbackQueryHandler(self.handle_buyer_selection, pattern=r"^brambler_buyer:"),
                    CallbackQueryHandler(self.brambler_menu_handler, pattern=r"^brambler_back$"),
                    CallbackQueryHandler(self.cancel_brambler, pattern=r"^brambler_cancel$"),
                ],
                BRAMBLER_CUSTOM_NAME_INPUT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_custom_name_input),
                    CallbackQueryHandler(self.brambler_menu_handler, pattern=r"^brambler_back$"),
                    CallbackQueryHandler(self.cancel_brambler, pattern=r"^brambler_cancel$"),
                ],
            },
            fallbacks=[
                CallbackQueryHandler(self.cancel_brambler, pattern=r"^brambler_cancel$"),
                CommandHandler("cancel", self.cancel_brambler),
            ],
            per_message=False,
        )

    @require_permission('admin')
    async def start_brambler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start brambler pirate name management."""
        request = self.create_request(update, context)

        message_text = (
            "🏴‍☠️ **Sistema Brambler - Gerenciamento de Nomes Piratas**\n\n"
            "Aqui você pode gerenciar os nomes de piratas dos seus compradores:\n\n"
            "🎲 **Gerar Nomes Aleatórios**: Cria nomes consistentes para todos os compradores\n"
            "✏️ **Atribuir Nome Personalizado**: Define um nome específico para um comprador\n"
            "👁️ **Ver Mapeamentos**: Lista todos os nomes de piratas existentes\n\n"
            "Escolha uma opção:"
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎲 Gerar Nomes Aleatórios", callback_data="brambler_generate_random")],
            [InlineKeyboardButton("✏️ Atribuir Nome Personalizado", callback_data="brambler_assign_custom")],
            [InlineKeyboardButton("👁️ Ver Mapeamentos", callback_data="brambler_view_mappings")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="brambler_cancel")]
        ])

        await update.message.reply_text(
            message_text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )

        return BRAMBLER_MENU

    async def brambler_menu_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle brambler menu callbacks."""
        query = update.callback_query

        # Handle cancel first before answering query
        if query.data == "brambler_cancel":
            return await self.cancel_brambler(update, context)

        await query.answer()

        request = self.create_request(update, context)

        if query.data == "brambler_generate_random":
            return await self.handle_generate_random_names(request)
        elif query.data == "brambler_assign_custom":
            return await self.show_buyer_selection(request)
        elif query.data == "brambler_view_mappings":
            return await self.show_pirate_mappings(request)
        elif query.data == "brambler_back":
            return await self.show_main_menu(request)

        return BRAMBLER_MENU

    async def handle_generate_random_names(self, request: HandlerRequest) -> int:
        """Generate random pirate names for all buyers."""
        try:
            brambler_service = get_brambler_service(request.context)

            # Get all available buyers
            available_buyers = brambler_service.get_available_buyers()

            if not available_buyers:
                message_text = (
                    "❌ **Nenhum comprador encontrado**\n\n"
                    "Não há compradores na base de dados.\n"
                    "Realize algumas vendas primeiro para ter compradores disponíveis."
                )
            else:
                # Generate consistent pirate names
                results = []
                new_count = 0
                existing_count = 0

                for buyer_name in available_buyers:
                    # Check if buyer already has a pirate name
                    existing_pirate = brambler_service.get_pirate_name_for_buyer(buyer_name)

                    if existing_pirate:
                        results.append(f"   🏴‍☠️ {buyer_name} → {existing_pirate} *(existente)*")
                        existing_count += 1
                    else:
                        # Generate new consistent pirate name
                        pirate_name = brambler_service._generate_deterministic_pirate_name(buyer_name)
                        # Store the mapping
                        brambler_service.create_global_pirate_mapping(buyer_name, pirate_name)
                        results.append(f"   🏴‍☠️ {buyer_name} → {pirate_name} *(novo)*")
                        new_count += 1

                message_text = (
                    f"🎲 **Nomes de Piratas Processados!**\n\n"
                    f"✅ **{len(available_buyers)}** compradores processados:\n"
                    f"🆕 **{new_count}** novos nomes gerados\n"
                    f"📋 **{existing_count}** nomes existentes\n\n"
                    "**Mapeamentos:**\n" + "\n".join(results)
                )

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="brambler_back")]
            ])

            await request.update.callback_query.edit_message_text(
                message_text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )

        except Exception as e:
            self.logger.error(f"Error generating random names: {e}", exc_info=True)
            await request.update.callback_query.edit_message_text(
                "❌ Erro ao gerar nomes aleatórios. Tente novamente.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Voltar", callback_data="brambler_back")]
                ])
            )

        return BRAMBLER_MENU

    async def show_buyer_selection(self, request: HandlerRequest) -> int:
        """Show buyer selection for custom name assignment."""
        try:
            brambler_service = get_brambler_service(request.context)
            available_buyers = brambler_service.get_available_buyers()

            if not available_buyers:
                message_text = (
                    "❌ **Nenhum comprador encontrado**\n\n"
                    "Não há compradores na base de dados para atribuir nomes personalizados."
                )
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Voltar", callback_data="brambler_back")]
                ])
            else:
                message_text = (
                    "✏️ **Atribuir Nome Personalizado**\n\n"
                    "Selecione um comprador para definir um nome de pirata personalizado:"
                )

                # Create buttons for buyers (max 10 per page for readability)
                buttons = []
                for buyer in available_buyers[:15]:  # Limit to first 15 for UI
                    current_pirate = brambler_service.get_pirate_name_for_buyer(buyer)
                    display_text = f"{buyer}"
                    if current_pirate:
                        display_text += f" → {current_pirate}"
                    buttons.append([InlineKeyboardButton(display_text, callback_data=f"brambler_buyer:{buyer}")])

                buttons.append([InlineKeyboardButton("🔙 Voltar", callback_data="brambler_back")])
                keyboard = InlineKeyboardMarkup(buttons)

            await request.update.callback_query.edit_message_text(
                message_text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )

            return BRAMBLER_CUSTOM_BUYER_SELECT

        except Exception as e:
            self.logger.error(f"Error showing buyer selection: {e}", exc_info=True)
            await request.update.callback_query.edit_message_text(
                "❌ Erro ao carregar compradores. Tente novamente.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Voltar", callback_data="brambler_back")]
                ])
            )
            return BRAMBLER_MENU

    async def handle_buyer_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle buyer selection for custom name assignment."""
        query = update.callback_query
        await query.answer()

        buyer_name = query.data.split(":", 1)[1]
        context.user_data['selected_buyer'] = buyer_name

        try:
            brambler_service = get_brambler_service(context)
            current_pirate = brambler_service.get_pirate_name_for_buyer(buyer_name)

            current_text = f" (atual: **{current_pirate}**)" if current_pirate else ""

            message_text = (
                f"✏️ **Definir Nome Personalizado**\n\n"
                f"Comprador selecionado: **{buyer_name}**{current_text}\n\n"
                f"Digite o nome de pirata personalizado que deseja atribuir a este comprador:\n\n"
                f"💡 *Exemplo: Capitão Barba Negra, Tempestade Vermelha, etc.*"
            )

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Voltar", callback_data="brambler_back")]
            ])

            await query.edit_message_text(
                message_text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )

            return BRAMBLER_CUSTOM_NAME_INPUT

        except Exception as e:
            self.logger.error(f"Error handling buyer selection: {e}", exc_info=True)
            await query.edit_message_text(
                "❌ Erro ao processar seleção. Tente novamente.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Voltar", callback_data="brambler_back")]
                ])
            )
            return BRAMBLER_CUSTOM_BUYER_SELECT

    async def handle_custom_name_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle custom pirate name input."""
        # 🔑 CRITICAL: Delete user's input message immediately per UX guide
        try:
            await update.message.delete()
        except Exception as e:
            self.logger.warning(f"Could not delete user input message: {e}")

        request = self.create_request(update, context)
        buyer_name = context.user_data.get('selected_buyer')
        custom_name = update.message.text.strip()

        if not buyer_name:
            await request.context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ Erro: Nenhum comprador selecionado. Use /brambler para começar novamente."
            )
            return ConversationHandler.END

        if not custom_name or len(custom_name) < 2:
            # Send error message with auto-deletion per UX guide (short delay for error messages)
            message = await request.context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ Nome muito curto. Digite um nome de pirata válido (mínimo 2 caracteres)."
            )
            # Auto-delete error message after 8 seconds per UX guide
            request.context.job_queue.run_once(
                lambda context: context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message.message_id),
                when=8
            )
            return BRAMBLER_CUSTOM_NAME_INPUT

        try:
            brambler_service = get_brambler_service(request.context)

            # Check if name already exists for another buyer
            existing_buyer = brambler_service.get_buyer_for_pirate_name(custom_name)
            if existing_buyer and existing_buyer != buyer_name:
                # Send error message with auto-deletion per UX guide
                message = await request.context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"❌ O nome **{custom_name}** já está sendo usado por **{existing_buyer}**.\n"
                         "Escolha um nome diferente.",
                    parse_mode='Markdown'
                )
                # Auto-delete error message after 8 seconds per UX guide
                request.context.job_queue.run_once(
                    lambda context: context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message.message_id),
                    when=8
                )
                return BRAMBLER_CUSTOM_NAME_INPUT

            # Create or update the mapping
            brambler_service.create_or_update_global_pirate_mapping(buyer_name, custom_name)

            message_text = (
                f"✅ **Nome Personalizado Atribuído!**\n\n"
                f"🏴‍☠️ **{buyer_name}** → **{custom_name}**\n\n"
                f"O comprador agora será conhecido como **{custom_name}** em todas as expedições."
            )

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✏️ Atribuir Outro Nome", callback_data="brambler_assign_custom")],
                [InlineKeyboardButton("🔙 Menu Principal", callback_data="brambler_back")]
            ])

            # Success message with manual control per UX guide (important content)
            await request.context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=message_text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )

            return BRAMBLER_MENU

        except Exception as e:
            self.logger.error(f"Error assigning custom name: {e}", exc_info=True)
            await request.context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ Erro ao atribuir nome personalizado. Tente novamente."
            )
            return BRAMBLER_CUSTOM_NAME_INPUT

    async def show_pirate_mappings(self, request: HandlerRequest) -> int:
        """Show all existing pirate name mappings."""
        try:
            brambler_service = get_brambler_service(request.context)
            all_mappings = brambler_service.get_all_pirate_mappings()

            if not all_mappings:
                message_text = (
                    "📋 **Mapeamentos de Nomes**\n\n"
                    "Nenhum mapeamento de nome de pirata encontrado.\n"
                    "Use 'Gerar Nomes Aleatórios' para criar mapeamentos."
                )
            else:
                mappings_text = []
                for buyer_name, pirate_name in all_mappings.items():
                    mappings_text.append(f"   🏴‍☠️ {buyer_name} → {pirate_name}")

                message_text = (
                    f"📋 **Mapeamentos de Nomes ({len(all_mappings)})**\n\n"
                    + "\n".join(mappings_text)
                )

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Voltar ao Menu", callback_data="brambler_back")]
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
                    [InlineKeyboardButton("🔙 Voltar", callback_data="brambler_back")]
                ])
            )

        return BRAMBLER_MENU

    async def show_main_menu(self, request: HandlerRequest) -> int:
        """Show the main brambler menu."""
        message_text = (
            "🏴‍☠️ **Sistema Brambler - Gerenciamento de Nomes Piratas**\n\n"
            "Aqui você pode gerenciar os nomes de piratas dos seus compradores:\n\n"
            "🎲 **Gerar Nomes Aleatórios**: Cria nomes consistentes para todos os compradores\n"
            "✏️ **Atribuir Nome Personalizado**: Define um nome específico para um comprador\n"
            "👁️ **Ver Mapeamentos**: Lista todos os nomes de piratas existentes\n\n"
            "Escolha uma opção:"
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎲 Gerar Nomes Aleatórios", callback_data="brambler_generate_random")],
            [InlineKeyboardButton("✏️ Atribuir Nome Personalizado", callback_data="brambler_assign_custom")],
            [InlineKeyboardButton("👁️ Ver Mapeamentos", callback_data="brambler_view_mappings")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="brambler_cancel")]
        ])

        await request.update.callback_query.edit_message_text(
            message_text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )

        return BRAMBLER_MENU

    async def cancel_brambler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel brambler conversation - instant deletion per UX guide."""
        if update.callback_query:
            try:
                # Answer callback query first
                await update.callback_query.answer()
                # Delete message immediately - NO confirmation message per UX guide
                await update.callback_query.message.delete()
            except Exception as e:
                self.logger.error(f"Failed to delete brambler menu message: {e}")

        # Clean up user data
        context.user_data.pop('selected_buyer', None)

        return ConversationHandler.END

    # Required abstract method implementations for MenuHandlerBase
    def create_main_menu_keyboard(self) -> InlineKeyboardMarkup:
        """Create the main brambler menu keyboard."""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🎲 Gerar Nomes Aleatórios", callback_data="brambler_generate_random")],
            [InlineKeyboardButton("✏️ Atribuir Nome Personalizado", callback_data="brambler_assign_custom")],
            [InlineKeyboardButton("👁️ Ver Mapeamentos", callback_data="brambler_view_mappings")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="brambler_cancel")]
        ])

    async def handle_menu_selection(self, request: HandlerRequest, selection: str) -> HandlerResponse:
        """Handle menu selection (not used in our implementation)."""
        return HandlerResponse(
            message="Menu selection not implemented for brambler",
            next_state=BRAMBLER_MENU
        )

    def get_menu_text(self) -> str:
        """Get the main menu text."""
        return (
            "🏴‍☠️ **Sistema Brambler - Gerenciamento de Nomes Piratas**\n\n"
            "Aqui você pode gerenciar os nomes de piratas dos seus compradores:\n\n"
            "🎲 **Gerar Nomes Aleatórios**: Cria nomes consistentes para todos os compradores\n"
            "✏️ **Atribuir Nome Personalizado**: Define um nome específico para um comprador\n"
            "👁️ **Ver Mapeamentos**: Lista todos os nomes de piratas existentes\n\n"
            "Escolha uma opção:"
        )

    def get_menu_state(self) -> int:
        """Get the menu state."""
        return BRAMBLER_MENU

    async def handle(self, request: HandlerRequest) -> HandlerResponse:
        """Handle brambler requests (not used in conversation handler implementation)."""
        return HandlerResponse(
            message="Brambler handle method called - not implemented for conversation handlers",
            next_state=BRAMBLER_MENU
        )


def get_brambler_handler() -> ConversationHandler:
    """Get the brambler conversation handler."""
    handler = BramblerHandler()
    return handler.get_conversation_handler()