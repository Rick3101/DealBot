"""
Response Builder Mixin - Standardizes message response patterns across handlers.
Eliminates repetitive message formatting and keyboard creation logic.
"""

from typing import Optional, List, Dict, Any, Union
from abc import ABC
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes
from handlers.base_handler import HandlerResponse, InteractionType, ContentType, DelayConstants
from utils.message_cleaner import send_and_delete, send_menu_with_delete
import logging


class ResponseBuilderMixin(ABC):
    """
    Mixin providing standardized response building patterns for handlers.
    Eliminates repetitive message formatting and keyboard creation.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

    def create_simple_keyboard(self, buttons: List[Dict[str, str]],
                              columns: int = 2) -> InlineKeyboardMarkup:
        """
        Create a simple inline keyboard from button definitions.

        Args:
            buttons: List of dicts with 'text' and 'callback_data' keys
            columns: Number of columns in the keyboard

        Returns:
            InlineKeyboardMarkup
        """
        keyboard = []
        for i in range(0, len(buttons), columns):
            row = []
            for j in range(i, min(i + columns, len(buttons))):
                button = buttons[j]
                row.append(InlineKeyboardButton(
                    text=button['text'],
                    callback_data=button['callback_data']
                ))
            keyboard.append(row)

        return InlineKeyboardMarkup(keyboard)

    def create_menu_keyboard(self, options: Dict[str, str],
                           back_button: bool = True,
                           cancel_button: bool = True,
                           columns: int = 1) -> InlineKeyboardMarkup:
        """
        Create a standard menu keyboard with optional back/cancel buttons.

        Args:
            options: Dict mapping display text to callback data
            back_button: Whether to include a back button
            cancel_button: Whether to include a cancel button
            columns: Number of columns for main options

        Returns:
            InlineKeyboardMarkup
        """
        buttons = [
            {'text': text, 'callback_data': data}
            for text, data in options.items()
        ]

        keyboard = []

        # Add main option buttons
        for i in range(0, len(buttons), columns):
            row = []
            for j in range(i, min(i + columns, len(buttons))):
                button = buttons[j]
                row.append(InlineKeyboardButton(
                    text=button['text'],
                    callback_data=button['callback_data']
                ))
            keyboard.append(row)

        # Add navigation buttons
        nav_row = []
        if back_button:
            nav_row.append(InlineKeyboardButton("⬅️ Back", callback_data="back"))
        if cancel_button:
            nav_row.append(InlineKeyboardButton("❌ Cancel", callback_data="cancel"))

        if nav_row:
            keyboard.append(nav_row)

        return InlineKeyboardMarkup(keyboard)

    def create_confirmation_keyboard(self, confirm_data: str = "confirm",
                                   cancel_data: str = "cancel") -> InlineKeyboardMarkup:
        """Create a confirmation keyboard with Yes/No options."""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Yes", callback_data=confirm_data),
                InlineKeyboardButton("❌ No", callback_data=cancel_data)
            ]
        ])

    def create_pagination_keyboard(self, current_page: int, total_pages: int,
                                 callback_prefix: str = "page") -> InlineKeyboardMarkup:
        """
        Create a pagination keyboard.

        Args:
            current_page: Current page number (1-based)
            total_pages: Total number of pages
            callback_prefix: Prefix for callback data

        Returns:
            InlineKeyboardMarkup
        """
        keyboard = []

        if total_pages > 1:
            nav_row = []

            # Previous page button
            if current_page > 1:
                nav_row.append(InlineKeyboardButton(
                    "⬅️ Previous",
                    callback_data=f"{callback_prefix}_{current_page - 1}"
                ))

            # Page indicator
            nav_row.append(InlineKeyboardButton(
                f"{current_page}/{total_pages}",
                callback_data="page_info"
            ))

            # Next page button
            if current_page < total_pages:
                nav_row.append(InlineKeyboardButton(
                    "Next ➡️",
                    callback_data=f"{callback_prefix}_{current_page + 1}"
                ))

            keyboard.append(nav_row)

        return InlineKeyboardMarkup(keyboard)

    def build_success_response(self, message: str,
                             keyboard: Optional[InlineKeyboardMarkup] = None,
                             delay: int = DelayConstants.SUCCESS) -> HandlerResponse:
        """Build a standardized success response."""
        return HandlerResponse(
            message=f"✅ {message}",
            keyboard=keyboard,
            interaction_type=InteractionType.FORM_SUBMIT,
            content_type=ContentType.SUCCESS,
            delete_after=delay
        )

    def build_error_response(self, message: str,
                           keyboard: Optional[InlineKeyboardMarkup] = None,
                           delay: int = DelayConstants.ERROR) -> HandlerResponse:
        """Build a standardized error response."""
        return HandlerResponse(
            message=f"❌ {message}",
            keyboard=keyboard,
            interaction_type=InteractionType.ERROR_DISPLAY,
            content_type=ContentType.ERROR,
            delete_after=delay
        )

    def build_validation_error_response(self, errors: List[str],
                                      delay: int = DelayConstants.ERROR) -> HandlerResponse:
        """Build a validation error response with multiple errors."""
        message = "❌ Validation errors:\n" + "\n".join(f"• {error}" for error in errors)
        return HandlerResponse(
            message=message,
            interaction_type=InteractionType.ERROR_DISPLAY,
            content_type=ContentType.VALIDATION_ERROR,
            delete_after=delay
        )

    def build_info_response(self, message: str,
                          keyboard: Optional[InlineKeyboardMarkup] = None,
                          delay: int = DelayConstants.INFO) -> HandlerResponse:
        """Build a standardized info response."""
        return HandlerResponse(
            message=f"ℹ️ {message}",
            keyboard=keyboard,
            interaction_type=InteractionType.MENU_NAVIGATION,
            content_type=ContentType.INFO,
            delete_after=delay
        )

    def build_menu_response(self, title: str, options: Dict[str, str],
                          back_button: bool = True,
                          cancel_button: bool = True) -> HandlerResponse:
        """Build a standardized menu response."""
        keyboard = self.create_menu_keyboard(options, back_button, cancel_button)
        return HandlerResponse(
            message=f"📋 {title}",
            keyboard=keyboard,
            interaction_type=InteractionType.MENU_NAVIGATION,
            content_type=ContentType.SELECTION
        )

    def build_input_request_response(self, prompt: str,
                                   instructions: Optional[str] = None) -> HandlerResponse:
        """Build a standardized input request response."""
        message = f"📝 {prompt}"
        if instructions:
            message += f"\n\n💡 {instructions}"

        return HandlerResponse(
            message=message,
            interaction_type=InteractionType.FORM_INPUT,
            content_type=ContentType.DATA
        )

    def build_data_response(self, data: str, title: Optional[str] = None,
                          keyboard: Optional[InlineKeyboardMarkup] = None,
                          delay: Optional[int] = None) -> HandlerResponse:
        """Build a standardized data display response."""
        message = data
        if title:
            message = f"📊 {title}\n\n{data}"

        return HandlerResponse(
            message=message,
            keyboard=keyboard,
            interaction_type=InteractionType.REPORT_DISPLAY,
            content_type=ContentType.DATA,
            delete_after=delay
        )

    def build_confirmation_response(self, message: str, confirm_data: str = "confirm",
                                  cancel_data: str = "cancel") -> HandlerResponse:
        """Build a standardized confirmation response."""
        keyboard = self.create_confirmation_keyboard(confirm_data, cancel_data)
        return HandlerResponse(
            message=f"❓ {message}",
            keyboard=keyboard,
            interaction_type=InteractionType.CONFIRMATION,
            content_type=ContentType.SELECTION
        )

    async def send_response(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                          response: HandlerResponse) -> Optional[int]:
        """
        Send a response using the appropriate method based on response configuration.

        Args:
            update: Telegram update
            context: Telegram context
            response: Response configuration

        Returns:
            Message ID of sent message
        """
        try:
            if response.delete_after is not None:
                # Use message cleaner for auto-deletion
                if response.interaction_type == InteractionType.MENU_NAVIGATION:
                    message = await send_menu_with_delete(
                        update, context,
                        text=response.message,
                        reply_markup=response.keyboard,
                        delete_after=response.delete_after
                    )
                else:
                    message = await send_and_delete(
                        update, context,
                        text=response.message,
                        reply_markup=response.keyboard,
                        delay=response.delete_after
                    )
            else:
                # Send regular message
                if update.callback_query:
                    message = await update.callback_query.edit_message_text(
                        text=response.message,
                        reply_markup=response.keyboard
                    )
                else:
                    message = await update.message.reply_text(
                        text=response.message,
                        reply_markup=response.keyboard
                    )

            return message.message_id if message else None

        except Exception as e:
            self.logger.error(f"Failed to send response: {e}")
            return None

    def format_list_data(self, items: List[Dict[str, Any]],
                        title: str = "Items",
                        max_items: int = 20) -> str:
        """
        Format a list of items for display.

        Args:
            items: List of dictionaries representing items
            title: Title for the list
            max_items: Maximum items to display

        Returns:
            Formatted string
        """
        if not items:
            return f"📭 No {title.lower()} found."

        message = f"📋 {title} ({len(items)} total):\n\n"

        displayed_items = items[:max_items]
        for i, item in enumerate(displayed_items, 1):
            if isinstance(item, dict):
                # Format dict items
                formatted_item = " | ".join(f"{k}: {v}" for k, v in item.items())
                message += f"{i}. {formatted_item}\n"
            else:
                # Format string items
                message += f"{i}. {item}\n"

        if len(items) > max_items:
            message += f"\n... and {len(items) - max_items} more items"

        return message

    def format_currency(self, amount: Union[int, float, str]) -> str:
        """Format currency values consistently."""
        try:
            if isinstance(amount, str):
                amount = float(amount)
            return f"R$ {amount:.2f}"
        except (ValueError, TypeError):
            return f"R$ {amount}"

    def format_summary_data(self, data: Dict[str, Any], title: str = "Summary") -> str:
        """
        Format summary data for display.

        Args:
            data: Dictionary with summary information
            title: Title for the summary

        Returns:
            Formatted string
        """
        message = f"📊 {title}\n\n"

        for key, value in data.items():
            formatted_key = key.replace('_', ' ').title()
            if isinstance(value, (int, float)) and 'price' in key.lower():
                formatted_value = self.format_currency(value)
            else:
                formatted_value = str(value)

            message += f"• {formatted_key}: {formatted_value}\n"

        return message