"""
API routes for Chrome Extension Builder.
"""

import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from ..models.extension import Extension, ExtensionManifest
from ..models.browser import BrowserSession, LogAnalysis

router = APIRouter()

# In-memory storage (replace with database in production)
extensions: dict = {}
browser_sessions: dict = {}


class ExtensionCreateRequest(BaseModel):
    """Request model for creating extensions."""
    name: str
    description: str
    session_id: str


class ExtensionUpdateRequest(BaseModel):
    """Request model for updating extensions."""
    name: Optional[str] = None
    description: Optional[str] = None
    manifest: Optional[ExtensionManifest] = None
    files: Optional[Dict[str, str]] = None


@router.post("/extensions", response_model=Extension)
async def create_extension(request: ExtensionCreateRequest):
    """Create a new extension."""
    extension_id = str(uuid.uuid4())
    
    manifest = ExtensionManifest(
        name=request.name,
        description=request.description
    )
    
    extension = Extension(
        id=extension_id,
        name=request.name,
        description=request.description,
        manifest=manifest,
        session_id=request.session_id
    )
    
    extensions[extension_id] = extension
    return extension


@router.get("/extensions/{extension_id}", response_model=Extension)
async def get_extension(extension_id: str):
    """Get an extension by ID."""
    if extension_id not in extensions:
        raise HTTPException(status_code=404, detail="Extension not found")
    return extensions[extension_id]


@router.get("/extensions", response_model=List[Extension])
async def list_extensions():
    """List all extensions."""
    return list(extensions.values())


@router.put("/extensions/{extension_id}", response_model=Extension)
async def update_extension(extension_id: str, request: ExtensionUpdateRequest):
    """Update an extension."""
    if extension_id not in extensions:
        raise HTTPException(status_code=404, detail="Extension not found")
    
    extension = extensions[extension_id]
    
    if request.name:
        extension.name = request.name
    if request.description:
        extension.description = request.description
    if request.manifest:
        extension.manifest = request.manifest
    if request.files:
        extension.files.update(request.files)
    
    extension.updated_at = datetime.utcnow()
    return extension


@router.post("/extensions/{extension_id}/files")
async def upload_extension_file(extension_id: str, file: UploadFile = File(...)):
    """Upload a file for an extension."""
    if extension_id not in extensions:
        raise HTTPException(status_code=404, detail="Extension not found")
    
    extension = extensions[extension_id]
    content = await file.read()
    extension.files[file.filename] = content.decode('utf-8')
    extension.updated_at = datetime.utcnow()
    
    return {"message": f"File {file.filename} uploaded successfully"}


@router.post("/browser/sessions", response_model=BrowserSession)
async def create_browser_session(extension_id: str):
    """Create a new browser session for testing an extension."""
    if extension_id not in extensions:
        raise HTTPException(status_code=404, detail="Extension not found")
    
    session_id = str(uuid.uuid4())
    session = BrowserSession(
        id=session_id,
        extension_id=extension_id
    )
    
    browser_sessions[session_id] = session
    return session


@router.get("/browser/sessions/{session_id}", response_model=BrowserSession)
async def get_browser_session(session_id: str):
    """Get a browser session by ID."""
    if session_id not in browser_sessions:
        raise HTTPException(status_code=404, detail="Browser session not found")
    return browser_sessions[session_id]


@router.post("/browser/sessions/{session_id}/load")
async def load_extension_in_browser(session_id: str):
    """Load an extension in the browser for testing."""
    if session_id not in browser_sessions:
        raise HTTPException(status_code=404, detail="Browser session not found")
    
    session = browser_sessions[session_id]
    extension = extensions[session.extension_id]
    
    # TODO: Implement actual browser automation
    session.status = "loaded"
    session.updated_at = datetime.utcnow()
    
    return {"message": f"Extension {extension.name} loaded in browser"}


# Global browser manager instance to keep browser alive
_browser_manager = None

@router.post("/browser/load-extension-manual")
async def load_extension_manual(extension_id: str, enable_debug: bool = True):
    """Manually load an extension - start browser with extension loaded."""
    global _browser_manager
    
    try:
        from ..browser.manager import BrowserManager
        
        # Get the extension
        if extension_id not in extensions:
            raise HTTPException(status_code=404, detail="Extension not found")
        
        extension = extensions[extension_id]
        
        # Close existing browser manager if it exists
        if _browser_manager:
            await _browser_manager.stop()
            _browser_manager = None
        
        # Create new browser manager and start with extension loaded
        _browser_manager = BrowserManager()
        await _browser_manager.start_with_extension(extension, enable_debug=enable_debug)
        
        debug_info = ""
        if enable_debug and _browser_manager.current_debug_session:
            debug_info = f" Debug session started: {_browser_manager.current_debug_session.id}"
        
        return {
            "status": "success",
            "message": f"Browser started with extension '{extension.name}' loaded!{debug_info}",
            "extension_dir": f"extensions/{extension.id}",
            "extension_id": _browser_manager.extension_id,
            "debug_session_id": _browser_manager.current_debug_session.id if _browser_manager.current_debug_session else None,
            "instructions": [
                "1. The extension is already loaded in the browser",
                "2. You can test it by navigating to any website",
                "3. Check the extension icon in the browser toolbar",
                "4. Click the extension icon to test the popup",
                "5. All events and errors are being logged for debugging"
            ]
        }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting browser with extension: {str(e)}")

@router.post("/browser/load-dummy-extension")
async def load_dummy_extension():
    """Load the dummy extension for testing."""
    global _browser_manager
    
    try:
        from ..browser.manager import BrowserManager
        
        # Close existing browser manager if it exists
        if _browser_manager:
            await _browser_manager.stop()
            _browser_manager = None
        
        # Create new browser manager and start with dummy extension
        _browser_manager = BrowserManager()
        await _browser_manager.start_with_dummy_extension()
        
        # Test the dummy extension
        print("🧪 Testing dummy extension...")
        
        # Test popup
        popup_success = False
        if _browser_manager.extension_id:
            try:
                popup_url = f"chrome-extension://{_browser_manager.extension_id}/popup.html"
                popup_page = await _browser_manager.context.new_page()
                await popup_page.goto(popup_url)
                await popup_page.wait_for_load_state('networkidle')
                
                popup_content = await popup_page.content()
                popup_success = "Dummy Extension" in popup_content
                
                await popup_page.close()
            except Exception as e:
                print(f"❌ Error testing popup: {e}")
        
        # Test content script
        content_success = await _browser_manager.test_extension_on_webpage()
        
        if popup_success and content_success:
            return {
                "status": "success",
                "message": "Dummy extension loaded and tested successfully! Both popup and content script are working.",
                "popup_working": popup_success,
                "content_script_working": content_success,
                "extension_id": _browser_manager.extension_id
            }
        elif popup_success:
            return {
                "status": "partial_success",
                "message": "Extension popup loaded but content script may not be working.",
                "popup_working": popup_success,
                "content_script_working": content_success,
                "extension_id": _browser_manager.extension_id
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to load dummy extension")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading dummy extension: {str(e)}")


@router.post("/browser/close")
async def close_browser():
    """Close the browser instance."""
    global _browser_manager
    
    try:
        if _browser_manager:
            await _browser_manager.stop()
            _browser_manager = None
            return {"status": "success", "message": "Browser closed successfully"}
        else:
            return {"status": "info", "message": "No browser instance to close"}
    except Exception as e:
        print(f"Error closing browser: {e}")
        return {"status": "error", "message": f"Error closing browser: {str(e)}"}


@router.get("/browser/sessions/{session_id}/logs")
async def get_browser_logs(session_id: str):
    """Get console logs from browser session."""
    if session_id not in browser_sessions:
        raise HTTPException(status_code=404, detail="Browser session not found")
    
    session = browser_sessions[session_id]
    return {
        "console_logs": session.console_logs,
        "errors": session.errors
    }


@router.post("/browser/test")
async def test_browser():
    """Test if browser can start successfully."""
    try:
        from ..browser.manager import BrowserManager
        
        # Create a temporary browser manager for testing
        temp_browser_manager = BrowserManager()
        await temp_browser_manager.start()
        
        # Create a simple page to test
        context = await temp_browser_manager.browser.new_context()
        page = await context.new_page()
        await page.goto("https://www.google.com")
        title = await page.title()
        
        await temp_browser_manager.stop()
        
        return {
            "status": "success",
            "message": f"Browser test successful. Page title: {title}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Browser test failed: {str(e)}")


@router.get("/browser/debug-logs/{session_id}")
async def get_debug_logs(session_id: str):
    """Get debug logs for a session."""
    global _browser_manager
    
    try:
        if not _browser_manager:
            raise HTTPException(status_code=404, detail="No active browser session")
        
        logs = await _browser_manager.get_debug_logs(session_id)
        if not logs:
            raise HTTPException(status_code=404, detail="No debug logs found for session")
        
        return {
            "status": "success",
            "session_id": session_id,
            "logs": logs.dict()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting debug logs: {str(e)}")


@router.get("/browser/debug-summary/{session_id}")
async def get_debug_summary(session_id: str):
    """Get debug session summary."""
    global _browser_manager
    
    try:
        if not _browser_manager:
            raise HTTPException(status_code=404, detail="No active browser session")
        
        summary = _browser_manager.get_debug_summary(session_id)
        if not summary:
            raise HTTPException(status_code=404, detail="No debug session found")
        
        return {
            "status": "success",
            "session_id": session_id,
            "summary": summary
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting debug summary: {str(e)}")


@router.post("/browser/stop-debug/{session_id}")
async def stop_debug_session(session_id: str):
    """Stop debug session and save logs."""
    global _browser_manager
    
    try:
        if not _browser_manager:
            raise HTTPException(status_code=404, detail="No active browser session")
        
        await _browser_manager.stop_debug_session(session_id)
        
        return {
            "status": "success",
            "message": f"Debug session {session_id} stopped and logs saved"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping debug session: {str(e)}")


@router.get("/browser/current-debug-session")
async def get_current_debug_session():
    """Get current debug session info."""
    global _browser_manager
    
    try:
        if not _browser_manager or not _browser_manager.current_debug_session:
            return {
                "status": "info",
                "message": "No active debug session"
            }
        
        session = _browser_manager.current_debug_session
        summary = _browser_manager.get_debug_summary(session.id)
        
        return {
            "status": "success",
            "session_id": session.id,
            "extension_id": session.extension_id,
            "is_active": session.is_active,
            "log_file_path": session.log_file_path,
            "summary": summary
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting current debug session: {str(e)}")


 