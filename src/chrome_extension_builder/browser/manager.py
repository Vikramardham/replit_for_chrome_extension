"""
Browser manager for Chrome automation and extension testing.
"""

import asyncio
import json
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any
from playwright.async_api import async_playwright, Browser, Page
from datetime import datetime

from ..models.extension import Extension
from ..models.browser import BrowserSession


class BrowserManager:
    """Manages Chrome browser automation for extension testing."""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.context = None  # Add persistent context
        self.sessions: Dict[str, BrowserSession] = {}
    
    async def start(self):
        """Start the browser automation with persistent context for extensions."""
        try:
            self.playwright = await async_playwright().start()
            
            # Use persistent context for Chrome extensions as per Playwright docs
            import tempfile
            import os
            
            # Create a temporary user data directory
            self.user_data_dir = tempfile.mkdtemp()
            
            # Get the absolute path to the dummy_extension folder
            current_dir = os.getcwd()
            dummy_extension_path = os.path.join(current_dir, "dummy_extension")
            
            # Launch persistent context - following official Playwright docs exactly
            self.context = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=False,  # Keep visible for testing
                channel='chromium',  # Use chromium channel for extension support
                args=[
                    f'--disable-extensions-except={dummy_extension_path}',
                    f'--load-extension={dummy_extension_path}'
                ]
            )
            
            # Get the first page from the persistent context
            self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()
            
            # Get the extension ID from service workers (as per docs)
            try:
                service_workers = self.context.service_workers()
                if service_workers:
                    service_worker = service_workers[0]
                    extension_id = service_worker.url.split('/')[2]
                    self.extension_id = extension_id
                else:
                    # Wait for service worker to appear
                    service_worker = await self.context.wait_for_event('serviceworker')
                    extension_id = service_worker.url.split('/')[2]
                    self.extension_id = extension_id
            except Exception as e:
                self.extension_id = None
                
        except Exception as e:
            print(f"Error starting browser: {e}")
            raise
    
    async def stop(self):
        """Stop the browser automation."""
        if self.context:
            await self.context.close()
        if self.playwright:
            await self.playwright.stop()
        
        # Clean up temporary user data directory
        if hasattr(self, 'user_data_dir') and os.path.exists(self.user_data_dir):
            import shutil
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
    
    async def load_extension(self, extension: Extension) -> bool:
        """Load an extension in the browser."""
        try:
            # Create temporary directory for extension files
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Write manifest.json
                manifest_path = temp_path / "manifest.json"
                with open(manifest_path, 'w') as f:
                    json.dump(extension.manifest.dict(), f, indent=2)
                
                # Write extension files
                for filename, content in extension.files.items():
                    file_path = temp_path / filename
                    with open(file_path, 'w') as f:
                        f.write(content)
                
                # Use the existing page from persistent context
                if not self.page:
                    self.page = await self.context.new_page()
                
                # Load extension
                await self.page.goto("chrome://extensions/")
                await self.page.wait_for_load_state('networkidle')
                
                # Enable developer mode
                developer_mode_found = False
                selectors = [
                    '[aria-label="Developer mode"]',
                    'input[type="checkbox"]',
                    'input[name="developer"]',
                    '.developer-mode-toggle',
                    'input[role="checkbox"]',
                    'input[type="checkbox"][aria-label*="Developer"]',
                    'input[type="checkbox"][aria-label*="developer"]'
                ]
                
                for selector in selectors:
                    try:
                        element = await self.page.wait_for_selector(selector, timeout=2000)
                        if element:
                            await element.click()
                            developer_mode_found = True
                            break
                    except Exception:
                        continue
                
                # Wait for developer mode to take effect
                await self.page.wait_for_timeout(2000)
                
                # Click load unpacked button
                load_unpacked_found = False
                load_selectors = [
                    '[aria-label="Load unpacked"]',
                    'button:has-text("Load unpacked")',
                    'button:has-text("LOAD UNPACKED")',
                    'button[data-testid="load-unpacked"]',
                    'button:has-text("Load")',
                    'button[aria-label*="Load unpacked"]',
                    'button[aria-label*="load unpacked"]'
                ]
                
                for selector in load_selectors:
                    try:
                        element = await self.page.wait_for_selector(selector, timeout=2000)
                        if element:
                            await element.click()
                            load_unpacked_found = True
                            break
                    except Exception:
                        continue
                
                # Wait for file dialog to appear
                await self.page.wait_for_timeout(3000)
                
                session = self.sessions.get(extension.id)
                if session:
                    session.status = "loaded"
                    session.url = self.page.url
                
                return True
                
        except Exception as e:
            print(f"Error loading extension: {e}")
            return False
    
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