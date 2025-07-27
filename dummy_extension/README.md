# Dummy Extension for Testing

This is a simple Chrome extension created for testing the Chrome Extension Builder environment.

## Files Included

- `manifest.json` - Extension manifest file
- `popup.html` - Extension popup interface
- `popup.js` - Popup functionality
- `content.js` - Content script that runs on web pages

## How to Load the Extension

1. **Open Chrome** and navigate to `chrome://extensions/`

2. **Enable Developer Mode** by toggling the switch in the top-right corner

3. **Click "Load unpacked"** button

4. **Select the `dummy_extension` folder** from this project

5. **The extension should now appear** in your extensions list

## Testing the Extension

### Visual Indicators
- When you visit any website, you'll see a small indicator in the top-right corner showing "🚀 Dummy Extension Active"
- This indicator will fade out after 3 seconds

### Popup Features
Click the extension icon in your toolbar to open the popup. You can:

1. **Test Function** - Shows a notification and logs to console
2. **Change Page Color** - Changes the background color of the current page
3. **Reset Page** - Restores the original page colors

### Console Logs
Open the browser's Developer Tools (F12) and check the Console tab to see:
- Extension initialization messages
- Function execution logs
- Message passing between popup and content script

## Features to Test

✅ **Extension Loading** - Should load without errors
✅ **Popup Interface** - Should display properly with buttons
✅ **Content Script** - Should run on web pages
✅ **Message Passing** - Popup should communicate with content script
✅ **Visual Effects** - Notifications and color changes should work
✅ **Console Logging** - Should log activity to browser console

## Troubleshooting

- If the extension doesn't load, check that all files are present
- If popup doesn't work, check the browser console for errors
- If content script doesn't run, make sure you're on a regular webpage (not chrome:// pages)

## Expected Behavior

1. **On any webpage**: Small indicator appears briefly
2. **Click extension icon**: Popup opens with 3 buttons
3. **Click "Test Function"**: Notification appears on page
4. **Click "Change Page Color"**: Page background changes color
5. **Click "Reset Page"**: Page returns to original colors
6. **Check console**: Should see various log messages

This extension demonstrates the basic functionality that the Chrome Extension Builder should be able to generate and test. 