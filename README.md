# Chrome Extension Builder

A modern, AI-powered Chrome Extension Builder with a sleek interface similar to Replit. Built with FastAPI, Tailwind CSS, and Monaco Editor.

## 🚀 Features

- **AI-Powered Code Generation**: Uses Google's Gemini CLI to generate Chrome extensions
- **Real-time Chat Interface**: WebSocket-based chat with streaming CLI output
- **Modern Code Editor**: Monaco Editor with syntax highlighting
- **File Explorer**: Visual file tree with syntax-colored icons
- **Browser Testing**: Integrated Chrome browser automation for extension testing
- **Responsive Design**: Modern UI with Tailwind CSS and smooth animations

## 🛠️ Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **WebSockets**: Real-time communication
- **Playwright**: Browser automation
- **Google Gemini CLI**: AI code generation

### Frontend
- **Tailwind CSS**: Utility-first CSS framework
- **Monaco Editor**: VS Code-like code editor
- **Font Awesome**: Icon library
- **Inter Font**: Modern typography

## 📁 Project Structure

```
src/chrome_extension_builder/
├── static/
│   ├── css/
│   │   └── tailwind.css          # Custom Tailwind styles
│   └── js/
│       └── app.js                # Modern JavaScript app
├── templates/
│   └── index.html                # Main HTML template
├── chat/
│   ├── agent.py                  # AI chat agent
│   └── routes.py                 # Chat API routes
├── browser/
│   └── manager.py                # Browser automation
├── models/                       # Data models
└── main.py                       # FastAPI app entry point
```

## 🚀 Quick Start

### Prerequisites

1. **Python 3.9+**
2. **Node.js 16+** (for Tailwind CSS)
3. **Google Gemini CLI** installed globally
4. **Chrome/Chromium** for browser testing

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd chrome-extension-builder
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Node.js dependencies**
   ```bash
   npm install
   ```

4. **Set up environment variables**
   ```bash
   # Create .env file
   echo "GEMINI_API_KEY=your_gemini_api_key_here" > .env
   ```

5. **Build Tailwind CSS** (optional, for development)
   ```bash
   npm run build
   ```

### Running the Application

1. **Start the development server**
   ```bash
   npm run dev
   # or
   python -m uvicorn src.chrome_extension_builder.main:app --reload
   ```

2. **Open your browser**
   Navigate to `http://localhost:8000`

## 🎨 UI Features

### Modern Design
- **Dark Theme**: Professional dark color scheme
- **Gradient Accents**: Beautiful gradient buttons and headers
- **Smooth Animations**: Fade-in and slide-in effects
- **Responsive Layout**: Works on desktop and tablet

### Chat Interface
- **Real-time Messaging**: Instant message delivery
- **CLI Output Streaming**: Live Gemini CLI output display
- **Extension Info Cards**: Beautiful extension generation summaries
- **Connection Status**: Visual connection indicators

### Code Editor
- **Monaco Editor**: Full-featured code editor
- **Syntax Highlighting**: Support for JSON, HTML, CSS, JS
- **File Tree**: Visual file explorer with colored icons
- **Active File Highlighting**: Clear indication of selected files

### Browser Controls
- **Load Extension**: Load generated extensions into Chrome
- **Test Browser**: Automated browser testing
- **Close Browser**: Clean browser shutdown

## 🔧 Configuration

### Environment Variables

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Optional (for compatibility)
GOOGLE_API_KEY=your_google_api_key_here
```

### Tailwind Configuration

The project uses a custom Tailwind configuration with:
- Custom color palette
- Inter font family
- Custom animations
- Glow effects

## 🎯 Usage

1. **Start a Chat Session**: The app automatically creates a new session
2. **Describe Your Extension**: Tell the AI what Chrome extension you want to build
3. **Watch Code Generation**: See real-time CLI output as the AI generates code
4. **Explore Files**: Click on files in the tree to view their contents
5. **Test Your Extension**: Use the browser controls to test your extension

## 🐛 Troubleshooting

### Common Issues

1. **Gemini CLI not found**
   - Ensure Gemini CLI is installed globally: `npm install -g @google/gemini`
   - Check your API key is set correctly

2. **Browser automation fails**
   - Ensure Chrome/Chromium is installed
   - Check Playwright installation: `playwright install chromium`

3. **Static files not loading**
   - Ensure the static directory exists
   - Check FastAPI static file mounting

4. **WebSocket connection fails**
   - Check if the server is running on the correct port
   - Ensure no firewall is blocking WebSocket connections

### Development Tips

1. **Hot Reload**: Use `npm run dev` for automatic server restart
2. **CSS Changes**: Run `npm run build` to rebuild Tailwind CSS
3. **Debug Mode**: Check browser console for detailed logs
4. **Network Tab**: Monitor WebSocket connections in browser dev tools

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- **Google Gemini**: For AI-powered code generation
- **Monaco Editor**: For the excellent code editing experience
- **Tailwind CSS**: For the utility-first CSS framework
- **FastAPI**: For the modern Python web framework 