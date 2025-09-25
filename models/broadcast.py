"""
Broadcast messaging models and DTOs for type-safe broadcast operations.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class BroadcastType(Enum):
    """Types of broadcast messages."""
    TEXT = "text"
    HTML = "html"
    MARKDOWN = "markdown"
    POLL = "poll"
    DICE = "dice"


class BroadcastStatus(Enum):
    """Status of broadcast messages."""
    PENDING = "pending"
    SENDING = "sending"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class BroadcastMessage:
    """Broadcast message entity."""
    id: int
    sender_chat_id: int
    message_type: BroadcastType
    message_content: str
    poll_question: Optional[str] = None
    poll_options: Optional[List[str]] = None
    dice_emoji: Optional[str] = None
    total_recipients: int = 0
    successful_deliveries: int = 0
    failed_deliveries: int = 0
    created_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: BroadcastStatus = BroadcastStatus.PENDING


@dataclass
class CreateTextBroadcastRequest:
    """Request to create a text broadcast message."""
    sender_chat_id: int
    content: str
    message_type: BroadcastType
    
    def __post_init__(self):
        if self.message_type not in [BroadcastType.TEXT, BroadcastType.HTML, BroadcastType.MARKDOWN]:
            raise ValueError("Invalid message type for text broadcast")


@dataclass
class CreatePollBroadcastRequest:
    """Request to create a poll broadcast message."""
    sender_chat_id: int
    question: str
    options: List[str]
    
    def __post_init__(self):
        if not self.question.strip():
            raise ValueError("Poll question cannot be empty")
        if len(self.options) < 2:
            raise ValueError("Poll must have at least 2 options")
        if len(self.options) > 10:
            raise ValueError("Poll cannot have more than 10 options")
        for option in self.options:
            if not option.strip():
                raise ValueError("Poll options cannot be empty")


@dataclass
class CreateDiceBroadcastRequest:
    """Request to create a dice broadcast message."""
    sender_chat_id: int
    emoji: str = "🎲"
    
    def __post_init__(self):
        valid_emojis = ["🎲", "🎯", "🎳", "🏀", "⚽", "🎰"]
        if self.emoji not in valid_emojis:
            raise ValueError(f"Invalid dice emoji. Must be one of: {', '.join(valid_emojis)}")


@dataclass
class BroadcastDeliveryResult:
    """Result of broadcast delivery to a specific user."""
    chat_id: int
    username: Optional[str]
    success: bool
    error_message: Optional[str] = None


@dataclass
class BroadcastSendResult:
    """Result of sending a broadcast message."""
    broadcast_id: int
    total_recipients: int
    successful_deliveries: int
    failed_deliveries: int
    delivery_results: List[BroadcastDeliveryResult] = field(default_factory=list)
    completed: bool = False
    error_message: Optional[str] = None


@dataclass
class BroadcastStats:
    """Statistics for broadcast messages."""
    total_broadcasts: int
    pending_broadcasts: int
    completed_broadcasts: int
    failed_broadcasts: int
    total_recipients_reached: int
    average_delivery_rate: float


class BroadcastMessageType:
    """Utility class for message type validation."""
    
    @staticmethod
    def validate_content(message_type: BroadcastType, content: str) -> bool:
        """Validate content for specific message type."""
        if not content.strip():
            return False
            
        if message_type == BroadcastType.HTML:
            # Basic HTML validation - ensure no script tags for security
            forbidden_tags = ['<script', '<iframe', '<object', '<embed']
            content_lower = content.lower()
            for tag in forbidden_tags:
                if tag in content_lower:
                    return False
                    
        return True
    
    @staticmethod
    def sanitize_content(content: str) -> str:
        """Sanitize content for safe transmission."""
        # Remove potentially dangerous characters
        dangerous_chars = ['<script>', '</script>', '<iframe>', '</iframe>']
        sanitized = content
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
            
        return sanitized.strip()
    
    @staticmethod
    def format_for_display(message_type: BroadcastType) -> str:
        """Format message type for user display."""
        type_display = {
            BroadcastType.TEXT: "Texto",
            BroadcastType.HTML: "HTML",
            BroadcastType.MARKDOWN: "Markdown",
            BroadcastType.POLL: "Enquete",
            BroadcastType.DICE: "Dado"
        }
        return type_display.get(message_type, "Desconhecido")


class BroadcastValidator:
    """Validation utilities for broadcast messages."""
    
    @staticmethod
    def validate_text_broadcast(request: CreateTextBroadcastRequest) -> List[str]:
        """Validate text broadcast request."""
        errors = []
        
        if not request.content.strip():
            errors.append("Conteúdo da mensagem não pode estar vazio")
            
        if len(request.content) > 4096:
            errors.append("Conteúdo da mensagem não pode exceder 4096 caracteres")
            
        if not BroadcastMessageType.validate_content(request.message_type, request.content):
            errors.append("Conteúdo da mensagem contém elementos não permitidos")
            
        return errors
    
    @staticmethod
    def validate_poll_broadcast(request: CreatePollBroadcastRequest) -> List[str]:
        """Validate poll broadcast request."""
        errors = []
        
        if not request.question.strip():
            errors.append("Pergunta da enquete não pode estar vazia")
            
        if len(request.question) > 300:
            errors.append("Pergunta da enquete não pode exceder 300 caracteres")
            
        if len(request.options) < 2:
            errors.append("Enquete deve ter pelo menos 2 opções")
            
        if len(request.options) > 10:
            errors.append("Enquete não pode ter mais que 10 opções")
            
        for i, option in enumerate(request.options):
            if not option.strip():
                errors.append(f"Opção {i+1} não pode estar vazia")
            if len(option) > 100:
                errors.append(f"Opção {i+1} não pode exceder 100 caracteres")
                
        return errors
    
    @staticmethod
    def validate_dice_broadcast(request: CreateDiceBroadcastRequest) -> List[str]:
        """Validate dice broadcast request."""
        errors = []
        
        valid_emojis = ["🎲", "🎯", "🎳", "🏀", "⚽", "🎰"]
        if request.emoji not in valid_emojis:
            errors.append(f"Emoji do dado deve ser um dos seguintes: {', '.join(valid_emojis)}")
            
        return errors