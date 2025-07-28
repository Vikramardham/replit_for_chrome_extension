# Chrome Extension Builder through a chat interface

The project aims to build `replit` like website where users can build and test a chrome extension just through a chat interface.
The website lets the user explain in detail what the chrome extension wants to do and this application will plan and write code for the extension.
The application will further load the extension in an environment into a chrome browser, test it carefully, iterate it, take feedback from the user

Architecture
1. Chat interface that talks to the user
2. Chrome browser environment where the extension is loaded and the console logs are viewed 
3. A background coding agent that writes and executes code (e.g: gemini cli)
