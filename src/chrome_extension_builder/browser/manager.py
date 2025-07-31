"""
Browser manager for Chrome automation and extension testing.
"""

import asyncio
import json
import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from playwright.async_api import async_playwright, Browser, Page
from datetime import datetime

from ..models.extension import Extension
from ..models.browser import BrowserSession, DebugSession, LogAnalysis
from .event_logger import BrowserEventLogger, DebugSessionManager


class BrowserManager:
    """Manages Chrome browser automation for extension testing."""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.context = None
        self.sessions: Dict[str, BrowserSession] = {}
        self.extensions_dir = Path("extensions")  # Directory to store generated extensions
        self.extension_id = None
        self.debug_manager = DebugSessionManager()
        self.current_debug_session: Optional[DebugSession] = None
    
    async def start(self):
        """Start the browser automation with persistent context for extensions."""
        try:
            self.playwright = await async_playwright().start()
            
            # Create extensions directory if it doesn't exist
            self.extensions_dir.mkdir(exist_ok=True)
            
            # Create a temporary user data directory
            self.user_data_dir = tempfile.mkdtemp()
            
            print("🚀 Starting browser with persistent context...")
            
            # Launch persistent context - following Playwright docs exactly
            self.context = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=False,  # Keep visible for testing
                channel='chromium',  # Use chromium channel for extension support
                args=[
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            # Get the first page from the persistent context
            self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()
            
            print("✅ Browser started successfully")
            
        except Exception as e:
            print(f"❌ Error starting browser: {e}")
            raise
    
    async def stop(self):
        """Stop the browser automation."""
        if self.context:
            await self.context.close()
        if self.playwright:
            await self.playwright.stop()
        
        # Clean up temporary user data directory
        if hasattr(self, 'user_data_dir') and os.path.exists(self.user_data_dir):
            try:
                shutil.rmtree(self.user_data_dir)
            except Exception:
                pass
    
    async def create_session(self, extension: Extension) -> BrowserSession:
        """Create a new browser session for testing an extension."""
        session = BrowserSession(
            id=extension.id,
            extension_id=extension.id
        )
        self.sessions[session.id] = session
        return session
    
    async def load_extension_automated(self, extension: Extension) -> Dict[str, Any]:
        """Automatically load an extension using proper Playwright approach."""
        try:
            print(f"🚀 Starting automated extension loading for: {extension.name}")
            
            # 1. Create extension directory and files
            extension_dir = self.extensions_dir / extension.id
            extension_dir.mkdir(exist_ok=True)
            
            # Write manifest.json
            manifest_path = extension_dir / "manifest.json"
            manifest_data = extension.manifest.dict() if extension.manifest else {
                "name": extension.name,
                "version": "1.0.0",
                "description": extension.description,
                "manifest_version": 3,
                "permissions": ["activeTab"],
                "action": {
                    "default_popup": "popup.html"
                },
                "content_scripts": [
                    {
                        "matches": ["<all_urls>"],
                        "js": ["content.js"]
                    }
                ]
            }
            
            with open(manifest_path, 'w') as f:
                json.dump(manifest_data, f, indent=2)
            
            # Write extension files
            for filename, content in extension.files.items():
                file_path = extension_dir / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, 'w') as f:
                    f.write(content)
            
            print(f"✅ Extension files created in: {extension_dir}")
            
            # 2. Close existing context if it exists
            if self.context:
                print("🔄 Closing existing browser context...")
                await self.context.close()
            
            # 3. Launch new persistent context with extension loaded (following Playwright docs)
            print("🚀 Launching new browser context with extension...")
            self.context = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=False,
                channel='chromium',
                args=[
                    f'--disable-extensions-except={extension_dir}',
                    f'--load-extension={extension_dir}',
                    '--disable-component-extensions-with-background-pages'
                ]
            )
            
            # 4. Get the extension ID from service workers (as per Playwright docs)
            print("🔍 Getting extension ID from service workers...")
            try:
                service_workers = self.context.service_workers()
                if service_workers:
                    service_worker = service_workers[0]
                    self.extension_id = service_worker.url.split('/')[2]
                    print(f"✅ Extension ID: {self.extension_id}")
                else:
                    # Wait for service worker to appear
                    print("⏳ Waiting for service worker to appear...")
                    service_worker = await self.context.wait_for_event('serviceworker')
                    self.extension_id = service_worker.url.split('/')[2]
                    print(f"✅ Extension ID: {self.extension_id}")
            except Exception as e:
                print(f"❌ Error getting extension ID: {e}")
                self.extension_id = None
            
            # 5. Get the first page
            self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()
            
            # 6. Test the extension
            print("🧪 Testing extension...")
            test_result = await self._test_extension_on_webpage(extension)
            
            return {
                "success": True,
                "extension_dir": str(extension_dir),
                "extension_id": self.extension_id,
                "extension_loaded": True,
                "test_result": test_result
            }
                
        except Exception as e:
            print(f"❌ Error in automated extension loading: {e}")
            return {"success": False, "error": str(e)}
    
    async def start_with_extension(self, extension: Extension, enable_debug: bool = True):
        """Start the browser with an extension loaded from the beginning."""
        try:
            print(f"🚀 Starting browser with extension: {extension.name}")
            
            # 1. Create extension directory and files with absolute path
            current_dir = Path.cwd()
            extension_dir = current_dir / "extensions" / extension.id
            extension_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"📁 Creating extension files in: {extension_dir}")
            
            # Write manifest.json
            manifest_path = extension_dir / "manifest.json"
            manifest_data = extension.manifest.dict() if extension.manifest else {
                "name": extension.name,
                "version": "1.0.0",
                "description": extension.description,
                "manifest_version": 3,
                "permissions": ["activeTab"],
                "action": {
                    "default_popup": "popup.html"
                },
                "content_scripts": [
                    {
                        "matches": ["<all_urls>"],
                        "js": ["content.js"]
                    }
                ]
            }
            
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest_data, f, indent=2)
            
            print(f"✅ Created manifest.json: {manifest_path}")
            
            # Write extension files
            for filename, content in extension.files.items():
                file_path = extension_dir / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ Created file: {file_path}")
            
            print(f"✅ Extension files created in: {extension_dir}")
            
            # List all files in the extension directory for debugging
            print("📋 Files in extension directory:")
            for file_path in extension_dir.rglob("*"):
                if file_path.is_file():
                    print(f"   - {file_path.relative_to(extension_dir)}")
            
            # Verify manifest.json exists and is readable
            if not manifest_path.exists():
                raise Exception(f"Manifest file was not created: {manifest_path}")
            
            # Read and verify manifest.json content
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest_content = f.read()
                print(f"📄 Manifest.json content:\n{manifest_content}")
            
            # 2. Start Playwright
            self.playwright = await async_playwright().start()
            
            # Create a temporary user data directory
            self.user_data_dir = tempfile.mkdtemp()
            
            print("🚀 Starting browser with extension loaded...")
            print(f"📂 Extension directory (absolute): {extension_dir.absolute()}")
            
            # 3. Launch persistent context with extension loaded (following Playwright docs)
            self.context = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=False,
                channel='chromium',
                args=[
                    f'--disable-extensions-except={extension_dir.absolute()}',
                    f'--load-extension={extension_dir.absolute()}',
                    '--disable-component-extensions-with-background-pages'
                ]
            )
            
            # 4. Get the extension ID from service workers (as per Playwright docs)
            print("🔍 Getting extension ID from service workers...")
            try:
                service_workers = self.context.service_workers()
                if service_workers:
                    service_worker = service_workers[0]
                    self.extension_id = service_worker.url.split('/')[2]
                    print(f"✅ Extension ID: {self.extension_id}")
                else:
                    # Wait for service worker to appear
                    print("⏳ Waiting for service worker to appear...")
                    service_worker = await self.context.wait_for_event('serviceworker')
                    self.extension_id = service_worker.url.split('/')[2]
                    print(f"✅ Extension ID: {self.extension_id}")
            except Exception as e:
                print(f"❌ Error getting extension ID: {e}")
                self.extension_id = None
            
            # 5. Get the first page
            self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()
            
            # 6. Start debug session if enabled
            if enable_debug and self.extension_id:
                session_id = f"debug_{extension.id}_{int(datetime.now().timestamp())}"
                self.current_debug_session = await self.debug_manager.start_debug_session(
                    session_id, extension.id, self.page, self.context
                )
                print(f"🔍 Debug session started: {session_id}")
            
            print("✅ Browser started with extension successfully")
            
        except Exception as e:
            print(f"❌ Error starting browser with extension: {e}")
            raise
    
    async def start_with_dummy_extension(self):
        """Start the browser with the dummy extension loaded from the beginning."""
        try:
            print("🚀 Starting browser with dummy extension...")
            
            # Get the path to the dummy extension
            current_dir = Path.cwd()
            dummy_extension_path = current_dir / "dummy_extension"
            
            if not dummy_extension_path.exists():
                raise Exception("Dummy extension directory not found")
            
            print(f"✅ Dummy extension found at: {dummy_extension_path}")
            
            # Start Playwright
            self.playwright = await async_playwright().start()
            
            # Create a temporary user data directory
            self.user_data_dir = tempfile.mkdtemp()
            
            print("🚀 Starting browser with dummy extension loaded...")
            
            # Launch persistent context with dummy extension loaded
            self.context = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=False,
                channel='chromium',
                args=[
                    f'--disable-extensions-except={dummy_extension_path}',
                    f'--load-extension={dummy_extension_path}',
                    '--disable-component-extensions-with-background-pages'
                ]
            )
            
            # Get the extension ID from service workers
            print("🔍 Getting dummy extension ID from service workers...")
            try:
                service_workers = self.context.service_workers()
                if service_workers:
                    service_worker = service_workers[0]
                    self.extension_id = service_worker.url.split('/')[2]
                    print(f"✅ Dummy Extension ID: {self.extension_id}")
                else:
                    # Wait for service worker to appear
                    print("⏳ Waiting for service worker to appear...")
                    service_worker = await self.context.wait_for_event('serviceworker')
                    self.extension_id = service_worker.url.split('/')[2]
                    print(f"✅ Dummy Extension ID: {self.extension_id}")
            except Exception as e:
                print(f"❌ Error getting dummy extension ID: {e}")
                self.extension_id = None
            
            # Get the first page
            self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()
            
            print("✅ Browser started with dummy extension successfully")
            
        except Exception as e:
            print(f"❌ Error starting browser with dummy extension: {e}")
            raise
    
    async def _test_extension_on_webpage(self, extension: Extension) -> Dict[str, Any]:
        """Test the extension on a webpage."""
        try:
            print("🌐 Navigating to test webpage...")
            await self.page.goto("https://www.google.com")
            await self.page.wait_for_load_state('networkidle')
            
            # Wait for content script to load
            await self.page.wait_for_timeout(3000)
            
            # Check for any extension indicators
            page_content = await self.page.content()
            
            # Look for common extension indicators
            indicators = [
                "extension",
                "chrome-extension",
                "content script",
                extension.name.lower()
            ]
            
            found_indicators = []
            for indicator in indicators:
                if indicator.lower() in page_content.lower():
                    found_indicators.append(indicator)
            
            # Take a screenshot for verification
            screenshot_path = f"extension_test_{extension.id}.png"
            await self.page.screenshot(path=screenshot_path)
            
            # Test popup if extension ID is available
            popup_test_result = None
            if self.extension_id:
                try:
                    popup_url = f"chrome-extension://{self.extension_id}/popup.html"
                    popup_page = await self.context.new_page()
                    await popup_page.goto(popup_url)
                    await popup_page.wait_for_load_state('networkidle')
                    
                    popup_content = await popup_page.content()
                    popup_test_result = {
                        "success": True,
                        "popup_loaded": "popup" in popup_content.lower(),
                        "popup_content_length": len(popup_content)
                    }
                    
                    await popup_page.close()
                except Exception as e:
                    popup_test_result = {
                        "success": False,
                        "error": str(e)
                    }
            
            return {
                "success": True,
                "indicators_found": found_indicators,
                "screenshot": screenshot_path,
                "page_title": await self.page.title(),
                "popup_test": popup_test_result
            }
            
        except Exception as e:
            print(f"❌ Error testing extension: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def load_dummy_extension(self) -> bool:
        """Load the dummy extension for testing."""
        try:
            # Use the existing page from persistent context
            if not self.page:
                self.page = await self.context.new_page()
            
            # Test 1: Navigate to the extension popup page
            if hasattr(self, 'extension_id') and self.extension_id:
                try:
                    popup_url = f"chrome-extension://{self.extension_id}/popup.html"
                    await self.page.goto(popup_url)
                    await self.page.wait_for_load_state('networkidle')
                    
                    # Check if popup content is loaded
                    popup_content = await self.page.content()
                    if "Dummy Extension" in popup_content:
                        return True
                    else:
                        return False
                except Exception as e:
                    return False
            else:
                return False
                
        except Exception as e:
            print(f"Error loading dummy extension: {e}")
            return False
    
    async def navigate_to(self, url: str, session_id: str):
        """Navigate to a URL in the browser."""
        if not self.page:
            raise Exception("No active browser page")
        
        await self.page.goto(url)
        
        session = self.sessions.get(session_id)
        if session:
            session.url = url
            session.updated_at = datetime.utcnow()
    
    async def get_console_logs(self, session_id: str) -> List[Dict[str, Any]]:
        """Get console logs from the browser."""
        if not self.page:
            return []
        
        # This is a simplified version. In production, you'd need to
        # properly capture console logs using CDP or similar
        return []
    
    async def execute_script(self, script: str, session_id: str) -> Any:
        """Execute JavaScript in the browser."""
        if not self.page:
            raise Exception("No active browser page")
        
        return await self.page.evaluate(script)
    
    async def take_screenshot(self, session_id: str) -> bytes:
        """Take a screenshot of the current page."""
        if not self.page:
            raise Exception("No active browser page")
        
        return await self.page.screenshot() 

    async def test_extension_on_webpage(self) -> bool:
        """Test the extension on a regular webpage to verify content script functionality."""
        try:
            # Navigate to a test page
            await self.page.goto("https://www.google.com")
            
            # Wait for page to load
            await self.page.wait_for_load_state('networkidle')
            
            # Wait a bit for content script to load
            await self.page.wait_for_timeout(3000)
            
            # Check if our extension indicator appears
            try:
                indicator_found = await self.page.wait_for_selector(
                    '#dummy-extension-indicator', 
                    timeout=5000
                )
                if indicator_found:
                    return True
                else:
                    return False
            except Exception as e:
                return False
                
        except Exception as e:
            print(f"Error testing extension on webpage: {e}")
            return False
    
    async def get_debug_logs(self, session_id: str = None) -> Optional[LogAnalysis]:
        """Get debug logs for analysis."""
        if not session_id and self.current_debug_session:
            session_id = self.current_debug_session.id
        
        if session_id:
            try:
                return await self.debug_manager.analyze_logs_for_ai(session_id)
            except Exception as e:
                print(f"❌ Error getting debug logs: {e}")
                return None
        return None
    
    async def stop_debug_session(self, session_id: str = None):
        """Stop debug session and save logs."""
        if not session_id and self.current_debug_session:
            session_id = self.current_debug_session.id
        
        if session_id:
            await self.debug_manager.stop_debug_session(session_id)
            if self.current_debug_session and self.current_debug_session.id == session_id:
                self.current_debug_session = None
    
    def get_debug_summary(self, session_id: str = None) -> Dict[str, Any]:
        """Get a summary of debug session."""
        if not session_id and self.current_debug_session:
            session_id = self.current_debug_session.id
        
        if session_id:
            logger = self.debug_manager.get_session_logs(session_id)
            if logger:
                return logger.get_log_summary()
        return {} 