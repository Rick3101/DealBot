"""
Poll Answer Handler - Handles poll answers for broadcast polls.
Tracks user responses and provides poll analytics.
"""

import logging
from telegram import Update, User
from telegram.ext import ContextTypes, PollAnswerHandler

from core.interfaces import IBroadcastService
from handlers.base_handler import BaseHandler
from services.base_service import ServiceError


class ModernPollAnswerHandler(BaseHandler):
    """Modern handler for poll answers."""

    def __init__(self):
        super().__init__("PollAnswerHandler")
    
    async def handle(self, update, context):
        """Abstract method implementation - not used for poll answer handler."""
        pass
        
    async def handle_poll_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle poll answer updates."""
        try:
            self.logger.info(f"Poll answer handler triggered - update: {update}")
            poll_answer = update.poll_answer
            if not poll_answer:
                return

            poll_id = poll_answer.poll_id
            user = poll_answer.user
            option_ids = poll_answer.option_ids

            if not option_ids:
                # User retracted their vote
                return

            # For broadcast polls, we only expect single-choice answers
            option_id = option_ids[0]
            
            # Get user info
            user_id = user.id
            username = user.username or user.first_name or f"User{user_id}"
            
            # Check if this is a broadcast poll
            if not hasattr(context.bot_data, 'broadcast_polls') or poll_id not in context.bot_data['broadcast_polls']:
                return
            
            poll_info = context.bot_data['broadcast_polls'][poll_id]
            
            # Get the poll from Telegram to find the option text
            try:
                from core.modern_service_container import get_broadcast_service
                broadcast_service = get_broadcast_service(context)
                
                # Get the actual option text from stored poll options
                broadcast_id = poll_info.get('broadcast_id')
                options = poll_info.get('options', [])
                
                # Get the correct option text
                if 0 <= option_id < len(options):
                    option_text = options[option_id]
                else:
                    option_text = f"Option {option_id}"
                
                # Record the poll answer with broadcast_id
                success = broadcast_service.record_poll_answer(
                    poll_id=poll_id,
                    user_id=user_id,
                    username=username,
                    option_id=option_id,
                    option_text=option_text,
                    broadcast_id=broadcast_id
                )
                
                if success:
                    self.logger.info(f"Recorded poll answer: user={username}, poll={poll_id}, option={option_id}")
                
                # Don't delete immediately - let the poll stay active for more votes
                # The poll will be cleaned up by the fallback auto-delete after 5 minutes in broadcast service
                
            except Exception as e:
                self.logger.error(f"Error processing poll answer: {e}")
                
        except Exception as e:
            self.logger.error(f"Error in handle_poll_answer: {e}")


def create_poll_answer_handler() -> PollAnswerHandler:
    """Create and configure the poll answer handler."""
    handler = ModernPollAnswerHandler()
    
    return PollAnswerHandler(handler.handle_poll_answer)