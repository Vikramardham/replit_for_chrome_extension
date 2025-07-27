"""
Main application entry point for Chrome Extension Builder.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

from .api.routes import router as api_router
from .chat.routes import router as chat_router

# Load environment variables
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("Starting Chrome Extension Builder...")
    yield
    # Shutdown
    print("Shutting down Chrome Extension Builder...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Chrome Extension Builder",
        description="A Replit-like website for building Chrome extensions through chat interface",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Mount static files
    app.mount("/static", StaticFiles(directory="src/chrome_extension_builder/static"), name="static")

    # Include routers
    app.include_router(api_router, prefix="/api")
    app.include_router(chat_router, prefix="/chat")

    # Templates
    templates = Jinja2Templates(directory="src/chrome_extension_builder/templates")

    @app.get("/")
    async def root(request: Request):
        """Root endpoint serving the main chat interface."""
        return templates.TemplateResponse("index.html", {"request": request})
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "message": "Chrome Extension Builder is running"}

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 