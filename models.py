from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

class ConversationMode(str, Enum):
    """Режимы проведения беседы"""
    PARALLEL = "parallel"  # Параллельный режим
    SEQUENTIAL = "sequential"  # Последовательный режим

class ParticipantRole(str, Enum):
    """Роли участников в эксперименте"""
    DETECTIVE = "detective"  # Детектив
    INNOCENT = "innocent"  # Невиновный
    MAFIA = "mafia"  # Мафия

class MessageType(str, Enum):
    """Типы сообщений в системе"""
    USER_INPUT = "user_input"
    AI_RESPONSE = "ai_response"
    SYSTEM_MESSAGE = "system_message"
    MODERATOR_ACTION = "moderator_action"

class Message(BaseModel):
    """Модель сообщения"""
    id: str
    type: MessageType
    content: str
    sender: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None

class Participant(BaseModel):
    """Модель участника беседы"""
    id: str
    name: str
    role: ParticipantRole
    model_name: str  # Название AI модели
    system_prompt: str
    active: bool = True
    messages_count: int = 0

class ConversationState(BaseModel):
    """Состояние беседы"""
    id: str
    mode: ConversationMode
    participants: List[Participant]
    messages: List[Message] = []
    current_speaker: Optional[str] = None
    round_number: int = 0
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None

class ModerationResult(BaseModel):
    """Результат модерации контента"""
    is_safe: bool
    confidence: float
    categories: List[str] = []
    explanation: Optional[str] = None

class IdentityProtectionConfig(BaseModel):
    """Конфигурация защиты идентичности"""
    enable_name_masking: bool = True
    enable_location_masking: bool = True
    enable_sensitive_data_filtering: bool = True
    custom_patterns: Optional[List[str]] = None
