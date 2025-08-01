"""
Function execution implementation for the chat agent using Pydantic AI.
"""

from typing import Dict, List, Any, Optional
from pathlib import Path

from ..models.chat import ChatMessage, MessageRole
from ..models.extension import Extension


class FunctionExecutor:
    """Handles execution of specific functions."""
    
    def __init__(self, model, websocket=None, cli_handler=None):
        """Initialize the function executor."""
        self.model = model
        self.websocket = websocket
        self.cli_handler = cli_handler
    
    async def execute_function(self, function_name: str, args: Dict[str, Any], 
                             messages: List[ChatMessage], session_id: str = None) -> Dict[str, Any]:
        """Execute the specified function with the given arguments."""
        print(f"🔧 Executing function: {function_name}")
        
        if function_name == "build_extension":
            return await self._build_extension(args, messages, session_id)
        elif function_name == "fix_extension":
            return await self._fix_extension(args, messages, session_id)
        elif function_name == "improve_extension":
            return await self._improve_extension(args, messages, session_id)
        elif function_name == "answer_user_question":
            return await self._answer_user_question(args, messages, session_id)
        else:
            print(f"❌ Unknown function: {function_name}")
            return await self._handle_general_conversation(messages, "Unknown function called")
    
    async def _build_extension(self, args: Dict[str, Any], messages: List[ChatMessage], 
                              session_id: str = None) -> Dict[str, Any]:
        """Build a new Chrome extension."""
        print(f"🏗️ Building new extension...")
        
        # Extract requirements from the args
        if 'message' in args:
            # This is from tool output
            requirements = args.get("message", "").replace("Building extension with requirements: ", "")
        else:
            # This is from direct function call
            requirements = args.get("requirements", "")
        
        features = args.get("features", [])
        target_websites = args.get("target_websites", [])
        
        print(f"📝 Requirements: {requirements}")
        print(f"📝 Features: {features}")
        print(f"📝 Target websites: {target_websites}")
        
        # Create extension using Gemini CLI
        extension = await self._generate_extension_with_gemini_cli(
            requirements, features, target_websites, messages, session_id
        )
        
        # Create response message
        features_text = f"\n- Features: {', '.join(features)}" if features else ""
        websites_text = f"\n- Target websites: {', '.join(target_websites)}" if target_websites else ""
        
        assistant_message = f"""I've created a new Chrome extension based on your requirements!

**Extension Details:**
- Name: {extension.name}
- Description: {extension.description}
- Files Created: {', '.join(extension.files.keys())}{features_text}{websites_text}

The extension has been created and is ready for testing. You can now load it in the browser environment to see how it works.

Would you like me to make any adjustments to the extension or explain any part of the code?"""
        
        messages.append(ChatMessage(role=MessageRole.ASSISTANT, content=assistant_message))
        
        return {
            "response": assistant_message,
            "extension": extension,
            "action": "extension_generated"
        }
    
    async def _fix_extension(self, args: Dict[str, Any], messages: List[ChatMessage], 
                            session_id: str = None) -> Dict[str, Any]:
        """Fix issues in an existing Chrome extension."""
        print(f"🔧 Fixing extension issues...")
        
        # Extract issues from the args
        if 'message' in args:
            # This is from tool output
            issues = args.get("message", "").replace("Fixing extension issues: ", "")
        else:
            # This is from direct function call
            issues = args.get("issues", "")
        
        error_logs = args.get("error_logs", "")
        current_behavior = args.get("current_behavior", "")
        
        print(f"📝 Issues to fix: {issues}")
        
        # Create fix prompt for Gemini CLI
        fix_prompt = f"""
Fix the following issues in the Chrome extension:

**Issues to Fix:**
{issues}

**Current Behavior:**
{current_behavior}

**Error Logs:**
{error_logs}

Please fix the issues and ensure the extension works correctly. Make sure to:
1. Address all reported issues
2. Maintain existing functionality
3. Follow Chrome extension best practices
4. Test the fixes thoroughly
"""
        
        # Generate fixed extension
        extension = await self._generate_extension_with_gemini_cli(
            fix_prompt, [], [], messages, session_id, is_fix=True
        )
        
        assistant_message = f"""I've fixed the issues in your Chrome extension!

**Fixed Issues:**
{issues}

**Updated Extension:**
- Name: {extension.name}
- Description: {extension.description}
- Files Updated: {', '.join(extension.files.keys())}

The extension has been updated with the fixes. You can now test it in the browser environment to verify the issues are resolved.

Would you like me to explain any of the changes made or help with further improvements?"""
        
        messages.append(ChatMessage(role=MessageRole.ASSISTANT, content=assistant_message))
        
        return {
            "response": assistant_message,
            "extension": extension,
            "action": "extension_fixed"
        }
    
    async def _improve_extension(self, args: Dict[str, Any], messages: List[ChatMessage], 
                                session_id: str = None) -> Dict[str, Any]:
        """Improve an existing Chrome extension."""
        print(f"🚀 Improving extension...")
        
        # Extract improvements from the args
        if 'message' in args:
            # This is from tool output
            improvements = args.get("message", "").replace("Improving extension with: ", "")
        else:
            # This is from direct function call
            improvements = args.get("improvements", "")
        
        current_features = args.get("current_features", "")
        performance_issues = args.get("performance_issues", "")
        
        print(f"📝 Improvements to add: {improvements}")
        
        # Create improvement prompt for Gemini CLI
        improve_prompt = f"""
Improve the Chrome extension with the following enhancements:

**Improvements to Add:**
{improvements}

**Current Features:**
{current_features}

**Performance Issues to Address:**
{performance_issues}

Please enhance the extension with the requested improvements while:
1. Maintaining existing functionality
2. Following Chrome extension best practices
3. Optimizing performance where needed
4. Adding the new features properly
"""
        
        # Generate improved extension
        extension = await self._generate_extension_with_gemini_cli(
            improve_prompt, [], [], messages, session_id, is_improvement=True
        )
        
        assistant_message = f"""I've improved your Chrome extension with the requested enhancements!

**Improvements Added:**
{improvements}

**Enhanced Extension:**
- Name: {extension.name}
- Description: {extension.description}
- Files Updated: {', '.join(extension.files.keys())}

The extension has been enhanced with the new features and improvements. You can now test it in the browser environment to see the improvements in action.

Would you like me to explain any of the new features or help with further enhancements?"""
        
        messages.append(ChatMessage(role=MessageRole.ASSISTANT, content=assistant_message))
        
        return {
            "response": assistant_message,
            "extension": extension,
            "action": "extension_improved"
        }
    
    async def _answer_user_question(self, args: Dict[str, Any], messages: List[ChatMessage], 
                                   session_id: str = None) -> Dict[str, Any]:
        """Answer general user questions about Chrome extensions."""
        print(f"❓ Answering user question...")
        
        # Extract answer from the args
        if 'answer' in args:
            # This is from tool output
            answer = args.get("answer", "I'm here to help with Chrome extension development!")
        else:
            # This is from direct function call
            answer = args.get("question", "I'm here to help with Chrome extension development!")
        
        topic = args.get("topic", "chrome extension development")
        
        messages.append(ChatMessage(role=MessageRole.ASSISTANT, content=answer))
        
        return {
            "response": answer,
            "extension": None,
            "action": "question_answered"
        }
    
    async def _handle_general_conversation(self, messages: List[ChatMessage], user_message: str) -> Dict[str, Any]:
        """Handle general conversation when no specific function is needed."""
        print(f"💭 Handling general conversation...")
        
        # Create conversation context
        conversation = "\n".join([
            f"{'User' if msg.role == MessageRole.USER else 'Assistant'}: {msg.content}"
            for msg in messages[-3:]  # Last 3 messages for context
        ])
        
        prompt = f"""
You are a helpful assistant for building Chrome extensions. The user is having a conversation about Chrome extensions.

Conversation history:
{conversation}

Provide a helpful, conversational response. If they seem to want to create an extension, encourage them to describe what they want to build. Keep responses friendly and informative.
"""
        
        # Use the model directly for general conversation
        from pydantic_ai import Agent
        temp_agent = Agent(self.model)
        result = await temp_agent.run(prompt)
        answer = str(result.output) if hasattr(result, 'output') else "I'm here to help with Chrome extension development!"
        messages.append(ChatMessage(role=MessageRole.ASSISTANT, content=answer))
        
        return {
            "response": answer,
            "extension": None,
            "action": "conversation"
        }
    
    async def _generate_extension_with_gemini_cli(self, requirements: str, features: List[str], 
                                                 target_websites: List[str], messages: List[ChatMessage], 
                                                 session_id: str = None, is_fix: bool = False, 
                                                 is_improvement: bool = False) -> Extension:
        """Use Gemini CLI to generate a Chrome extension."""
        # Use the CLI handler to generate the extension
        return await self.cli_handler.generate_extension_with_gemini_cli(
            requirements, features, target_websites, messages, session_id, is_fix, is_improvement
        ) 