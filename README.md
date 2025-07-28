# Chrome Extension Builder

A Replit-like platform for building Chrome extensions through an intuitive chat interface. Users can describe their extension ideas, generate code automatically, test in a simulated browser environment, and iterate on their creations.

## 🚀 Features

- **Chat Interface**: Natural language interaction for describing extension requirements
- **AI-Powered Code Generation**: Automatic extension code generation using Google Gemini
- **Browser Automation**: Real-time testing in a simulated Chrome environment using Playwright
- **Extension Management**: Create, load, and test extensions seamlessly
- **Modern UI**: Beautiful, responsive interface with real-time updates

## 🏗️ Architecture

The application consists of three main components:

1. **Chat Interface**: User interaction and requirements gathering
2. **Chrome Browser Environment**: Extension loading and testing using Playwright
3. **Background Coding Agent**: AI-powered code generation (Gemini)

## 🛠️ Technical Stack

- **Backend**: Python FastAPI
- **Frontend**: HTML/CSS/JavaScript
- **Browser Automation**: Playwright
- **AI**: Google Generative AI (Gemini)
- **Package Management**: uv
- **Data Models**: Pydantic

## 📦 Installation

### Prerequisites

- Python 3.11+
- uv package manager
- Git

### Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd extension-env
   ```

2. **Install dependencies**:
   ```bash
   uv venv
   uv venv activate
   uv pip install -r requirements.txt
   ```

3. **Install Playwright browsers**:
   ```bash
   playwright install chromium
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your Google Gemini API key
   ```

## 🚀 Usage

### Starting the Application

1. **Activate the virtual environment**:
   ```bash
   uv venv activate
   ```

2. **Run the FastAPI server**:
   ```bash
   python run.py
   ```

3. **Access the application**:
   Open your browser and navigate to `http://localhost:8000`

### Using the Application

1. **Chat Interface**: Describe your extension idea in natural language
2. **Browser Environment**: Use the browser controls to test extensions
3. **Extension Testing**: Load and test extensions in the simulated Chrome environment

## 🔧 API Endpoints

### Chat Endpoints
- `POST /chat/sessions` - Create a new chat session
- `GET /chat/sessions/{session_id}` - Get chat session details
- `POST /chat/sessions/{session_id}/messages` - Send a message

### Extension Endpoints
- `POST /api/extensions` - Create a new extension
- `GET /api/extensions/{extension_id}` - Get extension details
- `PUT /api/extensions/{extension_id}` - Update extension
- `POST /api/extensions/{extension_id}/files` - Upload extension files

### Browser Endpoints
- `POST /api/browser/load-dummy-extension` - Load test extension
- `POST /api/browser/test` - Test browser functionality
- `POST /api/browser/close` - Close browser session

## 🧪 Testing

### Dummy Extension

The project includes a test extension (`dummy_extension/`) that demonstrates:

- **Popup Interface**: Interactive popup with buttons and styling
- **Content Script**: Visual indicators and page modifications
- **Background Script**: Service worker functionality

### Browser Testing

The application provides comprehensive browser testing:

1. **Extension Loading**: Automatically loads extensions using Playwright's official method
2. **Popup Testing**: Validates extension popup functionality
3. **Content Script Testing**: Verifies extension behavior on web pages
4. **Visual Indicators**: Shows extension activity through UI elements

## 🔍 Browser Automation

The browser automation uses Playwright's official Chrome extension support:

- **Persistent Context**: Required for Chrome extension functionality
- **Extension Loading**: Uses `--load-extension` and `--disable-extensions-except` arguments
- **Extension ID Detection**: Extracts extension ID from service workers
- **Comprehensive Testing**: Tests both popup and content script functionality

## 📁 Project Structure

```
extension-env/
├── src/
│   └── chrome_extension_builder/
│       ├── api/              # API routes
│       ├── browser/          # Browser automation
│       ├── chat/             # Chat functionality
│       ├── codegen/          # AI code generation
│       ├── models/           # Pydantic data models
│       └── templates/        # HTML templates
├── dummy_extension/          # Test extension
├── scratchpad.md            # Development progress
├── plan.md                  # Project planning
└── README.md               # This file
```

## 🚧 Development Status

### ✅ Completed
- [x] Project setup and basic FastAPI structure
- [x] Chat interface with WebSocket support
- [x] Browser automation with Playwright
- [x] Dummy extension creation
- [x] Chrome extension loading implementation

### 🔄 In Progress
- [ ] AI integration with chat interface
- [ ] Extension code generation
- [ ] Database integration

### 📋 Planned
- [ ] User authentication
- [ ] Extension marketplace
- [ ] Advanced browser automation
- [ ] Real-time collaboration
- [ ] Extension analytics
- [ ] Multi-language support

## 🐛 Troubleshooting

### Common Issues

1. **Browser not starting**: Ensure Playwright browsers are installed
2. **Extension not loading**: Check that the extension path is correct
3. **API errors**: Verify that all dependencies are installed

### Debug Mode

Enable debug logging by setting environment variables:
```bash
export DEBUG=1
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [Playwright](https://playwright.dev/) for browser automation
- [Google Gemini](https://ai.google.dev/) for AI code generation
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework 