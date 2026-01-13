from typing import List, Dict, Optional
from datetime import datetime
import asyncio
import uuid
from models import (
    ConversationState, 
    ConversationMode, 
    Participant, 
    Message, 
    MessageType
)
from services.ai_service import AIService

class ConversationManager:
    """Менеджер для управления беседой между AI участниками"""
    
    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service
        self.active_conversations: Dict[str, ConversationState] = {}
    
    def create_conversation(
        self,
        participants: List[Participant],
        mode: ConversationMode
    ) -> ConversationState:
        """Создать новую беседу"""
        conversation_id = str(uuid.uuid4())
        
        # Initialize AI models for all participants
        for participant in participants:
            self.ai_service.initialize_model(participant)
        
        conversation = ConversationState(
            id=conversation_id,
            mode=mode,
            participants=participants,
            messages=[],
            round_number=0,
            is_active=True
        )
        
        self.active_conversations[conversation_id] = conversation
        return conversation
    
    async def process_parallel_round(
        self,
        conversation_id: str,
        user_message: str
    ) -> Dict[str, str]:
        """Обработать раунд в параллельном режиме"""
        conversation = self.active_conversations.get(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        # Add user message
        user_msg = Message(
            id=str(uuid.uuid4()),
            type=MessageType.USER_INPUT,
            content=user_message,
            sender="user"
        )
        conversation.messages.append(user_msg)
        
        # Send to all participants in parallel
        responses = await self.ai_service.send_parallel_messages(
            conversation.participants,
            user_message
        )
        
        # Store responses
        for participant_id, response in responses.items():
            participant = next(
                p for p in conversation.participants if p.id == participant_id
            )
            msg = Message(
                id=str(uuid.uuid4()),
                type=MessageType.AI_RESPONSE,
                content=response,
                sender=participant.name
            )
            conversation.messages.append(msg)
            participant.messages_count += 1
        
        conversation.round_number += 1
        return responses
    
    async def process_sequential_round(
        self,
        conversation_id: str,
        user_message: str
    ) -> Dict[str, str]:
        """Обработать раунд в последовательном режиме"""
        conversation = self.active_conversations.get(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        # Add user message
        user_msg = Message(
            id=str(uuid.uuid4()),
            type=MessageType.USER_INPUT,
            content=user_message,
            sender="user"
        )
        conversation.messages.append(user_msg)
        
        responses = {}
        current_context = user_message
        
        # Process each participant sequentially
        for participant in [p for p in conversation.participants if p.active]:
            response = await self.ai_service.send_message(
                participant.id,
                current_context,
                stream=True
            )
            
            msg = Message(
                id=str(uuid.uuid4()),
                type=MessageType.AI_RESPONSE,
                content=response,
                sender=participant.name
            )
            conversation.messages.append(msg)
            participant.messages_count += 1
            
            responses[participant.id] = response
            # Add previous response to context for next participant
            current_context = f"{current_context}\n\n{participant.name}: {response}"
        
        conversation.round_number += 1
        return responses
    
    def get_conversation(self, conversation_id: str) -> Optional[ConversationState]:
        """Получить беседу по ID"""
        return self.active_conversations.get(conversation_id)
    
    def end_conversation(self, conversation_id: str) -> None:
        """Завершить беседу"""
        conversation = self.active_conversations.get(conversation_id)
        if conversation:
            conversation.is_active = False
