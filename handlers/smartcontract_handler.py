import logging
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters
)
from handlers.base_handler import MenuHandlerBase, HandlerRequest, HandlerResponse
from handlers.error_handler import with_error_boundary, with_error_boundary_standalone
from models.handler_models import SmartContractRequest, SmartContractResponse
from services.handler_business_service import HandlerBusinessService
from utils.input_sanitizer import InputSanitizer
from utils.permissions import require_permission
from handlers.global_handlers import cancel, cancel_callback

logger = logging.getLogger(__name__)

# States
SMARTCONTRACT_MENU, SMARTCONTRACT_TRANSACTION_DESC = range(2)


class ModernSmartContractHandler(MenuHandlerBase):
    def __init__(self):
        super().__init__("smartcontract")
        
    def create_main_menu_keyboard(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🤝 Shakehands", callback_data="sc_shakehands")],
            [InlineKeyboardButton("➕ Adicionar Transação", callback_data="sc_add_transaction")],
            [InlineKeyboardButton("🚫 Cancelar", callback_data="sc_cancel")]
        ])
    
    def get_menu_text(self) -> str:
        contract_code = self.current_contract_code
        return f"📄 Contrato `{contract_code}` encontrado. O que deseja fazer?"
    
    def get_menu_state(self) -> int:
        return SMARTCONTRACT_MENU
    
    def get_retry_state(self) -> Optional[int]:
        return SMARTCONTRACT_TRANSACTION_DESC
        
    async def handle(self, request: HandlerRequest) -> HandlerResponse:
        return await self.show_main_menu(request)
    
    async def handle_menu_selection(self, request: HandlerRequest, selection: str) -> HandlerResponse:
        if selection == "sc_shakehands":
            return await self._handle_shakehands(request)
        elif selection == "sc_add_transaction":
            return await self._handle_start_add_transaction(request)
        elif selection == "sc_cancel":
            return HandlerResponse(
                message="🚫 Operação cancelada.",
                end_conversation=True
            )
        else:
            return HandlerResponse(
                message="❌ Opção inválida.",
                keyboard=self.create_main_menu_keyboard(),
                next_state=SMARTCONTRACT_MENU
            )
    
    async def _handle_shakehands(self, request: HandlerRequest) -> HandlerResponse:
        business_service = HandlerBusinessService(request.context)
        contract_id = request.user_data.get("contrato_id")
        
        if not contract_id:
            return HandlerResponse(
                message="❌ Contrato não encontrado.",
                end_conversation=True
            )
        
        # Get transactions for this contract
        transactions = business_service.get_contract_transactions(contract_id)
        
        if not transactions:
            return HandlerResponse(
                message="📭 Nenhuma transação registrada.",
                end_conversation=True
            )
        
        # Create keyboard with transactions
        keyboard = []
        for transaction in transactions:
            label = f"🧾 {transaction.description[:40]}"
            keyboard.append([
                InlineKeyboardButton(label, callback_data=f"sc_confirm:{transaction.id}")
            ])
        
        keyboard.append([InlineKeyboardButton("🚫 Cancelar", callback_data="sc_cancel")])
        
        return HandlerResponse(
            message="📜 Transações registradas:",
            keyboard=InlineKeyboardMarkup(keyboard),
            end_conversation=True
        )
    
    async def _handle_start_add_transaction(self, request: HandlerRequest) -> HandlerResponse:
        return HandlerResponse(
            message="✍️ Envie a descrição da transação:",
            next_state=SMARTCONTRACT_TRANSACTION_DESC
        )
    
    async def _handle_transaction_description(self, request: HandlerRequest) -> HandlerResponse:
        business_service = HandlerBusinessService(request.context)
        contract_id = request.user_data.get("contrato_id")
        
        if not contract_id:
            return HandlerResponse(
                message="❌ Contrato não encontrado.",
                end_conversation=True
            )
        
        # Validate and sanitize description
        description = InputSanitizer.sanitize_description(request.update.message.text)
        
        # Create transaction request
        sc_request = SmartContractRequest(
            action="add_transaction",
            description=description,
            participant_chat_id=request.chat_id
        )
        
        # Add transaction
        response = business_service.handle_smartcontract_operation(sc_request, contract_id)
        
        if response.success:
            return HandlerResponse(
                message="✅ Transação adicionada com sucesso!",
                end_conversation=True
            )
        else:
            return HandlerResponse(
                message=f"❌ {response.message}",
                end_conversation=True
            )
    
    async def _handle_confirm_transaction_prompt(self, request: HandlerRequest, transaction_id: str) -> HandlerResponse:
        request.user_data["transacao_a_confirmar"] = transaction_id
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Sim", callback_data="sc_confirm_yes")],
            [InlineKeyboardButton("❌ Não", callback_data="sc_confirm_no")]
        ])
        
        return HandlerResponse(
            message="✅ Confirmar esta transação?",
            keyboard=keyboard,
            end_conversation=True
        )
    
    async def _handle_confirm_transaction_exec(self, request: HandlerRequest, confirm: bool) -> HandlerResponse:
        transaction_id = request.user_data.get("transacao_a_confirmar")
        
        if confirm:
            message = f"🔐 Transação #{transaction_id} confirmada com sucesso!"
        else:
            message = "❌ Confirmação cancelada."
        
        return HandlerResponse(
            message=message,
            end_conversation=True
        )
    
    def get_conversation_handler(self) -> ConversationHandler:
        return ConversationHandler(
            entry_points=[CommandHandler("transactions", self._start_smartcontract)],
            states={
                SMARTCONTRACT_MENU: [
                    CallbackQueryHandler(self._menu_callback, pattern="^sc_")
                ],
                SMARTCONTRACT_TRANSACTION_DESC: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._transaction_desc_callback)
                ],
            },
            fallbacks=[
                CommandHandler("cancel", cancel),
                CallbackQueryHandler(cancel_callback, pattern="^sc_cancel$")
            ]
        )
    
    @require_permission("owner")
    @with_error_boundary
    async def _start_smartcontract(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        request = self.create_request(update, context)
        
        if not context.args:
            response = HandlerResponse(
                message="❗ Envie o código do contrato. Ex: /transactions 12345",
                end_conversation=True
            )
            return await self.send_response(response, request)
        
        codigo = " ".join(context.args).strip()
        business_service = HandlerBusinessService(context)
        
        # Find contract
        contract = business_service.get_contract_by_code(request.chat_id, codigo)
        
        if not contract:
            response = HandlerResponse(
                message=f"❌ Contrato `{codigo}` não encontrado.",
                end_conversation=True
            )
            return await self.send_response(response, request)
        
        # Store contract info in user data
        context.user_data["contrato_id"] = contract.id
        context.user_data["codigo_contrato"] = contract.code
        self.current_contract_code = codigo
        
        response = await self.handle(request)
        return await self.send_response(response, request)
    
    @with_error_boundary
    async def _menu_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        request = self.create_request(update, context)
        selection = update.callback_query.data
        
        if selection.startswith("sc_confirm:"):
            transaction_id = selection.split(":")[1]
            response = await self._handle_confirm_transaction_prompt(request, transaction_id)
        elif selection in ["sc_confirm_yes", "sc_confirm_no"]:
            confirm = selection == "sc_confirm_yes"
            response = await self._handle_confirm_transaction_exec(request, confirm)
        else:
            response = await self.handle_menu_selection(request, selection)
        
        return await self.send_response(response, request)
    
    @with_error_boundary
    async def _transaction_desc_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        request = self.create_request(update, context)
        response = await self._handle_transaction_description(request)
        return await self.send_response(response, request)


# Factory function for the smart contract conversation handler
def get_smartcontract_conversation_handler() -> ConversationHandler:
    handler = ModernSmartContractHandler()
    return handler.get_conversation_handler()


# Command handler for creating smart contracts
@require_permission("owner")
@with_error_boundary_standalone("criar_smart_contract")
async def criar_smart_contract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create a new smart contract with the provided code"""
    logger.info("→ Entrando em criar_smart_contract()")
    chat_id = update.effective_chat.id

    if not context.args:
        logger.warning(f"Chat {chat_id} não enviou código do contrato.")
        from utils.message_cleaner import send_and_delete
        await send_and_delete("❗ Envie o código do contrato. Ex: /smartcontract 12345", update, context)
        return

    codigo = " ".join(context.args).strip()
    business_service = HandlerBusinessService(context)
    
    # Create smart contract request
    sc_request = SmartContractRequest(
        action="create",
        contract_code=codigo
    )
    
    response = business_service.create_smartcontract(sc_request, chat_id)
    
    if response.success:
        logger.info(f"Contrato '{codigo}' criado para chat_id={chat_id}")
        message = f"✅ Contrato `{codigo}` criado com sucesso!"
    else:
        message = f"❌ {response.message}"
    
    from utils.message_cleaner import send_and_delete
    await send_and_delete(message, update, context)


# Command handler registration
smartcontract_command_handler = CommandHandler("smartcontract", criar_smart_contract)