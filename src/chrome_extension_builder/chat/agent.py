"""
Chat agent that manages conversations and integrates with Gemini CLI for code generation.
"""

import os
import json
import subprocess
import tempfile
import asyncio
from typing import Dict, List, Optional, Any
from pathlib import Path
from google import genai
from google.genai import types

from ..models.chat import ChatMessage, MessageRole
from ..models.extension import Extension


class ChatAgent:
    """Manages chat conversations and integrates with Gemini CLI for code generation."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the chat agent."""
        # Try to get API key from parameter, then environment variables
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "Google API key is required. Please set either GOOGLE_API_KEY or GEMINI_API_KEY "
                "in your .env file or pass it as a parameter."
            )
        
        # Create client with the new API
        self.client = genai.Client(api_key=self.api_key)
        
        # WebSocket for streaming (will be set by routes)
        self.websocket = None
        
        print(f"ChatAgent initialized with API key: {self.api_key[:10]}...")
    
    async def process_message(self, messages: List[ChatMessage], user_message: str, session_id: str = None) -> Dict[str, Any]:
        """Process a user message and determine the appropriate response."""
        print(f"💬 Processing message for session: {session_id or 'new'}")
        print(f"📝 User message: {user_message[:100]}{'...' if len(user_message) > 100 else ''}")
        
        # Add the new user message
        messages.append(ChatMessage(role=MessageRole.USER, content=user_message))
        
        # Check if user is asking about debugging or logs
        debug_keywords = ['debug', 'error', 'log', 'bug', 'issue', 'problem', 'fix', 'broken']
        is_debug_request = any(keyword in user_message.lower() for keyword in debug_keywords)
        
        if is_debug_request:
            print(f"🔍 Debug request detected! Analyzing logs...")
            return await self._handle_debug_request(messages, user_message, session_id)
        
        # Analyze the conversation to determine if code generation is needed
        print(f"🤔 Analyzing conversation for code generation intent...")
        should_generate_code = await self._should_generate_code(messages)
        
        if should_generate_code:
            print(f"🎯 Code generation detected! Starting extension creation...")
            # Generate extension using Gemini CLI
            extension = await self._generate_extension_with_gemini_cli(messages, session_id)
            
            # Create assistant response
            assistant_message = f"""I've generated a Chrome extension based on your requirements! 

**Extension Details:**
- Name: {extension.name}
- Description: {extension.description}
- Files Created: {', '.join(extension.files.keys())}

The extension has been created and is ready for testing. You can now load it in the browser environment to see how it works.

Would you like me to make any adjustments to the extension or explain any part of the code?"""
            
            messages.append(ChatMessage(role=MessageRole.ASSISTANT, content=assistant_message))
            
            print(f"✅ Extension generation response sent to user")
            return {
                "response": assistant_message,
                "extension": extension,
                "action": "extension_generated"
            }
        else:
            print(f"💭 Continuing conversation...")
            # Continue the conversation
            response = await self._generate_conversation_response(messages)
            messages.append(ChatMessage(role=MessageRole.ASSISTANT, content=response))
            
            print(f"✅ Conversation response sent to user")
            return {
                "response": response,
                "extension": None,
                "action": "conversation"
            }
    
    async def _should_generate_code(self, messages: List[ChatMessage]) -> bool:
        """Determine if the conversation indicates code generation is needed."""
        # Get the last few messages for context
        recent_messages = messages[-3:] if len(messages) >= 3 else messages
        
        # Combine recent messages
        conversation_text = "\n".join([msg.content for msg in recent_messages])
        
        prompt = f"""
        Analyze this conversation and determine if the user wants to generate a Chrome extension:
        
        Conversation:
        {conversation_text}
        
        Respond with only "YES" if the user wants to create/generate a Chrome extension, or "NO" if they're just asking questions or having a general conversation.
        
        Look for keywords like: create, build, make, generate, extension, chrome extension, develop, code, etc.
        """
        
        response = self.client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt
        )
        return "YES" in response.text.upper()
    
    async def _generate_conversation_response(self, messages: List[ChatMessage]) -> str:
        """Generate a conversational response."""
        # Create conversation context
        conversation = "\n".join([
            f"{'User' if msg.role == MessageRole.USER else 'Assistant'}: {msg.content}"
            for msg in messages
        ])
        
        prompt = f"""
        You are a helpful assistant for building Chrome extensions. The user is having a conversation about Chrome extensions.

        Conversation history:
        {conversation}

        Provide a helpful, conversational response. If they seem to want to create an extension, encourage them to describe what they want to build. Keep responses friendly and informative.
        """
        
        response = self.client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt
        )
        return response.text
    
    async def _generate_extension_with_gemini_cli(self, messages: List[ChatMessage], session_id: str = None) -> Extension:
        """Use Gemini CLI to generate a Chrome extension."""
        print(f"🎯 Starting extension generation for session: {session_id or 'new'}")
        
        # Create persistent extension directory based on session ID
        if session_id:
            extensions_dir = Path("extensions")
            extensions_dir.mkdir(exist_ok=True)
            extension_dir = extensions_dir / session_id
            extension_dir.mkdir(exist_ok=True)
            print(f"📂 Using persistent directory: {extension_dir}")
        else:
            # Fallback to temporary directory for non-session cases
            temp_dir = tempfile.mkdtemp()
            extension_dir = Path(temp_dir)
            print(f"📂 Using temporary directory: {extension_dir}")
        
        try:
            # Prepare the prompt for Gemini CLI
            user_requirements = "\n".join([
                msg.content for msg in messages if msg.role == MessageRole.USER
            ])
            
            # Check if this is a modification request (extension already exists)
            existing_files = list(extension_dir.rglob("*")) if extension_dir.exists() else []
            is_modification = len(existing_files) > 0
            
            if is_modification:
                print(f"🔧 Modifying existing extension with {len(existing_files)} files")
                # For modifications, provide context about existing files
                file_list = "\n".join([f"- {f.relative_to(extension_dir)}" for f in existing_files if f.is_file()])
                cli_prompt = f"""
                Modify the existing Chrome extension based on these requirements:
                
                {user_requirements}
                
                The extension currently has these files:
                {file_list}
                
                Please modify the existing files or add new files as needed to implement the requested changes.
                Make sure the extension remains functional and follows Chrome extension best practices.
                """
            else:
                print(f"🆕 Creating new extension from scratch")
                # For new extensions, create complete structure
                cli_prompt = f"""
                Create a complete Chrome extension based on these requirements:
                
                {user_requirements}
                
                Generate all necessary files including:
                - manifest.json
                - popup.html, popup.css, popup.js (if needed)
                - content.js (if needed)
                - background.js (if needed)
                - Any other required files
                
                Make sure the extension is functional and follows Chrome extension best practices.
                """
            
            print(f"📝 User requirements: {user_requirements[:100]}{'...' if len(user_requirements) > 100 else ''}")
            
            # Call Gemini CLI
            print(f"🤖 Calling Gemini CLI...")
            extension_files = await self._call_gemini_cli(cli_prompt, extension_dir)
            
            print(f"📖 Reading generated files...")
            # Read the generated files
            files = {}
            manifest_data = {}
            
            for file_path in extension_dir.rglob("*"):
                if file_path.is_file():
                    relative_path = file_path.relative_to(extension_dir)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        files[str(relative_path)] = content
                        
                        # Extract manifest data
                        if relative_path.name == "manifest.json":
                            try:
                                manifest_data = json.loads(content)
                                print(f"📋 Found manifest.json with name: {manifest_data.get('name', 'Unknown')}")
                            except json.JSONDecodeError:
                                print(f"⚠️  Warning: Could not parse manifest.json")
            
            print(f"📦 Creating extension object with {len(files)} files")
            # Create extension object
            from ..models.extension import ExtensionManifest
            
            manifest = ExtensionManifest(
                name=manifest_data.get("name", "Chrome Extension"),
                description=manifest_data.get("description", "A Chrome extension"),
                permissions=manifest_data.get("permissions", []),
                host_permissions=manifest_data.get("host_permissions", [])
            )
            
            extension = Extension(
                id=session_id or f"ext_{len(files)}",
                name=manifest_data.get("name", "Chrome Extension"),
                description=manifest_data.get("description", "A Chrome extension"),
                manifest=manifest,
                files=files
            )
            
            print(f"✅ Extension generation completed successfully!")
            print(f"📊 Extension summary:")
            print(f"   - Name: {extension.name}")
            print(f"   - Description: {extension.description}")
            print(f"   - Files: {len(files)}")
            print(f"   - ID: {extension.id}")
            
            return extension
            
        except Exception as e:
            print(f"❌ Error generating extension: {e}")
            # Fallback to basic extension
            return await self._create_fallback_extension(extension_dir)
    
    async def _call_gemini_cli(self, prompt: str, output_dir: Path) -> List[str]:
        """Call Gemini CLI to generate code."""
        import subprocess
        import os
        
        try:
            print(f"🚀 Starting Gemini CLI code generation...")
            print(f"📁 Working directory: {output_dir}")
            
            # Set up environment variables
            env = os.environ.copy()
            env["GEMINI_API_KEY"] = self.api_key
            env["GOOGLE_API_KEY"] = self.api_key  # Also set this for compatibility
            
            # Add npm global bin to PATH for Windows
            npm_bin_path = r"C:\Users\vikra\AppData\Roaming\npm"
            if npm_bin_path not in env.get("PATH", ""):
                env["PATH"] = npm_bin_path + os.pathsep + env.get("PATH", "")
            
            # Run Gemini CLI command with full path and correct options
            gemini_path = r"C:\Users\vikra\AppData\Roaming\npm\gemini.cmd"
            
            # Test if the gemini command exists and is accessible
            
            # Check if the file actually exists
            if not os.path.exists(gemini_path):
                print(f"❌ Gemini CLI file not found at: {gemini_path}")
                # Try alternative paths
                alt_paths = [
                    r"C:\Users\vikra\AppData\Roaming\npm\gemini",
                    r"C:\Users\vikra\AppData\Roaming\npm\gemini.cmd",
                    r"C:\Users\vikra\AppData\Local\npm\gemini.cmd",
                    r"C:\Users\vikra\AppData\Local\npm\gemini"
                ]
                
                for alt_path in alt_paths:
                    if os.path.exists(alt_path):
                        print(f"✅ Found Gemini CLI at: {alt_path}")
                        gemini_path = alt_path
                        break
                else:
                    raise Exception(f"Gemini CLI not found at any of the expected paths: {[gemini_path] + alt_paths}")
            
            # Test if the command is accessible
            try:
                test_result = subprocess.run([gemini_path, "--help"], 
                                          capture_output=True, text=True, timeout=5)
                print(f"✅ Gemini CLI is accessible (help output length: {len(test_result.stdout)})")
            except Exception as e:
                print(f"❌ Gemini CLI test failed: {e}")
                raise Exception(f"Gemini CLI not accessible at {gemini_path}: {e}")
            
            print(f"🔧 Executing: {gemini_path} --yolo --model gemini-2.5-flash --prompt [prompt]")
            print(f"📁 Working directory: {output_dir}")
            print(f"🔑 API Key available: {'✓' if self.api_key else '✗'}")
            print(f"🌐 PATH includes npm: {'✓' if npm_bin_path in env.get('PATH', '') else '✗'}")
            # Convert multi-line prompt to single line
            single_line_prompt = prompt.replace('\n', ' ').replace('\r', ' ').strip()
            # Remove extra spaces
            single_line_prompt = ' '.join(single_line_prompt.split())
            
            print(f"📝 Original prompt length: {len(prompt)} characters")
            print(f"📝 Single-line prompt length: {len(single_line_prompt)} characters")
            print(f"📝 Single-line prompt preview: {single_line_prompt[:100]}...")
            
            # Test with a simple prompt first to see if the issue is with the prompt
            test_prompt = "Create a simple Chrome extension that shows 'Hello World' in a popup"
            test_command = f"{gemini_path} --yolo --model gemini-2.5-flash --prompt \"{test_prompt}\""
            print(f"🧪 Testing with simple prompt first...")
            print(f"🧪 Test command: {test_command}")
            print(f"🧪 Test command length: {len(test_command)} characters")
            
            test_process = await asyncio.create_subprocess_exec(
                gemini_path,
                "--yolo",
                "--model", "gemini-2.5-flash",
                "--prompt", test_prompt,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=str(output_dir)
            )
            
            # Wait a bit for test process
            await asyncio.sleep(3)
            if test_process.returncode is not None:
                stdout, stderr = await test_process.communicate()
                print(f"🧪 Test process completed with return code: {test_process.returncode}")
                print(f"🧪 Test STDOUT: {stdout.decode()}")
                print(f"🧪 Test STDERR: {stderr.decode()}")
            else:
                print(f"🧪 Test process is still running, proceeding with main process...")
                test_process.terminate()
            
            # Use the exact command structure that works in terminal
            try:
                # First, let's try the command that works in terminal exactly
                cmd_args = [
                    gemini_path,
                    "--yolo",
                    "--model", "gemini-2.5-flash",
                    "--prompt", single_line_prompt
                ]
                print(f"🔧 Command args: {cmd_args}")
                
                # Log the full command that would be executed in terminal
                full_command = f"{gemini_path} --yolo --model gemini-2.5-flash --prompt \"{single_line_prompt}\""
                print(f"🔧 Full command to execute:")
                print(f"   {full_command}")
                print(f"🔧 Command length: {len(full_command)} characters")
                print(f"🔧 Working directory: {output_dir}")
                print(f"🔧 Environment variables:")
                print(f"   GEMINI_API_KEY: {'✓' if env.get('GEMINI_API_KEY') else '✗'}")
                print(f"   GOOGLE_API_KEY: {'✓' if env.get('GOOGLE_API_KEY') else '✗'}")
                print(f"   PATH includes npm: {'✓' if npm_bin_path in env.get('PATH', '') else '✗'}")
                print(f"🔧 Full PATH: {env.get('PATH', '')[:200]}...")
                
                process = await asyncio.create_subprocess_exec(
                    *cmd_args,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=env,
                    cwd=str(output_dir)
                )
                print(f"✅ Subprocess created successfully with PID: {process.pid}")
            except Exception as e:
                print(f"❌ Failed to create subprocess: {e}")
                raise
            
            print(f"⏳ Streaming Gemini CLI output...")
            
            # Add a small delay to see if process starts
            await asyncio.sleep(1)
            
            # Check if process is still running
            if process.returncode is not None:
                print(f"❌ Process exited immediately with return code: {process.returncode}")
                # Get any output that might have been produced
                stdout, stderr = await process.communicate()
                print(f"STDOUT: {stdout.decode()}")
                print(f"STDERR: {stderr.decode()}")
                raise Exception("Process exited immediately")
            
            print(f"✅ Process is still running, starting real-time streaming...")
            
            # Stream stdout and stderr in real-time
            stdout_lines = []
            stderr_lines = []
            
            async def read_stream(stream, lines_list, stream_name):
                """Read from stream and collect lines in real-time."""
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    line_str = line.decode('utf-8', errors='ignore').strip()
                    if line_str:
                        lines_list.append(line_str)
                        print(f"📤 {stream_name.upper()}: {line_str}")
                        
                        # Send to WebSocket if available
                        if self.websocket:
                            try:
                                await self.websocket.send_json({
                                    "type": "cli_output",
                                    "stream": stream_name,
                                    "content": line_str
                                })
                            except Exception as e:
                                print(f"⚠️ WebSocket error: {e}")
            
            # Start reading from both streams concurrently
            try:
                await asyncio.gather(
                    read_stream(process.stdout, stdout_lines, "stdout"),
                    read_stream(process.stderr, stderr_lines, "stderr")
                )
                return_code = await process.wait()
                print(f"✅ Process completed with return code: {return_code}")
            except Exception as e:
                print(f"❌ Error during streaming: {e}")
                process.terminate()
                raise
            
            if return_code != 0:
                print(f"❌ Gemini CLI error (return code: {return_code}):")
                if stderr_lines:
                    print(f"❌ STDERR:")
                    for line in stderr_lines:
                        print(f"   {line}")
                if stdout_lines:
                    print(f"📤 STDOUT:")
                    for line in stdout_lines:
                        print(f"   {line}")
                
                # Send error to WebSocket if available
                if self.websocket:
                    try:
                        error_message = f"Gemini CLI failed with return code {return_code}"
                        if stderr_lines:
                            error_message += f"\nError: {' '.join(stderr_lines)}"
                        await self.websocket.send_json({
                            "type": "cli_output",
                            "stream": "stderr",
                            "content": error_message
                        })
                    except Exception as e:
                        print(f"⚠️ WebSocket error: {e}")
                
                # Fallback to basic extension
                return await self._create_fallback_extension(output_dir)
            
            print(f"✅ Gemini CLI completed successfully!")
            print(f"📄 Generated files:")
            
            # Return list of generated files
            files = [str(f.relative_to(output_dir)) for f in output_dir.rglob("*") if f.is_file()]
            for file in files:
                print(f"   - {file}")
            
            return files
            
        except Exception as e:
            print(f"❌ Error calling Gemini CLI: {e}")
            # Fallback to basic extension
            return await self._create_fallback_extension(output_dir)
    
    async def _handle_debug_request(self, messages: List[ChatMessage], user_message: str, session_id: str = None) -> Dict[str, Any]:
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
                
                messages.append(ChatMessage(role=MessageRole.ASSISTANT, content=response))
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
                messages.append(ChatMessage(role=MessageRole.ASSISTANT, content=response))
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
            
            ai_response = self.client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=analysis_prompt
            )
            
            response = ai_response.text
            
            messages.append(ChatMessage(role=MessageRole.ASSISTANT, content=response))
            
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
            
            messages.append(ChatMessage(role=MessageRole.ASSISTANT, content=response))
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
    
    async def _create_fallback_extension(self, output_dir: Path) -> List[str]:
        """Create a basic fallback extension if Gemini CLI fails."""
        # Create basic manifest.json
        manifest = {
            "manifest_version": 3,
            "name": "Chrome Extension",
            "version": "1.0.0",
            "description": "A Chrome extension",
            "permissions": ["activeTab"],
            "action": {
                "default_popup": "popup.html"
            }
        }
        
        with open(output_dir / "manifest.json", 'w') as f:
            json.dump(manifest, f, indent=2)
        
        # Create basic popup.html
        popup_html = """<!DOCTYPE html>
<html>
<head>
    <title>Chrome Extension</title>
    <style>
        body { width: 300px; padding: 20px; font-family: Arial, sans-serif; }
        .header { background: #4285f4; color: white; padding: 10px; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="header">
        <h2>Chrome Extension</h2>
    </div>
    <p>This is a basic Chrome extension.</p>
    <script src="popup.js"></script>
</body>
</html>"""
        
        with open(output_dir / "popup.html", 'w') as f:
            f.write(popup_html)
        
        # Create basic popup.js
        popup_js = """// Basic popup script
console.log('Chrome extension popup loaded!');"""
        
        with open(output_dir / "popup.js", 'w') as f:
            f.write(popup_js)
        
        return ["manifest.json", "popup.html", "popup.js"] 