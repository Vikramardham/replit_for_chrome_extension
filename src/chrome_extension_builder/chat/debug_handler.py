"""
Debug handling implementation for the chat agent using Pydantic AI.
"""

from typing import Dict, List, Any, Optional

from ..models.chat import ChatMessage


class DebugHandler:
    """Handles debug-related requests and log analysis."""
    
    def __init__(self, model, websocket=None):
        """Initialize the debug handler."""
        self.model = model
        self.websocket = websocket
    
    async def handle_debug_request(self, messages: List[ChatMessage], user_message: str, session_id: str = None) -> Dict[str, Any]:
        """Handle debug-related requests by analyzing browser logs."""
        print(f"🔍 Handling debug request for session: {session_id}")
        
        try:
            # Try to get debug logs from browser manager
            from ..browser.manager import BrowserManager
            from ..api.routes import _browser_manager
            
            if not _browser_manager or not _browser_manager.current_debug_session:
                response = """I don't see any active debug session. To analyze issues with your extension:

1. First load your extension in the browser using "Load Extension in Browser"
2. Test the extension and reproduce any issues
3. Then ask me about debugging, errors, or logs

The debug system will capture all events, errors, and console output for analysis."""
                
                messages.append(ChatMessage(role="assistant", content=response))
                return {
                    "response": response,
                    "extension": None,
                    "action": "debug_no_session"
                }
            
            # Get debug logs
            debug_session = _browser_manager.current_debug_session
            logs = await _browser_manager.get_debug_logs(debug_session.id)
            
            if not logs:
                response = "No debug logs found. Please test your extension first to generate some logs."
                messages.append(ChatMessage(role="assistant", content=response))
                return {
                    "response": response,
                    "extension": None,
                    "action": "debug_no_logs"
                }
            
            # Analyze logs with AI
            analysis_prompt = f"""
            Analyze these browser debug logs and help the user understand any issues:

            **User Question:** {user_message}

            **Debug Summary:**
            {logs.summary}

            **Errors Found ({len(logs.errors)}):**
            {self._format_errors_for_ai(logs.errors)}

            **User Actions ({len(logs.user_actions)}):**
            {self._format_user_actions_for_ai(logs.user_actions)}

            **Console Output ({len(logs.console_output)} entries):**
            {self._format_console_output_for_ai(logs.console_output)}

            **AI Recommendations:**
            {logs.recommendations}

            Please provide:
            1. A clear analysis of any issues found
            2. Specific recommendations for fixing problems
            3. Suggestions for improving the extension
            4. Code examples if needed for fixes

            Be helpful and actionable in your response.
            """
            
            # Use the model directly for debug analysis
            from pydantic_ai import Agent
            temp_agent = Agent(self.model)
            result = await temp_agent.run(analysis_prompt)
            response = str(result.output) if hasattr(result, 'output') else "I'm analyzing the debug logs..."
            
            messages.append(ChatMessage(role="assistant", content=response))
            
            print(f"✅ Debug analysis completed")
            return {
                "response": response,
                "extension": None,
                "action": "debug_analysis",
                "debug_session_id": debug_session.id,
                "log_summary": {
                    "total_errors": len(logs.errors),
                    "total_events": len(logs.user_actions),
                    "total_console_logs": len(logs.console_output)
                }
            }
            
        except Exception as e:
            print(f"❌ Error handling debug request: {e}")
            response = f"I encountered an error while analyzing the debug logs: {str(e)}. Please try again or check if the browser session is still active."
            
            messages.append(ChatMessage(role="assistant", content=response))
            return {
                "response": response,
                "extension": None,
                "action": "debug_error"
            }
    
    def _format_errors_for_ai(self, errors: List) -> str:
        """Format errors for AI analysis."""
        if not errors:
            return "No errors found."
        
        formatted = []
        for error in errors:
            formatted.append(f"- Type: {error.type}")
            formatted.append(f"  Message: {error.message}")
            formatted.append(f"  URL: {error.url or 'unknown'}")
            formatted.append(f"  Severity: {error.severity}")
            if error.stack_trace:
                formatted.append(f"  Stack: {error.stack_trace[:200]}...")
            formatted.append("")
        
        return "\n".join(formatted)
    
    def _format_user_actions_for_ai(self, actions: List) -> str:
        """Format user actions for AI analysis."""
        if not actions:
            return "No user actions recorded."
        
        formatted = []
        for action in actions:
            formatted.append(f"- {action.type.value}: {action.data}")
            formatted.append(f"  URL: {action.url or 'unknown'}")
            formatted.append(f"  Time: {action.timestamp}")
            formatted.append("")
        
        return "\n".join(formatted)
    
    def _format_console_output_for_ai(self, console_logs: List[str]) -> str:
        """Format console output for AI analysis."""
        if not console_logs:
            return "No console output recorded."
        
        # Show last 10 console entries
        recent_logs = console_logs[-10:] if len(console_logs) > 10 else console_logs
        return "\n".join(recent_logs) 