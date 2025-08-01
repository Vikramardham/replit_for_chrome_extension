"""
Structured output models for function responses using Pydantic AI.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class ExtensionResponse(BaseModel):
    """Structured response for extension operations."""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Human-readable response message")
    extension_name: Optional[str] = Field(None, description="Name of the extension")
    extension_description: Optional[str] = Field(None, description="Description of the extension")
    files_created: Optional[List[str]] = Field(None, description="List of files created or modified")
    action_type: str = Field(..., description="Type of action performed (build, fix, improve)")


class QuestionResponse(BaseModel):
    """Structured response for question answering."""
    answer: str = Field(..., description="The answer to the user's question")
    topic: str = Field(..., description="The topic area of the question")
    helpful_links: Optional[List[str]] = Field(None, description="Helpful links or resources")
    next_steps: Optional[List[str]] = Field(None, description="Suggested next steps")


class DebugAnalysisResponse(BaseModel):
    """Structured response for debug analysis."""
    issues_found: List[str] = Field(..., description="List of issues found in the logs")
    recommendations: List[str] = Field(..., description="Specific recommendations for fixes")
    code_examples: Optional[List[str]] = Field(None, description="Code examples for fixes")
    severity_level: str = Field(..., description="Overall severity level (low, medium, high, critical)")


class ConversationResponse(BaseModel):
    """Structured response for general conversation."""
    response: str = Field(..., description="The conversational response")
    suggested_actions: Optional[List[str]] = Field(None, description="Suggested next actions")
    needs_clarification: bool = Field(False, description="Whether the response needs clarification") 