from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from handlers.base_handler import MenuHandlerBase, HandlerRequest, HandlerResponse, InteractionType, ContentType, DelayConstants
from handlers.error_handler import with_error_boundary
from core.modern_service_container import get_expedition_service, get_brambler_service
from services.expedition_utilities_service import ExpeditionUtilitiesService
from utils.input_sanitizer import InputSanitizer
from utils.permissions import require_permission
from services.base_service import ValidationError, NotFoundError, ServiceError
from datetime import datetime, timedelta
import logging


# States
(EXPEDITION_MENU, EXPEDITION_CREATE_NAME,
 EXPEDITION_ADD_ITEMS, EXPEDITION_ADD_ITEM_PRODUCT, EXPEDITION_ADD_ITEM_QUANTITY, EXPEDITION_ADD_ITEM_PRICE, EXPEDITION_ADD_ITEM_COST,
 EXPEDITION_MANAGE_PIRATES, EXPEDITION_ADD_PIRATE, EXPEDITION_REMOVE_PIRATE, EXPEDITION_LIST_MENU,
 EXPEDITION_STATUS_MENU, EXPEDITION_ITEM_MENU, EXPEDITION_CUSTOM_ASSIGNMENT, EXPEDITION_CUSTOM_NAME_INPUT,
 EXPEDITION_CONSUME_MENU, EXPEDITION_CONSUME_SELECT_PIRATE, EXPEDITION_CONSUME_SELECT_ITEM,
 EXPEDITION_CONSUME_QUANTITY, EXPEDITION_CONSUME_PRICE) = range(20)


class ExpeditionHandler(MenuHandlerBase):
    """Handler for expedition management commands with conversation states and error boundaries."""

    def __init__(self):
        super().__init__("expedition")
        self.logger = logging.getLogger("handlers.expedition")

    def create_main_menu_keyboard(self) -> InlineKeyboardMarkup:
        """Create the main expedition menu keyboard."""
        keyboard = [
            [InlineKeyboardButton("🏴‍☠️ Nova Expedição", callback_data="exp_create")],
            [InlineKeyboardButton("📋 Minhas Expedições", callback_data="exp_list")],
            [InlineKeyboardButton("👥 Gerenciar Piratas", callback_data="exp_manage_pirates")],
            [InlineKeyboardButton("📦 Gerenciar Itens", callback_data="exp_manage_items")],
            [InlineKeyboardButton("📊 Status da Expedição", callback_data="exp_status")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="exp_cancel")]
        ]
        return InlineKeyboardMarkup(keyboard)

    def get_menu_text(self) -> str:
        return "🏴‍☠️ **Gerenciamento de Expedições**\n\nEscolha uma opção:"

    def get_menu_state(self) -> int:
        return EXPEDITION_MENU

    async def handle(self, request: HandlerRequest) -> HandlerResponse:
        """Handle initial expedition command."""
        # Clear previous data
        request.user_data.clear()
        request.context.chat_data.clear()

        return self.create_smart_response(
            message=self.get_menu_text(),
            keyboard=self.create_main_menu_keyboard(),
            interaction_type=InteractionType.MENU_NAVIGATION,
            content_type=ContentType.SELECTION,
            next_state=EXPEDITION_MENU
        )

    async def handle_menu_selection(self, request: HandlerRequest, selection: str) -> HandlerResponse:
        """Handle menu selections."""
        if selection == "exp_create":
            return self.create_smart_response(
                message="🏴‍☠️ **Nova Expedição**\n\nQual será o nome da expedição?",
                keyboard=None,
                interaction_type=InteractionType.FORM_INPUT,
                content_type=ContentType.INFO,
                next_state=EXPEDITION_CREATE_NAME
            )

        elif selection == "exp_list":
            return await self.list_expeditions_command(request)

        elif selection == "exp_manage_pirates":
            return await self.show_pirate_management_menu(request)

        elif selection == "exp_manage_items":
            return await self.show_item_management_menu(request)

        elif selection == "exp_status":
            return await self.show_status_selection(request)

        elif selection == "exp_cancel":
            # Pattern 2.1: Instant deletion for close/cancel - no confirmation message
            if hasattr(request.update, 'callback_query') and request.update.callback_query:
                try:
                    await request.update.callback_query.answer()
                    await request.update.callback_query.message.delete()
                except Exception as e:
                    self.logger.warning(f"Could not delete message: {e}")

            return HandlerResponse(
                message="",  # Empty message, conversation ends cleanly
                end_conversation=True
                # NO delay, NO confirmation message - instant clean dismissal
            )

        else:
            return self.create_smart_response(
                message="❌ Opção inválida.",
                keyboard=self.create_main_menu_keyboard(),
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.VALIDATION_ERROR,
                next_state=EXPEDITION_MENU
            )

    async def create_expedition_command(self, request: HandlerRequest) -> HandlerResponse:
        """Handle expedition name input and create expedition immediately."""
        try:
            # Delete user input message immediately for privacy
            await self.batch_cleanup_messages([request.update.message], strategy="instant")

            expedition_name = InputSanitizer.sanitize_text(request.update.message.text, max_length=100)

            # Create expedition using service
            expedition_service = get_expedition_service(request.context)

            # Create proper request object
            from models.expedition import ExpeditionCreateRequest
            expedition_request = ExpeditionCreateRequest(
                name=expedition_name,
                owner_chat_id=request.chat_id,
                deadline=None  # Deadline can be set later from details page
            )

            expedition = expedition_service.create_expedition(expedition_request)

            # Generate pirate name for the owner
            brambler_service = get_brambler_service(request.context)

            # Get owner username from user service
            from core.modern_service_container import get_user_service
            user_service = get_user_service(request.context)
            owner_user = user_service.get_user_by_chat_id(request.chat_id)
            owner_name = owner_user.username if owner_user else f"User_{request.chat_id}"

            pirate_names = brambler_service.generate_pirate_names(expedition.id, [owner_name])
            pirate_name = pirate_names[0].pirate_name if pirate_names else "Captain Anonymous"

            success_message = (
                f"✅ **Expedição Criada!**\n\n"
                f"🏴‍☠️ Nome: {expedition.name}\n"
                f"🦜 Seu nome pirata: **{pirate_name}**\n\n"
                f"*ID: {expedition.id}*\n\n"
                f"Use o menu de detalhes para adicionar itens, piratas e definir prazo."
            )

            return HandlerResponse(
                message=success_message,
                keyboard=None,
                end_conversation=True,
                edit_message=True,
                delay=DelayConstants.IMPORTANT
            )

        except ValueError as e:
            return self.create_smart_response(
                message=f"❌ {str(e)}\n\nDigite um nome válido para a expedição:",
                keyboard=None,
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.VALIDATION_ERROR,
                next_state=EXPEDITION_CREATE_NAME
            )
        except ServiceError as e:
            self.logger.error(f"Error creating expedition: {e}")

            # Pattern 2: Delete-and-Replace for workflow transition back to menu
            try:
                await request.update.message.delete()
            except Exception as e:
                self.logger.warning(f"Could not delete message during error recovery: {e}")

            return HandlerResponse(
                message="❌ Erro ao criar expedição. Tente novamente.",
                keyboard=self.create_main_menu_keyboard(),
                next_state=EXPEDITION_MENU
                # No edit_message - using delete-and-replace pattern
            )


    async def show_pirate_management_menu(self, request: HandlerRequest) -> HandlerResponse:
        """Show pirate management options."""
        try:
            expedition_service = get_expedition_service(request.context)
            expeditions = expedition_service.get_expeditions_by_owner(request.chat_id)

            if not expeditions:
                return self.create_smart_response(
                    message="🏴‍☠️ Você não possui expedições para gerenciar piratas.\n\nCrie uma expedição primeiro.",
                    keyboard=self.create_main_menu_keyboard(),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.INFO,
                    next_state=EXPEDITION_MENU
                )

            keyboard_buttons = []
            for expedition in expeditions:
                status_emoji = self._get_status_emoji(expedition.status)
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        f"{status_emoji} {expedition.name[:25]}{'...' if len(expedition.name) > 25 else ''}",
                        callback_data=f"exp_pirates:{expedition.id}"
                    )
                ])

            keyboard_buttons.append([InlineKeyboardButton("🔙 Voltar", callback_data="exp_back")])
            keyboard = InlineKeyboardMarkup(keyboard_buttons)

            return self.create_smart_response(
                message="👥 **Gerenciamento de Piratas**\n\nEscolha uma expedição para gerenciar piratas:",
                keyboard=keyboard,
                interaction_type=InteractionType.MENU_NAVIGATION,
                content_type=ContentType.SELECTION,
                next_state=EXPEDITION_MANAGE_PIRATES
            )

        except ServiceError as e:
            self.logger.error(f"Error showing pirate management: {e}")
            return self.create_smart_response(
                message="❌ Erro ao carregar expedições. Tente novamente.",
                keyboard=self.create_main_menu_keyboard(),
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.ERROR,
                next_state=EXPEDITION_MENU
            )

    async def show_item_management_menu(self, request: HandlerRequest) -> HandlerResponse:
        """Show item management options."""
        try:
            expedition_service = get_expedition_service(request.context)
            expeditions = expedition_service.get_expeditions_by_owner(request.chat_id)

            if not expeditions:
                return self.create_smart_response(
                    message="📦 Você não possui expedições para gerenciar itens.\n\nCrie uma expedição primeiro.",
                    keyboard=self.create_main_menu_keyboard(),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.INFO,
                    next_state=EXPEDITION_MENU
                )

            keyboard_buttons = []
            for expedition in expeditions:
                status_emoji = self._get_status_emoji(expedition.status)
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        f"{status_emoji} {expedition.name[:25]}{'...' if len(expedition.name) > 25 else ''}",
                        callback_data=f"exp_items:{expedition.id}"
                    )
                ])

            keyboard_buttons.append([InlineKeyboardButton("🔙 Voltar", callback_data="exp_back")])
            keyboard = InlineKeyboardMarkup(keyboard_buttons)

            return self.create_smart_response(
                message="📦 **Gerenciamento de Itens**\n\nEscolha uma expedição para gerenciar itens:",
                keyboard=keyboard,
                interaction_type=InteractionType.MENU_NAVIGATION,
                content_type=ContentType.SELECTION,
                next_state=EXPEDITION_ITEM_MENU
            )

        except ServiceError as e:
            self.logger.error(f"Error showing item management: {e}")
            return self.create_smart_response(
                message="❌ Erro ao carregar expedições. Tente novamente.",
                keyboard=self.create_main_menu_keyboard(),
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.ERROR,
                next_state=EXPEDITION_MENU
            )

    async def show_expedition_pirate_options(self, request: HandlerRequest, expedition_id: int) -> HandlerResponse:
        """Show pirate management options for specific expedition."""
        try:
            expedition_service = get_expedition_service(request.context)
            expedition = expedition_service.get_expedition_by_id(expedition_id)

            if not expedition or expedition.owner_chat_id != request.chat_id:
                return self.create_smart_response(
                    message="❌ Expedição não encontrada ou sem permissão.",
                    keyboard=self.create_main_menu_keyboard(),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.ERROR,
                    next_state=EXPEDITION_MENU
                )

            # Get current pirates
            brambler_service = get_brambler_service(request.context)
            pirates = brambler_service.get_expedition_pirate_names(expedition_id)

            message_lines = [
                f"👥 **Piratas da Expedição: {expedition.name}**\n"
            ]

            if pirates:
                message_lines.append("**Piratas atuais:**")
                for pirate in pirates:
                    message_lines.append(f"   🏴‍☠️ {pirate.pirate_name}")
                message_lines.append("")

            keyboard = [
                [InlineKeyboardButton("➕ Adicionar Pirata", callback_data=f"exp_add_pirate:{expedition_id}")],
                [InlineKeyboardButton("➖ Remover Pirata", callback_data=f"exp_remove_pirate:{expedition_id}")],
                [InlineKeyboardButton("🔙 Voltar", callback_data="exp_manage_pirates")]
            ]

            return self.create_smart_response(
                message="\n".join(message_lines),
                keyboard=InlineKeyboardMarkup(keyboard),
                interaction_type=InteractionType.MENU_NAVIGATION,
                content_type=ContentType.DATA,
                next_state=EXPEDITION_MANAGE_PIRATES
            )

        except ServiceError as e:
            self.logger.error(f"Error showing pirate options: {e}")
            return self.create_smart_response(
                message="❌ Erro ao carregar opções de piratas.",
                keyboard=self.create_main_menu_keyboard(),
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.ERROR,
                next_state=EXPEDITION_MENU
            )

    async def handle_generate_random_pirates(self, request: HandlerRequest, expedition_id: int) -> HandlerResponse:
        """Handle random pirate name generation for all available buyers."""
        try:
            expedition_service = get_expedition_service(request.context)
            expedition = expedition_service.get_expedition_by_id(expedition_id)

            if not expedition or expedition.owner_chat_id != request.chat_id:
                return self.create_smart_response(
                    message="❌ Expedição não encontrada ou sem permissão.",
                    keyboard=self.create_main_menu_keyboard(),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.ERROR,
                    next_state=EXPEDITION_MENU
                )

            # Get brambler service
            from core.modern_service_container import get_brambler_service
            brambler_service = get_brambler_service(request.context)

            # Get available buyers
            available_buyers = brambler_service.get_available_buyers()

            if not available_buyers:
                return self.create_smart_response(
                    message="❌ Nenhum comprador encontrado na base de dados.\n\nRealize algumas vendas primeiro para ter compradores disponíveis.",
                    keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data=f"exp_pirates:{expedition_id}")]]),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.INFO,
                    next_state=EXPEDITION_MANAGE_PIRATES
                )

            # Generate random pirate names for all buyers
            generated_pirates = brambler_service.generate_random_pirate_names_for_buyers(expedition_id, available_buyers)

            message_lines = [
                f"🎲 **Nomes de Piratas Gerados!**\n",
                f"✅ Gerados {len(generated_pirates)} nomes aleatórios para a expedição **{expedition.name}**\n"
            ]

            if generated_pirates:
                message_lines.append("**Novos Piratas:**")
                for pirate in generated_pirates:
                    message_lines.append(f"   🏴‍☠️ {pirate.original_name} → {pirate.pirate_name}")
            else:
                message_lines.append("ℹ️ Todos os compradores já possuem nomes de piratas nesta expedição.")

            return self.create_smart_response(
                message="\n".join(message_lines),
                keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data=f"exp_pirates:{expedition_id}")]]),
                interaction_type=InteractionType.REPORT_DISPLAY,
                content_type=ContentType.SUCCESS,
                next_state=EXPEDITION_MANAGE_PIRATES
            )

        except ServiceError as e:
            self.logger.error(f"Error generating random pirates: {e}")
            return self.create_smart_response(
                message=f"❌ Erro ao gerar nomes aleatórios: {str(e)}",
                keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data=f"exp_pirates:{expedition_id}")]]),
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.ERROR,
                next_state=EXPEDITION_MANAGE_PIRATES
            )

    async def start_custom_assignment_flow(self, request: HandlerRequest, expedition_id: int) -> HandlerResponse:
        """Start the custom pirate name assignment flow."""
        try:
            expedition_service = get_expedition_service(request.context)
            expedition = expedition_service.get_expedition_by_id(expedition_id)

            if not expedition or expedition.owner_chat_id != request.chat_id:
                return self.create_smart_response(
                    message="❌ Expedição não encontrada ou sem permissão.",
                    keyboard=self.create_main_menu_keyboard(),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.ERROR,
                    next_state=EXPEDITION_MENU
                )

            # Get brambler service
            from core.modern_service_container import get_brambler_service
            brambler_service = get_brambler_service(request.context)

            # Get available buyers (those without pirate names in this expedition)
            available_buyers = brambler_service.get_available_buyers()
            existing_pirates = brambler_service.get_expedition_pirate_names(expedition_id)
            existing_buyer_names = {pirate.original_name for pirate in existing_pirates}

            # Filter out buyers who already have pirate names
            available_buyers = [buyer for buyer in available_buyers if buyer not in existing_buyer_names]

            if not available_buyers:
                return self.create_smart_response(
                    message="❌ Nenhum comprador disponível para atribuição.\n\nTodos os compradores já possuem nomes de piratas nesta expedição.",
                    keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data=f"exp_pirates:{expedition_id}")]]),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.INFO,
                    next_state=EXPEDITION_MANAGE_PIRATES
                )

            # Store expedition ID for the flow
            request.user_data["expedition_id"] = expedition_id

            # Create buyer selection keyboard
            keyboard_buttons = []
            for buyer in available_buyers[:20]:  # Limit to 20 for UI
                keyboard_buttons.append([InlineKeyboardButton(f"👤 {buyer}", callback_data=f"exp_select_buyer:{buyer}")])

            keyboard_buttons.append([InlineKeyboardButton("🔙 Voltar", callback_data=f"exp_pirates:{expedition_id}")])

            return self.create_smart_response(
                message=f"✏️ **Atribuir Nome Personalizado**\n\nEscolha um comprador para atribuir um nome de pirata personalizado na expedição **{expedition.name}**:",
                keyboard=InlineKeyboardMarkup(keyboard_buttons),
                interaction_type=InteractionType.MENU_NAVIGATION,
                content_type=ContentType.SELECTION,
                next_state=EXPEDITION_CUSTOM_ASSIGNMENT
            )

        except ServiceError as e:
            self.logger.error(f"Error starting custom assignment flow: {e}")
            return self.create_smart_response(
                message=f"❌ Erro ao iniciar atribuição personalizada: {str(e)}",
                keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data=f"exp_pirates:{expedition_id}")]]),
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.ERROR,
                next_state=EXPEDITION_MANAGE_PIRATES
            )

    async def show_remove_pirate_options(self, request: HandlerRequest, expedition_id: int) -> HandlerResponse:
        """Show options to remove existing pirates."""
        try:
            expedition_service = get_expedition_service(request.context)
            expedition = expedition_service.get_expedition_by_id(expedition_id)

            if not expedition or expedition.owner_chat_id != request.chat_id:
                return self.create_smart_response(
                    message="❌ Expedição não encontrada ou sem permissão.",
                    keyboard=self.create_main_menu_keyboard(),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.ERROR,
                    next_state=EXPEDITION_MENU
                )

            # Get current pirates
            from core.modern_service_container import get_brambler_service
            brambler_service = get_brambler_service(request.context)
            pirates = brambler_service.get_expedition_pirate_names(expedition_id)

            if not pirates:
                return self.create_smart_response(
                    message="❌ Nenhum pirata encontrado nesta expedição.",
                    keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data=f"exp_pirates:{expedition_id}")]]),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.INFO,
                    next_state=EXPEDITION_MANAGE_PIRATES
                )

            # Create removal keyboard
            keyboard_buttons = []
            for pirate in pirates:
                keyboard_buttons.append([InlineKeyboardButton(
                    f"❌ {pirate.pirate_name}",
                    callback_data=f"exp_confirm_remove:{expedition_id}:{pirate.original_name}"
                )])

            keyboard_buttons.append([InlineKeyboardButton("🔙 Voltar", callback_data=f"exp_pirates:{expedition_id}")])

            return self.create_smart_response(
                message=f"➖ **Remover Pirata**\n\nEscolha um pirata para remover da expedição **{expedition.name}**:",
                keyboard=InlineKeyboardMarkup(keyboard_buttons),
                interaction_type=InteractionType.MENU_NAVIGATION,
                content_type=ContentType.SELECTION,
                next_state=EXPEDITION_MANAGE_PIRATES
            )

        except ServiceError as e:
            self.logger.error(f"Error showing remove pirate options: {e}")
            return self.create_smart_response(
                message=f"❌ Erro ao carregar piratas: {str(e)}",
                keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data=f"exp_pirates:{expedition_id}")]]),
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.ERROR,
                next_state=EXPEDITION_MANAGE_PIRATES
            )

    async def handle_buyer_selection(self, request: HandlerRequest, buyer_name: str) -> HandlerResponse:
        """Handle buyer selection for custom pirate name assignment."""
        try:
            expedition_id = request.user_data.get("expedition_id")
            if not expedition_id:
                return self.create_smart_response(
                    message="❌ Erro: Expedição não encontrada na sessão.",
                    keyboard=self.create_main_menu_keyboard(),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.ERROR,
                    next_state=EXPEDITION_MENU
                )

            # Store buyer name for the flow
            request.user_data["selected_buyer"] = buyer_name

            return self.create_smart_response(
                message=f"✏️ **Atribuir Nome Personalizado**\n\nComprador selecionado: **{buyer_name}**\n\nDigite o nome de pirata personalizado que deseja atribuir:",
                keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancelar", callback_data=f"exp_pirates:{expedition_id}")]]),
                interaction_type=InteractionType.INPUT_REQUEST,
                content_type=ContentType.INPUT,
                next_state=EXPEDITION_CUSTOM_NAME_INPUT
            )

        except Exception as e:
            self.logger.error(f"Error handling buyer selection: {e}")
            return self.create_smart_response(
                message="❌ Erro ao processar seleção de comprador.",
                keyboard=self.create_main_menu_keyboard(),
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.ERROR,
                next_state=EXPEDITION_MENU
            )

    async def handle_custom_pirate_name_input(self, request: HandlerRequest) -> HandlerResponse:
        """Handle custom pirate name input."""
        try:
            expedition_id = request.user_data.get("expedition_id")
            buyer_name = request.user_data.get("selected_buyer")

            if not expedition_id or not buyer_name:
                return self.create_smart_response(
                    message="❌ Erro: Dados da sessão perdidos.",
                    keyboard=self.create_main_menu_keyboard(),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.ERROR,
                    next_state=EXPEDITION_MENU
                )

            # Get and validate pirate name input
            pirate_name = request.message.text.strip()

            if not pirate_name:
                return self.create_smart_response(
                    message="❌ Nome de pirata não pode estar vazio. Digite um nome válido:",
                    keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancelar", callback_data=f"exp_pirates:{expedition_id}")]]),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.INPUT,
                    next_state=EXPEDITION_CUSTOM_NAME_INPUT
                )

            # Sanitize input
            pirate_name = InputSanitizer.sanitize_text_input(pirate_name)

            if len(pirate_name) > 50:
                return self.create_smart_response(
                    message="❌ Nome de pirata muito longo (máximo 50 caracteres). Digite um nome menor:",
                    keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancelar", callback_data=f"exp_pirates:{expedition_id}")]]),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.INPUT,
                    next_state=EXPEDITION_CUSTOM_NAME_INPUT
                )

            # Assign custom pirate name
            from core.modern_service_container import get_brambler_service
            brambler_service = get_brambler_service(request.context)

            pirate = brambler_service.assign_custom_pirate_name(expedition_id, buyer_name, pirate_name)

            if pirate:
                # Clear session data
                request.user_data.pop("expedition_id", None)
                request.user_data.pop("selected_buyer", None)

                return self.create_smart_response(
                    message=f"✅ **Nome de Pirata Atribuído!**\n\n👤 **{buyer_name}** agora é conhecido como:\n🏴‍☠️ **{pirate_name}**",
                    keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data=f"exp_pirates:{expedition_id}")]]),
                    interaction_type=InteractionType.REPORT_DISPLAY,
                    content_type=ContentType.SUCCESS,
                    next_state=EXPEDITION_MANAGE_PIRATES
                )
            else:
                return self.create_smart_response(
                    message="❌ Erro ao atribuir nome de pirata. Tente novamente:",
                    keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancelar", callback_data=f"exp_pirates:{expedition_id}")]]),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.INPUT,
                    next_state=EXPEDITION_CUSTOM_NAME_INPUT
                )

        except ValidationError as e:
            return self.create_smart_response(
                message=f"❌ {str(e)}\n\nDigite um nome de pirata diferente:",
                keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancelar", callback_data=f"exp_pirates:{expedition_id}")]]),
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.INPUT,
                next_state=EXPEDITION_CUSTOM_NAME_INPUT
            )
        except ServiceError as e:
            self.logger.error(f"Error assigning custom pirate name: {e}")
            return self.create_smart_response(
                message=f"❌ Erro ao atribuir nome: {str(e)}",
                keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data=f"exp_pirates:{expedition_id}")]]),
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.ERROR,
                next_state=EXPEDITION_MANAGE_PIRATES
            )

    async def handle_pirate_removal(self, request: HandlerRequest, expedition_id: int, buyer_name: str) -> HandlerResponse:
        """Handle pirate name removal confirmation."""
        try:
            expedition_service = get_expedition_service(request.context)
            expedition = expedition_service.get_expedition_by_id(expedition_id)

            if not expedition or expedition.owner_chat_id != request.chat_id:
                return self.create_smart_response(
                    message="❌ Expedição não encontrada ou sem permissão.",
                    keyboard=self.create_main_menu_keyboard(),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.ERROR,
                    next_state=EXPEDITION_MENU
                )

            # Remove pirate name
            from core.modern_service_container import get_brambler_service
            brambler_service = get_brambler_service(request.context)

            success = brambler_service.remove_pirate_name(expedition_id, buyer_name)

            if success:
                return self.create_smart_response(
                    message=f"✅ **Pirata Removido!**\n\nO comprador **{buyer_name}** foi removido da expedição **{expedition.name}**.",
                    keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data=f"exp_pirates:{expedition_id}")]]),
                    interaction_type=InteractionType.REPORT_DISPLAY,
                    content_type=ContentType.SUCCESS,
                    next_state=EXPEDITION_MANAGE_PIRATES
                )
            else:
                return self.create_smart_response(
                    message="❌ Erro ao remover pirata. Pirata não encontrado.",
                    keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data=f"exp_pirates:{expedition_id}")]]),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.ERROR,
                    next_state=EXPEDITION_MANAGE_PIRATES
                )

        except ServiceError as e:
            self.logger.error(f"Error removing pirate: {e}")
            return self.create_smart_response(
                message=f"❌ Erro ao remover pirata: {str(e)}",
                keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data=f"exp_pirates:{expedition_id}")]]),
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.ERROR,
                next_state=EXPEDITION_MANAGE_PIRATES
            )

    async def expedition_custom_name_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle custom pirate name input."""
        request = self.create_request(update, context)
        response = await self.handle_custom_pirate_name_input(request)
        return await self.send_response(response, request)

    async def show_expedition_item_options(self, request: HandlerRequest, expedition_id: int) -> HandlerResponse:
        """Show item management options for specific expedition."""
        try:
            expedition_service = get_expedition_service(request.context)
            expedition = expedition_service.get_expedition_by_id(expedition_id)

            if not expedition or expedition.owner_chat_id != request.chat_id:
                return self.create_smart_response(
                    message="❌ Expedição não encontrada ou sem permissão.",
                    keyboard=self.create_main_menu_keyboard(),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.ERROR,
                    next_state=EXPEDITION_MENU
                )

            # Get current items
            items = expedition_service.get_expedition_items(expedition_id)

            message_lines = [
                f"📦 **Itens da Expedição: {expedition.name}**\n"
            ]

            if items:
                message_lines.append("**Itens definidos:**")

                # Get product service to fetch product details
                from core.modern_service_container import get_product_service
                product_service = get_product_service(request.context)

                for item in items:
                    try:
                        # Get product details
                        product = product_service.get_product_by_id(item.produto_id)
                        product_name = self._get_product_display_name(product) if product else f"Produto {item.produto_id}"
                    except:
                        product_name = f"Produto {item.produto_id}"

                    message_lines.append(f"   📦 {product_name}: {item.quantity_required}x")
                    if hasattr(item, 'target_unit_price') and item.target_unit_price:
                        message_lines.append(f"      💰 Preço alvo: R$ {item.target_unit_price:.2f}")
                message_lines.append("")

            keyboard = [
                [InlineKeyboardButton("➕ Adicionar Item", callback_data=f"exp_add_item:{expedition_id}")],
                [InlineKeyboardButton("➖ Remover Item", callback_data=f"exp_remove_item:{expedition_id}")],
                [InlineKeyboardButton("🔙 Voltar", callback_data="exp_manage_items")]
            ]

            return self.create_smart_response(
                message="\n".join(message_lines),
                keyboard=InlineKeyboardMarkup(keyboard),
                interaction_type=InteractionType.MENU_NAVIGATION,
                content_type=ContentType.DATA,
                next_state=EXPEDITION_ITEM_MENU
            )

        except ServiceError as e:
            self.logger.error(f"Error showing item options: {e}")
            return self.create_smart_response(
                message="❌ Erro ao carregar opções de itens.",
                keyboard=self.create_main_menu_keyboard(),
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.ERROR,
                next_state=EXPEDITION_MENU
            )

    async def start_add_item_flow(self, request: HandlerRequest, expedition_id: int) -> HandlerResponse:
        """Start the flow to add an item to expedition."""
        try:
            expedition_service = get_expedition_service(request.context)
            expedition = expedition_service.get_expedition_by_id(expedition_id)

            if not expedition or expedition.owner_chat_id != request.chat_id:
                return self.create_smart_response(
                    message="❌ Expedição não encontrada ou sem permissão.",
                    keyboard=self.create_main_menu_keyboard(),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.ERROR,
                    next_state=EXPEDITION_MENU
                )

            # Store expedition ID for the flow
            request.user_data["expedition_id"] = expedition_id

            # Get available products
            from core.modern_service_container import get_product_service
            product_service = get_product_service(request.context)
            products = product_service.get_all_products()

            if not products:
                return self.create_smart_response(
                    message="❌ Nenhum produto encontrado para adicionar à expedição.",
                    keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data=f"exp_items:{expedition_id}")]]),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.ERROR,
                    next_state=EXPEDITION_ITEM_MENU
                )

            # Create keyboard with products
            keyboard_buttons = []
            for product in products:
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        self._get_product_display_name(product),
                        callback_data=f"exp_select_product:{product.id}"
                    )
                ])

            keyboard_buttons.append([InlineKeyboardButton("🔙 Voltar", callback_data=f"exp_items:{expedition_id}")])
            keyboard = InlineKeyboardMarkup(keyboard_buttons)

            return self.create_smart_response(
                message=f"📦 **Adicionar Item à Expedição: {expedition.name}**\n\nEscolha um produto:",
                keyboard=keyboard,
                interaction_type=InteractionType.MENU_NAVIGATION,
                content_type=ContentType.SELECTION,
                next_state=EXPEDITION_ADD_ITEM_PRODUCT
            )

        except ServiceError as e:
            self.logger.error(f"Error starting add item flow: {e}")
            return self.create_smart_response(
                message="❌ Erro ao iniciar adição de item.",
                keyboard=self.create_main_menu_keyboard(),
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.ERROR,
                next_state=EXPEDITION_MENU
            )

    async def start_remove_item_flow(self, request: HandlerRequest, expedition_id: int) -> HandlerResponse:
        """Start the flow to remove an item from expedition."""
        try:
            expedition_service = get_expedition_service(request.context)
            expedition = expedition_service.get_expedition_by_id(expedition_id)

            if not expedition or expedition.owner_chat_id != request.chat_id:
                return self.create_smart_response(
                    message="❌ Expedição não encontrada ou sem permissão.",
                    keyboard=self.create_main_menu_keyboard(),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.ERROR,
                    next_state=EXPEDITION_MENU
                )

            # Get current expedition items
            items = expedition_service.get_expedition_items(expedition_id)

            if not items:
                return self.create_smart_response(
                    message="❌ Esta expedição não possui itens para remover.",
                    keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data=f"exp_items:{expedition_id}")]]),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.ERROR,
                    next_state=EXPEDITION_ITEM_MENU
                )

            # Create keyboard with current items
            keyboard_buttons = []

            # Get product service to fetch product details
            from core.modern_service_container import get_product_service
            product_service = get_product_service(request.context)

            for item in items:
                try:
                    # Get product details for display
                    product = product_service.get_product_by_id(item.produto_id)
                    product_display = self._get_product_display_name(product) if product else f"Produto {item.produto_id}"
                except:
                    product_display = f"Produto {item.produto_id}"

                keyboard_buttons.append([
                    InlineKeyboardButton(
                        f"{product_display}: {item.quantity_required}x",
                        callback_data=f"exp_remove_product:{item.produto_id}:{expedition_id}"
                    )
                ])

            keyboard_buttons.append([InlineKeyboardButton("🔙 Voltar", callback_data=f"exp_items:{expedition_id}")])
            keyboard = InlineKeyboardMarkup(keyboard_buttons)

            return self.create_smart_response(
                message=f"📦 **Remover Item da Expedição: {expedition.name}**\n\nEscolha um item para remover:",
                keyboard=keyboard,
                interaction_type=InteractionType.MENU_NAVIGATION,
                content_type=ContentType.SELECTION,
                next_state=EXPEDITION_ITEM_MENU
            )

        except ServiceError as e:
            self.logger.error(f"Error starting remove item flow: {e}")
            return self.create_smart_response(
                message="❌ Erro ao iniciar remoção de item.",
                keyboard=self.create_main_menu_keyboard(),
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.ERROR,
                next_state=EXPEDITION_MENU
            )

    async def handle_product_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle product selection for adding to expedition."""
        query = update.callback_query
        await query.answer()

        request = self.create_request(update, context)
        product_id = int(query.data.split(":")[1])

        # Store product ID
        request.user_data["selected_product_id"] = product_id

        # Get product details for display
        try:
            from core.modern_service_container import get_product_service
            product_service = get_product_service(request.context)
            product = product_service.get_product_by_id(product_id)

            if not product:
                response = self.create_smart_response(
                    message="❌ Produto não encontrado.",
                    keyboard=self.create_main_menu_keyboard(),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.ERROR,
                    next_state=EXPEDITION_MENU
                )
            else:
                response = self.create_smart_response(
                    message=f"📦 **Produto selecionado:** {self._get_product_display_name(product)}\n\nQuantos itens precisam ser coletados?",
                    keyboard=None,
                    interaction_type=InteractionType.FORM_INPUT,
                    content_type=ContentType.INFO,
                    next_state=EXPEDITION_ADD_ITEM_QUANTITY
                )

        except ServiceError as e:
            self.logger.error(f"Error getting product details: {e}")
            response = self.create_smart_response(
                message="❌ Erro ao buscar produto.",
                keyboard=self.create_main_menu_keyboard(),
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.ERROR,
                next_state=EXPEDITION_MENU
            )

        return await self.send_response(response, request)

    async def handle_quantity_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle quantity input for expedition item."""
        request = self.create_request(update, context)

        try:
            # Delete user input message immediately
            await self.batch_cleanup_messages([update.message], strategy="instant")

            quantity = int(update.message.text.strip())
            if quantity <= 0:
                raise ValueError("Quantidade deve ser maior que zero")

            request.user_data["item_quantity"] = quantity

            response = self.create_smart_response(
                message=f"📦 **Quantidade:** {quantity} itens\n\nQual o preço alvo por unidade? (opcional - digite 0 para pular)",
                keyboard=None,
                interaction_type=InteractionType.FORM_INPUT,
                content_type=ContentType.INFO,
                next_state=EXPEDITION_ADD_ITEM_PRICE
            )

        except ValueError as e:
            response = self.create_smart_response(
                message=f"❌ {str(e)}\n\nDigite uma quantidade válida:",
                keyboard=None,
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.VALIDATION_ERROR,
                next_state=EXPEDITION_ADD_ITEM_QUANTITY
            )

        return await self.send_response(response, request)

    async def handle_price_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle price input for expedition item."""
        request = self.create_request(update, context)

        try:
            # Delete user input message immediately
            await self.batch_cleanup_messages([update.message], strategy="instant")

            price_text = update.message.text.strip()
            price = float(price_text) if price_text != "0" else 0.0

            # Store price for later use
            request.user_data["item_price"] = price

            price_display = f"R$ {price:.2f}" if price > 0 else "Não definido"
            response = self.create_smart_response(
                message=f"💰 **Preço:** {price_display}\n\nQual o custo por unidade? (digite 0 se não souber)",
                keyboard=None,
                interaction_type=InteractionType.FORM_INPUT,
                content_type=ContentType.INFO,
                next_state=EXPEDITION_ADD_ITEM_COST
            )

        except ValueError as e:
            response = self.create_smart_response(
                message=f"❌ {str(e)}\n\nDigite um preço válido (ou 0 para pular):",
                keyboard=None,
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.VALIDATION_ERROR,
                next_state=EXPEDITION_ADD_ITEM_PRICE
            )

        return await self.send_response(response, request)

    async def handle_cost_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle cost input for expedition item and finalize by adding to expedition and estoque."""
        request = self.create_request(update, context)

        try:
            # Delete user input message immediately
            await self.batch_cleanup_messages([update.message], strategy="instant")

            cost_text = update.message.text.strip()
            cost = float(cost_text) if cost_text != "0" else 0.0

            # Get all stored data
            expedition_id = request.user_data.get("expedition_id")
            product_id = request.user_data.get("selected_product_id")
            quantity = request.user_data.get("item_quantity")
            price = request.user_data.get("item_price", 0.0)

            if not all([expedition_id, product_id, quantity is not None]):
                raise ValueError("Dados da sessão perdidos. Tente novamente.")

            # Add item to expedition
            expedition_service = get_expedition_service(request.context)

            from models.expedition import ExpeditionItemRequest
            item_request = ExpeditionItemRequest(
                expedition_id=expedition_id,
                produto_id=product_id,
                quantity_required=quantity
            )

            expedition_service.add_expedition_item(item_request)

            # Add stock to estoque using unified business service
            from services.handler_business_service import HandlerBusinessService
            from models.handler_models import InventoryAddRequest

            business_service = HandlerBusinessService(request.context)
            inventory_request = InventoryAddRequest(
                product_id=product_id,
                quantity=quantity,
                unit_price=price,
                unit_cost=cost
            )

            inventory_response = business_service.add_inventory(inventory_request)

            # Get product name from the response
            product_name = inventory_response.product_name

            price_display = f"R$ {price:.2f}" if price > 0 else "Não definido"
            cost_display = f"R$ {cost:.2f}" if cost > 0 else "Não definido"

            success_message = (
                f"✅ **Item adicionado com sucesso!**\n\n"
                f"📦 Produto: {product_name}\n"
                f"📊 Quantidade: {quantity}\n"
                f"💰 Preço: {price_display}\n"
                f"💸 Custo: {cost_display}\n\n"
                f"📈 Estoque atualizado: +{quantity} itens (Total: {inventory_response.new_total})"
            )

            response = HandlerResponse(
                message=success_message,
                keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data=f"exp_items:{expedition_id}")]]),
                next_state=EXPEDITION_ITEM_MENU,
                edit_message=True,
                delay=DelayConstants.IMPORTANT
            )

        except ValueError as e:
            response = self.create_smart_response(
                message=f"❌ {str(e)}\n\nDigite um custo válido (ou 0 se não souber):",
                keyboard=None,
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.VALIDATION_ERROR,
                next_state=EXPEDITION_ADD_ITEM_COST
            )
        except ServiceError as e:
            self.logger.error(f"Error adding expedition item and stock: {e}")
            response = self.create_smart_response(
                message="❌ Erro ao adicionar item à expedição.",
                keyboard=self.create_main_menu_keyboard(),
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.ERROR,
                next_state=EXPEDITION_MENU
            )

        return await self.send_response(response, request)

    async def handle_product_removal(self, request: HandlerRequest, product_id: int, expedition_id: int) -> HandlerResponse:
        """Handle product removal from expedition."""
        try:
            expedition_service = get_expedition_service(request.context)
            expedition = expedition_service.get_expedition_by_id(expedition_id)

            if not expedition or expedition.owner_chat_id != request.chat_id:
                return self.create_smart_response(
                    message="❌ Expedição não encontrada ou sem permissão.",
                    keyboard=self.create_main_menu_keyboard(),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.ERROR,
                    next_state=EXPEDITION_MENU
                )

            # Remove the item
            expedition_service.remove_expedition_item(expedition_id, product_id)

            # Pattern 2: Instant Delete-and-Replace for workflow completion
            try:
                await request.update.callback_query.message.delete()
            except Exception as e:
                self.logger.warning(f"Could not delete message after item removal: {e}")

            return self.create_smart_response(
                message="✅ Item removido da expedição com sucesso!",
                keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data=f"exp_items:{expedition_id}")]]),
                interaction_type=InteractionType.CONFIRMATION,
                content_type=ContentType.SUCCESS,
                next_state=EXPEDITION_ITEM_MENU
            )

        except ServiceError as e:
            self.logger.error(f"Error removing expedition item: {e}")
            return self.create_smart_response(
                message="❌ Erro ao remover item da expedição.",
                keyboard=self.create_main_menu_keyboard(),
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.ERROR,
                next_state=EXPEDITION_MENU
            )

    async def list_expeditions_command(self, request: HandlerRequest) -> HandlerResponse:
        """List user's expeditions with message management."""
        try:
            expedition_service = get_expedition_service(request.context)
            expeditions = expedition_service.get_expeditions_by_owner(request.chat_id)

            if not expeditions:
                return self.create_smart_response(
                    message="🏴‍☠️ Você não possui expedições ativas.\n\nUse o menu para criar uma nova expedição.",
                    keyboard=self.create_main_menu_keyboard(),
                    interaction_type=InteractionType.REPORT_DISPLAY,
                    content_type=ContentType.INFO,
                    next_state=EXPEDITION_MENU
                )

            # Build expeditions list
            message_lines = ["🏴‍☠️ **Suas Expedições:**\n"]
            keyboard_buttons = []

            for expedition in expeditions:
                status_emoji = self._get_status_emoji(expedition.status)
                days_left = (expedition.deadline.date() - datetime.now().date()).days

                if days_left < 0:
                    time_info = f"⚠️ Vencida há {abs(days_left)} dias"
                elif days_left == 0:
                    time_info = "⏰ Vence hoje"
                else:
                    time_info = f"⏱️ {days_left} dias restantes"

                message_lines.append(
                    f"{status_emoji} **{expedition.name}**\n"
                    f"   {time_info}\n"
                    f"   *ID: {expedition.id}*\n"
                )

                # Add both detail view and consumption option for each expedition
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        f"📄 {expedition.name[:15]}{'...' if len(expedition.name) > 15 else ''}",
                        callback_data=f"exp_details:{expedition.id}"
                    ),
                    InlineKeyboardButton(
                        f"🍽️ Consumir",
                        callback_data=f"exp_consume:{expedition.id}"
                    )
                ])

            keyboard_buttons.append([InlineKeyboardButton("🔙 Voltar", callback_data="exp_back")])
            keyboard = InlineKeyboardMarkup(keyboard_buttons)

            return self.create_smart_response(
                message="\n".join(message_lines),
                keyboard=keyboard,
                interaction_type=InteractionType.REPORT_DISPLAY,
                content_type=ContentType.DATA,
                next_state=EXPEDITION_LIST_MENU
            )

        except ServiceError as e:
            self.logger.error(f"Error listing expeditions: {e}")
            return self.create_smart_response(
                message="❌ Erro ao listar expedições. Tente novamente.",
                keyboard=self.create_main_menu_keyboard(),
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.ERROR,
                next_state=EXPEDITION_MENU
            )

    async def show_status_selection(self, request: HandlerRequest) -> HandlerResponse:
        """Show expedition status selection."""
        try:
            expedition_service = get_expedition_service(request.context)
            expeditions = expedition_service.get_expeditions_by_owner(request.chat_id)

            if not expeditions:
                return self.create_smart_response(
                    message="🏴‍☠️ Você não possui expedições para verificar status.",
                    keyboard=self.create_main_menu_keyboard(),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.INFO,
                    next_state=EXPEDITION_MENU
                )

            keyboard_buttons = []
            for expedition in expeditions:
                status_emoji = self._get_status_emoji(expedition.status)
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        f"{status_emoji} {expedition.name[:25]}{'...' if len(expedition.name) > 25 else ''}",
                        callback_data=f"exp_status_detail:{expedition.id}"
                    )
                ])

            keyboard_buttons.append([InlineKeyboardButton("🔙 Voltar", callback_data="exp_back")])
            keyboard = InlineKeyboardMarkup(keyboard_buttons)

            return self.create_smart_response(
                message="📊 **Status das Expedições**\n\nEscolha uma expedição para ver detalhes:",
                keyboard=keyboard,
                interaction_type=InteractionType.MENU_NAVIGATION,
                content_type=ContentType.SELECTION,
                next_state=EXPEDITION_STATUS_MENU
            )

        except ServiceError as e:
            self.logger.error(f"Error showing status selection: {e}")
            return self.create_smart_response(
                message="❌ Erro ao carregar expedições. Tente novamente.",
                keyboard=self.create_main_menu_keyboard(),
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.ERROR,
                next_state=EXPEDITION_MENU
            )

    async def expedition_status_command(self, request: HandlerRequest, expedition_id: int) -> HandlerResponse:
        """Show detailed expedition status with auto-cleanup."""
        try:
            expedition_service = get_expedition_service(request.context)
            expedition = expedition_service.get_expedition_by_id(expedition_id)

            if not expedition:
                return self.create_smart_response(
                    message="❌ Expedição não encontrada.",
                    keyboard=self.create_main_menu_keyboard(),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.ERROR,
                    next_state=EXPEDITION_MENU
                )

            # Verify ownership
            if expedition.owner_chat_id != request.chat_id:
                return self.create_smart_response(
                    message="⛔ Você não tem permissão para ver esta expedição.",
                    keyboard=self.create_main_menu_keyboard(),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.ERROR,
                    next_state=EXPEDITION_MENU
                )

            # Get expedition items and progress
            items = expedition_service.get_expedition_items(expedition_id)
            progress_info = expedition_service.get_expedition_progress(expedition_id)

            # Build status message
            status_emoji = self._get_status_emoji(expedition.status)
            days_left = (expedition.deadline.date() - datetime.now().date()).days

            if days_left < 0:
                time_info = f"⚠️ **Vencida há {abs(days_left)} dias**"
            elif days_left == 0:
                time_info = "⏰ **Vence hoje!**"
            elif days_left <= 3:
                time_info = f"🔥 **{days_left} dias restantes!**"
            else:
                time_info = f"⏱️ {days_left} dias restantes"

            message_lines = [
                f"📊 **Status da Expedição**\n",
                f"{status_emoji} **{expedition.name}**",
                f"{time_info}",
                f"📅 Criada: {expedition.created_at.strftime('%d/%m/%Y %H:%M')}",
                f"🎯 Prazo: {expedition.deadline.strftime('%d/%m/%Y')}",
                f"📈 Progresso: {progress_info.get('completion_percentage', 0):.1f}%\n"
            ]

            if items:
                message_lines.append("📦 **Itens da Expedição:**")
                for item in items:
                    consumed = progress_info.get('items_consumed', {}).get(str(item.produto_id), 0)
                    remaining = item.quantity_required - consumed

                    if remaining <= 0:
                        status_icon = "✅"
                    elif consumed > 0:
                        status_icon = "🔄"
                    else:
                        status_icon = "⏳"

                    message_lines.append(
                        f"   {status_icon} {item.produto_id}: {consumed}/{item.quantity_required}"
                    )
            else:
                message_lines.append("📦 Nenhum item adicionado ainda")

            # Add action buttons
            keyboard_buttons = [
                [InlineKeyboardButton("🔙 Voltar", callback_data="exp_status")]
            ]
            keyboard = InlineKeyboardMarkup(keyboard_buttons)

            return self.create_smart_response(
                message="\n".join(message_lines),
                keyboard=keyboard,
                interaction_type=InteractionType.REPORT_DISPLAY,
                content_type=ContentType.DATA,
                next_state=EXPEDITION_STATUS_MENU
                # Longer display time for detailed info handled by base handler
            )

        except ServiceError as e:
            self.logger.error(f"Error getting expedition status: {e}")
            return self.create_smart_response(
                message="❌ Erro ao carregar status da expedição.",
                keyboard=self.create_main_menu_keyboard(),
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.ERROR,
                next_state=EXPEDITION_MENU
            )

    def _get_status_emoji(self, status: str) -> str:
        """Get emoji for expedition status."""
        status_emojis = {
            "planning": "📋",
            "active": "🏴‍☠️",
            "completed": "✅",
            "failed": "💀",
            "cancelled": "❌"
        }
        return status_emojis.get(status, "🏴‍☠️")

    def _get_product_display_name(self, product) -> str:
        """Get display name for a product, preferring custom name if available."""
        if not product:
            return "Produto Desconhecido"

        try:
            # Try to get custom name from item mappings
            utils_service = ExpeditionUtilitiesService()
            custom_name = utils_service.get_custom_name_for_product(product.nome)

            if custom_name:
                return f"{product.emoji} {custom_name}"
            else:
                return f"{product.emoji} {product.nome}"
        except Exception as e:
            self.logger.warning(f"Error getting custom product name: {e}")
            return f"{product.emoji} {product.nome}"

    # Wrapper methods for conversation handler
    @with_error_boundary("expedition_start")
    @require_permission("owner")
    async def start_expedition(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return await self.safe_handle(self.handle, update, context)

    @with_error_boundary("expedition_menu")
    async def expedition_menu_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        request = self.create_request(update, context)
        response = await self.handle_menu_selection(request, query.data)
        return await self.send_response(response, request)

    @with_error_boundary("expedition_create_name")
    async def expedition_create_name_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        request = self.create_request(update, context)
        response = await self.create_expedition_command(request)
        return await self.send_response(response, request)


    @with_error_boundary("expedition_pirate")
    async def expedition_pirate_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        request = self.create_request(update, context)

        if query.data == "exp_manage_pirates":
            response = await self.show_pirate_management_menu(request)
        elif query.data.startswith("exp_pirates:"):
            expedition_id = int(query.data.split(":")[1])
            response = await self.show_expedition_pirate_options(request, expedition_id)
        elif query.data.startswith("exp_add_pirate:"):
            expedition_id = int(query.data.split(":")[1])
            response = await self.show_add_pirate_selection(request, expedition_id)
        elif query.data.startswith("exp_select_buyer:"):
            parts = query.data.split(":", 2)
            buyer_name = parts[1]
            expedition_id = int(parts[2])
            response = await self.handle_buyer_addition(request, expedition_id, buyer_name)
        elif query.data.startswith("exp_generate_random:"):
            expedition_id = int(query.data.split(":")[1])
            response = await self.handle_generate_random_pirates(request, expedition_id)
        elif query.data.startswith("exp_assign_custom:"):
            expedition_id = int(query.data.split(":")[1])
            response = await self.start_custom_assignment_flow(request, expedition_id)
        elif query.data.startswith("exp_remove_pirate:"):
            expedition_id = int(query.data.split(":")[1])
            response = await self.show_remove_pirate_options(request, expedition_id)
        elif query.data.startswith("exp_select_buyer:"):
            buyer_name = query.data.split(":", 1)[1]
            response = await self.handle_buyer_selection(request, buyer_name)
        elif query.data.startswith("exp_confirm_remove:"):
            parts = query.data.split(":", 2)
            expedition_id = int(parts[1])
            buyer_name = parts[2]
            response = await self.handle_pirate_removal(request, expedition_id, buyer_name)
        elif query.data == "exp_back":
            # Pattern 2: Instant Delete-and-Replace for workflow transitions
            try:
                await request.update.callback_query.message.delete()
            except Exception as e:
                self.logger.warning(f"Could not delete message on back: {e}")

            response = self.create_smart_response(
                message=self.get_menu_text(),
                keyboard=self.create_main_menu_keyboard(),
                interaction_type=InteractionType.MENU_NAVIGATION,
                content_type=ContentType.SELECTION,
                next_state=EXPEDITION_MENU
            )
        else:
            response = await self.show_pirate_management_menu(request)

        return await self.send_response(response, request)

    @with_error_boundary("expedition_item")
    async def expedition_item_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        request = self.create_request(update, context)

        if query.data == "exp_manage_items":
            response = await self.show_item_management_menu(request)
        elif query.data.startswith("exp_items:"):
            expedition_id = int(query.data.split(":")[1])
            response = await self.show_expedition_item_options(request, expedition_id)
        elif query.data.startswith("exp_add_item:"):
            expedition_id = int(query.data.split(":")[1])
            response = await self.start_add_item_flow(request, expedition_id)
        elif query.data.startswith("exp_remove_item:"):
            expedition_id = int(query.data.split(":")[1])
            response = await self.start_remove_item_flow(request, expedition_id)
        elif query.data.startswith("exp_remove_product:"):
            parts = query.data.split(":")
            product_id = int(parts[1])
            expedition_id = int(parts[2])
            response = await self.handle_product_removal(request, product_id, expedition_id)
        elif query.data == "exp_back":
            # Pattern 2: Instant Delete-and-Replace for workflow transitions
            try:
                await request.update.callback_query.message.delete()
            except Exception as e:
                self.logger.warning(f"Could not delete message on back: {e}")

            response = self.create_smart_response(
                message=self.get_menu_text(),
                keyboard=self.create_main_menu_keyboard(),
                interaction_type=InteractionType.MENU_NAVIGATION,
                content_type=ContentType.SELECTION,
                next_state=EXPEDITION_MENU
            )
        else:
            response = await self.show_item_management_menu(request)

        return await self.send_response(response, request)

    @with_error_boundary("expedition_list")
    async def expedition_list_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        request = self.create_request(update, context)

        if query.data == "exp_back":
            # Pattern 2: Instant Delete-and-Replace for workflow transitions
            try:
                await request.update.callback_query.message.delete()
            except Exception as e:
                self.logger.warning(f"Could not delete message on back: {e}")

            response = self.create_smart_response(
                message=self.get_menu_text(),
                keyboard=self.create_main_menu_keyboard(),
                interaction_type=InteractionType.MENU_NAVIGATION,
                content_type=ContentType.SELECTION,
                next_state=EXPEDITION_MENU
            )
        elif query.data.startswith("exp_details:"):
            expedition_id = int(query.data.split(":")[1])
            response = await self.expedition_status_command(request, expedition_id)
        elif query.data.startswith("exp_consume:"):
            expedition_id = int(query.data.split(":")[1])
            response = await self.start_consumption_flow(request, expedition_id)
        else:
            response = await self.list_expeditions_command(request)

        return await self.send_response(response, request)

    @with_error_boundary("expedition_status")
    async def expedition_status_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        request = self.create_request(update, context)

        if query.data == "exp_status":
            response = await self.show_status_selection(request)
        elif query.data.startswith("exp_status_detail:"):
            expedition_id = int(query.data.split(":")[1])
            response = await self.expedition_status_command(request, expedition_id)
        elif query.data == "exp_back":
            # Pattern 2: Instant Delete-and-Replace for workflow transitions
            try:
                await request.update.callback_query.message.delete()
            except Exception as e:
                self.logger.warning(f"Could not delete message on back: {e}")

            response = self.create_smart_response(
                message=self.get_menu_text(),
                keyboard=self.create_main_menu_keyboard(),
                interaction_type=InteractionType.MENU_NAVIGATION,
                content_type=ContentType.SELECTION,
                next_state=EXPEDITION_MENU
            )
        else:
            response = await self.show_status_selection(request)

        return await self.send_response(response, request)

    @with_error_boundary("expedition_quantity")
    async def handle_quantity_input_wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return await self.handle_quantity_input(update, context)

    @with_error_boundary("expedition_price")
    async def handle_price_input_wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return await self.handle_price_input(update, context)

    @with_error_boundary("expedition_cost")
    async def handle_cost_input_wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return await self.handle_cost_input(update, context)

    @with_error_boundary("expedition_cancel")
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle cancel command - Pattern 2.1: Instant deletion without confirmation."""
        # Delete the message directly if it's a callback query
        if hasattr(update, 'callback_query') and update.callback_query:
            try:
                await update.callback_query.answer()
                await update.callback_query.message.delete()
            except Exception as e:
                self.logger.warning(f"Could not delete message during cancel: {e}")

        request = self.create_request(update, context)
        response = HandlerResponse(
            message="",  # Empty message, conversation ends cleanly
            end_conversation=True
            # NO delay, NO confirmation message - instant clean dismissal
        )
        return await self.send_response(response, request)

    @with_error_boundary("expedition_consumption")
    async def expedition_consumption_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle consumption-related callback queries."""
        query = update.callback_query
        await query.answer()

        request = self.create_request(update, context)

        if query.data.startswith("exp_consume_pirate:"):
            # Parse pirate selection: exp_consume_pirate:consumer_name:pirate_name
            parts = query.data.split(":", 2)
            consumer_name = parts[1]
            pirate_name = parts[2]
            response = await self.handle_pirate_selection_for_consumption(request, consumer_name, pirate_name)
        elif query.data.startswith("exp_consume_item:"):
            # Parse item selection: exp_consume_item:item_id:product_id
            parts = query.data.split(":")
            item_id = int(parts[1])
            product_id = int(parts[2])
            response = await self.handle_item_selection_for_consumption(request, item_id, product_id)
        elif query.data == "exp_list":
            response = await self.list_expeditions_command(request)
        else:
            response = await self.list_expeditions_command(request)

        return await self.send_response(response, request)

    @with_error_boundary("expedition_consume_quantity")
    async def handle_consumption_quantity_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle quantity input for consumption."""
        request = self.create_request(update, context)
        response = await self.handle_quantity_input_for_consumption(request)
        return await self.send_response(response, request)

    @with_error_boundary("expedition_consume_price")
    async def handle_consumption_price_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle price input for consumption."""
        request = self.create_request(update, context)
        response = await self.handle_price_input_for_consumption(request)
        return await self.send_response(response, request)

    async def show_add_pirate_selection(self, request: HandlerRequest, expedition_id: int) -> HandlerResponse:
        """Show selection of available buyers to add to expedition."""
        try:
            expedition_service = get_expedition_service(request.context)
            expedition = expedition_service.get_expedition_by_id(expedition_id)

            if not expedition or expedition.owner_chat_id != request.chat_id:
                return self.create_smart_response(
                    message="❌ Expedição não encontrada ou sem permissão.",
                    keyboard=self.create_main_menu_keyboard(),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.ERROR,
                    next_state=EXPEDITION_MENU
                )

            # Get brambler service
            from core.modern_service_container import get_brambler_service
            brambler_service = get_brambler_service(request.context)

            # Get buyers who have global pirate names
            all_pirate_mappings = brambler_service.get_all_pirate_mappings()
            buyers_with_pirate_names = list(all_pirate_mappings.keys())

            if not buyers_with_pirate_names:
                return self.create_smart_response(
                    message="❌ Não há compradores com nomes de piratas.\n\nUse o comando /brambler primeiro para criar nomes de piratas globais.",
                    keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data=f"exp_pirates:{expedition_id}")]]),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.ERROR,
                    next_state=EXPEDITION_MANAGE_PIRATES
                )

            # Get current pirates in this expedition to exclude them
            current_pirates = brambler_service.get_expedition_pirate_names(expedition_id)
            current_buyer_names = [p.original_name for p in current_pirates]

            # Filter out buyers already in this expedition
            available_buyers = [buyer for buyer in buyers_with_pirate_names if buyer not in current_buyer_names]

            if not available_buyers:
                return self.create_smart_response(
                    message="❌ Todos os compradores com nomes de piratas já estão nesta expedição.",
                    keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data=f"exp_pirates:{expedition_id}")]]),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.ERROR,
                    next_state=EXPEDITION_MANAGE_PIRATES
                )

            # Create keyboard with available buyers and their pirate names
            keyboard_buttons = []
            for buyer_name in available_buyers[:20]:  # Limit to 20 for UI
                pirate_name = all_pirate_mappings[buyer_name]
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        f"👤 {buyer_name} → 🏴‍☠️ {pirate_name}",
                        callback_data=f"exp_select_buyer:{buyer_name}:{expedition_id}"
                    )
                ])

            keyboard_buttons.append([InlineKeyboardButton("🔙 Voltar", callback_data=f"exp_pirates:{expedition_id}")])
            keyboard = InlineKeyboardMarkup(keyboard_buttons)

            return self.create_smart_response(
                message=f"➕ **Adicionar Pirata à Expedição: {expedition.name}**\n\nEscolha um comprador com nome de pirata para adicionar:",
                keyboard=keyboard,
                interaction_type=InteractionType.MENU_NAVIGATION,
                content_type=ContentType.SELECTION,
                next_state=EXPEDITION_MANAGE_PIRATES
            )

        except ServiceError as e:
            self.logger.error(f"Error showing add pirate selection: {e}")
            return self.create_smart_response(
                message="❌ Erro ao carregar compradores disponíveis.",
                keyboard=self.create_main_menu_keyboard(),
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.ERROR,
                next_state=EXPEDITION_MENU
            )

    async def handle_buyer_addition(self, request: HandlerRequest, expedition_id: int, buyer_name: str) -> HandlerResponse:
        """Handle adding a buyer to an expedition with generated pirate name."""
        try:
            expedition_service = get_expedition_service(request.context)
            expedition = expedition_service.get_expedition_by_id(expedition_id)

            if not expedition or expedition.owner_chat_id != request.chat_id:
                return self.create_smart_response(
                    message="❌ Expedição não encontrada ou sem permissão.",
                    keyboard=self.create_main_menu_keyboard(),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.ERROR,
                    next_state=EXPEDITION_MENU
                )

            # Get brambler service
            from core.modern_service_container import get_brambler_service
            brambler_service = get_brambler_service(request.context)

            # Add buyer to expedition with generated pirate name
            success = brambler_service.add_pirate_to_expedition(expedition_id, buyer_name)

            if success:
                # Get the global pirate name for display
                global_pirate_name = brambler_service.get_pirate_name_for_buyer(buyer_name)

                return self.create_smart_response(
                    message=f"✅ **Pirata Adicionado!**\n\n👤 **{buyer_name}** (🏴‍☠️ **{global_pirate_name}**) foi adicionado à expedição.",
                    keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data=f"exp_pirates:{expedition_id}")]]),
                    interaction_type=InteractionType.REPORT_DISPLAY,
                    content_type=ContentType.SUCCESS,
                    next_state=EXPEDITION_MANAGE_PIRATES
                )
            else:
                return self.create_smart_response(
                    message=f"❌ Erro ao adicionar comprador {buyer_name} à expedição.",
                    keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data=f"exp_pirates:{expedition_id}")]]),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.ERROR,
                    next_state=EXPEDITION_MANAGE_PIRATES
                )

        except ServiceError as e:
            self.logger.error(f"Error adding buyer to expedition: {e}")
            return self.create_smart_response(
                message="❌ Erro ao adicionar comprador à expedição.",
                keyboard=self.create_main_menu_keyboard(),
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.ERROR,
                next_state=EXPEDITION_MENU
            )

    async def start_consumption_flow(self, request: HandlerRequest, expedition_id: int) -> HandlerResponse:
        """Start the item consumption flow for an expedition."""
        try:
            expedition_service = get_expedition_service(request.context)
            expedition = expedition_service.get_expedition_by_id(expedition_id)

            if not expedition:
                return self.create_smart_response(
                    message="❌ Expedição não encontrada.",
                    keyboard=self.create_main_menu_keyboard(),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.ERROR,
                    next_state=EXPEDITION_MENU
                )

            # Check if user has permission to consume (owner or has pirate name)
            brambler_service = get_brambler_service(request.context)
            expedition_pirates = brambler_service.get_expedition_pirate_names(expedition_id)

            # Get user info to check permissions
            from core.modern_service_container import get_user_service
            user_service = get_user_service(request.context)
            user = user_service.get_user_by_chat_id(request.chat_id)
            user_name = user.username if user else f"User_{request.chat_id}"

            is_owner = expedition.owner_chat_id == request.chat_id
            user_pirate = next((p for p in expedition_pirates if p.original_name == user_name), None)

            if not is_owner and not user_pirate:
                return self.create_smart_response(
                    message="⛔ Você não tem permissão para consumir itens desta expedição.\n\nApenas o dono da expedição ou piratas registrados podem consumir itens.",
                    keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data="exp_list")]]),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.ERROR,
                    next_state=EXPEDITION_LIST_MENU
                )

            # Get expedition items
            items = expedition_service.get_expedition_items(expedition_id)
            if not items:
                return self.create_smart_response(
                    message="📦 Esta expedição não possui itens para consumir.",
                    keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data="exp_list")]]),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.INFO,
                    next_state=EXPEDITION_LIST_MENU
                )

            # Check if there are items available for consumption
            consumable_items = [item for item in items if (item.quantity_consumed or 0) < item.quantity_required]
            if not consumable_items:
                return self.create_smart_response(
                    message="✅ Todos os itens desta expedição já foram totalmente consumidos.",
                    keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data="exp_list")]]),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.INFO,
                    next_state=EXPEDITION_LIST_MENU
                )

            # Store expedition ID for the consumption flow
            request.user_data["consume_expedition_id"] = expedition_id

            # Show pirate selection if owner, or directly proceed if user has pirate name
            if is_owner:
                # Owner can choose any pirate
                return await self.show_pirate_selection_for_consumption(request, expedition_id)
            else:
                # User can only consume with their own pirate name
                request.user_data["consume_pirate_name"] = user_pirate.pirate_name
                request.user_data["consume_consumer_name"] = user_name
                return await self.show_item_selection_for_consumption(request, expedition_id)

        except ServiceError as e:
            self.logger.error(f"Error starting consumption flow: {e}")
            return self.create_smart_response(
                message="❌ Erro ao iniciar consumo de itens. Tente novamente.",
                keyboard=self.create_main_menu_keyboard(),
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.ERROR,
                next_state=EXPEDITION_MENU
            )

    async def show_pirate_selection_for_consumption(self, request: HandlerRequest, expedition_id: int) -> HandlerResponse:
        """Show pirate selection for consumption (owner only)."""
        try:
            expedition_service = get_expedition_service(request.context)
            expedition = expedition_service.get_expedition_by_id(expedition_id)

            brambler_service = get_brambler_service(request.context)
            pirates = brambler_service.get_expedition_pirate_names(expedition_id)

            if not pirates:
                return self.create_smart_response(
                    message="❌ Nenhum pirata registrado nesta expedição.\n\nAdicione piratas primeiro para poder consumir itens.",
                    keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data="exp_list")]]),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.ERROR,
                    next_state=EXPEDITION_LIST_MENU
                )

            # Create pirate selection keyboard
            keyboard_buttons = []
            for pirate in pirates:
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        f"🏴‍☠️ {pirate.pirate_name}",
                        callback_data=f"exp_consume_pirate:{pirate.original_name}:{pirate.pirate_name}"
                    )
                ])

            keyboard_buttons.append([InlineKeyboardButton("🔙 Voltar", callback_data="exp_list")])
            keyboard = InlineKeyboardMarkup(keyboard_buttons)

            return self.create_smart_response(
                message=f"🍽️ **Consumir Itens - {expedition.name}**\n\nEscolha qual pirata irá consumir os itens:",
                keyboard=keyboard,
                interaction_type=InteractionType.MENU_NAVIGATION,
                content_type=ContentType.SELECTION,
                next_state=EXPEDITION_CONSUME_SELECT_PIRATE
            )

        except ServiceError as e:
            self.logger.error(f"Error showing pirate selection: {e}")
            return self.create_smart_response(
                message="❌ Erro ao carregar piratas da expedição.",
                keyboard=self.create_main_menu_keyboard(),
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.ERROR,
                next_state=EXPEDITION_MENU
            )

    async def handle_pirate_selection_for_consumption(self, request: HandlerRequest, consumer_name: str, pirate_name: str) -> HandlerResponse:
        """Handle pirate selection for consumption."""
        expedition_id = request.user_data.get("consume_expedition_id")
        if not expedition_id:
            return self.create_smart_response(
                message="❌ Erro: Expedição não encontrada na sessão.",
                keyboard=self.create_main_menu_keyboard(),
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.ERROR,
                next_state=EXPEDITION_MENU
            )

        # Store pirate information
        request.user_data["consume_pirate_name"] = pirate_name
        request.user_data["consume_consumer_name"] = consumer_name

        return await self.show_item_selection_for_consumption(request, expedition_id)

    async def show_item_selection_for_consumption(self, request: HandlerRequest, expedition_id: int) -> HandlerResponse:
        """Show item selection for consumption."""
        try:
            expedition_service = get_expedition_service(request.context)
            expedition = expedition_service.get_expedition_by_id(expedition_id)
            items = expedition_service.get_expedition_items(expedition_id)

            # Filter consumable items
            consumable_items = [item for item in items if (item.quantity_consumed or 0) < item.quantity_required]

            if not consumable_items:
                return self.create_smart_response(
                    message="✅ Todos os itens desta expedição já foram totalmente consumidos.",
                    keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data="exp_list")]]),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.INFO,
                    next_state=EXPEDITION_LIST_MENU
                )

            # Get product details for display
            from core.modern_service_container import get_product_service
            product_service = get_product_service(request.context)

            keyboard_buttons = []
            message_lines = [
                f"🍽️ **Consumir Itens - {expedition.name}**",
                f"🏴‍☠️ Pirata: {request.user_data.get('consume_pirate_name', 'N/A')}",
                "",
                "📦 **Itens disponíveis para consumo:**"
            ]

            for item in consumable_items:
                try:
                    product = product_service.get_product_by_id(item.produto_id)
                    product_name = self._get_product_display_name(product) if product else f"Produto {item.produto_id}"
                except:
                    product_name = f"Produto {item.produto_id}"

                remaining = item.quantity_required - (item.quantity_consumed or 0)
                consumed = item.quantity_consumed or 0

                message_lines.append(f"   {product_name}")
                message_lines.append(f"   📊 Progresso: {consumed}/{item.quantity_required} (restam {remaining})")

                keyboard_buttons.append([
                    InlineKeyboardButton(
                        f"{product_name} ({remaining} restantes)",
                        callback_data=f"exp_consume_item:{item.id}:{item.produto_id}"
                    )
                ])

            keyboard_buttons.append([InlineKeyboardButton("🔙 Voltar", callback_data="exp_list")])
            keyboard = InlineKeyboardMarkup(keyboard_buttons)

            return self.create_smart_response(
                message="\n".join(message_lines),
                keyboard=keyboard,
                interaction_type=InteractionType.MENU_NAVIGATION,
                content_type=ContentType.SELECTION,
                next_state=EXPEDITION_CONSUME_SELECT_ITEM
            )

        except ServiceError as e:
            self.logger.error(f"Error showing item selection: {e}")
            return self.create_smart_response(
                message="❌ Erro ao carregar itens da expedição.",
                keyboard=self.create_main_menu_keyboard(),
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.ERROR,
                next_state=EXPEDITION_MENU
            )

    async def handle_item_selection_for_consumption(self, request: HandlerRequest, item_id: int, product_id: int) -> HandlerResponse:
        """Handle item selection for consumption."""
        expedition_id = request.user_data.get("consume_expedition_id")
        if not expedition_id:
            return self.create_smart_response(
                message="❌ Erro: Expedição não encontrada na sessão.",
                keyboard=self.create_main_menu_keyboard(),
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.ERROR,
                next_state=EXPEDITION_MENU
            )

        # Store item information
        request.user_data["consume_item_id"] = item_id
        request.user_data["consume_product_id"] = product_id

        # Get item details for display
        try:
            expedition_service = get_expedition_service(request.context)
            items = expedition_service.get_expedition_items(expedition_id)
            selected_item = next((item for item in items if item.id == item_id), None)

            if not selected_item:
                return self.create_smart_response(
                    message="❌ Item não encontrado.",
                    keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data="exp_list")]]),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.ERROR,
                    next_state=EXPEDITION_LIST_MENU
                )

            # Get product name
            from core.modern_service_container import get_product_service
            product_service = get_product_service(request.context)
            product = product_service.get_product_by_id(product_id)
            product_name = self._get_product_display_name(product) if product else f"Produto {product_id}"

            remaining = selected_item.quantity_required - (selected_item.quantity_consumed or 0)

            return self.create_smart_response(
                message=f"🍽️ **Consumir Item**\n\n📦 {product_name}\n🏴‍☠️ Pirata: {request.user_data.get('consume_pirate_name')}\n\n📊 Disponível para consumo: {remaining} unidades\n\nQuantas unidades deseja consumir? (1-{remaining})",
                keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancelar", callback_data="exp_list")]]),
                interaction_type=InteractionType.INPUT_REQUEST,
                content_type=ContentType.INPUT,
                next_state=EXPEDITION_CONSUME_QUANTITY
            )

        except ServiceError as e:
            self.logger.error(f"Error handling item selection: {e}")
            return self.create_smart_response(
                message="❌ Erro ao processar seleção de item.",
                keyboard=self.create_main_menu_keyboard(),
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.ERROR,
                next_state=EXPEDITION_MENU
            )

    async def handle_quantity_input_for_consumption(self, request: HandlerRequest) -> HandlerResponse:
        """Handle quantity input for consumption."""
        try:
            # Delete user input message immediately
            await self.batch_cleanup_messages([request.update.message], strategy="instant")

            quantity_text = request.update.message.text.strip()
            expedition_id = request.user_data.get("consume_expedition_id")
            item_id = request.user_data.get("consume_item_id")

            if not expedition_id or not item_id:
                return self.create_smart_response(
                    message="❌ Erro: Dados da sessão perdidos.",
                    keyboard=self.create_main_menu_keyboard(),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.ERROR,
                    next_state=EXPEDITION_MENU
                )

            # Validate quantity
            try:
                quantity = int(quantity_text)
                if quantity <= 0:
                    raise ValueError("Quantidade deve ser maior que zero")
            except ValueError:
                return self.create_smart_response(
                    message="❌ Digite um número válido maior que zero:",
                    keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancelar", callback_data="exp_list")]]),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.VALIDATION_ERROR,
                    next_state=EXPEDITION_CONSUME_QUANTITY
                )

            # Validate against available quantity
            expedition_service = get_expedition_service(request.context)
            items = expedition_service.get_expedition_items(expedition_id)
            selected_item = next((item for item in items if item.id == item_id), None)

            if not selected_item:
                return self.create_smart_response(
                    message="❌ Item não encontrado.",
                    keyboard=self.create_main_menu_keyboard(),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.ERROR,
                    next_state=EXPEDITION_MENU
                )

            remaining = selected_item.quantity_required - (selected_item.quantity_consumed or 0)
            if quantity > remaining:
                return self.create_smart_response(
                    message=f"❌ Quantidade excede o disponível.\n\nDisponível: {remaining} unidades\nDigite uma quantidade válida (1-{remaining}):",
                    keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancelar", callback_data="exp_list")]]),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.VALIDATION_ERROR,
                    next_state=EXPEDITION_CONSUME_QUANTITY
                )

            # Store quantity
            request.user_data["consume_quantity"] = quantity

            # Get product name for display
            from core.modern_service_container import get_product_service
            product_service = get_product_service(request.context)
            product = product_service.get_product_by_id(request.user_data.get("consume_product_id"))
            product_name = self._get_product_display_name(product) if product else "Produto"

            return self.create_smart_response(
                message=f"💰 **Definir Preço**\n\n📦 {product_name}\n🏴‍☠️ Pirata: {request.user_data.get('consume_pirate_name')}\n📊 Quantidade: {quantity} unidades\n\nQual será o preço por unidade? (R$)",
                keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancelar", callback_data="exp_list")]]),
                interaction_type=InteractionType.INPUT_REQUEST,
                content_type=ContentType.INPUT,
                next_state=EXPEDITION_CONSUME_PRICE
            )

        except Exception as e:
            self.logger.error(f"Error handling quantity input: {e}")
            return self.create_smart_response(
                message="❌ Erro ao processar quantidade.",
                keyboard=self.create_main_menu_keyboard(),
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.ERROR,
                next_state=EXPEDITION_MENU
            )

    async def handle_price_input_for_consumption(self, request: HandlerRequest) -> HandlerResponse:
        """Handle price input for consumption and complete the consumption."""
        try:
            # Delete user input message immediately
            await self.batch_cleanup_messages([request.update.message], strategy="instant")

            price_text = request.update.message.text.strip()

            # Get all stored data
            expedition_id = request.user_data.get("consume_expedition_id")
            item_id = request.user_data.get("consume_item_id")
            product_id = request.user_data.get("consume_product_id")
            quantity = request.user_data.get("consume_quantity")
            pirate_name = request.user_data.get("consume_pirate_name")
            consumer_name = request.user_data.get("consume_consumer_name")

            if not all([expedition_id, item_id, quantity, pirate_name, consumer_name]):
                return self.create_smart_response(
                    message="❌ Erro: Dados da sessão perdidos.",
                    keyboard=self.create_main_menu_keyboard(),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.ERROR,
                    next_state=EXPEDITION_MENU
                )

            # Validate price
            try:
                price = float(price_text)
                if price < 0:
                    raise ValueError("Preço não pode ser negativo")
            except ValueError:
                return self.create_smart_response(
                    message="❌ Digite um preço válido (ex: 10.50):",
                    keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancelar", callback_data="exp_list")]]),
                    interaction_type=InteractionType.ERROR_DISPLAY,
                    content_type=ContentType.VALIDATION_ERROR,
                    next_state=EXPEDITION_CONSUME_PRICE
                )

            # Create consumption
            expedition_service = get_expedition_service(request.context)

            from models.expedition import ItemConsumptionRequest
            consumption_request = ItemConsumptionRequest(
                expedition_item_id=item_id,
                consumer_name=consumer_name,
                pirate_name=pirate_name,
                quantity_consumed=quantity,
                unit_price=price
            )

            consumption = expedition_service.consume_item(consumption_request)

            # Get product name for confirmation
            from core.modern_service_container import get_product_service
            product_service = get_product_service(request.context)
            product = product_service.get_product_by_id(product_id)
            product_name = self._get_product_display_name(product) if product else "Produto"

            total_cost = quantity * price

            success_message = (
                f"✅ **Consumo Registrado!**\n\n"
                f"📦 {product_name}\n"
                f"🏴‍☠️ Pirata: {pirate_name}\n"
                f"👤 Comprador: {consumer_name}\n"
                f"📊 Quantidade: {quantity} unidades\n"
                f"💰 Preço unitário: R$ {price:.2f}\n"
                f"💸 Total: R$ {total_cost:.2f}\n\n"
                f"💳 Status: Pendente de pagamento"
            )

            # Clear session data
            request.user_data.pop("consume_expedition_id", None)
            request.user_data.pop("consume_item_id", None)
            request.user_data.pop("consume_product_id", None)
            request.user_data.pop("consume_quantity", None)
            request.user_data.pop("consume_pirate_name", None)
            request.user_data.pop("consume_consumer_name", None)

            return HandlerResponse(
                message=success_message,
                keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Voltar", callback_data="exp_list")]]),
                next_state=EXPEDITION_LIST_MENU,
                edit_message=True,
                delay=DelayConstants.IMPORTANT
            )

        except ValidationError as e:
            return self.create_smart_response(
                message=f"❌ {str(e)}\n\nTente novamente:",
                keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancelar", callback_data="exp_list")]]),
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.VALIDATION_ERROR,
                next_state=EXPEDITION_CONSUME_PRICE
            )
        except ServiceError as e:
            self.logger.error(f"Error creating consumption: {e}")
            return self.create_smart_response(
                message="❌ Erro ao registrar consumo. Tente novamente.",
                keyboard=self.create_main_menu_keyboard(),
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.ERROR,
                next_state=EXPEDITION_MENU
            )

    def get_conversation_handler(self) -> ConversationHandler:
        """Create the conversation handler."""
        return ConversationHandler(
            entry_points=[CommandHandler("expedition", self.start_expedition)],
            states={
                EXPEDITION_MENU: [
                    CallbackQueryHandler(self.expedition_menu_handler, pattern="^exp_(create|list|manage_pirates|manage_items|status|cancel)$"),
                ],
                EXPEDITION_CREATE_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.expedition_create_name_handler)
                ],
                EXPEDITION_MANAGE_PIRATES: [
                    CallbackQueryHandler(self.expedition_pirate_handler, pattern="^exp_(pirates|add_pirate|remove_pirate|manage_pirates|back|generate_random|assign_custom)"),
                    CallbackQueryHandler(self.expedition_pirate_handler, pattern=r"^exp_pirates:\d+$"),
                    CallbackQueryHandler(self.expedition_pirate_handler, pattern=r"^exp_add_pirate:\d+$"),
                    CallbackQueryHandler(self.expedition_pirate_handler, pattern=r"^exp_select_buyer:.+:\d+$"),
                    CallbackQueryHandler(self.expedition_pirate_handler, pattern=r"^exp_generate_random:\d+$"),
                    CallbackQueryHandler(self.expedition_pirate_handler, pattern=r"^exp_assign_custom:\d+$"),
                    CallbackQueryHandler(self.expedition_pirate_handler, pattern=r"^exp_remove_pirate:\d+$"),
                    CallbackQueryHandler(self.expedition_pirate_handler, pattern=r"^exp_confirm_remove:\d+:.+$"),
                ],
                EXPEDITION_CUSTOM_ASSIGNMENT: [
                    CallbackQueryHandler(self.expedition_pirate_handler, pattern=r"^exp_select_buyer:.+$"),
                    CallbackQueryHandler(self.expedition_pirate_handler, pattern=r"^exp_pirates:\d+$"),
                ],
                EXPEDITION_CUSTOM_NAME_INPUT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.expedition_custom_name_handler),
                    CallbackQueryHandler(self.expedition_pirate_handler, pattern=r"^exp_pirates:\d+$"),
                ],
                EXPEDITION_ITEM_MENU: [
                    CallbackQueryHandler(self.expedition_item_handler, pattern="^exp_(items|add_item|remove_item|manage_items|back)"),
                    CallbackQueryHandler(self.expedition_item_handler, pattern=r"^exp_items:\d+$"),
                    CallbackQueryHandler(self.expedition_item_handler, pattern=r"^exp_add_item:\d+$"),
                    CallbackQueryHandler(self.expedition_item_handler, pattern=r"^exp_remove_item:\d+$"),
                    CallbackQueryHandler(self.expedition_item_handler, pattern=r"^exp_remove_product:\d+:\d+$"),
                ],
                EXPEDITION_ADD_ITEM_PRODUCT: [
                    CallbackQueryHandler(self.handle_product_selection, pattern=r"^exp_select_product:\d+$"),
                    CallbackQueryHandler(self.expedition_item_handler, pattern=r"^exp_items:\d+$"),
                ],
                EXPEDITION_ADD_ITEM_QUANTITY: [
                    MessageHandler(filters.Regex(r"^\d+$"), self.handle_quantity_input_wrapper)
                ],
                EXPEDITION_ADD_ITEM_PRICE: [
                    MessageHandler(filters.Regex(r"^\d+(\.\d{1,2})?$"), self.handle_price_input_wrapper),
                    CallbackQueryHandler(self.expedition_item_handler, pattern=r"^exp_items:\d+$"),
                ],
                EXPEDITION_ADD_ITEM_COST: [
                    MessageHandler(filters.Regex(r"^\d+(\.\d{1,2})?$"), self.handle_cost_input_wrapper),
                    CallbackQueryHandler(self.expedition_item_handler, pattern=r"^exp_items:\d+$"),
                ],
                EXPEDITION_LIST_MENU: [
                    CallbackQueryHandler(self.expedition_list_handler, pattern="^exp_(details|back)"),
                    CallbackQueryHandler(self.expedition_list_handler, pattern=r"^exp_details:\d+$"),
                    CallbackQueryHandler(self.expedition_list_handler, pattern=r"^exp_consume:\d+$"),
                ],
                EXPEDITION_STATUS_MENU: [
                    CallbackQueryHandler(self.expedition_status_handler, pattern="^exp_(status|back)"),
                    CallbackQueryHandler(self.expedition_status_handler, pattern=r"^exp_status_detail:\d+$"),
                ],
                EXPEDITION_CONSUME_MENU: [
                    CallbackQueryHandler(self.expedition_consumption_handler, pattern=r"^exp_consume:\d+$"),
                    CallbackQueryHandler(self.expedition_consumption_handler, pattern="^exp_list$"),
                ],
                EXPEDITION_CONSUME_SELECT_PIRATE: [
                    CallbackQueryHandler(self.expedition_consumption_handler, pattern=r"^exp_consume_pirate:.+:.+$"),
                    CallbackQueryHandler(self.expedition_consumption_handler, pattern="^exp_list$"),
                ],
                EXPEDITION_CONSUME_SELECT_ITEM: [
                    CallbackQueryHandler(self.expedition_consumption_handler, pattern=r"^exp_consume_item:\d+:\d+$"),
                    CallbackQueryHandler(self.expedition_consumption_handler, pattern="^exp_list$"),
                ],
                EXPEDITION_CONSUME_QUANTITY: [
                    MessageHandler(filters.Regex(r"^\d+$"), self.handle_consumption_quantity_input),
                    CallbackQueryHandler(self.expedition_consumption_handler, pattern="^exp_list$"),
                ],
                EXPEDITION_CONSUME_PRICE: [
                    MessageHandler(filters.Regex(r"^\d+(\.\d{1,2})?$"), self.handle_consumption_price_input),
                    CallbackQueryHandler(self.expedition_consumption_handler, pattern="^exp_list$"),
                ],
            },
            fallbacks=[
                CommandHandler("cancel", self.cancel),
                CallbackQueryHandler(self.cancel, pattern="^exp_cancel$")
            ],
            allow_reentry=True
        )


# Factory function
def get_expedition_handler():
    """Get the expedition conversation handler."""
    handler = ExpeditionHandler()
    return handler.get_conversation_handler()