import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union, Callable, List
from dataclasses import dataclass
from enum import Enum
import asyncio
from telegram import Update, InlineKeyboardMarkup, Message
from telegram.ext import ContextTypes, ConversationHandler
from utils.message_cleaner import send_and_delete, send_menu_with_delete
from utils.permissions import require_permission
from services.base_service import ServiceError, ValidationError, NotFoundError, DuplicateError
from core.modern_service_container import get_user_service


class DelayConstants:
    """Standardized delay constants for message management"""
    INSTANT = 0
    SUCCESS = 5
    ERROR = 8
    INFO = 10
    IMPORTANT = 15
    FILE_TRANSFER = 120
    MANUAL_ONLY = None


class InteractionType(Enum):
    """Types of user interactions"""
    MENU_NAVIGATION = "menu_navigation"
    FORM_SUBMIT = "form_submit"
    FORM_INPUT = "form_input"
    REPORT_DISPLAY = "report_display"
    SECURITY = "security"
    ERROR_DISPLAY = "error_display"
    CONFIRMATION = "confirmation"
    FILE_TRANSFER = "file_transfer"


class ContentType(Enum):
    """Types of content being displayed"""
    SELECTION = "selection"
    SUCCESS = "success"
    VALIDATION_ERROR = "validation_error"
    DATA = "data"
    CREDENTIALS = "credentials"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class MessageStrategy:
    """Strategy for handling a message"""
    edit_message: bool = False
    delete_instant: bool = False
    delay: Optional[int] = 10
    protected: bool = False
    batch_operation: bool = False
    
    
class SmartMessageManager:
    """Context-aware message handling strategy selector"""
    
    def __init__(self):
        self._strategies = self._initialize_strategies()
    
    def _initialize_strategies(self) -> Dict[tuple, MessageStrategy]:
        """Initialize predefined strategies for common interaction patterns"""
        return {
            # Menu navigation patterns - edit in place for smooth UX
            (InteractionType.MENU_NAVIGATION, ContentType.SELECTION): MessageStrategy(
                edit_message=True,
                delay=DelayConstants.MANUAL_ONLY,
                protected=True
            ),
            
            # Form submission patterns
            (InteractionType.FORM_SUBMIT, ContentType.SUCCESS): MessageStrategy(
                delete_instant=True,
                delay=DelayConstants.SUCCESS
            ),
            (InteractionType.FORM_SUBMIT, ContentType.VALIDATION_ERROR): MessageStrategy(
                edit_message=True,
                delay=DelayConstants.ERROR
            ),
            
            # Form input patterns - progressive forms
            (InteractionType.FORM_INPUT, ContentType.VALIDATION_ERROR): MessageStrategy(
                edit_message=True,
                delay=DelayConstants.MANUAL_ONLY,
                protected=True
            ),
            (InteractionType.FORM_INPUT, ContentType.SUCCESS): MessageStrategy(
                edit_message=True,
                delay=DelayConstants.MANUAL_ONLY,
                protected=True
            ),
            
            # Report display patterns - manual control
            (InteractionType.REPORT_DISPLAY, ContentType.DATA): MessageStrategy(
                delay=DelayConstants.MANUAL_ONLY,
                protected=True
            ),
            
            # Security patterns - immediate deletion
            (InteractionType.SECURITY, ContentType.CREDENTIALS): MessageStrategy(
                delete_instant=True,
                delay=DelayConstants.INSTANT
            ),
            
            # Error patterns
            (InteractionType.ERROR_DISPLAY, ContentType.ERROR): MessageStrategy(
                delay=DelayConstants.ERROR
            ),
            (InteractionType.ERROR_DISPLAY, ContentType.WARNING): MessageStrategy(
                delay=DelayConstants.INFO
            ),
            
            # Confirmation patterns
            (InteractionType.CONFIRMATION, ContentType.SUCCESS): MessageStrategy(
                delay=DelayConstants.SUCCESS
            ),
            
            # File transfer patterns
            (InteractionType.FILE_TRANSFER, ContentType.DATA): MessageStrategy(
                delay=DelayConstants.FILE_TRANSFER,
                protected=True
            )
        }
    
    def get_strategy(self, interaction_type: InteractionType, content_type: ContentType) -> MessageStrategy:
        """Get the optimal message handling strategy for given interaction and content types"""
        strategy = self._strategies.get((interaction_type, content_type))
        
        if strategy:
            return strategy
        
        # Fallback strategies based on interaction type
        fallback_strategies = {
            InteractionType.MENU_NAVIGATION: MessageStrategy(edit_message=True, delay=DelayConstants.MANUAL_ONLY),
            InteractionType.FORM_INPUT: MessageStrategy(edit_message=True, delay=DelayConstants.MANUAL_ONLY),
            InteractionType.SECURITY: MessageStrategy(delete_instant=True, delay=DelayConstants.INSTANT),
            InteractionType.ERROR_DISPLAY: MessageStrategy(delay=DelayConstants.ERROR),
            InteractionType.FILE_TRANSFER: MessageStrategy(delay=DelayConstants.FILE_TRANSFER, protected=True)
        }
        
        return fallback_strategies.get(interaction_type, MessageStrategy(delay=DelayConstants.INFO))
    
    def create_response_with_strategy(self, message: str, keyboard: Optional[InlineKeyboardMarkup], 
                                    interaction_type: InteractionType, content_type: ContentType,
                                    next_state: Optional[int] = None, end_conversation: bool = False) -> 'HandlerResponse':
        """Create a HandlerResponse with optimal strategy applied"""
        strategy = self.get_strategy(interaction_type, content_type)
        
        return HandlerResponse(
            message=message,
            keyboard=keyboard,
            next_state=next_state,
            end_conversation=end_conversation,
            delay=strategy.delay,
            protected=strategy.protected,
            edit_message=strategy.edit_message
        )


class BatchMessageManager:
    """Efficient multi-message management utilities"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    async def batch_cleanup(self, messages: List[Union[Message, Any]], strategy: str = "safe") -> None:
        """Efficiently clean up multiple messages"""
        if not messages:
            return
            
        if strategy == "instant":
            # Delete all messages immediately in parallel
            tasks = []
            for msg in messages:
                if msg:
                    tasks.append(self._safe_delete_single(msg))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
                
        elif strategy == "delayed":
            # Delete messages with delays
            for msg in messages:
                if msg:
                    asyncio.create_task(self._delayed_delete_single(msg, delay=10))
                    
        elif strategy == "safe":
            # Delete one by one with error handling
            for msg in messages:
                if msg:
                    await self._safe_delete_single(msg)
    
    async def _safe_delete_single(self, message: Union[Message, Any]) -> None:
        """Safely delete a single message"""
        try:
            if hasattr(message, 'message'):
                # It's a callback query
                await message.message.delete()
                if hasattr(message, 'answer'):
                    await message.answer()
            else:
                # It's a message object
                await message.delete()
        except Exception as e:
            self.logger.debug(f"Could not delete message in batch operation: {e}")
    
    async def _delayed_delete_single(self, message: Union[Message, Any], delay: int = 10) -> None:
        """Delete a message after a delay"""
        try:
            await asyncio.sleep(delay)
            await self._safe_delete_single(message)
        except Exception as e:
            self.logger.debug(f"Could not delete message in delayed batch operation: {e}")
    
    async def batch_edit(self, messages_and_content: List[tuple], context: ContextTypes.DEFAULT_TYPE) -> List[bool]:
        """Edit multiple messages in batch with content tuples (message, new_text, keyboard)"""
        results = []
        tasks = []
        
        for message, new_text, keyboard in messages_and_content:
            if message:
                tasks.append(self._safe_edit_single(message, new_text, keyboard, context))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return [result is not Exception for result in results]
    
    async def _safe_edit_single(self, message: Union[Message, Any], new_text: str, 
                               keyboard: Optional[InlineKeyboardMarkup], 
                               context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Safely edit a single message"""
        try:
            from telegram.constants import ParseMode
            
            if hasattr(message, 'edit_text'):
                await message.edit_text(
                    text=new_text,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.MARKDOWN
                )
            elif hasattr(message, 'message'):
                await message.edit_message_text(
                    text=new_text,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                # Try using bot context to edit
                await context.bot.edit_message_text(
                    chat_id=message.chat_id,
                    message_id=message.message_id,
                    text=new_text,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.MARKDOWN
                )
            return True
        except Exception as e:
            self.logger.debug(f"Could not edit message in batch operation: {e}")
            return False


@dataclass
class HandlerResponse:
    message: str
    keyboard: Optional[InlineKeyboardMarkup] = None
    next_state: Optional[int] = None
    end_conversation: bool = False
    delay: int = 10
    protected: bool = False
    edit_message: bool = False
    parse_mode: Optional[str] = None


@dataclass
class HandlerRequest:
    update: Update
    context: ContextTypes.DEFAULT_TYPE
    user_data: Dict[str, Any]
    chat_id: int
    user_id: int


class BaseHandler(ABC):
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"handlers.{name}")
        self.smart_message_manager = SmartMessageManager()
        self.batch_message_manager = BatchMessageManager(self.logger)
        
    def create_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> HandlerRequest:
        return HandlerRequest(
            update=update,
            context=context,
            user_data=context.user_data,
            chat_id=update.effective_chat.id,
            user_id=update.effective_user.id
        )
    
    async def safe_delete_message(self, query_or_message, logger=None):
        """Safely delete a message with proper error handling"""
        if logger is None:
            logger = self.logger
            
        try:
            if hasattr(query_or_message, 'message'):
                # It's a callback query
                await query_or_message.message.delete()
                await query_or_message.answer()
            else:
                # It's a message object
                await query_or_message.delete()
        except Exception as e:
            logger.warning(f"Could not delete message: {e}")
    
    def create_smart_response(self, message: str, keyboard: Optional[InlineKeyboardMarkup], 
                            interaction_type: InteractionType, content_type: ContentType,
                            next_state: Optional[int] = None, end_conversation: bool = False) -> HandlerResponse:
        """Create a response using smart message strategy"""
        return self.smart_message_manager.create_response_with_strategy(
            message=message,
            keyboard=keyboard,
            interaction_type=interaction_type,
            content_type=content_type,
            next_state=next_state,
            end_conversation=end_conversation
        )
    
    async def batch_cleanup_messages(self, messages: List[Union[Message, Any]], strategy: str = "safe") -> None:
        """Clean up multiple messages using batch manager"""
        await self.batch_message_manager.batch_cleanup(messages, strategy)
    
    async def batch_edit_messages(self, messages_and_content: List[tuple], context: ContextTypes.DEFAULT_TYPE) -> List[bool]:
        """Edit multiple messages in batch"""
        return await self.batch_message_manager.batch_edit(messages_and_content, context)
    
    async def handle_error(self, error: Exception, request: HandlerRequest) -> HandlerResponse:
        self.logger.error(f"Error in {self.name}: {error}", exc_info=True)
        
        if isinstance(error, ValidationError):
            return self.create_smart_response(
                message=f"❌ {str(error)}",
                keyboard=None,
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.VALIDATION_ERROR,
                next_state=self.get_retry_state()
            )
        elif isinstance(error, NotFoundError):
            return self.create_smart_response(
                message="❌ Item não encontrado.",
                keyboard=None,
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.ERROR,
                end_conversation=True
            )
        elif isinstance(error, DuplicateError):
            return self.create_smart_response(
                message=f"❌ {str(error)}",
                keyboard=None,
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.VALIDATION_ERROR,
                next_state=self.get_retry_state()
            )
        elif isinstance(error, ServiceError):
            return self.create_smart_response(
                message="❌ Erro interno. Tente novamente.",
                keyboard=None,
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.ERROR,
                next_state=self.get_retry_state()
            )
        else:
            return self.create_smart_response(
                message="❌ Erro inesperado. Operação cancelada.",
                keyboard=None,
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.ERROR,
                end_conversation=True
            )
    
    def ensure_services_initialized(self):
        """Ensure services are initialized, with fallback initialization if needed."""
        try:
            from services.handler_business_service import HandlerBusinessService
            return HandlerBusinessService()
        except RuntimeError as e:
            if "not initialized" in str(e):
                self.logger.warning("Services not initialized, attempting fallback initialization...")
                try:
                    from core.modern_service_container import initialize_services
                    from database import initialize_database
                    from database.schema import initialize_schema
                    
                    initialize_database()
                    initialize_schema()
                    initialize_services({})
                    
                    return HandlerBusinessService()
                except Exception as init_error:
                    self.logger.error(f"Failed to initialize services: {init_error}")
                    raise ServiceError("Serviços não disponíveis. Tente novamente.")
            else:
                raise
    
    def ensure_user_service_initialized(self, context):
        """Ensure user service is initialized, with fallback initialization if needed."""
        try:
            from core.modern_service_container import get_user_service
            return get_user_service(context)
        except Exception as e:
            if "not initialized" in str(e):
                self.logger.warning("User service not initialized, attempting fallback initialization...")
                try:
                    from core.modern_service_container import initialize_services
                    from database import initialize_database
                    from database.schema import initialize_schema
                    
                    initialize_database()
                    initialize_schema()
                    initialize_services({})
                    
                    return get_user_service(context)
                except Exception as init_error:
                    self.logger.error(f"Failed to initialize user service: {init_error}")
                    raise ServiceError("Serviços não disponíveis. Tente novamente.")
            else:
                raise
    
    async def send_response(self, response: HandlerResponse, request: HandlerRequest) -> int:
        # Edit previous message if requested
        if response.edit_message:
            try:
                from telegram.constants import ParseMode
                
                # Handle callback query editing
                if hasattr(request.update, 'callback_query') and request.update.callback_query:
                    parse_mode = getattr(ParseMode, response.parse_mode, ParseMode.MARKDOWN) if response.parse_mode else ParseMode.MARKDOWN
                    await request.update.callback_query.edit_message_text(
                        text=response.message,
                        reply_markup=response.keyboard,
                        parse_mode=parse_mode
                    )
                    await request.update.callback_query.answer()
                    return self._handle_conversation_end_or_next_state(response)
                    
                # Handle text message editing (for progressive forms)
                elif hasattr(request.update, 'message') and request.update.message:
                    # For text-based interactions, try to edit the bot's last message
                    # Get the last bot message from chat history if available
                    if hasattr(request.context, 'user_data') and 'last_bot_message_id' in request.context.user_data:
                        try:
                            parse_mode = getattr(ParseMode, response.parse_mode, ParseMode.MARKDOWN) if response.parse_mode else ParseMode.MARKDOWN
                            await request.context.bot.edit_message_text(
                                chat_id=request.chat_id,
                                message_id=request.context.user_data['last_bot_message_id'],
                                text=response.message,
                                reply_markup=response.keyboard,
                                parse_mode=parse_mode
                            )
                            return self._handle_conversation_end_or_next_state(response)
                        except Exception as edit_error:
                            self.logger.debug(f"Could not edit last bot message: {edit_error}")
                            # Fallback to normal flow
                    
                    # Fallback: send new message and store its ID for future edits
                    sent_message = await self._send_new_message(response, request)
                    if sent_message:
                        request.context.user_data['last_bot_message_id'] = sent_message.message_id
                    return self._handle_conversation_end_or_next_state(response)
                    
            except Exception as e:
                self.logger.warning(f"Could not edit previous message: {e}")
                # Fallback to normal flow if editing fails
        
        # Normal flow when not editing or edit failed
        sent_message = await self._send_new_message(response, request)
        if sent_message:
            request.context.user_data['last_bot_message_id'] = sent_message.message_id
        return self._handle_conversation_end_or_next_state(response)
    
    async def _send_new_message(self, response: HandlerResponse, request: HandlerRequest):
        """Send a new message using the existing message management utilities."""
        from telegram.constants import ParseMode
        
        parse_mode = getattr(ParseMode, response.parse_mode, ParseMode.MARKDOWN) if response.parse_mode else ParseMode.MARKDOWN
        
        if response.keyboard:
            return await send_menu_with_delete(
                response.message,
                request.update,
                request.context,
                response.keyboard,
                delay=response.delay,
                protected=response.protected,
                parse_mode=parse_mode
            )
        else:
            return await send_and_delete(
                response.message,
                request.update,
                request.context,
                delay=response.delay,
                parse_mode=parse_mode
            )
    
    def _handle_conversation_end_or_next_state(self, response: HandlerResponse) -> int:
        """Handle conversation state transitions."""
        if response.end_conversation:
            return ConversationHandler.END
        elif response.next_state is not None:
            return response.next_state
        else:
            return ConversationHandler.END
    
    def get_retry_state(self) -> Optional[int]:
        return None
    
    def require_permission_decorator(self, level: str):
        return require_permission(level)
    
    async def validate_user_permission(self, request: HandlerRequest, required_level: str) -> bool:
        try:
            user_service = get_user_service(request.context)
            user_level_enum = user_service.get_user_permission_level(request.chat_id)
            
            if user_level_enum is None:
                return False
                
            # Convert enum to string for comparison
            user_level = user_level_enum.value if user_level_enum else None
            
            levels = {"user": 1, "admin": 2, "owner": 3}
            user_level_num = levels.get(user_level, 0)
            required_level_num = levels.get(required_level, 3)
            
            return user_level_num >= required_level_num
        except ServiceError:
            return False
    
    @abstractmethod
    async def handle(self, request: HandlerRequest) -> HandlerResponse:
        pass


class ConversationHandlerBase(BaseHandler):
    def __init__(self, name: str):
        super().__init__(name)
    
    @abstractmethod
    def get_conversation_handler(self) -> ConversationHandler:
        pass
    
    async def safe_handle(self, handler_func: Callable, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        request = self.create_request(update, context)
        
        try:
            response = await handler_func(request)
            return await self.send_response(response, request)
        except Exception as e:
            error_response = await self.handle_error(e, request)
            return await self.send_response(error_response, request)


class MenuHandlerBase(ConversationHandlerBase):
    def __init__(self, name: str):
        super().__init__(name)
    
    @abstractmethod 
    def create_main_menu_keyboard(self) -> InlineKeyboardMarkup:
        pass
    
    @abstractmethod
    async def handle_menu_selection(self, request: HandlerRequest, selection: str) -> HandlerResponse:
        pass
    
    async def show_main_menu(self, request: HandlerRequest) -> HandlerResponse:
        return HandlerResponse(
            message=self.get_menu_text(),
            keyboard=self.create_main_menu_keyboard(),
            next_state=self.get_menu_state()
        )
    
    @abstractmethod
    def get_menu_text(self) -> str:
        pass
    
    @abstractmethod
    def get_menu_state(self) -> int:
        pass


class FormHandlerBase(ConversationHandlerBase):
    def __init__(self, name: str):
        super().__init__(name)
        self.form_fields = []
        self.current_field_index = 0
    
    @abstractmethod
    def get_form_fields(self) -> list:
        pass
    
    @abstractmethod
    async def process_form_data(self, request: HandlerRequest, form_data: Dict[str, Any]) -> HandlerResponse:
        pass
    
    async def handle_form_input(self, request: HandlerRequest, field_name: str, input_value: str) -> HandlerResponse:
        try:
            validated_value = await self.validate_field(field_name, input_value)
            request.user_data[field_name] = validated_value
            
            next_field = self.get_next_field(field_name)
            if next_field:
                return HandlerResponse(
                    message=self.get_field_prompt(next_field),
                    next_state=self.get_field_state(next_field)
                )
            else:
                return await self.process_form_data(request, request.user_data)
                
        except ValidationError as e:
            return HandlerResponse(
                message=f"❌ {str(e)}\n\n{self.get_field_prompt(field_name)}",
                next_state=self.get_field_state(field_name),
                edit_message=True
            )
    
    @abstractmethod
    async def validate_field(self, field_name: str, value: str) -> Any:
        pass
    
    @abstractmethod
    def get_field_prompt(self, field_name: str) -> str:
        pass
    
    @abstractmethod
    def get_field_state(self, field_name: str) -> int:
        pass
    
    @abstractmethod
    def get_next_field(self, current_field: str) -> Optional[str]:
        pass