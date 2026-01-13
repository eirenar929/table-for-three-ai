import google.generativeai as genai
from typing import List, Optional, Dict, Any
import asyncio
import os
from models import Message, Participant, MessageType
from utils.buffer import ResponseBuffer

class AIService:
    """Сервис для взаимодействия с Google Generative AI"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize AI service with API key"""
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not provided")
        genai.configure(api_key=self.api_key)
        self.models = {}
        self.buffer = ResponseBuffer()
    
    def initialize_model(self, participant: Participant) -> None:
        """Инициализировать модель для участника"""
        generation_config = {
            "temperature": 1.0,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
        }
        
        model = genai.GenerativeModel(
            model_name=participant.model_name,
            generation_config=generation_config,
            system_instruction=participant.system_prompt
        )
        
        self.models[participant.id] = model.start_chat(history=[])
    
    async def send_message(
        self, 
        participant_id: str, 
        message: str,
        stream: bool = True
    ) -> str:
        """Отправить сообщение и получить ответ"""
        if participant_id not in self.models:
            raise ValueError(f"Model for participant {participant_id} not initialized")
        
        chat = self.models[participant_id]
        
        if stream:
            response = await chat.send_message_async(message, stream=True)
            full_response = ""
            async for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    await self.buffer.add_chunk(participant_id, chunk.text)
            return full_response
        else:
            response = await chat.send_message_async(message)
            return response.text
    
    async def send_parallel_messages(
        self,
        participants: List[Participant],
        message: str
    ) -> Dict[str, str]:
        """Отправить сообщение нескольким участникам параллельно"""
        tasks = [
            self.send_message(p.id, message, stream=True)
            for p in participants if p.active
        ]
        results = await asyncio.gather(*tasks)
        
        return {
            p.id: result 
            for p, result in zip([p for p in participants if p.active], results)
        }
    
    async def get_buffered_response(self, participant_id: str) -> str:
        """Получить буферизованный ответ"""
        return await self.buffer.get_response(participant_id)
    
    def clear_history(self, participant_id: str) -> None:
        """Очистить историю чата"""
        if participant_id in self.models:
            chat = self.models[participant_id]
            chat.history.clear()
