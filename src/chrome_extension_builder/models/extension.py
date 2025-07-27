"""
Extension-related data models.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ExtensionManifest(BaseModel):
    """Chrome extension manifest model."""
    manifest_version: int = Field(default=3, description="Manifest version")
    name: str = Field(..., description="Extension name")
    version: str = Field(default="1.0.0", description="Extension version")
    description: str = Field(..., description="Extension description")
    permissions: List[str] = Field(default_factory=list, description="Required permissions")
    host_permissions: List[str] = Field(default_factory=list, description="Host permissions")
    action: Optional[Dict[str, Any]] = Field(None, description="Browser action")
    background: Optional[Dict[str, Any]] = Field(None, description="Background script")
    content_scripts: List[Dict[str, Any]] = Field(default_factory=list, description="Content scripts")
    web_accessible_resources: List[Dict[str, Any]] = Field(default_factory=list, description="Web accessible resources")


class Extension(BaseModel):
    """Represents a Chrome extension."""
    id: str = Field(..., description="Unique extension ID")
    name: str = Field(..., description="Extension name")
    description: str = Field(..., description="Extension description")
    manifest: ExtensionManifest = Field(..., description="Extension manifest")
    files: Dict[str, str] = Field(default_factory=dict, description="Extension files")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    session_id: Optional[str] = Field(None, description="Associated chat session ID")
    status: str = Field(default="draft", description="Extension status") 