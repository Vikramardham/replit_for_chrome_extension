#!/usr/bin/env python3
"""
Simple script to run the Chrome Extension Builder application.
"""

import uvicorn
from src.chrome_extension_builder.main import app

if __name__ == "__main__":
    print("🚀 Starting Chrome Extension Builder...")
    print("📱 Open http://localhost:8000 in your browser")
    print("🛑 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 