"""
Telegram Mini App handler for launching the Pirates Expedition interface.
Provides commands to open the Mini App for authorized users.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

from handlers.base_handler import BaseHandler
from core.interfaces import IUserService
from utils.permissions import require_permission
from models.user import UserLevel
from utils.message_cleaner import send_and_delete

logger = logging.getLogger(__name__)


class MiniAppHandler(BaseHandler):
    """Handler for Mini App functionality."""

    def __init__(self, user_service: IUserService):
        super().__init__("miniapp")
        self.user_service = user_service

    async def handle(self, request) -> 'HandlerResponse':
        """Required abstract method implementation."""
        from handlers.base_handler import HandlerResponse, InteractionType, ContentType
        return HandlerResponse(
            message="Mini App handler - use specific commands like /miniapp, /dashboard, or /expedition",
            keyboard=None,
            next_state=None,
            end_conversation=True
        )

    @require_permission('admin')
    async def handle_miniapp_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Launch the Pirates Expedition Mini App."""
        try:
            chat_id = update.effective_chat.id
            user = self.user_service.get_user_by_chat_id(chat_id)

            if not user:
                await update.message.reply_text(
                    "🏴‍☠️ Access denied! You need to be logged in to access the expedition dashboard.\n\n"
                    "Use /login to authenticate first."
                )
                return

            # Get the webapp URL - this should be configured based on your deployment
            webapp_url = self._get_webapp_url()

            # Create Mini App button
            keyboard = [
                [InlineKeyboardButton(
                    "🏴‍☠️ Open Expedition Dashboard",
                    web_app=WebAppInfo(url=webapp_url)
                )],
                [InlineKeyboardButton(
                    "📊 Quick Stats",
                    callback_data="miniapp_stats"
                )],
                [InlineKeyboardButton(
                    "🗺️ Active Expeditions",
                    callback_data="miniapp_active"
                )]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)

            message_text = (
                "⛵ *Welcome to your Expedition Dashboard, Captain!*\n\n"
                f"🏴‍☠️ *Captain:* {user.username}\n"
                f"⚓ *Rank:* {user.level.value.title()}\n\n"
                "🗺️ *Available Actions:*\n"
                "• View expedition timeline\n"
                "• Track real-time progress\n"
                "• Manage pirate crews\n"
                "• Monitor treasure collection\n"
                "• Access Brambler (name anonymization)\n\n"
                "Tap the button below to launch your full expedition management interface!"
            )

            await send_and_delete(
                message_text,
                update,
                context,
                delay=300,
                protected=False,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )

            logger.info(f"Mini App launched for user {user.username} (chat_id: {chat_id})")

        except Exception as e:
            logger.error(f"Error in miniapp command: {e}", exc_info=True)
            await update.message.reply_text("❌ Ocorreu um erro inesperado. Tente novamente.")

    async def handle_miniapp_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle Mini App related callback queries."""
        try:
            query = update.callback_query
            await query.answer()

            chat_id = update.effective_chat.id
            user = self.user_service.get_user_by_chat_id(chat_id)

            if not user:
                await query.edit_message_text("Access denied. Please login first.")
                return

            callback_data = query.data

            if callback_data == "miniapp_stats":
                await self._show_quick_stats(query, user)
            elif callback_data == "miniapp_active":
                await self._show_active_expeditions(query, user)
            else:
                await query.edit_message_text("Unknown action.")

        except Exception as e:
            logger.error(f"Error in miniapp callback: {e}", exc_info=True)
            await query.edit_message_text("An error occurred. Please try again.")

    async def _show_quick_stats(self, query, user) -> None:
        """Show quick expedition statistics."""
        try:
            # Import here to avoid circular imports
            from core.modern_service_container import get_expedition_service
            expedition_service = get_expedition_service()

            # Get user's expeditions or all expeditions based on permission
            if user.level.value == 'owner':
                expeditions = expedition_service.get_all_expeditions()
            else:
                expeditions = expedition_service.get_expeditions_by_owner(user.chat_id)

            active_count = len([e for e in expeditions if e.status.value == 'active'])
            completed_count = len([e for e in expeditions if e.status.value == 'completed'])
            total_count = len(expeditions)

            # Get overdue expeditions
            overdue_expeditions = expedition_service.get_overdue_expeditions()
            overdue_count = len([e for e in overdue_expeditions if user.level.value == 'owner' or e.owner_chat_id == user.chat_id])

            stats_text = (
                f"📊 *Quick Expedition Stats for {user.username}*\n\n"
                f"⛵ *Total Expeditions:* {total_count}\n"
                f"🟢 *Active:* {active_count}\n"
                f"✅ *Completed:* {completed_count}\n"
                f"🔴 *Overdue:* {overdue_count}\n\n"
                f"📈 *Completion Rate:* {(completed_count/total_count*100):.1f}%" if total_count > 0 else "No expeditions yet"
            )

            # Add back button
            keyboard = [[InlineKeyboardButton("⬅️ Back to Dashboard", callback_data="miniapp_back")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                stats_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )

        except Exception as e:
            logger.error(f"Error showing quick stats: {e}")
            await query.edit_message_text("Error loading stats. Please try again.")

    async def _show_active_expeditions(self, query, user) -> None:
        """Show active expeditions summary."""
        try:
            from core.modern_service_container import get_expedition_service
            expedition_service = get_expedition_service()

            # Get active expeditions
            if user.level.value == 'owner':
                all_expeditions = expedition_service.get_all_expeditions()
            else:
                all_expeditions = expedition_service.get_expeditions_by_owner(user.chat_id)

            active_expeditions = [e for e in all_expeditions if e.status.value == 'active']

            if not active_expeditions:
                expeditions_text = (
                    f"🗺️ *Active Expeditions for {user.username}*\n\n"
                    "No active expeditions found.\n"
                    "Use the Mini App to create new expeditions!"
                )
            else:
                expeditions_text = f"🗺️ *Active Expeditions for {user.username}*\n\n"

                for i, expedition in enumerate(active_expeditions[:5], 1):  # Show max 5
                    # Get expedition progress
                    try:
                        response = expedition_service.get_expedition_response(expedition.id)
                        progress = response.completion_percentage if response else 0
                        progress_bar = "🟢" * int(progress // 20) + "⚪" * (5 - int(progress // 20))
                    except:
                        progress = 0
                        progress_bar = "⚪⚪⚪⚪⚪"

                    expeditions_text += f"{i}. *{expedition.name}*\n"
                    expeditions_text += f"   Progress: {progress_bar} {progress:.1f}%\n"
                    if expedition.deadline:
                        expeditions_text += f"   Deadline: {expedition.deadline.strftime('%d/%m/%Y')}\n"
                    expeditions_text += "\n"

                if len(active_expeditions) > 5:
                    expeditions_text += f"... and {len(active_expeditions) - 5} more expeditions.\n"
                    expeditions_text += "Open the Mini App to see all expeditions."

            # Add back button
            keyboard = [[InlineKeyboardButton("⬅️ Back to Dashboard", callback_data="miniapp_back")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                expeditions_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )

        except Exception as e:
            logger.error(f"Error showing active expeditions: {e}")
            await query.edit_message_text("Error loading expeditions. Please try again.")

    def _get_webapp_url(self) -> str:
        """Get the webapp URL based on environment configuration."""
        import os

        # Use RAILWAY_URL from .env file as the base URL
        base_url = os.getenv('RAILWAY_URL', 'https://your-app.render.com')
        return f"{base_url}/webapp"

    def get_handlers(self):
        """Return list of handlers for registration."""
        return [
            CommandHandler("expedition", self.handle_miniapp_command),
            CommandHandler("dashboard", self.handle_miniapp_command),
            CommandHandler("miniapp", self.handle_miniapp_command),
            CallbackQueryHandler(self.handle_miniapp_callback, pattern=r"^miniapp_"),
        ]