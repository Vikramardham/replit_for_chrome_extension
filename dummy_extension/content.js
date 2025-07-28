// Content script for Dummy Extension
console.log('🚀 Dummy Extension content script loaded!');

// Store original page styles
let originalStyles = {};

// Initialize the extension
function initializeExtension() {
    console.log('✅ Dummy Extension initialized on:', window.location.href);
    
    // Add a more visible indicator to show the extension is active
    const indicator = document.createElement('div');
    indicator.id = 'dummy-extension-indicator';
    indicator.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px 20px;
        border-radius: 25px;
        font-size: 14px;
        font-family: Arial, sans-serif;
        font-weight: bold;
        z-index: 10000;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        pointer-events: none;
        opacity: 1;
        border: 2px solid white;
        animation: pulse 2s infinite;
    `;
    indicator.textContent = '🚀 Dummy Extension Active';
    document.body.appendChild(indicator);
    
    // Add a permanent floating button for testing
    const testButton = document.createElement('button');
    testButton.id = 'dummy-extension-test-btn';
    testButton.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: #28a745;
        color: white;
        border: none;
        padding: 12px 20px;
        border-radius: 25px;
        font-size: 14px;
        font-family: Arial, sans-serif;
        font-weight: bold;
        z-index: 10000;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        cursor: pointer;
        border: 2px solid white;
    `;
    testButton.textContent = '🧪 Test Extension';
    testButton.onclick = testFunction;
    document.body.appendChild(testButton);
    
    // Show success message
    setTimeout(() => {
        const successMsg = document.createElement('div');
        successMsg.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: #28a745;
            color: white;
            padding: 20px 30px;
            border-radius: 15px;
            font-family: Arial, sans-serif;
            font-size: 16px;
            font-weight: bold;
            z-index: 10001;
            box-shadow: 0 6px 25px rgba(0,0,0,0.4);
            animation: fadeInOut 3s ease-in-out;
        `;
        successMsg.textContent = '✅ Dummy Extension Successfully Loaded!';
        document.body.appendChild(successMsg);
        
        setTimeout(() => successMsg.remove(), 3000);
    }, 1000);
}

// Test function
function testFunction() {
    console.log('🧪 Test function executed!');
    
    // Show a notification
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: #28a745;
        color: white;
        padding: 20px;
        border-radius: 10px;
        font-family: Arial, sans-serif;
        z-index: 10001;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        animation: fadeInOut 2s ease-in-out;
    `;
    notification.textContent = '✅ Test function executed successfully!';
    document.body.appendChild(notification);
    
    // Remove notification after 2 seconds
    setTimeout(() => notification.remove(), 2000);
}

// Change page color
function changePageColor() {
    console.log('🎨 Changing page color...');
    
    // Store original styles if not already stored
    if (!originalStyles.backgroundColor) {
        originalStyles.backgroundColor = document.body.style.backgroundColor;
        originalStyles.color = document.body.style.color;
    }
    
    // Change to a random color
    const colors = ['#f0f8ff', '#ffe4e1', '#f0fff0', '#fff8dc', '#f5f5dc'];
    const randomColor = colors[Math.floor(Math.random() * colors.length)];
    
    document.body.style.backgroundColor = randomColor;
    document.body.style.color = '#333';
    
    // Show notification
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #17a2b8;
        color: white;
        padding: 15px;
        border-radius: 8px;
        font-family: Arial, sans-serif;
        z-index: 10001;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    `;
    notification.textContent = '🎨 Page color changed!';
    document.body.appendChild(notification);
    
    setTimeout(() => notification.remove(), 2000);
}

// Reset page
function resetPage() {
    console.log('🔄 Resetting page...');
    
    // Restore original styles
    if (originalStyles.backgroundColor) {
        document.body.style.backgroundColor = originalStyles.backgroundColor;
        document.body.style.color = originalStyles.color;
    } else {
        document.body.style.backgroundColor = '';
        document.body.style.color = '';
    }
    
    // Show notification
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #6c757d;
        color: white;
        padding: 15px;
        border-radius: 8px;
        font-family: Arial, sans-serif;
        z-index: 10001;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    `;
    notification.textContent = '🔄 Page reset to original state!';
    document.body.appendChild(notification);
    
    setTimeout(() => notification.remove(), 2000);
}

// Listen for messages from popup
chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
    console.log('📨 Received message:', request);
    
    switch(request.action) {
        case 'test':
            testFunction();
            break;
        case 'changeColor':
            changePageColor();
            break;
        case 'reset':
            resetPage();
            break;
        default:
            console.log('❓ Unknown action:', request.action);
    }
    
    // Send response back to popup
    sendResponse({status: 'success', action: request.action});
});

// Add CSS for animations
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeInOut {
        0% { opacity: 0; transform: translate(-50%, -50%) scale(0.8); }
        50% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
        100% { opacity: 0; transform: translate(-50%, -50%) scale(0.8); }
    }
    @keyframes pulse {
        0% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.05); opacity: 0.8; }
        100% { transform: scale(1); opacity: 1; }
    }
`;
document.head.appendChild(style);

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeExtension);
} else {
    initializeExtension();
} 