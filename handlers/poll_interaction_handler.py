"""
Global poll interaction handler for broadcast polls.
Deletes poll messages immediately when users vote.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes, PollAnswerHandler
from telegram.error import TelegramError


logger = logging.getLogger(__name__)


async def handle_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle poll answers and delete broadcast polls immediately after vote."""
    try:
        poll_answer = update.poll_answer
        if not poll_answer:
            return
            
        poll_id = poll_answer.poll_id
        
        # Check if this is a broadcast poll we're tracking
        broadcast_polls = context.bot_data.get('broadcast_polls', {})
        poll_info = broadcast_polls.get(poll_id)
        
        if not poll_info:
            # Not a broadcast poll we're tracking, ignore
            return
            
        chat_id = poll_info['chat_id']
        message_id = poll_info['message_id']
        
        # Don't delete immediately - let poll stay active for more votes
        # Poll will auto-delete after timeout in broadcast service
        logger.info(f"Poll answer received for poll {poll_id} in chat {chat_id} - keeping poll active")
        
    except Exception as e:
        logger.error(f"Error handling poll answer: {e}", exc_info=True)


def get_poll_interaction_handler():
    """Get the poll interaction handler."""
    return PollAnswerHandler(handle_poll_answer)