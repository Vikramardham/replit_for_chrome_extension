"""
Chat routes for Chrome Extension Builder.
"""

import uuid
from datetime import datetime
from typing import List, Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from ..models.chat import ChatSession, ChatMessage, MessageRole
from ..chat.agent import ChatAgent

router = APIRouter()

# In-memory storage for chat sessions
chat_sessions: Dict[str, ChatSession] = {}

# Import extensions dictionary from api routes
from ..api.routes import extensions

# Global chat agent instance
_chat_agent = None


class MessageRequest(BaseModel):
    """Request model for sending a message."""
    message: str


def get_chat_agent():
    """Get or create the ChatAgent instance."""
    global _chat_agent
    if _chat_agent is None:
        _chat_agent = ChatAgent()
    return _chat_agent


@router.get("/", response_class=HTMLResponse)
async def get_chat_interface():
    """Serve the chat interface."""
    with open("src/chrome_extension_builder/templates/index.html", "r") as f:
        return HTMLResponse(content=f.read())


@router.post("/sessions", response_model=ChatSession)
async def create_chat_session():
    """Create a new chat session."""
    session_id = str(uuid.uuid4())
    session = ChatSession(
        id=session_id,
        messages=[],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    chat_sessions[session_id] = session
    return session


@router.get("/sessions/{session_id}", response_model=ChatSession)
async def get_chat_session(session_id: str):
    """Get a chat session by ID."""
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return chat_sessions[session_id]


@router.post("/sessions/{session_id}/messages")
async def send_message(session_id: str, request: MessageRequest):
    """Send a message in a chat session."""
    print(f"📨 Received message request for session: {session_id}")
    
    if session_id not in chat_sessions:
        print(f"❌ Session not found: {session_id}")
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    session = chat_sessions[session_id]
    print(f"✅ Session found, processing message...")
    
    # Create a proper ChatMessage object
    user_message = ChatMessage(
        role=MessageRole.USER,
        content=request.message,
        session_id=session_id
    )
    
    # Process the message using the ChatAgent
    print(f"🤖 Sending to ChatAgent for processing...")
    chat_agent = get_chat_agent()
    result = await chat_agent.process_message(session.messages, request.message, session_id)
    
    # Add the user message to the session
    session.messages.append(user_message)
    
    # Update session
    session.updated_at = datetime.utcnow()
    
    print(f"✅ Message processed successfully. Action: {result.get('action', 'unknown')}")
    
    # Store generated extension in extensions dictionary
    extension_dict = None
    if result.get("extension"):
        extension = result.get("extension")
        # Store the extension in the global extensions dictionary
        extensions[extension.id] = extension
        print(f"💾 Stored extension '{extension.name}' with ID: {extension.id}")
        
        extension_dict = {
            "id": extension.id,
            "name": extension.name,
            "description": extension.description,
            "version": extension.manifest.version if extension.manifest else "1.0.0",
            "files": extension.files,
            "created_at": extension.created_at.isoformat() if extension.created_at else None,
            "updated_at": extension.updated_at.isoformat() if extension.updated_at else None
        }
    
    return {
        "session_id": session_id,
        "response": result["response"],
        "action": result["action"],
        "extension": extension_dict
    }


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat."""
    print(f"🔌 WebSocket connection request for session: {session_id}")
    await websocket.accept()
    print(f"✅ WebSocket connection established for session: {session_id}")
    
    if session_id not in chat_sessions:
        print(f"❌ Session not found for WebSocket: {session_id}")
        await websocket.close(code=4004, reason="Session not found")
        return
    
    session = chat_sessions[session_id]
    print(f"✅ Session found for WebSocket, ready for messages")
    
    try:
        while True:
            # Receive message from client
            print(f"📥 Waiting for WebSocket message from session: {session_id}")
            data = await websocket.receive_text()
            print(f"📨 Received WebSocket message: {data[:100]}{'...' if len(data) > 100 else ''}")
            
            # Create a proper ChatMessage object
            user_message = ChatMessage(
                role=MessageRole.USER,
                content=data,
                session_id=session_id
            )
            
            # Process the message using the ChatAgent
            print(f"🤖 Processing WebSocket message with ChatAgent...")
            chat_agent = get_chat_agent()
            # Set WebSocket for streaming
            chat_agent.websocket = websocket
            result = await chat_agent.process_message(session.messages, data, session_id)
            
            # Add the user message to the session
            session.messages.append(user_message)
            
            # Update session
            session.updated_at = datetime.utcnow()
            
            # Store generated extension in extensions dictionary
            extension_dict = None
            if result.get("extension"):
                extension = result.get("extension")
                # Store the extension in the global extensions dictionary
                extensions[extension.id] = extension
                print(f"💾 Stored extension '{extension.name}' with ID: {extension.id}")
                
                extension_dict = {
                    "id": extension.id,
                    "name": extension.name,
                    "description": extension.description,
                    "version": extension.manifest.version if extension.manifest else "1.0.0",
                    "files": extension.files,
                    "created_at": extension.created_at.isoformat() if extension.created_at else None,
                    "updated_at": extension.updated_at.isoformat() if extension.updated_at else None
                }
            
            # Send response back to client
            print(f"📤 Sending WebSocket response...")
            await websocket.send_json({
                "type": "message",
                "content": result["response"],
                "action": result["action"],
                "extension": extension_dict
            })
            print(f"✅ WebSocket response sent successfully")
            
    except WebSocketDisconnect:
        print(f"🔌 WebSocket disconnected for session {session_id}")
    except Exception as e:
        print(f"❌ WebSocket error for session {session_id}: {e}")
        await websocket.close() 