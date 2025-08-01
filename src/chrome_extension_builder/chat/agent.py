"""
Chat agent that manages conversations and integrates with Pydantic AI for function calling.
"""

import os
from typing import Dict, List, Optional, Any
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.tools import Tool

from ..models.chat import ChatMessage, MessageRole
from .function_caller import FunctionCaller
from .function_executor import FunctionExecutor
from .cli_handler import CLIHandler
from .debug_handler import DebugHandler
from .output_models import ExtensionResponse, QuestionResponse, DebugAnalysisResponse, ConversationResponse


class ChatAgent:
    """Manages chat conversations and integrates with Pydantic AI for function calling."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the chat agent."""
        # Try to get API key from parameter, then environment variables
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "Google API key is required. Please set either GOOGLE_API_KEY or GEMINI_API_KEY "
                "in your .env file or pass it as a parameter."
            )
        
        # Create Pydantic AI agent with Gemini model
        self.model = GeminiModel('gemini-2.0-flash', provider='google-gla')
        
        # Initialize modular components first
        self.function_caller = FunctionCaller()
        self.cli_handler = CLIHandler(self.model, None)  # Will set websocket later
        self.function_executor = FunctionExecutor(self.model, None, self.cli_handler)
        self.debug_handler = DebugHandler(self.model, None)
        
        # Create tools with proper decorators
        build_tool = Tool(
            self._build_extension_tool,
            name="build_extension",
            description="Create a new Chrome extension from scratch based on user requirements"
        )
        
        fix_tool = Tool(
            self._fix_extension_tool,
            name="fix_extension", 
            description="Fix issues or bugs in an existing Chrome extension"
        )
        
        improve_tool = Tool(
            self._improve_extension_tool,
            name="improve_extension",
            description="Enhance or improve an existing Chrome extension with new features or optimizations"
        )
        
        answer_tool = Tool(
            self._answer_user_question_tool,
            name="answer_user_question",
            description="Answer general questions about Chrome extensions, development, or provide guidance"
        )
        
        # Create agent with tools
        self.agent = Agent(
            self.model,
            tools=[build_tool, fix_tool, improve_tool, answer_tool]
        )
        
        # WebSocket for streaming (will be set by routes)
        self.websocket = None
        
        print(f"ChatAgent initialized with API key: {self.api_key[:10]}...")
    
    def _build_extension_tool(self, requirements: str, features: List[str] = None, target_websites: List[str] = None) -> ExtensionResponse:
        """Create a new Chrome extension from scratch based on user requirements."""
        # This will be called by the agent when it decides to build an extension
        return ExtensionResponse(
            success=True,
            message=f"Building extension with requirements: {requirements}",
            action_type="build",
            extension_name="New Chrome Extension",
            extension_description="A Chrome extension based on your requirements",
            files_created=["manifest.json", "popup.html", "popup.js"]
        )
    
    def _fix_extension_tool(self, issues: str, error_logs: str = "", current_behavior: str = "") -> ExtensionResponse:
        """Fix issues or bugs in an existing Chrome extension."""
        return ExtensionResponse(
            success=True,
            message=f"Fixing extension issues: {issues}",
            action_type="fix",
            extension_name="Fixed Chrome Extension",
            extension_description="A Chrome extension with fixes applied"
        )
    
    def _improve_extension_tool(self, improvements: str, current_features: str = "", performance_issues: str = "") -> ExtensionResponse:
        """Enhance or improve an existing Chrome extension with new features or optimizations."""
        return ExtensionResponse(
            success=True,
            message=f"Improving extension with: {improvements}",
            action_type="improve",
            extension_name="Improved Chrome Extension",
            extension_description="A Chrome extension with improvements applied"
        )
    
    def _answer_user_question_tool(self, question: str, topic: str = "chrome extension development") -> QuestionResponse:
        """Answer general questions about Chrome extensions, development, or provide guidance."""
        return QuestionResponse(
            answer=f"Answering question about {topic}: {question}",
            topic=topic,
            helpful_links=["https://developer.chrome.com/docs/extensions/"],
            next_steps=["Review the documentation", "Try the example code"]
        )
    
    async def _analyze_user_intent(self, user_message: str, messages: List[ChatMessage]) -> Dict[str, Any]:
        """Use LLM to intelligently analyze user intent and determine the appropriate action."""
        # Create context from recent messages
        recent_context = "\n".join([
            f"{'User' if msg.role == MessageRole.USER else 'Assistant'}: {msg.content}"
            for msg in messages[-3:]  # Last 3 messages for context
        ])
        
        intent_prompt = f"""
Analyze the user's intent and determine the appropriate action. Consider the conversation context and the user's message.

**Conversation Context:**
{recent_context}

**User's Message:**
{user_message}

**Available Actions:**
1. **build_extension** - User wants to create a new Chrome extension from scratch
2. **improve_extension** - User wants to add features or enhance an existing extension
3. **fix_extension** - User reports issues or bugs that need fixing
4. **debug_analysis** - User is asking about debugging, errors, or logs
5. **clarification_needed** - User wants to build something but needs more details
6. **general_conversation** - General chat or questions about Chrome extensions

**Analysis Guidelines:**
- If user wants to create something new, it's likely build_extension
- If user mentions "add", "enhance", "improve", "also", "can we", it's likely improve_extension
- If user mentions "fix", "broken", "not working", "error", it's likely fix_extension
- If user mentions "debug", "error", "log", "bug", it's likely debug_analysis
- If user wants to build but lacks specific details, suggest clarification_needed
- Otherwise, it's general_conversation

**Important Notes:**
- Custom icons will be automatically copied from the template
- Gemini CLI should NOT generate any PNG image files
- Focus on functionality and code generation

**Response Format:**
Return a JSON object with:
- "action": one of the actions above
- "confidence": 0.0 to 1.0 (how confident you are)
- "reasoning": brief explanation of your decision
- "needs_clarification": true/false (if user needs to provide more details)
"""
        
        # Use a simple agent to analyze intent
        temp_agent = Agent(self.model)
        result = await temp_agent.run(intent_prompt)
        
        # Parse the response (fallback to general conversation if parsing fails)
        try:
            import json
            response_text = str(result.output)
            # Try to extract JSON from the response
            if '{' in response_text and '}' in response_text:
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                json_str = response_text[start:end]
                intent_data = json.loads(json_str)
            else:
                # Fallback to general conversation
                intent_data = {
                    "action": "general_conversation",
                    "confidence": 0.5,
                    "reasoning": "Could not parse intent analysis",
                    "needs_clarification": False
                }
        except Exception as e:
            print(f"⚠️ Error parsing intent analysis: {e}")
            intent_data = {
                "action": "general_conversation",
                "confidence": 0.5,
                "reasoning": "Error parsing intent",
                "needs_clarification": False
            }
        
        print(f"🧠 Intent Analysis: {intent_data}")
        return intent_data
    
    async def process_message(self, messages: List[ChatMessage], user_message: str, session_id: str = None) -> Dict[str, Any]:
        """Process a user message using intelligent intent analysis."""
        print(f"💬 Processing message for session: {session_id or 'new'}")
        print(f"📝 User message: {user_message[:100]}{'...' if len(user_message) > 100 else ''}")
        
        # Add the new user message
        messages.append(ChatMessage(role=MessageRole.USER, content=user_message))
        
        # Use LLM to intelligently analyze user intent
        intent_data = await self._analyze_user_intent(user_message, messages)
        action = intent_data.get("action", "general_conversation")
        confidence = intent_data.get("confidence", 0.5)
        needs_clarification = intent_data.get("needs_clarification", False)
        
        print(f"🎯 Detected action: {action} (confidence: {confidence:.2f})")
        
        # Handle debug requests
        if action == "debug_analysis":
            print(f"🔍 Debug request detected! Analyzing logs...")
            return await self.debug_handler.handle_debug_request(messages, user_message, session_id)
        
        # Handle build requests
        if action == "build_extension":
            if needs_clarification:
                print(f"🏗️ Build request detected but needs clarification...")
                clarification_message = f"""I'd be happy to help you build a Chrome extension! 

To create the best extension for your needs, could you please provide more details about:

1. **What should the extension do?** (e.g., "A chatbot that helps with web browsing")
2. **What features do you want?** (e.g., "Side panel interface", "API integration", "User settings")
3. **Which websites should it work on?** (e.g., "All websites", "Only GitHub", "Specific domains")

Your current request: "{user_message}"

Please provide more specific details so I can create exactly what you need!"""
                
                messages.append(ChatMessage(role=MessageRole.ASSISTANT, content=clarification_message))
                return {
                    "response": clarification_message,
                    "extension": None,
                    "action": "clarification_needed"
                }
            else:
                print(f"🏗️ Build request detected! Creating extension...")
                return await self.function_executor.execute_function(
                    'build_extension',
                    {'requirements': user_message, 'features': [], 'target_websites': []},
                    messages,
                    session_id
                )
        
        # Handle improve requests
        if action == "improve_extension":
            print(f"🚀 Improve request detected! Improving extension...")
            return await self.function_executor.execute_function(
                'improve_extension',
                {'improvements': user_message, 'current_features': '', 'performance_issues': ''},
                messages,
                session_id
            )
        
        # Handle fix requests
        if action == "fix_extension":
            print(f"🔧 Fix request detected! Fixing extension...")
            return await self.function_executor.execute_function(
                'fix_extension',
                {'issues': user_message, 'error_logs': '', 'current_behavior': ''},
                messages,
                session_id
            )
        
        # Handle clarification responses (user provided more details after being asked)
        if len(messages) >= 3:
            last_assistant_message = messages[-2].content if messages[-2].role == MessageRole.ASSISTANT else ""
            if "clarification" in last_assistant_message.lower() or "more details" in last_assistant_message.lower():
                print(f"📝 Clarification response detected! Building extension...")
                return await self.function_executor.execute_function(
                    'build_extension',
                    {'requirements': user_message, 'features': [], 'target_websites': []},
                    messages,
                    session_id
                )
        
        # Handle general conversation
        print(f"💭 General conversation detected...")
        return await self.function_executor._handle_general_conversation(messages, user_message) 