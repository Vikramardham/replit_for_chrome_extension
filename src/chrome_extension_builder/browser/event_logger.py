"""
Browser event logging service for debugging extensions.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from playwright.async_api import Page, BrowserContext
import asyncio

from ..models.browser import (
    BrowserEvent, BrowserError, BrowserSession, DebugSession, 
    EventType, LogAnalysis
)


class BrowserEventLogger:
    """Logs browser events, errors, and console output for debugging."""
    
    def __init__(self, session_id: str, extension_id: Optional[str] = None):
        self.session_id = session_id
        self.extension_id = extension_id
        self.events: List[BrowserEvent] = []
        self.errors: List[BrowserError] = []
        self.console_logs: List[str] = []
        self.is_logging = False
        self.log_file_path: Optional[str] = None
        self.event_callbacks: List[Callable] = []
        
        # Create logs directory
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        
        # Create session-specific log file
        self.log_file_path = self.logs_dir / f"session_{session_id}.json"
        
    async def start_logging(self, page: Page, context: BrowserContext):
        """Start logging browser events."""
        if self.is_logging:
            return
            
        self.is_logging = True
        print(f"🔍 Starting event logging for session: {self.session_id}")
        
        # Set up event listeners
        await self._setup_page_listeners(page)
        await self._setup_context_listeners(context)
        
        # Set up console logging
        await self._setup_console_logging(page)
        
        # Set up error logging
        await self._setup_error_logging(page)
        
        print(f"✅ Event logging started. Log file: {self.log_file_path}")
    
    async def stop_logging(self):
        """Stop logging and save logs to file."""
        self.is_logging = False
        await self._save_logs()
        print(f"🛑 Event logging stopped for session: {self.session_id}")
    
    async def _setup_page_listeners(self, page: Page):
        """Set up page event listeners."""
        
        # Click events
        page.on("click", lambda: self._log_event(EventType.CLICK, {
            "element": "clicked_element",
            "coordinates": "click_coordinates"
        }))
        
        # Keyboard events
        page.on("keydown", lambda: self._log_event(EventType.KEYBOARD, {
            "key": "pressed_key",
            "modifiers": "key_modifiers"
        }))
        
        # Navigation events
        page.on("framenavigated", lambda frame: self._log_event(EventType.NAVIGATION, {
            "url": frame.url,
            "type": "navigation"
        }))
        
        # DOM changes
        page.on("domcontentloaded", lambda: self._log_event(EventType.DOM_CHANGE, {
            "type": "dom_loaded"
        }))
        
        # Scroll events
        page.on("scroll", lambda: self._log_event(EventType.SCROLL, {
            "scroll_position": "scroll_coordinates"
        }))
        
        # Resize events
        page.on("resize", lambda: self._log_event(EventType.RESIZE, {
            "new_size": "window_dimensions"
        }))
    
    async def _setup_context_listeners(self, context: BrowserContext):
        """Set up context-level event listeners."""
        
        # Service worker events (for extension debugging)
        context.on("serviceworker", lambda worker: self._log_event(EventType.EXTENSION_ERROR, {
            "service_worker": worker.url,
            "type": "service_worker_event"
        }))
    
    async def _setup_console_logging(self, page: Page):
        """Set up console log capture."""
        
        async def handle_console(msg):
            log_entry = f"[{datetime.now().isoformat()}] {msg.type}: {msg.text}"
            self.console_logs.append(log_entry)
            
            # Log as event
            event_type = EventType.CONSOLE_LOG if msg.type == "log" else EventType.CONSOLE_ERROR
            await self._log_event(event_type, {
                "message": msg.text,
                "level": msg.type,
                "location": f"{msg.location.get('url', 'unknown')}:{msg.location.get('lineNumber', 'unknown')}"
            })
        
        page.on("console", handle_console)
    
    async def _setup_error_logging(self, page: Page):
        """Set up error logging."""
        
        async def handle_error(error):
            browser_error = BrowserError(
                type="javascript_error",
                message=error.message,
                stack_trace=error.stack,
                url=page.url,
                session_id=self.session_id,
                extension_id=self.extension_id,
                severity="error"
            )
            
            self.errors.append(browser_error)
            print(f"❌ JavaScript error logged: {error.message}")
        
        # Listen for page errors
        page.on("pageerror", handle_error)
        
        # Listen for request failures
        async def handle_request_failure(request):
            if request.failure:
                browser_error = BrowserError(
                    type="network_error",
                    message=f"Request failed: {request.failure}",
                    url=request.url,
                    session_id=self.session_id,
                    extension_id=self.extension_id,
                    severity="warning"
                )
                self.errors.append(browser_error)
        
        page.on("requestfailed", handle_request_failure)
    
    async def _log_event(self, event_type: EventType, data: Dict[str, Any]):
        """Log a browser event."""
        if not self.is_logging:
            return
            
        event = BrowserEvent(
            type=event_type,
            url="current_page_url",  # Will be updated with actual URL
            data=data,
            session_id=self.session_id,
            extension_id=self.extension_id
        )
        
        self.events.append(event)
        
        # Notify callbacks
        for callback in self.event_callbacks:
            try:
                await callback(event)
            except Exception as e:
                print(f"⚠️ Event callback error: {e}")
    
    async def _save_logs(self):
        """Save all logs to file."""
        if not self.log_file_path:
            return
            
        log_data = {
            "session_id": self.session_id,
            "extension_id": self.extension_id,
            "timestamp": datetime.now().isoformat(),
            "events": [event.dict() for event in self.events],
            "errors": [error.dict() for error in self.errors],
            "console_logs": self.console_logs,
            "summary": {
                "total_events": len(self.events),
                "total_errors": len(self.errors),
                "total_console_logs": len(self.console_logs)
            }
        }
        
        with open(self.log_file_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, default=str)
        
        print(f"💾 Logs saved to: {self.log_file_path}")
    
    def add_event_callback(self, callback: Callable):
        """Add a callback to be called when events are logged."""
        self.event_callbacks.append(callback)
    
    def get_log_summary(self) -> Dict[str, Any]:
        """Get a summary of logged events."""
        return {
            "session_id": self.session_id,
            "extension_id": self.extension_id,
            "total_events": len(self.events),
            "total_errors": len(self.errors),
            "total_console_logs": len(self.console_logs),
            "event_types": {event.type.value: len([e for e in self.events if e.type == event.type]) 
                          for event in EventType},
            "error_types": {error.type: len([e for e in self.errors if e.type == error.type]) 
                          for error in self.errors},
            "log_file_path": str(self.log_file_path) if self.log_file_path else None
        }
    
    def get_errors_for_ai(self) -> List[Dict[str, Any]]:
        """Get errors formatted for AI analysis."""
        return [
            {
                "type": error.type,
                "message": error.message,
                "url": error.url,
                "timestamp": error.timestamp.isoformat(),
                "severity": error.severity
            }
            for error in self.errors
        ]
    
    def get_user_actions_for_ai(self) -> List[Dict[str, Any]]:
        """Get user actions formatted for AI analysis."""
        user_actions = [event for event in self.events 
                       if event.type in [EventType.CLICK, EventType.KEYBOARD, EventType.NAVIGATION]]
        
        return [
            {
                "type": event.type.value,
                "timestamp": event.timestamp.isoformat(),
                "url": event.url,
                "element": event.element,
                "data": event.data
            }
            for event in user_actions
        ]
    
    def get_console_output_for_ai(self) -> List[str]:
        """Get console output formatted for AI analysis."""
        return self.console_logs.copy()


class DebugSessionManager:
    """Manages debug sessions and log analysis."""
    
    def __init__(self):
        self.active_sessions: Dict[str, BrowserEventLogger] = {}
        self.debug_sessions: Dict[str, DebugSession] = {}
    
    async def start_debug_session(self, session_id: str, extension_id: str, 
                                page: Page, context: BrowserContext) -> DebugSession:
        """Start a new debug session."""
        logger = BrowserEventLogger(session_id, extension_id)
        
        debug_session = DebugSession(
            id=session_id,
            browser_session_id=session_id,
            extension_id=extension_id,
            log_file_path=str(logger.log_file_path) if logger.log_file_path else None
        )
        
        self.active_sessions[session_id] = logger
        self.debug_sessions[session_id] = debug_session
        
        await logger.start_logging(page, context)
        
        print(f"🔍 Debug session started: {session_id}")
        return debug_session
    
    async def stop_debug_session(self, session_id: str):
        """Stop a debug session."""
        if session_id in self.active_sessions:
            logger = self.active_sessions[session_id]
            await logger.stop_logging()
            
            # Update debug session
            if session_id in self.debug_sessions:
                debug_session = self.debug_sessions[session_id]
                debug_session.is_active = False
                debug_session.updated_at = datetime.utcnow()
                debug_session.events_count = len(logger.events)
                debug_session.errors_count = len(logger.errors)
            
            del self.active_sessions[session_id]
            print(f"🛑 Debug session stopped: {session_id}")
    
    def get_session_logs(self, session_id: str) -> Optional[BrowserEventLogger]:
        """Get logs for a session."""
        return self.active_sessions.get(session_id)
    
    async def analyze_logs_for_ai(self, session_id: str) -> LogAnalysis:
        """Analyze logs and format for AI consumption."""
        logger = self.get_session_logs(session_id)
        if not logger:
            raise ValueError(f"No logs found for session: {session_id}")
        
        # Generate summary
        summary = self._generate_log_summary(logger)
        
        # Get AI-formatted data
        errors = logger.get_errors_for_ai()
        user_actions = logger.get_user_actions_for_ai()
        console_output = logger.get_console_output_for_ai()
        
        # Generate recommendations
        recommendations = self._generate_recommendations(logger)
        
        return LogAnalysis(
            session_id=session_id,
            summary=summary,
            errors=logger.errors,
            user_actions=logger.events,
            console_output=console_output,
            recommendations=recommendations
        )
    
    def _generate_log_summary(self, logger: BrowserEventLogger) -> str:
        """Generate a human-readable summary of logs."""
        summary_parts = []
        
        summary_parts.append(f"Session logged {len(logger.events)} events over {len(logger.errors)} errors.")
        
        if logger.events:
            event_types = {}
            for event in logger.events:
                event_types[event.type.value] = event_types.get(event.type.value, 0) + 1
            
            summary_parts.append(f"Event breakdown: {', '.join([f'{k}: {v}' for k, v in event_types.items()])}")
        
        if logger.errors:
            error_types = {}
            for error in logger.errors:
                error_types[error.type] = error_types.get(error.type, 0) + 1
            
            summary_parts.append(f"Error breakdown: {', '.join([f'{k}: {v}' for k, v in error_types.items()])}")
        
        if logger.console_logs:
            summary_parts.append(f"Console output: {len(logger.console_logs)} log entries")
        
        return " ".join(summary_parts)
    
    def _generate_recommendations(self, logger: BrowserEventLogger) -> List[str]:
        """Generate recommendations based on logged events."""
        recommendations = []
        
        # Check for JavaScript errors
        js_errors = [e for e in logger.errors if e.type == "javascript_error"]
        if js_errors:
            recommendations.append(f"Found {len(js_errors)} JavaScript errors that may need fixing")
        
        # Check for network errors
        network_errors = [e for e in logger.errors if e.type == "network_error"]
        if network_errors:
            recommendations.append(f"Found {len(network_errors)} network errors that may indicate connectivity issues")
        
        # Check for extension-specific issues
        extension_errors = [e for e in logger.errors if e.type == "extension_error"]
        if extension_errors:
            recommendations.append(f"Found {len(extension_errors)} extension-specific errors that may need code review")
        
        # Check for user interaction patterns
        clicks = [e for e in logger.events if e.type == EventType.CLICK]
        if len(clicks) > 10:
            recommendations.append("High number of clicks detected - consider optimizing user interface")
        
        return recommendations 