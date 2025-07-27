"""
Browser session data models.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class BrowserSession(BaseModel):
    """Represents a browser session for testing extensions."""
    id: str = Field(..., description="Unique session ID")
    extension_id: str = Field(..., description="Extension being tested")
    status: str = Field(default="initializing", description="Session status")
    url: Optional[str] = Field(None, description="Current browser URL")
    console_logs: list = Field(default_factory=list, description="Console logs")
    errors: list = Field(default_factory=list, description="Error logs")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata") 