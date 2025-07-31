// Modern Chrome Extension Builder App
class ChromeExtensionBuilder {
    constructor() {
        this.editor = null;
        this.currentSession = null;
        this.currentExtension = null;
        this.currentExtensionId = null;
        this.websocket = null;
        this.isConnected = false;
        this.openTabs = [];
        this.activeTab = null;
        this.editorModels = new Map();
        
        this.init();
    }
    
    async init() {
        await this.initializeMonacoEditor();
        await this.initializeSession();
        this.setupEventListeners();
        this.setupWebSocket();
        this.setupTabSystem();
    }
    
    async initializeMonacoEditor() {
        return new Promise((resolve) => {
            require.config({ 
                paths: { 
                    vs: 'https://unpkg.com/monaco-editor@0.45.0/min/vs' 
                } 
            });
            
            require(['vs/editor/editor.main'], () => {
                this.editor = monaco.editor.create(document.getElementById('monaco-editor'), {
                    value: '// Your extension code will appear here\n// Select a file from the file tree to view its contents',
                    language: 'javascript',
                    theme: 'vs-dark',
                    automaticLayout: true,
                    minimap: { enabled: false },
                    fontSize: 14,
                    lineNumbers: 'on',
                    roundedSelection: false,
                    scrollBeyondLastLine: false,
                    readOnly: false,
                    cursorStyle: 'line',
                    contextmenu: true,
                    mouseWheelZoom: true,
                    quickSuggestions: true,
                    suggestOnTriggerCharacters: true,
                    acceptSuggestionOnEnter: 'on'
                });
                
                // Start with editor hidden
                document.getElementById('monaco-editor').classList.add('hidden');
                document.getElementById('editor-tabs').classList.add('hidden');
                
                resolve();
            });
        });
    }
    
    async initializeSession() {
        try {
            const response = await fetch('/chat/sessions', { method: 'POST' });
            const session = await response.json();
            this.currentSession = session.id;
            console.log('Session initialized:', this.currentSession);
        } catch (error) {
            console.error('Failed to initialize session:', error);
            this.showNotification('Failed to initialize session', 'error');
        }
    }
    
    setupWebSocket() {
        if (!this.currentSession) return;
        
        this.websocket = new WebSocket(`ws://localhost:8000/chat/ws/${this.currentSession}`);
        
        this.websocket.onopen = () => {
            console.log('WebSocket connected');
            this.isConnected = true;
            this.updateConnectionStatus(true);
        };
        
        this.websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };
        
        this.websocket.onclose = () => {
            console.log('WebSocket disconnected');
            this.isConnected = false;
            this.updateConnectionStatus(false);
        };
        
        this.websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.showNotification('WebSocket connection error', 'error');
        };
    }
    
    handleWebSocketMessage(data) {
        console.log('WebSocket message received:', data);
        
        if (data.type === 'message') {
            this.addMessage(data.content, 'assistant');
            
            if (data.action === 'extension_generated' && data.extension) {
                console.log('Extension received:', data.extension);
                console.log('Extension files:', data.extension.files);
                
                // Show extension info
                this.currentExtension = data.extension;
                this.currentExtensionId = data.extension.id;
                this.displayExtensionInfo(data.extension);
                this.updateFileTree(data.extension.files);
                
                // Show success message with manual loading instructions
                this.showNotification(`
                    <div class="mb-4">
                        <h4 class="text-lg font-semibold mb-2">✅ Extension Generated Successfully!</h4>
                        <p class="mb-2">Extension "${data.extension.name}" has been created with ${Object.keys(data.extension.files).length} files.</p>
                        <p class="text-sm text-gray-300">Click "Load Extension in Browser" to start the browser with the extension loaded.</p>
                    </div>
                `, 'success');
            } else if (data.action === 'debug_analysis' && data.debug_session_id) {
                console.log('Debug analysis completed:', data);
                
                // Update debug session ID
                this.currentDebugSessionId = data.debug_session_id;
                
                // Show debug summary if available
                if (data.log_summary) {
                    this.showNotification(`
                        <div class="mb-4">
                            <h4 class="text-lg font-semibold mb-2">🔍 Debug Analysis Complete!</h4>
                            <p class="mb-2">Analyzed ${data.log_summary.total_events} events, ${data.log_summary.total_errors} errors, and ${data.log_summary.total_console_logs} console logs.</p>
                            <p class="text-sm text-gray-300">Check the chat for detailed analysis and recommendations.</p>
                        </div>
                    `, 'success');
                }
            }
        } else if (data.type === 'cli_output') {
            this.addCliOutput(data.content, data.stream);
        }
    }
    
    addMessage(content, type) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const icon = type === 'user' ? 'fa-user' : 'fa-robot';
        messageDiv.innerHTML = `<i class="fas ${icon} mr-2"></i> ${content}`;
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    addCliOutput(content, stream) {
        const messagesContainer = document.getElementById('chat-messages');
        
        let cliContainer = messagesContainer.querySelector('.cli-output-container');
        if (!cliContainer) {
            cliContainer = document.createElement('div');
            cliContainer.className = 'cli-output-container card p-4 mb-4';
            cliContainer.innerHTML = `
                <div class="flex items-center gap-2 mb-2 text-sm font-medium">
                    <i class="fas fa-terminal text-green-400"></i>
                    Gemini CLI Output
                </div>
                <div class="cli-output-content space-y-1"></div>
            `;
            messagesContainer.appendChild(cliContainer);
        }
        
        const cliContent = cliContainer.querySelector('.cli-output-content');
        const outputLine = document.createElement('div');
        outputLine.className = `message cli-output ${stream} text-xs`;
        outputLine.textContent = content;
        
        cliContent.appendChild(outputLine);
        cliContent.scrollTop = cliContent.scrollHeight;
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    displayExtensionInfo(extension) {
        const messagesContainer = document.getElementById('chat-messages');
        const infoDiv = document.createElement('div');
        infoDiv.className = 'extension-info animate-fade-in';
        infoDiv.innerHTML = `
            <div class="flex items-center gap-2 mb-3">
                <i class="fas fa-puzzle-piece text-xl"></i>
                <h3 class="text-lg font-semibold">Extension Generated!</h3>
            </div>
            <div class="space-y-2">
                <p><strong>Name:</strong> ${extension.name}</p>
                <p><strong>Description:</strong> ${extension.description}</p>
                <div class="mt-3">
                    <strong>Files Created:</strong>
                    <div class="mt-2 space-y-1">
                        ${Object.keys(extension.files).map(file => 
                            `<div class="flex items-center gap-2 text-sm">
                                <i class="fas fa-file text-blue-300"></i>
                                ${file}
                            </div>`
                        ).join('')}
                    </div>
                </div>
            </div>
        `;
        messagesContainer.appendChild(infoDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    updateFileTree(files) {
        console.log('Updating file tree with files:', files);
        const fileTree = document.getElementById('file-tree');
        
        if (!fileTree) {
            console.error('File tree element not found!');
            return;
        }
        
        if (!files || Object.keys(files).length === 0) {
            console.log('No files to display');
            fileTree.innerHTML = `
                <div class="text-gray-400 text-sm px-2 py-1">
                    <i class="fas fa-info-circle mr-2"></i>
                    No extension files yet
                </div>
            `;
            return;
        }
        
        console.log(`Found ${Object.keys(files).length} files to display`);
        
        // Clear existing files
        fileTree.innerHTML = '';
        
        Object.keys(files).forEach(filename => {
            console.log('Adding file to tree:', filename);
            this.createFileItem(filename, files[filename], fileTree);
        });
        
        console.log('File tree updated successfully');
    }
    
    createFileItem(filename, content, container) {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.onclick = () => this.openFileInTab(filename, content);
        
        const icon = this.getFileIcon(filename);
        const iconClass = this.getFileIconClass(filename);
        
        fileItem.innerHTML = `
            <i class="fas ${icon} file-icon ${iconClass}"></i>
            <span class="text-sm">${filename}</span>
        `;
        
        container.appendChild(fileItem);
    }
    
    setupTabSystem() {
        // Add tab management methods
        this.openTabs = [];
        this.activeTab = null;
    }
    
    openFileInTab(filename, content) {
        // Check if file is already open
        const existingTab = this.openTabs.find(tab => tab.filename === filename);
        if (existingTab) {
            this.switchToTab(existingTab);
            return;
        }
        
        // Create new tab
        const tab = {
            id: `tab-${Date.now()}`,
            filename: filename,
            content: content,
            language: this.getLanguageFromFilename(filename)
        };
        
        this.openTabs.push(tab);
        this.createTabElement(tab);
        this.switchToTab(tab);
        
        // Show editor modal
        this.showInlineEditor();
    }
    
    createTabElement(tab) {
        const tabsContainer = document.getElementById('editor-tabs');
        const tabElement = document.createElement('div');
        tabElement.className = 'flex items-center gap-2 px-3 py-2 text-sm border-r border-gray-700 cursor-pointer hover:bg-gray-700';
        tabElement.id = `tab-${tab.id}`;
        
        const icon = this.getFileIcon(tab.filename);
        const iconClass = this.getFileIconClass(tab.filename);
        
        tabElement.innerHTML = `
            <i class="fas ${icon} ${iconClass} text-xs"></i>
            <span>${tab.filename}</span>
            <button class="close-tab ml-2 text-gray-400 hover:text-white" onclick="event.stopPropagation(); app.closeTab('${tab.id}')">
                <i class="fas fa-times text-xs"></i>
            </button>
        `;
        
        tabElement.onclick = () => this.switchToTab(tab);
        tabsContainer.appendChild(tabElement);
    }
    
    switchToTab(tab) {
        // Update active tab
        this.activeTab = tab;
        
        // Update tab styling
        document.querySelectorAll('#editor-tabs > div').forEach(tabEl => {
            tabEl.classList.remove('bg-gray-700', 'text-white');
            tabEl.classList.add('text-gray-400');
        });
        
        const activeTabElement = document.getElementById(`tab-${tab.id}`);
        if (activeTabElement) {
            activeTabElement.classList.remove('text-gray-400');
            activeTabElement.classList.add('bg-gray-700', 'text-white');
        }
        
        // Load content in editor
        this.loadFileContent(tab.filename, tab.content, tab.language);
    }
    
    closeTab(tabId) {
        const tabIndex = this.openTabs.findIndex(tab => tab.id === tabId);
        if (tabIndex === -1) return;
        
        // Remove tab from array
        this.openTabs.splice(tabIndex, 1);
        
        // Remove tab element
        const tabElement = document.getElementById(`tab-${tabId}`);
        if (tabElement) {
            tabElement.remove();
        }
        
        // If this was the active tab, switch to another tab
        if (this.activeTab && this.activeTab.id === tabId) {
            if (this.openTabs.length > 0) {
                this.switchToTab(this.openTabs[Math.max(0, tabIndex - 1)]);
            } else {
                this.activeTab = null;
                this.editor.setValue('// No files open');
            }
        }
        
        // Hide modal if no tabs open
        if (this.openTabs.length === 0) {
            this.hideInlineEditor();
        }
    }
    
    showInlineEditor() {
        const editorContainer = document.getElementById('code-editor-container');
        const placeholder = document.getElementById('editor-placeholder');
        const monacoEditor = document.getElementById('monaco-editor');
        const editorTabs = document.getElementById('editor-tabs');
        
        editorContainer.classList.remove('hidden');
        placeholder.classList.add('hidden');
        monacoEditor.classList.remove('hidden');
        editorTabs.classList.remove('hidden');
    }
    
    hideInlineEditor() {
        const editorContainer = document.getElementById('code-editor-container');
        const placeholder = document.getElementById('editor-placeholder');
        const monacoEditor = document.getElementById('monaco-editor');
        const editorTabs = document.getElementById('editor-tabs');
        
        placeholder.classList.remove('hidden');
        monacoEditor.classList.add('hidden');
        editorTabs.classList.add('hidden');
    }
    
    getFileIcon(filename) {
        if (filename.endsWith('.json')) return 'fa-file-code';
        if (filename.endsWith('.html')) return 'fa-file-code';
        if (filename.endsWith('.css')) return 'fa-file-code';
        if (filename.endsWith('.js')) return 'fa-file-code';
        return 'fa-file';
    }
    
    getFileIconClass(filename) {
        if (filename.endsWith('.json')) return 'text-orange-400';
        if (filename.endsWith('.html')) return 'text-pink-400';
        if (filename.endsWith('.css')) return 'text-blue-400';
        if (filename.endsWith('.js')) return 'text-yellow-400';
        return 'text-gray-400';
    }
    
    loadFileContent(filename, content, language) {
        // Create or reuse model
        let model = this.editorModels.get(filename);
        if (!model) {
            model = monaco.editor.createModel(content, language);
            this.editorModels.set(filename, model);
        }
        
        this.editor.setModel(model);
    }
    
    getLanguageFromFilename(filename) {
        if (filename.endsWith('.json')) return 'json';
        if (filename.endsWith('.html')) return 'html';
        if (filename.endsWith('.css')) return 'css';
        if (filename.endsWith('.js')) return 'javascript';
        return 'plaintext';
    }
    
    sendMessage() {
        const input = document.getElementById('message-input');
        const message = input.value.trim();
        
        if (message && this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.addMessage(message, 'user');
            this.websocket.send(message);
            input.value = '';
        } else if (!this.isConnected) {
            this.showNotification('Not connected to server', 'error');
        }
    }
    
    async loadDummyExtension() {
        try {
            const response = await fetch('/api/browser/load-dummy-extension', { method: 'POST' });
            const result = await response.json();
            console.log('Load extension result:', result);
            this.showNotification('Dummy extension loaded', 'success');
        } catch (error) {
            console.error('Failed to load extension:', error);
            this.showNotification('Failed to load extension', 'error');
        }
    }
    
    async loadExtensionManual() {
        try {
            if (!this.currentExtensionId) {
                this.showNotification('No extension available to load. Please generate an extension first.', 'warning');
                return;
            }
            
            console.log("🔄 Loading extension manually...");
            console.log("Extension ID:", this.currentExtensionId);
            
            const response = await fetch(`/api/browser/load-extension-manual?extension_id=${this.currentExtensionId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            console.log("Manual extension loading result:", result);
            
            if (response.ok) {
                this.showNotification(result.message, 'success');
                
                // Store debug session ID if available
                if (result.debug_session_id) {
                    this.currentDebugSessionId = result.debug_session_id;
                    console.log("🔍 Debug session started:", this.currentDebugSessionId);
                }
                
                // Show instructions
                if (result.instructions) {
                    let instructionsHtml = '<div class="mb-4"><h4 class="text-lg font-semibold mb-2">Manual Loading Instructions:</h4><ol class="list-decimal list-inside space-y-1">';
                    result.instructions.forEach(instruction => {
                        instructionsHtml += `<li class="text-sm">${instruction}</li>`;
                    });
                    instructionsHtml += '</ol></div>';
                    
                    this.showNotification(instructionsHtml, 'info');
                }
            } else {
                this.showNotification(`Error: ${result.detail}`, 'error');
            }
        } catch (error) {
            console.error("Error loading extension manually:", error);
            this.showNotification("Failed to load extension manually", 'error');
        }
    }
    
    async testBrowser() {
        try {
            const response = await fetch('/api/browser/test', { method: 'POST' });
            const result = await response.json();
            console.log('Test browser result:', result);
            this.showNotification('Browser test completed', 'success');
        } catch (error) {
            console.error('Failed to test browser:', error);
            this.showNotification('Failed to test browser', 'error');
        }
    }
    
    async closeBrowser() {
        try {
            const response = await fetch('/api/browser/close', { method: 'POST' });
            const result = await response.json();
            console.log('Close browser result:', result);
            this.showNotification('Browser closed', 'success');
            
            // Clear debug session
            this.currentDebugSessionId = null;
        } catch (error) {
            console.error('Failed to close browser:', error);
            this.showNotification('Failed to close browser', 'error');
        }
    }
    
    async getDebugSummary() {
        try {
            if (!this.currentDebugSessionId) {
                this.showNotification('No active debug session', 'warning');
                return;
            }
            
            const response = await fetch(`/api/browser/debug-summary/${this.currentDebugSessionId}`);
            const result = await response.json();
            
            if (response.ok) {
                console.log('Debug summary:', result);
                this.showNotification(`Debug session: ${result.summary.total_events} events, ${result.summary.total_errors} errors`, 'info');
            } else {
                this.showNotification(`Error: ${result.detail}`, 'error');
            }
        } catch (error) {
            console.error('Failed to get debug summary:', error);
            this.showNotification('Failed to get debug summary', 'error');
        }
    }
    
    async getCurrentDebugSession() {
        try {
            const response = await fetch('/api/browser/current-debug-session');
            const result = await response.json();
            
            if (response.ok && result.status === 'success') {
                this.currentDebugSessionId = result.session_id;
                console.log('Current debug session:', result);
                return result;
            } else {
                console.log('No active debug session');
                return null;
            }
        } catch (error) {
            console.error('Failed to get current debug session:', error);
            return null;
        }
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 animate-fade-in status-${type}`;
        notification.innerHTML = `
            <div class="flex items-center gap-2">
                <i class="fas ${this.getNotificationIcon(type)}"></i>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
    
    getNotificationIcon(type) {
        switch (type) {
            case 'success': return 'fa-check-circle';
            case 'error': return 'fa-exclamation-circle';
            case 'warning': return 'fa-exclamation-triangle';
            default: return 'fa-info-circle';
        }
    }
    
    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            if (connected) {
                statusElement.className = 'flex items-center gap-2 text-sm text-green-400';
                statusElement.innerHTML = `
                    <i class="fas fa-circle animate-pulse"></i>
                    <span>Connected</span>
                `;
            } else {
                statusElement.className = 'flex items-center gap-2 text-sm text-red-400';
                statusElement.innerHTML = `
                    <i class="fas fa-circle"></i>
                    <span>Disconnected</span>
                `;
            }
        }
    }
    
    setupEventListeners() {
        // Send message
        document.getElementById('send-button').addEventListener('click', () => this.sendMessage());
        document.getElementById('message-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Open editor button
        document.getElementById('open-editor-btn').addEventListener('click', () => {
            if (this.openTabs.length > 0) {
                this.showInlineEditor();
            } else {
                this.showNotification('No files to open', 'info');
            }
        });
        
        // Browser control buttons
        document.getElementById('load-extension-btn').addEventListener('click', () => this.loadExtensionManual());
        document.getElementById('test-browser-btn').addEventListener('click', () => this.testBrowser());
        document.getElementById('close-browser-btn').addEventListener('click', () => this.closeBrowser());
        
        // Debug functionality
        this.currentDebugSessionId = null;
        
        // Test file tree update (for debugging)
        window.testFileTree = () => {
            console.log('Testing file tree update...');
            const testFiles = {
                'manifest.json': '{"name": "Test Extension", "version": "1.0.0"}',
                'popup.html': '<html><body>Test Popup</body></html>',
                'content.js': 'console.log("Test content script");'
            };
            this.updateFileTree(testFiles);
        };
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new ChromeExtensionBuilder();
}); 