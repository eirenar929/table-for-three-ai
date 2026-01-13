from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from typing import List, Dict
import json
from models import (
    Conversation Mode,
    Participant,
    ParticipantRole,
    ConversationState
)
from services import AIService, ConversationManager

router = APIRouter()

# Initialize services
ai_service = AIService()
conversation_manager = ConversationManager(ai_service)

# Active WebSocket connections
active_connections: Dict[str, List[WebSocket]] = {}

@router.post("/conversations/create")
async def create_conversation(
    participants: List[Dict],
    mode: str
) -> JSONResponse:
    """Создать новую беседу"""
    try:
        # Create participant objects
        participant_objects = [
            Participant(**p) for p in participants
        ]
        
        # Create conversation
        conversation = conversation_manager.create_conversation(
            participant_objects,
            ConversationMode(mode)
        )
        
        return JSONResponse({
            "conversation_id": conversation.id,
            "mode": conversation.mode,
            "participants": [
                {"id": p.id, "name": p.name, "role": p.role}
                for p in conversation.participants
            ]
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/conversations/{conversation_id}/message")
async def send_message(
    conversation_id: str,
    message: str
) -> JSONResponse:
    """Отправить сообщение в беседу"""
    try:
        conversation = conversation_manager.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Process based on mode
        if conversation.mode == ConversationMode.PARALLEL:
            responses = await conversation_manager.process_parallel_round(
                conversation_id,
                message
            )
        else:
            responses = await conversation_manager.process_sequential_round(
                conversation_id,
                message
            )
        
        return JSONResponse({
            "conversation_id": conversation_id,
            "responses": responses,
            "round": conversation.round_number
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str) -> JSONResponse:
    """Получить информацию о беседе"""
    conversation = conversation_manager.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return JSONResponse(conversation.dict())

@router.websocket("/ws/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: str):
    """Обработчик WebSocket для real-time обновлений"""
    await websocket.accept()
    
    # Add connection to active connections
    if conversation_id not in active_connections:
        active_connections[conversation_id] = []
    active_connections[conversation_id].append(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Process message
            conversation = conversation_manager.get_conversation(conversation_id)
            if conversation:
                if conversation.mode == ConversationMode.PARALLEL:
                    responses = await conversation_manager.process_parallel_round(
                        conversation_id,
                        message_data["message"]
                    )
                else:
                    responses = await conversation_manager.process_sequential_round(
                        conversation_id,
                        message_data["message"]
                    )
                
                # Send responses to all connected clients
                for conn in active_connections[conversation_id]:
                    await conn.send_json({
                        "type": "responses",
                        "data": responses,
                        "round": conversation.round_number
                    })
    
    except WebSocketDisconnect:
        active_connections[conversation_id].remove(websocket)
        if not active_connections[conversation_id]:
            del active_connections[conversation_id]
