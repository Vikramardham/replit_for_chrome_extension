"""
AI code generation agent for Chrome extensions.
"""

import os
import json
from typing import Dict, List, Optional, Any
from google.generativeai import GenerativeModel
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from ..models.extension import Extension, ExtensionManifest
from ..models.chat import ChatMessage, MessageRole


class CodeGenerationAgent:
    """AI agent for generating Chrome extension code."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the code generation agent."""
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google API key is required")
        
        # Configure the model
        self.model = GenerativeModel(
            model_name="gemini-pro",
            generation_config={
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 8192,
            },
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            },
        )
    
    async def analyze_requirements(self, messages: List[ChatMessage]) -> Dict[str, Any]:
        """Analyze chat messages to extract extension requirements."""
        # Combine all user messages
        user_messages = [msg.content for msg in messages if msg.role == MessageRole.USER]
        combined_content = "\n".join(user_messages)
        
        prompt = f"""
        Analyze the following user requirements for a Chrome extension and extract key information:
        
        User Requirements:
        {combined_content}
        
        Please provide a JSON response with the following structure:
        {{
            "name": "Extension name",
            "description": "Extension description",
            "permissions": ["list", "of", "required", "permissions"],
            "host_permissions": ["list", "of", "host", "permissions"],
            "features": ["list", "of", "main", "features"],
            "content_scripts": ["list", "of", "content", "script", "files"],
            "background_scripts": ["list", "of", "background", "script", "files"],
            "popup_files": ["list", "of", "popup", "files"],
            "action_type": "popup|background|content_script"
        }}
        """
        
        response = await self.model.generate_content_async(prompt)
        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            # Fallback to basic extraction
            return {
                "name": "Chrome Extension",
                "description": "A Chrome extension based on user requirements",
                "permissions": [],
                "host_permissions": [],
                "features": [],
                "content_scripts": [],
                "background_scripts": [],
                "popup_files": [],
                "action_type": "popup"
            }
    
    async def generate_manifest(self, requirements: Dict[str, Any]) -> ExtensionManifest:
        """Generate a Chrome extension manifest based on requirements."""
        prompt = f"""
        Generate a Chrome extension manifest.json file based on these requirements:
        {json.dumps(requirements, indent=2)}
        
        Return only the JSON manifest object, no additional text.
        """
        
        response = await self.model.generate_content_async(prompt)
        try:
            manifest_data = json.loads(response.text)
            return ExtensionManifest(**manifest_data)
        except (json.JSONDecodeError, Exception):
            # Fallback to basic manifest
            return ExtensionManifest(
                name=requirements.get("name", "Chrome Extension"),
                description=requirements.get("description", "A Chrome extension"),
                permissions=requirements.get("permissions", []),
                host_permissions=requirements.get("host_permissions", [])
            )
    
    async def generate_file_content(self, filename: str, requirements: Dict[str, Any], file_type: str) -> str:
        """Generate content for a specific file."""
        prompt = f"""
        Generate a {file_type} file for a Chrome extension with these requirements:
        {json.dumps(requirements, indent=2)}
        
        File: {filename}
        Type: {file_type}
        
        Generate the complete file content. Return only the code, no explanations.
        """
        
        response = await self.model.generate_content_async(prompt)
        return response.text
    
    async def generate_extension(self, messages: List[ChatMessage]) -> Extension:
        """Generate a complete Chrome extension from chat messages."""
        # Analyze requirements
        requirements = await self.analyze_requirements(messages)
        
        # Generate manifest
        manifest = await self.generate_manifest(requirements)
        
        # Generate files
        files = {}
        
        # Generate popup HTML if needed
        if requirements.get("action_type") == "popup":
            popup_html = await self.generate_file_content(
                "popup.html", requirements, "HTML"
            )
            files["popup.html"] = popup_html
            
            popup_css = await self.generate_file_content(
                "popup.css", requirements, "CSS"
            )
            files["popup.css"] = popup_css
            
            popup_js = await self.generate_file_content(
                "popup.js", requirements, "JavaScript"
            )
            files["popup.js"] = popup_js
        
        # Generate content scripts
        for script in requirements.get("content_scripts", []):
            content = await self.generate_file_content(script, requirements, "JavaScript")
            files[script] = content
        
        # Generate background scripts
        for script in requirements.get("background_scripts", []):
            content = await self.generate_file_content(script, requirements, "JavaScript")
            files[script] = content
        
        # Create extension object
        extension = Extension(
            id=f"ext_{len(files)}",  # Simple ID generation
            name=requirements.get("name", "Chrome Extension"),
            description=requirements.get("description", "A Chrome extension"),
            manifest=manifest,
            files=files
        )
        
        return extension
    
    async def improve_extension(self, extension: Extension, feedback: str) -> Extension:
        """Improve an extension based on user feedback."""
        prompt = f"""
        Improve this Chrome extension based on the following feedback:
        
        Current Extension:
        {json.dumps(extension.dict(), indent=2)}
        
        User Feedback:
        {feedback}
        
        Return the improved extension as JSON with the same structure.
        """
        
        response = await self.model.generate_content_async(prompt)
        try:
            improved_data = json.loads(response.text)
            return Extension(**improved_data)
        except (json.JSONDecodeError, Exception):
            return extension  # Return original if improvement fails 