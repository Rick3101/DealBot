"""
Broadcast service implementation for sending messages to all users.
"""

import logging
import json
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import TelegramError

from core.interfaces import IBroadcastService, IUserService
from services.base_service import ServiceError, ValidationError, NotFoundError
from utils.message_cleaner import delayed_delete
from models.broadcast import (
    BroadcastMessage, BroadcastType, BroadcastStatus,
    CreateTextBroadcastRequest, CreatePollBroadcastRequest, CreateDiceBroadcastRequest,
    BroadcastSendResult, BroadcastDeliveryResult, BroadcastValidator
)


class BroadcastService(IBroadcastService):
    """Service for managing broadcast messages."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._db_manager = None
    
    @property
    def db_manager(self):
        """Lazy initialization of database manager."""
        if self._db_manager is None:
            from database import get_db_manager
            self._db_manager = get_db_manager()
        return self._db_manager
    
    def create_text_broadcast(self, sender_chat_id: int, content: str, message_type: str) -> int:
        """Create a text broadcast message (text, html, markdown)."""
        try:
            # Convert string to enum
            broadcast_type = BroadcastType(message_type.lower())
            
            # Create request and validate
            request = CreateTextBroadcastRequest(
                sender_chat_id=sender_chat_id,
                content=content,
                message_type=broadcast_type
            )
            
            # Validate request
            errors = BroadcastValidator.validate_text_broadcast(request)
            if errors:
                raise ValidationError("; ".join(errors))
            
            # Insert into database
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO BroadcastMessages 
                        (sender_chat_id, message_type, message_content, status)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id
                    """, (sender_chat_id, message_type.lower(), content, BroadcastStatus.PENDING.value))
                    
                    broadcast_id = cursor.fetchone()[0]
                    conn.commit()
                    
                    self.logger.info(f"Created text broadcast {broadcast_id} for chat {sender_chat_id}")
                    return broadcast_id
                    
        except ValueError as e:
            raise ValidationError(f"Tipo de mensagem inválido: {message_type}")
        except Exception as e:
            self.logger.error(f"Error creating text broadcast: {e}")
            raise ServiceError(f"Erro ao criar broadcast de texto: {str(e)}")
    
    def create_poll_broadcast(self, sender_chat_id: int, question: str, options: List[str]) -> int:
        """Create a poll broadcast message."""
        try:
            # Create request and validate
            request = CreatePollBroadcastRequest(
                sender_chat_id=sender_chat_id,
                question=question,
                options=options
            )
            
            # Validate request
            errors = BroadcastValidator.validate_poll_broadcast(request)
            if errors:
                raise ValidationError("; ".join(errors))
            
            # Insert into database
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO BroadcastMessages 
                        (sender_chat_id, message_type, message_content, poll_question, poll_options, status)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        sender_chat_id, 
                        BroadcastType.POLL.value, 
                        f"Enquete: {question}",
                        question,
                        json.dumps(options),
                        BroadcastStatus.PENDING.value
                    ))
                    
                    broadcast_id = cursor.fetchone()[0]
                    conn.commit()
                    
                    self.logger.info(f"Created poll broadcast {broadcast_id} for chat {sender_chat_id}")
                    return broadcast_id
                    
        except Exception as e:
            self.logger.error(f"Error creating poll broadcast: {e}")
            raise ServiceError(f"Erro ao criar broadcast de enquete: {str(e)}")
    
    def create_dice_broadcast(self, sender_chat_id: int, emoji: str) -> int:
        """Create a dice broadcast message."""
        try:
            # Create request and validate
            request = CreateDiceBroadcastRequest(
                sender_chat_id=sender_chat_id,
                emoji=emoji
            )
            
            # Validate request
            errors = BroadcastValidator.validate_dice_broadcast(request)
            if errors:
                raise ValidationError("; ".join(errors))
            
            # Insert into database
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO BroadcastMessages 
                        (sender_chat_id, message_type, message_content, dice_emoji, status)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        sender_chat_id, 
                        BroadcastType.DICE.value, 
                        f"Dado: {emoji}",
                        emoji,
                        BroadcastStatus.PENDING.value
                    ))
                    
                    broadcast_id = cursor.fetchone()[0]
                    conn.commit()
                    
                    self.logger.info(f"Created dice broadcast {broadcast_id} for chat {sender_chat_id}")
                    return broadcast_id
                    
        except Exception as e:
            self.logger.error(f"Error creating dice broadcast: {e}")
            raise ServiceError(f"Erro ao criar broadcast de dado: {str(e)}")
    
    async def send_broadcast(self, broadcast_id: int, bot_context: ContextTypes.DEFAULT_TYPE) -> BroadcastSendResult:
        """Send broadcast message to all users."""
        try:
            # Get broadcast message
            broadcast = self._get_broadcast_by_id(broadcast_id)
            if not broadcast:
                raise NotFoundError("Broadcast não encontrado")
            
            if broadcast['status'] != BroadcastStatus.PENDING.value:
                raise ValidationError("Broadcast já foi enviado ou está em processo de envio")
            
            # Update status to sending
            self._update_broadcast_status(broadcast_id, BroadcastStatus.SENDING)
            
            # Get all users with chat_id
            users = self._get_all_users_with_chat_id()
            total_recipients = len(users)
            
            if total_recipients == 0:
                raise ValidationError("Nenhum usuário encontrado para envio")
            
            # Update total recipients
            self._update_broadcast_recipients(broadcast_id, total_recipients)
            
            # Send messages
            delivery_results = await self._send_to_all_users(broadcast, users, bot_context)
            
            # Calculate results
            successful = sum(1 for result in delivery_results if result.success)
            failed = total_recipients - successful
            
            # Update final statistics
            self._update_broadcast_completion(broadcast_id, successful, failed, BroadcastStatus.COMPLETED)
            
            result = BroadcastSendResult(
                broadcast_id=broadcast_id,
                total_recipients=total_recipients,
                successful_deliveries=successful,
                failed_deliveries=failed,
                delivery_results=delivery_results,
                completed=True
            )
            
            self.logger.info(f"Broadcast {broadcast_id} completed: {successful}/{total_recipients} delivered")
            return result
            
        except Exception as e:
            # Update status to failed
            self._update_broadcast_status(broadcast_id, BroadcastStatus.FAILED)
            self.logger.error(f"Error sending broadcast {broadcast_id}: {e}")
            raise ServiceError(f"Erro ao enviar broadcast: {str(e)}")
    
    async def _send_to_all_users(self, broadcast: Dict[str, Any], users: List[Dict[str, Any]], 
                                bot_context: ContextTypes.DEFAULT_TYPE) -> List[BroadcastDeliveryResult]:
        """Send message to all users."""
        results = []
        
        for user in users:
            try:
                chat_id = user['chat_id']
                username = user.get('username', 'Unknown')
                
                success = await self._send_to_single_user(broadcast, chat_id, bot_context)
                
                results.append(BroadcastDeliveryResult(
                    chat_id=chat_id,
                    username=username,
                    success=success
                ))
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                results.append(BroadcastDeliveryResult(
                    chat_id=user['chat_id'],
                    username=user.get('username', 'Unknown'),
                    success=False,
                    error_message=str(e)
                ))
                
        return results
    
    async def _send_to_single_user(self, broadcast: Dict[str, Any], chat_id: int, 
                                  bot_context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Send message to a single user."""
        try:
            message_type = broadcast['message_type']
            
            if message_type in ['text', 'html', 'markdown']:
                return await self._send_text_message(broadcast, chat_id, bot_context)
            elif message_type == 'poll':
                return await self._send_poll_message(broadcast, chat_id, bot_context)
            elif message_type == 'dice':
                return await self._send_dice_message(broadcast, chat_id, bot_context)
            else:
                self.logger.warning(f"Unknown message type: {message_type}")
                return False
                
        except TelegramError as e:
            self.logger.warning(f"Telegram error sending to {chat_id}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error sending to {chat_id}: {e}")
            return False
    
    async def _send_text_message(self, broadcast: Dict[str, Any], chat_id: int, 
                                bot_context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Send text message with auto-delete."""
        message_type = broadcast['message_type']
        content = broadcast['message_content']
        
        parse_mode = None
        if message_type == 'html':
            parse_mode = ParseMode.HTML
        elif message_type == 'markdown':
            parse_mode = ParseMode.MARKDOWN_V2
        
        message = await bot_context.bot.send_message(
            chat_id=chat_id,
            text=content,
            parse_mode=parse_mode
        )
        
        # Schedule auto-delete after 30 seconds (consistent with your app's pattern)
        asyncio.create_task(delayed_delete(message, bot_context, delay=30))
        
        return True
    
    async def _send_poll_message(self, broadcast: Dict[str, Any], chat_id: int, 
                                bot_context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Send poll message with delete-on-interaction."""
        question = broadcast['poll_question']
        poll_options = broadcast['poll_options']
        
        # Handle both cases: raw JSON string from DB or already parsed list
        if isinstance(poll_options, str):
            options = json.loads(poll_options)
        else:
            options = poll_options
        
        message = await bot_context.bot.send_poll(
            chat_id=chat_id,
            question=question,
            options=options,
            is_anonymous=True
        )
        
        # Store poll message for deletion on interaction
        if not hasattr(bot_context.bot_data, 'broadcast_polls'):
            bot_context.bot_data['broadcast_polls'] = {}
        
        # Map poll_id to message info for deletion on vote
        poll_id = message.poll.id
        bot_context.bot_data['broadcast_polls'][poll_id] = {
            'chat_id': chat_id,
            'message_id': message.message_id,
            'broadcast_id': broadcast['id'],
            'question': question,
            'options': options  # Store options for answer recording
        }
        
        # Also schedule fallback auto-delete after 5 minutes if no interaction
        asyncio.create_task(delayed_delete(message, bot_context, delay=300))
        
        return True
    
    async def _send_dice_message(self, broadcast: Dict[str, Any], chat_id: int, 
                                bot_context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Send dice message with quick delete after result."""
        emoji = broadcast['dice_emoji']
        
        message = await bot_context.bot.send_dice(
            chat_id=chat_id,
            emoji=emoji
        )
        
        # Dice shows animation and result, then delete after 5 seconds to let users see result
        asyncio.create_task(delayed_delete(message, bot_context, delay=5))
        
        return True
    
    def get_broadcast_status(self, broadcast_id: int) -> Optional[Dict[str, Any]]:
        """Get broadcast status and statistics."""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT id, sender_chat_id, message_type, message_content, 
                               poll_question, poll_options, dice_emoji,
                               total_recipients, successful_deliveries, failed_deliveries,
                               created_at, sent_at, completed_at, status
                        FROM BroadcastMessages
                        WHERE id = %s
                    """, (broadcast_id,))
                    
                    row = cursor.fetchone()
                    if not row:
                        return None
                    
                    return {
                        'id': row[0],
                        'sender_chat_id': row[1],
                        'message_type': row[2],
                        'message_content': row[3],
                        'poll_question': row[4],
                        'poll_options': json.loads(row[5]) if row[5] else None,
                        'dice_emoji': row[6],
                        'total_recipients': row[7],
                        'successful_deliveries': row[8],
                        'failed_deliveries': row[9],
                        'created_at': row[10],
                        'sent_at': row[11],
                        'completed_at': row[12],
                        'status': row[13]
                    }
                    
        except Exception as e:
            self.logger.error(f"Error getting broadcast status: {e}")
            raise ServiceError(f"Erro ao obter status do broadcast: {str(e)}")
    
    def get_all_broadcasts(self, sender_chat_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all broadcast messages, optionally filtered by sender."""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    if sender_chat_id:
                        cursor.execute("""
                            SELECT id, sender_chat_id, message_type, message_content,
                                   total_recipients, successful_deliveries, failed_deliveries,
                                   created_at, status
                            FROM BroadcastMessages
                            WHERE sender_chat_id = %s
                            ORDER BY created_at DESC
                        """, (sender_chat_id,))
                    else:
                        cursor.execute("""
                            SELECT id, sender_chat_id, message_type, message_content,
                                   total_recipients, successful_deliveries, failed_deliveries,
                                   created_at, status
                            FROM BroadcastMessages
                            ORDER BY created_at DESC
                        """)
                    
                    rows = cursor.fetchall()
                    
                    return [
                        {
                            'id': row[0],
                            'sender_chat_id': row[1],
                            'message_type': row[2],
                            'message_content': row[3][:100] + '...' if len(row[3]) > 100 else row[3],
                            'total_recipients': row[4],
                            'successful_deliveries': row[5],
                            'failed_deliveries': row[6],
                            'created_at': row[7],
                            'status': row[8]
                        }
                        for row in rows
                    ]
                    
        except Exception as e:
            self.logger.error(f"Error getting all broadcasts: {e}")
            raise ServiceError(f"Erro ao obter broadcasts: {str(e)}")
    
    def delete_broadcast(self, broadcast_id: int) -> bool:
        """Delete a broadcast message."""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        DELETE FROM BroadcastMessages WHERE id = %s
                    """, (broadcast_id,))
                    
                    deleted = cursor.rowcount > 0
                    conn.commit()
                    
                    if deleted:
                        self.logger.info(f"Deleted broadcast {broadcast_id}")
                    
                    return deleted
                    
        except Exception as e:
            self.logger.error(f"Error deleting broadcast: {e}")
            raise ServiceError(f"Erro ao deletar broadcast: {str(e)}")
    
    def _get_broadcast_by_id(self, broadcast_id: int) -> Optional[Dict[str, Any]]:
        """Get broadcast by ID."""
        with self.db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, sender_chat_id, message_type, message_content,
                           poll_question, poll_options, dice_emoji, status
                    FROM BroadcastMessages
                    WHERE id = %s
                """, (broadcast_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                return {
                    'id': row[0],
                    'sender_chat_id': row[1],
                    'message_type': row[2],
                    'message_content': row[3],
                    'poll_question': row[4],
                    'poll_options': row[5],
                    'dice_emoji': row[6],
                    'status': row[7]
                }
    
    def _get_all_users_with_chat_id(self) -> List[Dict[str, Any]]:
        """Get all users with chat_id."""
        with self.db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT chat_id, username
                    FROM Usuarios
                    WHERE chat_id IS NOT NULL
                """)
                
                rows = cursor.fetchall()
                return [
                    {
                        'chat_id': row[0],
                        'username': row[1]
                    }
                    for row in rows
                ]
    
    def _update_broadcast_status(self, broadcast_id: int, status: BroadcastStatus) -> None:
        """Update broadcast status."""
        with self.db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                if status == BroadcastStatus.SENDING:
                    cursor.execute("""
                        UPDATE BroadcastMessages
                        SET status = %s, sent_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (status.value, broadcast_id))
                else:
                    cursor.execute("""
                        UPDATE BroadcastMessages
                        SET status = %s
                        WHERE id = %s
                    """, (status.value, broadcast_id))
                
                conn.commit()
    
    def _update_broadcast_recipients(self, broadcast_id: int, total_recipients: int) -> None:
        """Update total recipients count."""
        with self.db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE BroadcastMessages
                    SET total_recipients = %s
                    WHERE id = %s
                """, (total_recipients, broadcast_id))
                
                conn.commit()
    
    def _update_broadcast_completion(self, broadcast_id: int, successful: int, 
                                   failed: int, status: BroadcastStatus) -> None:
        """Update broadcast completion statistics."""
        with self.db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE BroadcastMessages
                    SET successful_deliveries = %s, failed_deliveries = %s,
                        completed_at = CURRENT_TIMESTAMP, status = %s
                    WHERE id = %s
                """, (successful, failed, status.value, broadcast_id))
                
                conn.commit()
    
    def record_poll_answer(self, poll_id: str, user_id: int, username: str, 
                          option_id: int, option_text: str, broadcast_id: int = None) -> bool:
        """Record a poll answer from a user."""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    # If broadcast_id not provided, try to find it
                    if not broadcast_id:
                        cursor.execute("""
                            SELECT id FROM BroadcastMessages 
                            WHERE message_type = 'poll' 
                            AND status = 'completed'
                            ORDER BY created_at DESC
                            LIMIT 1
                        """)
                        
                        row = cursor.fetchone()
                        if not row:
                            self.logger.warning(f"Could not find broadcast for poll_id: {poll_id}")
                            return False
                        broadcast_id = row[0]
                    
                    # Insert or update poll answer (UPSERT)
                    cursor.execute("""
                        INSERT INTO PollAnswers 
                        (broadcast_id, poll_id, user_id, username, option_id, option_text)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (poll_id, user_id) 
                        DO UPDATE SET 
                            option_id = EXCLUDED.option_id,
                            option_text = EXCLUDED.option_text,
                            answered_at = CURRENT_TIMESTAMP
                    """, (broadcast_id, poll_id, user_id, username, option_id, option_text))
                    
                    conn.commit()
                    self.logger.info(f"Recorded poll answer from user {username} ({user_id}) for poll {poll_id}, broadcast {broadcast_id}")
                    return True
                    
        except Exception as e:
            self.logger.error(f"Error recording poll answer: {e}")
            return False
    
    def get_poll_results(self, broadcast_id: int) -> Dict[str, Any]:
        """Get poll results for a broadcast."""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Get broadcast info
                    cursor.execute("""
                        SELECT poll_question, poll_options, created_at, total_recipients
                        FROM BroadcastMessages
                        WHERE id = %s AND message_type = 'poll'
                    """, (broadcast_id,))
                    
                    broadcast_row = cursor.fetchone()
                    if not broadcast_row:
                        return None
                    
                    question, options_json, created_at, total_recipients = broadcast_row
                    
                    # Parse options
                    if isinstance(options_json, str):
                        options = json.loads(options_json)
                    else:
                        options = options_json
                    
                    # Get all answers
                    cursor.execute("""
                        SELECT option_id, option_text, user_id, username, answered_at
                        FROM PollAnswers
                        WHERE broadcast_id = %s
                        ORDER BY answered_at DESC
                    """, (broadcast_id,))
                    
                    answers = cursor.fetchall()
                    
                    # Count votes by option
                    vote_counts = {}
                    user_answers = []
                    
                    for answer in answers:
                        option_id, option_text, user_id, username, answered_at = answer
                        
                        if option_id not in vote_counts:
                            vote_counts[option_id] = {'text': option_text, 'count': 0, 'percentage': 0}
                        vote_counts[option_id]['count'] += 1
                        
                        user_answers.append({
                            'user_id': user_id,
                            'username': username,
                            'option_id': option_id,
                            'option_text': option_text,
                            'answered_at': answered_at
                        })
                    
                    # Calculate percentages
                    total_votes = len(answers)
                    for option_data in vote_counts.values():
                        if total_votes > 0:
                            option_data['percentage'] = (option_data['count'] / total_votes) * 100
                    
                    return {
                        'broadcast_id': broadcast_id,
                        'question': question,
                        'options': options,
                        'total_recipients': total_recipients,
                        'total_votes': total_votes,
                        'vote_counts': vote_counts,
                        'user_answers': user_answers,
                        'created_at': created_at,
                        'response_rate': (total_votes / total_recipients * 100) if total_recipients > 0 else 0
                    }
                    
        except Exception as e:
            self.logger.error(f"Error getting poll results: {e}")
            raise ServiceError(f"Erro ao obter resultados da enquete: {str(e)}")
    
    def get_all_poll_results(self, sender_chat_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get results for all polls, optionally filtered by sender."""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    if sender_chat_id:
                        cursor.execute("""
                            SELECT DISTINCT bm.id, bm.poll_question, bm.created_at, 
                                   bm.total_recipients,
                                   (SELECT COUNT(*) FROM PollAnswers pa WHERE pa.broadcast_id = bm.id) as total_votes
                            FROM BroadcastMessages bm
                            WHERE bm.message_type = 'poll' AND bm.sender_chat_id = %s
                            ORDER BY bm.created_at DESC
                        """, (sender_chat_id,))
                    else:
                        cursor.execute("""
                            SELECT DISTINCT bm.id, bm.poll_question, bm.created_at, 
                                   bm.total_recipients,
                                   (SELECT COUNT(*) FROM PollAnswers pa WHERE pa.broadcast_id = bm.id) as total_votes
                            FROM BroadcastMessages bm
                            WHERE bm.message_type = 'poll'
                            ORDER BY bm.created_at DESC
                        """)
                    
                    rows = cursor.fetchall()
                    
                    results = []
                    for row in rows:
                        broadcast_id, question, created_at, total_recipients, total_votes = row
                        response_rate = (total_votes / total_recipients * 100) if total_recipients > 0 else 0
                        
                        results.append({
                            'broadcast_id': broadcast_id,
                            'question': question[:100] + '...' if len(question) > 100 else question,
                            'created_at': created_at,
                            'total_recipients': total_recipients,
                            'total_votes': total_votes,
                            'response_rate': round(response_rate, 1)
                        })
                    
                    return results
                    
        except Exception as e:
            self.logger.error(f"Error getting all poll results: {e}")
            raise ServiceError(f"Erro ao obter lista de enquetes: {str(e)}")