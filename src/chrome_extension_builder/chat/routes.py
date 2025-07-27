"""
Chat API routes for Chrome Extension Builder.
"""

import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from ..models.chat import ChatMessage, ChatSession, MessageRole

router = APIRouter()

# In-memory storage (replace with database in production)
chat_sessions: dict = {}
active_connections: dict = {}


class ChatRequest(BaseModel):
    """Request model for chat messages."""
    content: str
    session_id: str


class ChatResponse(BaseModel):
    """Response model for chat messages."""
    message: ChatMessage
    session: ChatSession


@router.post("/sessions", response_model=ChatSession)
async def create_session(title: str = "New Extension Project"):
    """Create a new chat session."""
    session_id = str(uuid.uuid4())
    session = ChatSession(
        id=session_id,
        title=title,
        messages=[]
    )
    chat_sessions[session_id] = session
    return session


@router.get("/sessions/{session_id}", response_model=ChatSession)
async def get_session(session_id: str):
    """Get a chat session by ID."""
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return chat_sessions[session_id]


@router.get("/sessions", response_model=List[ChatSession])
async def list_sessions():
    """List all chat sessions."""
    return list(chat_sessions.values())


@router.post("/messages", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """Send a message in a chat session."""
    if request.session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = chat_sessions[request.session_id]
    
    # Create user message
    user_message = ChatMessage(
        id=str(uuid.uuid4()),
        role=MessageRole.USER,
        content=request.content,
        session_id=request.session_id
    )
    
    session.messages.append(user_message)
    session.updated_at = datetime.utcnow()
    
    # TODO: Process with AI agent to generate response
    # For now, create a simple response
    assistant_message = ChatMessage(
        id=str(uuid.uuid4()),
        role=MessageRole.ASSISTANT,
        content="I understand you want to create a Chrome extension. Let me help you with that!",
        session_id=request.session_id
    )
    
    session.messages.append(assistant_message)
    session.updated_at = datetime.utcnow()
    
    return ChatResponse(message=assistant_message, session=session)


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat."""
    await websocket.accept()
    
    if session_id not in active_connections:
        active_connections[session_id] = []
    active_connections[session_id].append(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            # Handle real-time messaging
            # TODO: Implement real-time message handling
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        active_connections[session_id].remove(websocket) 