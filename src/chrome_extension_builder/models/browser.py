"""
Browser-related data models.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field
import uuid


class EventType(str, Enum):
    """Types of browser events."""
    CLICK = "click"
    KEYBOARD = "keyboard"
    NAVIGATION = "navigation"
    CONSOLE_LOG = "console_log"
    CONSOLE_ERROR = "console_error"
    NETWORK_ERROR = "network_error"
    EXTENSION_ERROR = "extension_error"
    DOM_CHANGE = "dom_change"
    SCROLL = "scroll"
    RESIZE = "resize"


class BrowserEvent(BaseModel):
    """Represents a browser event."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: EventType = Field(..., description="Event type")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    url: Optional[str] = Field(None, description="Current page URL")
    element: Optional[str] = Field(None, description="Element that triggered the event")
    data: Dict[str, Any] = Field(default_factory=dict, description="Event-specific data")
    session_id: str = Field(..., description="Browser session ID")
    extension_id: Optional[str] = Field(None, description="Extension ID if relevant")


class BrowserError(BaseModel):
    """Represents a browser error."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    stack_trace: Optional[str] = Field(None, description="Stack trace")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    url: Optional[str] = Field(None, description="Page URL where error occurred")
    session_id: str = Field(..., description="Browser session ID")
    extension_id: Optional[str] = Field(None, description="Extension ID if relevant")
    severity: str = Field(default="error", description="Error severity")


class BrowserSession(BaseModel):
    """Represents a browser session."""
    id: str = Field(..., description="Unique session ID")
    extension_id: Optional[str] = Field(None, description="Extension being tested")
    url: Optional[str] = Field(None, description="Current page URL")
    status: str = Field(default="active", description="Session status")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    events: List[BrowserEvent] = Field(default_factory=list, description="Session events")
    errors: List[BrowserError] = Field(default_factory=list, description="Session errors")
    console_logs: List[str] = Field(default_factory=list, description="Console logs")
    is_debug_mode: bool = Field(default=False, description="Whether debug logging is enabled")


class DebugSession(BaseModel):
    """Represents a debugging session with comprehensive logging."""
    id: str = Field(..., description="Unique debug session ID")
    browser_session_id: str = Field(..., description="Associated browser session")
    extension_id: str = Field(..., description="Extension being debugged")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    log_file_path: Optional[str] = Field(None, description="Path to log file")
    events_count: int = Field(default=0, description="Number of events logged")
    errors_count: int = Field(default=0, description="Number of errors logged")
    is_active: bool = Field(default=True, description="Whether session is active")


class LogAnalysis(BaseModel):
    """Represents analysis of browser logs for AI consumption."""
    session_id: str = Field(..., description="Session ID")
    summary: str = Field(..., description="Summary of logged events")
    errors: List[BrowserError] = Field(default_factory=list, description="Errors found")
    user_actions: List[BrowserEvent] = Field(default_factory=list, description="User actions")
    console_output: List[str] = Field(default_factory=list, description="Console output")
    recommendations: List[str] = Field(default_factory=list, description="AI recommendations")
    timestamp: datetime = Field(default_factory=datetime.utcnow) 