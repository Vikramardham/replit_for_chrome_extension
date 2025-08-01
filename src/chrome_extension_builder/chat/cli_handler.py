"""
Gemini CLI integration for code generation using Pydantic AI.
"""

import os
import json
import subprocess
import tempfile
import asyncio
import shutil
from typing import List, Optional
from pathlib import Path

from ..models.extension import Extension, ExtensionManifest


class CLIHandler:
    """Handles Gemini CLI integration for code generation."""
    
    def __init__(self, model, websocket=None):
        """Initialize the CLI handler."""
        self.model = model
        self.websocket = websocket
    
    async def generate_extension_with_gemini_cli(self, requirements: str, features: List[str], 
                                               target_websites: List[str], messages: List, 
                                               session_id: str = None, is_fix: bool = False, 
                                               is_improvement: bool = False) -> Extension:
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
            features_text = f"\nFeatures: {', '.join(features)}" if features else ""
            websites_text = f"\nTarget websites: {', '.join(target_websites)}" if target_websites else ""
            
            # Check if this is a modification request (extension already exists)
            existing_files = list(extension_dir.rglob("*")) if extension_dir.exists() else []
            is_modification = len(existing_files) > 0 or is_fix or is_improvement
            
            if is_modification:
                print(f"🔧 Modifying existing extension with {len(existing_files)} files")
                # For modifications, provide context about existing files
                file_list = "\n".join([f"- {f.relative_to(extension_dir)}" for f in existing_files if f.is_file()])
                cli_prompt = f"""
                Modify the existing Chrome extension based on these requirements:
                
                {requirements}{features_text}{websites_text}
                
                The extension currently has these files:
                {file_list}
                
                Please modify the existing files or add new files as needed to implement the requested changes.
                Make sure the extension remains functional and follows Chrome extension best practices.
                
                IMPORTANT: Do NOT generate any PNG image files. Use the existing icon files or create text-based placeholders.
                """
            else:
                print(f"🆕 Creating new extension from scratch")
                # For new extensions, create complete structure
                cli_prompt = f"""
                Create a complete Chrome extension based on these requirements:
                
                {requirements}{features_text}{websites_text}
                
                Generate all necessary files including:
                - manifest.json
                - popup.html, popup.css, popup.js (if needed)
                - content.js (if needed)
                - background.js (if needed)
                - Any other required files
                
                Make sure the extension is functional and follows Chrome extension best practices.
                
                IMPORTANT: Do NOT generate any PNG image files. The icon files will be copied from the existing template.
                """
            
            print(f"📝 Requirements: {requirements[:100]}{'...' if len(requirements) > 100 else ''}")
            
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
            
            # Copy custom icons to the extension directory
            await self._copy_custom_icons(extension_dir)
            
            print(f"📦 Creating extension object with {len(files)} files")
            # Create extension object
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
    
    async def _copy_custom_icons(self, extension_dir: Path):
        """Copy custom icons from the dummy_extension to the new extension directory."""
        try:
            # Source icon directory
            source_icon_dir = Path("dummy_extension")
            
            # Icon files to copy
            icon_files = ["icon16.png", "icon48.png", "icon128.png"]
            
            print(f"🎨 Copying custom icons...")
            for icon_file in icon_files:
                source_path = source_icon_dir / icon_file
                dest_path = extension_dir / icon_file
                
                if source_path.exists():
                    shutil.copy2(source_path, dest_path)
                    print(f"   ✅ Copied {icon_file}")
                else:
                    print(f"   ⚠️  Source icon {icon_file} not found")
            
            # Also copy to images directory if it exists
            images_dir = extension_dir / "images"
            if images_dir.exists():
                for icon_file in icon_files:
                    source_path = source_icon_dir / icon_file
                    dest_path = images_dir / icon_file
                    
                    if source_path.exists():
                        shutil.copy2(source_path, dest_path)
                        print(f"   ✅ Copied {icon_file} to images/")
            
        except Exception as e:
            print(f"⚠️  Error copying icons: {e}")
    
    async def _call_gemini_cli(self, prompt: str, output_dir: Path) -> List[str]:
        """Call Gemini CLI to generate code."""
        import subprocess
        import os
        
        try:
            print(f"🚀 Starting Gemini CLI code generation...")
            print(f"📁 Working directory: {output_dir}")
            
            # Set up environment variables
            env = os.environ.copy()
            # Get API key from the agent's model configuration
            env["GEMINI_API_KEY"] = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
            env["GOOGLE_API_KEY"] = env["GEMINI_API_KEY"]  # Also set this for compatibility
            
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
            print(f"🔑 API Key available: {'✓' if env.get('GEMINI_API_KEY') else '✗'}")
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
        
        # Copy custom icons
        await self._copy_custom_icons(output_dir)
        
        return ["manifest.json", "popup.html", "popup.js"] 