# Chrome Extension Builder

A Replit-like website for building Chrome extensions through a chat interface. Users can describe their extension requirements in natural language, and the AI will generate the code, load it in a browser environment, and test it.

## Features

- **Chat Interface**: Natural language interaction to describe extension requirements
- **AI Code Generation**: Uses Google's Gemini AI to generate Chrome extension code
- **Browser Automation**: Automated Chrome browser for testing extensions
- **Real-time Testing**: Load and test extensions in a controlled environment
- **Iterative Development**: Improve extensions based on feedback

## Architecture

1. **Chat Interface**: User interaction and requirements gathering
2. **Chrome Browser Environment**: Extension loading and testing environment
3. **Background Coding Agent**: AI-powered code generation (Gemini CLI)

## Tech Stack

- **Backend**: Python FastAPI
- **Frontend**: HTML/CSS/JavaScript with modern UI
- **Browser Automation**: Playwright
- **AI Code Generation**: Google Generative AI (Gemini)
- **Package Management**: uv

## Project Structure

```
src/chrome_extension_builder/
├── api/              # API routes for extension management
├── browser/          # Browser automation components
├── chat/             # Chat interface components
├── codegen/          # AI code generation agent
├── models/           # Data models
├── static/           # Static files
├── templates/        # HTML templates
└── main.py          # Application entry point
```

## Setup

1. **Install Dependencies**:
   ```bash
   uv venv
   source .venv/Scripts/activate  # On Windows
   uv add fastapi uvicorn pydantic selenium playwright google-generativeai python-multipart websockets jinja2 aiofiles python-dotenv
   ```

2. **Install Playwright Browsers**:
   ```bash
   playwright install chromium
   ```

3. **Set Environment Variables**:
   Create a `.env` file:
   ```
   GOOGLE_API_KEY=your_gemini_api_key_here
   ```

4. **Run the Application**:
   ```bash
   python -m src.chrome_extension_builder.main
   ```

5. **Access the Application**:
   Open http://localhost:8000 in your browser

## Usage

1. **Start a Chat Session**: The application creates a new chat session automatically
2. **Describe Your Extension**: Tell the AI what kind of Chrome extension you want to build
3. **Review Generated Code**: The AI will generate the extension code based on your requirements
4. **Test the Extension**: Use the browser environment to load and test your extension
5. **Iterate**: Provide feedback to improve the extension

## API Endpoints

### Chat
- `POST /chat/sessions` - Create a new chat session
- `GET /chat/sessions/{session_id}` - Get chat session
- `POST /chat/messages` - Send a message
- `GET /chat/sessions` - List all sessions

### Extensions
- `POST /api/extensions` - Create a new extension
- `GET /api/extensions/{extension_id}` - Get extension details
- `PUT /api/extensions/{extension_id}` - Update extension
- `POST /api/extensions/{extension_id}/files` - Upload extension files

### Browser
- `POST /api/browser/sessions` - Create browser session
- `POST /api/browser/sessions/{session_id}/load` - Load extension in browser
- `GET /api/browser/sessions/{session_id}/logs` - Get browser logs

## Development

### Code Style
- Use Black for code formatting
- Use isort for import sorting
- Follow PEP 8 guidelines

### Testing
- Run tests with pytest
- Ensure all endpoints are covered

### Adding New Features
1. Create new models in `models/`
2. Add API routes in `api/routes.py`
3. Update the frontend in `templates/index.html`
4. Test thoroughly

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Roadmap

- [ ] Database integration (PostgreSQL)
- [ ] User authentication
- [ ] Extension marketplace
- [ ] Advanced browser automation
- [ ] Real-time collaboration
- [ ] Extension analytics
- [ ] Multi-language support 