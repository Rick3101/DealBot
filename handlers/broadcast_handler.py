"""
Broadcast handler for sending messages to all users.
Supports text, HTML, Markdown, polls, and dice messages.
"""

import logging
import asyncio
from typing import Dict, Any, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters
)

from handlers.base_handler import (
    ConversationHandlerBase, HandlerRequest, HandlerResponse,
    InteractionType, ContentType, DelayConstants
)
from utils.permissions import require_permission
from utils.message_cleaner import delayed_delete
from services.base_service import ValidationError, ServiceError, NotFoundError
from core.modern_service_container import get_broadcast_service
from models.broadcast import BroadcastType, BroadcastValidator, BroadcastMessageType


# Conversation states
(BROADCAST_MENU, BROADCAST_TYPE, BROADCAST_TEXT_CONTENT, BROADCAST_POLL_QUESTION, 
 BROADCAST_POLL_OPTIONS, BROADCAST_DICE_EMOJI, BROADCAST_CONFIRM, BROADCAST_SEND) = range(8)


class BroadcastHandler(ConversationHandlerBase):
    """Handler for broadcast messaging system."""
    
    def __init__(self):
        super().__init__("broadcast")
    
    @require_permission('owner')
    async def start_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start broadcast creation process."""
        request = self.create_request(update, context)
        response = await self.show_main_menu(request)
        return await self.send_response(response, request)
    
    async def show_main_menu(self, request: HandlerRequest) -> HandlerResponse:
        """Show main broadcast menu."""
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📝 Texto simples", callback_data="type_text")],
            [InlineKeyboardButton("🌐 HTML", callback_data="type_html")],
            [InlineKeyboardButton("📄 Markdown", callback_data="type_markdown")],
            [InlineKeyboardButton("📊 Enquete", callback_data="type_poll")],
            [InlineKeyboardButton("🎲 Dado", callback_data="type_dice")],
            [InlineKeyboardButton("📋 Ver histórico", callback_data="view_history")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancel")]
        ])
        
        message = (
            "🔔 *Sistema de Broadcast*\n\n"
            "Escolha o tipo de mensagem que deseja enviar para todos os usuários:\n\n"
            "📝 *Texto simples* - Mensagem de texto normal\n"
            "🌐 *HTML* - Formatação HTML (negrito, itálico, links)\n"
            "📄 *Markdown* - Formatação Markdown\n"
            "📊 *Enquete* - Criar uma enquete interativa\n"
            "🎲 *Dado* - Enviar um dado animado\n"
            "📋 *Histórico* - Ver broadcasts enviados"
        )
        
        return self.create_smart_response(
            message=message,
            keyboard=keyboard,
            interaction_type=InteractionType.MENU_NAVIGATION,
            content_type=ContentType.SELECTION,
            next_state=BROADCAST_MENU
        )
    
    async def handle_menu_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle main menu selection."""
        request = self.create_request(update, context)
        query = update.callback_query
        await query.answer()
        
        selection = query.data
        
        if selection == "cancel":
            return await self._handle_cancel(request)
        elif selection == "view_history":
            return await self._show_history(request)
        elif selection.startswith("type_"):
            message_type = selection.replace("type_", "")
            context.user_data['broadcast_type'] = message_type
            return await self._handle_type_selection(request, message_type)
        elif selection.startswith("poll_results_"):
            broadcast_id = int(selection.replace("poll_results_", ""))
            return await self._show_poll_results(request, broadcast_id)
        
        return ConversationHandler.END
    
    async def _handle_type_selection(self, request: HandlerRequest, message_type: str) -> int:
        """Handle broadcast type selection."""
        try:
            if message_type in ['text', 'html', 'markdown']:
                response = await self._prompt_for_text_content(request, message_type)
                return await self.send_response(response, request)
            elif message_type == 'poll':
                response = await self._prompt_for_poll_question(request)
                return await self.send_response(response, request)
            elif message_type == 'dice':
                response = await self._prompt_for_dice_emoji(request)
                return await self.send_response(response, request)
            else:
                raise ValidationError("Tipo de mensagem inválido")
                
        except Exception as e:
            error_response = await self.handle_error(e, request)
            return await self.send_response(error_response, request)
    
    async def _prompt_for_text_content(self, request: HandlerRequest, message_type: str) -> HandlerResponse:
        """Prompt for text content."""
        type_info = {
            'text': ("texto simples", "Digite a mensagem que será enviada:"),
            'html': ("HTML", "Digite a mensagem com formatação HTML:\n\nExemplo: `<b>Negrito</b> <i>Itálico</i> <a href='https://example.com'>Link</a>`"),
            'markdown': ("Markdown", "Digite a mensagem com formatação Markdown:\n\nExemplo: `**Negrito** *Itálico* [Link](https://example.com)`")
        }
        
        type_name, prompt = type_info.get(message_type, ("texto", "Digite a mensagem:"))
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("↩ Voltar ao menu", callback_data="back_to_menu")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancel")]
        ])
        
        message = f"📝 *Criando broadcast de {type_name}*\n\n{prompt}"
        
        response = self.create_smart_response(
            message=message,
            keyboard=keyboard,
            interaction_type=InteractionType.FORM_INPUT,
            content_type=ContentType.INFO,
            next_state=BROADCAST_TEXT_CONTENT
        )
        # Override delay and protection for creation messages to auto-delete after 30 seconds
        response.delay = DelayConstants.FILE_TRANSFER // 4  # 30 seconds
        response.protected = False
        return response
    
    async def handle_text_content(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle text content input."""
        request = self.create_request(update, context)
        
        try:
            content = update.message.text.strip()
            message_type = context.user_data.get('broadcast_type')
            
            if not content:
                raise ValidationError("Conteúdo não pode estar vazio")
            
            # Store content and show confirmation
            context.user_data['broadcast_content'] = content
            response = await self._show_text_confirmation(request, message_type, content)
            return await self.send_response(response, request)
            
        except Exception as e:
            error_response = await self.handle_error(e, request)
            return await self.send_response(error_response, request)
    
    async def _show_text_confirmation(self, request: HandlerRequest, message_type: str, content: str) -> HandlerResponse:
        """Show text broadcast confirmation."""
        preview = content[:200] + "..." if len(content) > 200 else content
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Enviar agora", callback_data="send_broadcast")],
            [InlineKeyboardButton("✏ Editar mensagem", callback_data="edit_content")],
            [InlineKeyboardButton("↩ Voltar ao menu", callback_data="back_to_menu")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancel")]
        ])
        
        type_display = BroadcastMessageType.format_for_display(BroadcastType(message_type))
        
        message = (
            f"📝 *Confirmar Broadcast - {type_display}*\n\n"
            f"**Conteúdo:**\n{preview}\n\n"
            f"**Tamanho:** {len(content)} caracteres\n\n"
            "⚠ *Esta mensagem será enviada para todos os usuários cadastrados!*"
        )
        
        return self.create_smart_response(
            message=message,
            keyboard=keyboard,
            interaction_type=InteractionType.CONFIRMATION,
            content_type=ContentType.WARNING,
            next_state=BROADCAST_CONFIRM
        )
    
    async def _prompt_for_poll_question(self, request: HandlerRequest) -> HandlerResponse:
        """Prompt for poll question."""
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("↩ Voltar ao menu", callback_data="back_to_menu")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancel")]
        ])
        
        message = (
            "📊 *Criando Broadcast de Enquete*\n\n"
            "Digite a pergunta da enquete:\n\n"
            "*Exemplo:* Qual é o seu produto favorito?"
        )
        
        response = self.create_smart_response(
            message=message,
            keyboard=keyboard,
            interaction_type=InteractionType.FORM_INPUT,
            content_type=ContentType.INFO,
            next_state=BROADCAST_POLL_QUESTION
        )
        # Override delay and protection for creation messages to auto-delete after 30 seconds
        response.delay = DelayConstants.FILE_TRANSFER // 4  # 30 seconds
        response.protected = False
        return response
    
    async def handle_poll_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle poll question input."""
        request = self.create_request(update, context)
        
        try:
            question = update.message.text.strip()
            
            if not question:
                raise ValidationError("Pergunta não pode estar vazia")
            
            context.user_data['poll_question'] = question
            response = await self._prompt_for_poll_options(request, question)
            return await self.send_response(response, request)
            
        except Exception as e:
            error_response = await self.handle_error(e, request)
            return await self.send_response(error_response, request)
    
    async def _prompt_for_poll_options(self, request: HandlerRequest, question: str) -> HandlerResponse:
        """Prompt for poll options."""
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("↩ Voltar ao menu", callback_data="back_to_menu")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancel")]
        ])
        
        message = (
            f"📊 *Criando Enquete*\n\n"
            f"**Pergunta:** {question}\n\n"
            "Agora digite as opções da enquete, *uma por linha*:\n\n"
            "*Exemplo:*\n"
            "Opção 1\n"
            "Opção 2\n"
            "Opção 3\n\n"
            "*Mínimo: 2 opções | Máximo: 10 opções*"
        )
        
        return self.create_smart_response(
            message=message,
            keyboard=keyboard,
            interaction_type=InteractionType.FORM_INPUT,
            content_type=ContentType.INFO,
            next_state=BROADCAST_POLL_OPTIONS
        )
    
    async def handle_poll_options(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle poll options input."""
        request = self.create_request(update, context)
        
        try:
            options_text = update.message.text.strip()
            options = [opt.strip() for opt in options_text.split('\n') if opt.strip()]
            
            if len(options) < 2:
                raise ValidationError("Você deve fornecer pelo menos 2 opções")
            
            if len(options) > 10:
                raise ValidationError("Máximo de 10 opções permitidas")
            
            context.user_data['poll_options'] = options
            response = await self._show_poll_confirmation(request)
            return await self.send_response(response, request)
            
        except Exception as e:
            error_response = await self.handle_error(e, request)
            return await self.send_response(error_response, request)
    
    async def _show_poll_confirmation(self, request: HandlerRequest) -> HandlerResponse:
        """Show poll broadcast confirmation."""
        question = request.user_data['poll_question']
        options = request.user_data['poll_options']
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Enviar enquete", callback_data="send_broadcast")],
            [InlineKeyboardButton("✏ Editar enquete", callback_data="edit_content")],
            [InlineKeyboardButton("↩ Voltar ao menu", callback_data="back_to_menu")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancel")]
        ])
        
        options_preview = "\n".join([f"• {opt}" for opt in options])
        
        message = (
            f"📊 *Confirmar Broadcast - Enquete*\n\n"
            f"**Pergunta:** {question}\n\n"
            f"**Opções:**\n{options_preview}\n\n"
            "⚠ *Esta enquete será enviada para todos os usuários cadastrados!*"
        )
        
        return self.create_smart_response(
            message=message,
            keyboard=keyboard,
            interaction_type=InteractionType.CONFIRMATION,
            content_type=ContentType.WARNING,
            next_state=BROADCAST_CONFIRM
        )
    
    async def _prompt_for_dice_emoji(self, request: HandlerRequest) -> HandlerResponse:
        """Show dice emoji selection."""
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎲", callback_data="dice_🎲"), InlineKeyboardButton("🎯", callback_data="dice_🎯")],
            [InlineKeyboardButton("🎳", callback_data="dice_🎳"), InlineKeyboardButton("🏀", callback_data="dice_🏀")],
            [InlineKeyboardButton("⚽", callback_data="dice_⚽"), InlineKeyboardButton("🎰", callback_data="dice_🎰")],
            [InlineKeyboardButton("↩ Voltar ao menu", callback_data="back_to_menu")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancel")]
        ])
        
        message = (
            "🎲 *Criando Broadcast de Dado*\n\n"
            "Escolha o tipo de dado que será enviado:\n\n"
            "🎲 Dado clássico (1-6)\n"
            "🎯 Dardo (1-6)\n"
            "🎳 Boliche (1-6)\n"
            "🏀 Basquete (1-5)\n"
            "⚽ Futebol (1-5)\n"
            "🎰 Caça-níqueis (1-64)"
        )
        
        response = self.create_smart_response(
            message=message,
            keyboard=keyboard,
            interaction_type=InteractionType.MENU_NAVIGATION,
            content_type=ContentType.SELECTION,
            next_state=BROADCAST_DICE_EMOJI
        )
        # Override delay and protection for creation messages to auto-delete after 30 seconds
        response.delay = DelayConstants.FILE_TRANSFER // 4  # 30 seconds
        response.protected = False
        return response
    
    async def handle_dice_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle dice emoji selection."""
        request = self.create_request(update, context)
        query = update.callback_query
        await query.answer()
        
        try:
            if query.data.startswith("dice_"):
                emoji = query.data.replace("dice_", "")
                context.user_data['dice_emoji'] = emoji
                response = await self._show_dice_confirmation(request, emoji)
                return await self.send_response(response, request)
            else:
                return await self._handle_navigation(request, query.data)
                
        except Exception as e:
            error_response = await self.handle_error(e, request)
            return await self.send_response(error_response, request)
    
    async def _show_dice_confirmation(self, request: HandlerRequest, emoji: str) -> HandlerResponse:
        """Show dice broadcast confirmation."""
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Enviar dado", callback_data="send_broadcast")],
            [InlineKeyboardButton("🎲 Escolher outro", callback_data="edit_content")],
            [InlineKeyboardButton("↩ Voltar ao menu", callback_data="back_to_menu")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancel")]
        ])
        
        emoji_names = {
            "🎲": "Dado clássico",
            "🎯": "Dardo",
            "🎳": "Boliche",
            "🏀": "Basquete",
            "⚽": "Futebol",
            "🎰": "Caça-níqueis"
        }
        
        emoji_name = emoji_names.get(emoji, "Desconhecido")
        
        message = (
            f"🎲 *Confirmar Broadcast - Dado*\n\n"
            f"**Tipo de dado:** {emoji} {emoji_name}\n\n"
            "⚠ *Este dado será enviado para todos os usuários cadastrados!*"
        )
        
        return self.create_smart_response(
            message=message,
            keyboard=keyboard,
            interaction_type=InteractionType.CONFIRMATION,
            content_type=ContentType.WARNING,
            next_state=BROADCAST_CONFIRM
        )
    
    async def handle_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle broadcast confirmation actions."""
        request = self.create_request(update, context)
        query = update.callback_query
        await query.answer()
        
        try:
            action = query.data
            
            if action == "send_broadcast":
                return await self._send_broadcast(request)
            elif action == "edit_content":
                return await self._handle_edit_content(request)
            else:
                return await self._handle_navigation(request, action)
                
        except Exception as e:
            error_response = await self.handle_error(e, request)
            return await self.send_response(error_response, request)
    
    async def _send_broadcast(self, request: HandlerRequest) -> int:
        """Send the broadcast message."""
        try:
            broadcast_service = get_broadcast_service(request.context)
            broadcast_type = request.user_data.get('broadcast_type')
            
            # Create broadcast based on type
            if broadcast_type in ['text', 'html', 'markdown']:
                content = request.user_data['broadcast_content']
                broadcast_id = broadcast_service.create_text_broadcast(
                    sender_chat_id=request.chat_id,
                    content=content,
                    message_type=broadcast_type
                )
            elif broadcast_type == 'poll':
                question = request.user_data['poll_question']
                options = request.user_data['poll_options']
                broadcast_id = broadcast_service.create_poll_broadcast(
                    sender_chat_id=request.chat_id,
                    question=question,
                    options=options
                )
            elif broadcast_type == 'dice':
                emoji = request.user_data['dice_emoji']
                broadcast_id = broadcast_service.create_dice_broadcast(
                    sender_chat_id=request.chat_id,
                    emoji=emoji
                )
            else:
                raise ValidationError("Tipo de broadcast inválido")
            
            # Show sending status
            response = HandlerResponse(
                message="⏳ Enviando broadcast para todos os usuários...\nIsto pode levar alguns minutos.",
                next_state=ConversationHandler.END,
                delay=DelayConstants.SUCCESS,
                end_conversation=True
            )
            
            # Send broadcast in background
            asyncio.create_task(self._send_broadcast_async(broadcast_id, request.context, request.chat_id))
            
            return await self.send_response(response, request)
            
        except Exception as e:
            error_response = await self.handle_error(e, request)
            return await self.send_response(error_response, request)
    
    async def _send_broadcast_async(self, broadcast_id: int, context: ContextTypes.DEFAULT_TYPE, sender_chat_id: int):
        """Send broadcast asynchronously and notify sender."""
        try:
            broadcast_service = get_broadcast_service(context)
            result = await broadcast_service.send_broadcast(broadcast_id, context)
            
            # Notify sender of completion
            success_rate = (result.successful_deliveries / result.total_recipients * 100) if result.total_recipients > 0 else 0
            
            completion_message = (
                f"✅ *Broadcast enviado com sucesso!*\n\n"
                f"**Estatísticas:**\n"
                f"• Total de usuários: {result.total_recipients}\n"
                f"• Enviados com sucesso: {result.successful_deliveries}\n"
                f"• Falhas: {result.failed_deliveries}\n"
                f"• Taxa de sucesso: {success_rate:.1f}%"
            )
            
            message = await context.bot.send_message(
                chat_id=sender_chat_id,
                text=completion_message,
                parse_mode="Markdown"
            )
            
            # Schedule auto-delete after 30 seconds
            asyncio.create_task(delayed_delete(message, context, delay=DelayConstants.FILE_TRANSFER // 4))
            
        except Exception as e:
            await context.bot.send_message(
                chat_id=sender_chat_id,
                text=f"❌ Erro ao enviar broadcast: {str(e)}",
                parse_mode="Markdown"
            )
    
    async def _show_history(self, request: HandlerRequest) -> int:
        """Show broadcast history."""
        try:
            broadcast_service = get_broadcast_service(request.context)
            broadcasts = broadcast_service.get_all_broadcasts(request.chat_id)
            
            if not broadcasts:
                message = "📋 *Histórico de Broadcasts*\n\nNenhum broadcast encontrado."
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("↩ Voltar", callback_data="back_to_menu")]
                ])
            else:
                message = "📋 *Histórico de Broadcasts*\n\n"
                keyboard_buttons = []
                
                for broadcast in broadcasts[:10]:  # Show last 10
                    type_display = BroadcastMessageType.format_for_display(BroadcastType(broadcast['message_type']))
                    status = "✅" if broadcast['status'] == 'completed' else "❌" if broadcast['status'] == 'failed' else "⏳"
                    
                    message += (
                        f"{status} *{type_display}* - {broadcast['created_at'].strftime('%d/%m %H:%M')}\n"
                        f"   {broadcast['message_content']}\n"
                        f"   📊 {broadcast['successful_deliveries']}/{broadcast['total_recipients']} usuários"
                    )
                    
                    # Add poll results if it's a poll broadcast
                    if broadcast['message_type'] == 'poll' and broadcast['status'] == 'completed':
                        try:
                            poll_results = broadcast_service.get_poll_results(broadcast['id'])
                            if poll_results and poll_results['total_votes'] > 0:
                                message += f" | 📊 {poll_results['total_votes']} votos ({poll_results['response_rate']:.1f}%)"
                                keyboard_buttons.append([
                                    InlineKeyboardButton(f"📊 Ver resultados: {broadcast['message_content'][:30]}...", 
                                                       callback_data=f"poll_results_{broadcast['id']}")
                                ])
                        except Exception as e:
                            self.logger.warning(f"Could not load poll results for broadcast {broadcast['id']}: {e}")
                    
                    message += "\n\n"
                
                keyboard_buttons = [
                    [InlineKeyboardButton("↩ Voltar", callback_data="back_to_menu")],
                    [InlineKeyboardButton("❌ Fechar", callback_data="cancel")]
                ]
                keyboard = InlineKeyboardMarkup(keyboard_buttons)
            
            response = self.create_smart_response(
                message=message,
                keyboard=keyboard,
                interaction_type=InteractionType.REPORT_DISPLAY,
                content_type=ContentType.DATA,
                next_state=BROADCAST_MENU
            )
            
            return await self.send_response(response, request)
            
        except Exception as e:
            error_response = await self.handle_error(e, request)
            return await self.send_response(error_response, request)
    
    async def _show_poll_results(self, request: HandlerRequest, broadcast_id: int) -> int:
        """Show detailed poll results."""
        try:
            broadcast_service = get_broadcast_service(request.context)
            poll_results = broadcast_service.get_poll_results(broadcast_id)
            
            if not poll_results:
                message = "❌ Resultados da enquete não encontrados."
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("↩ Voltar", callback_data="view_history")]
                ])
            else:
                message = f"📊 *Resultados da Enquete*\n\n"
                message += f"**Pergunta:** {poll_results['question']}\n\n"
                message += f"**Estatísticas:**\n"
                message += f"• Total de usuários: {poll_results['total_recipients']}\n"
                message += f"• Total de votos: {poll_results['total_votes']}\n"
                message += f"• Taxa de resposta: {poll_results['response_rate']:.1f}%\n\n"
                
                if poll_results['total_votes'] > 0:
                    message += "**Resultados por opção:**\n"
                    for option_id, option_data in poll_results['vote_counts'].items():
                        percentage_bar = "▓" * int(option_data['percentage'] / 10) + "░" * (10 - int(option_data['percentage'] / 10))
                        message += f"{option_data['text']}: {option_data['count']} ({option_data['percentage']:.1f}%)\n"
                        message += f"{percentage_bar}\n\n"
                    
                    message += "**Últimas respostas:**\n"
                    for answer in poll_results['user_answers'][:10]:  # Show last 10 answers
                        timestamp = answer['answered_at'].strftime('%d/%m %H:%M')
                        message += f"• {answer['username']}: {answer['option_text']} ({timestamp})\n"
                else:
                    message += "Nenhum voto recebido ainda."
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("↩ Voltar ao histórico", callback_data="view_history")],
                    [InlineKeyboardButton("🏠 Menu principal", callback_data="back_to_menu")]
                ])
            
            response = self.create_smart_response(
                message=message,
                keyboard=keyboard,
                interaction_type=InteractionType.REPORT_DISPLAY,
                content_type=ContentType.DATA,
                next_state=BROADCAST_MENU
            )
            
            return await self.send_response(response, request)
            
        except Exception as e:
            error_response = await self.handle_error(e, request)
            return await self.send_response(error_response, request)
    
    async def _handle_navigation(self, request: HandlerRequest, action: str) -> int:
        """Handle navigation actions."""
        if action == "back_to_menu":
            # Clear user data
            for key in ['broadcast_type', 'broadcast_content', 'poll_question', 'poll_options', 'dice_emoji']:
                request.user_data.pop(key, None)
            
            response = await self.show_main_menu(request)
            return await self.send_response(response, request)
        elif action == "cancel":
            return await self._handle_cancel(request)
        
        return ConversationHandler.END
    
    async def _handle_edit_content(self, request: HandlerRequest) -> int:
        """Handle content editing."""
        broadcast_type = request.user_data.get('broadcast_type')
        
        if broadcast_type in ['text', 'html', 'markdown']:
            response = await self._prompt_for_text_content(request, broadcast_type)
        elif broadcast_type == 'poll':
            response = await self._prompt_for_poll_question(request)
        elif broadcast_type == 'dice':
            response = await self._prompt_for_dice_emoji(request)
        else:
            response = await self.show_main_menu(request)
        
        return await self.send_response(response, request)
    
    async def _handle_cancel(self, request: HandlerRequest) -> int:
        """Handle cancellation - instant deletion without confirmation."""
        # Delete the message directly if it's a callback query
        if request.update.callback_query:
            try:
                # Answer the callback query first
                await request.update.callback_query.answer()
                # Delete the message immediately
                await request.update.callback_query.message.delete()
            except Exception as e:
                self.logger.error(f"Failed to delete broadcast menu message: {e}")

        response = HandlerResponse(
            message="",  # Empty message, conversation ends cleanly
            end_conversation=True
            # NO delay, NO confirmation message
        )
        return await self.send_response(response, request)
    
    async def handle(self, request: HandlerRequest) -> HandlerResponse:
        """Implementation of abstract handle method from BaseHandler."""
        return await self.show_main_menu(request)
    
    def get_conversation_handler(self) -> ConversationHandler:
        """Get the conversation handler."""
        return ConversationHandler(
            entry_points=[CommandHandler("message", self.start_broadcast)],
            states={
                BROADCAST_MENU: [
                    CallbackQueryHandler(self.handle_menu_selection),
                ],
                BROADCAST_TEXT_CONTENT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_content),
                    CallbackQueryHandler(self.handle_menu_selection),
                ],
                BROADCAST_POLL_QUESTION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_poll_question),
                    CallbackQueryHandler(self.handle_menu_selection),
                ],
                BROADCAST_POLL_OPTIONS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_poll_options),
                    CallbackQueryHandler(self.handle_menu_selection),
                ],
                BROADCAST_DICE_EMOJI: [
                    CallbackQueryHandler(self.handle_dice_selection),
                ],
                BROADCAST_CONFIRM: [
                    CallbackQueryHandler(self.handle_confirmation),
                ],
            },
            fallbacks=[
                CommandHandler("cancel", lambda update, context: self.safe_handle(self._handle_cancel, update, context)),
                CallbackQueryHandler(self.handle_menu_selection, pattern="^(cancel|back_to_menu)$"),
            ],
            name="broadcast_conversation",
            persistent=False
        )


def get_modern_broadcast_handler() -> ConversationHandler:
    """Get the modern broadcast conversation handler."""
    handler = BroadcastHandler()
    return handler.get_conversation_handler()