"""
Function calling implementation for the chat agent using Pydantic AI.
"""

from typing import Dict, List, Any
from pydantic import BaseModel, Field

from ..models.chat import ChatMessage, MessageRole


class BuildExtensionRequest(BaseModel):
    """Request model for building a new Chrome extension."""
    requirements: str = Field(..., description="Detailed description of what the user wants the extension to do")
    features: List[str] = Field(default=[], description="List of specific features the extension should have")
    target_websites: List[str] = Field(default=[], description="List of websites the extension should work on")


class FixExtensionRequest(BaseModel):
    """Request model for fixing issues in an existing Chrome extension."""
    issues: str = Field(..., description="Description of the issues or bugs to fix")
    error_logs: str = Field(default="", description="Any error logs or debug information available")
    current_behavior: str = Field(default="", description="Description of what the extension is currently doing vs what it should do")


class ImproveExtensionRequest(BaseModel):
    """Request model for improving an existing Chrome extension."""
    improvements: str = Field(..., description="Description of improvements or new features to add")
    current_features: str = Field(default="", description="Description of current extension features")
    performance_issues: str = Field(default="", description="Any performance issues to address")


class AnswerUserQuestionRequest(BaseModel):
    """Request model for answering general user questions."""
    question: str = Field(..., description="The user's question to answer")
    topic: str = Field(default="chrome extension development", description="The topic area (e.g., 'chrome extension development', 'manifest v3', 'permissions')")


class FunctionCaller:
    """Handles function calling with Pydantic AI."""
    
    def __init__(self):
        """Initialize the function caller."""
        # Function definitions will be handled by Pydantic AI's built-in function calling
        pass
    
    def create_conversation_context(self, messages: List[ChatMessage]) -> str:
        """Create conversation context for the model."""
        # Get the last few messages for context
        recent_messages = messages[-5:] if len(messages) >= 5 else messages
        
        conversation = "\n".join([
            f"{'User' if msg.role == MessageRole.USER else 'Assistant'}: {msg.content}"
            for msg in recent_messages
        ])
        
        return f"""
You are a helpful Chrome extension development assistant. Based on the conversation below, determine which function to call or provide a helpful response.

Available functions:
- build_extension: Create a new Chrome extension from scratch
- fix_extension: Fix issues or bugs in an existing extension  
- improve_extension: Enhance an existing extension with new features
- answer_user_question: Answer general questions about Chrome extensions

Important Notes:
- Custom icons (icon16.png, icon48.png, icon128.png) will be automatically copied from the template
- Do NOT generate any PNG image files - focus on functionality and code
- The extension will use the existing robot icon design

Conversation:
{conversation}

If the user wants to create a new extension, call build_extension.
If the user reports issues or bugs, call fix_extension.
If the user wants to add features or improvements, call improve_extension.
If the user asks general questions, call answer_user_question.
If the user is just chatting or asking for clarification, provide a helpful response without calling any function.
""" 