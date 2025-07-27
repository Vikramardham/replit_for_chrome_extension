// Popup script for Dummy Extension
document.addEventListener('DOMContentLoaded', function() {
    const statusDiv = document.getElementById('status');
    const testButton = document.getElementById('testButton');
    const colorButton = document.getElementById('colorButton');
    const resetButton = document.getElementById('resetButton');

    // Test function button
    testButton.addEventListener('click', function() {
        statusDiv.textContent = '✅ Test function executed successfully!';
        statusDiv.className = 'status success';
        
        // Send message to content script
        chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
            chrome.tabs.sendMessage(tabs[0].id, {action: "test"});
        });
    });

    // Change page color button
    colorButton.addEventListener('click', function() {
        statusDiv.textContent = '🎨 Changing page background color...';
        statusDiv.className = 'status info';
        
        chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
            chrome.tabs.sendMessage(tabs[0].id, {action: "changeColor"});
        });
    });

    // Reset page button
    resetButton.addEventListener('click', function() {
        statusDiv.textContent = '🔄 Resetting page to original state...';
        statusDiv.className = 'status info';
        
        chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
            chrome.tabs.sendMessage(tabs[0].id, {action: "reset"});
        });
    });

    // Listen for messages from content script
    chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
        if (request.action === "updateStatus") {
            statusDiv.textContent = request.message;
            statusDiv.className = `status ${request.type || 'info'}`;
        }
    });
}); 