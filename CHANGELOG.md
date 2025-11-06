# Changelog

All notable changes to ArchieAI will be documented in this file.

## [Unreleased] - 2025-11-04

### Added
- **Tool-Based Web Search Integration**
  - Implemented using Ollama's tool calling feature
  - AI automatically decides when to search the web based on query context
  - Defines `search_web` tool that the AI can call when needed
  - Requires a model with tool calling support (e.g., qwen3)

- **Session Management**
  - Full session-based conversation context
  - Persistent storage of chat history in JSON files
  - Session history includes timestamps and message roles
  - Support for multiple concurrent sessions per user
  - Last 5 messages used for context in responses

- **Account System**
  - User authentication with secure password hashing (werkzeug)
  - Auto-creation of accounts on first login
  - Login and guest access options
  - User-specific session tracking

- **Chat History Management**
  - Sidebar interface for viewing all previous conversations
  - Load previous chat sessions with full message history
  - Delete individual chat sessions
  - Create new chat sessions
  - Session preview showing first user message
  - Visual indicator for currently active session

- **API Endpoints**
  - `GET /api/sessions/history` - Get current session conversation history
  - `GET /api/sessions/list` - List all sessions for logged-in user
  - `GET /api/sessions/<id>` - Get details of specific session
  - `DELETE /api/sessions/<id>` - Delete a chat session
  - `POST /api/sessions/new` - Create new chat session
  - `POST /api/sessions/switch/<id>` - Switch to different session

### Changed
- Updated GemInterface to support conversation history in Archie methods
- Modified streaming endpoint to include session context
- Enhanced Archie() and Archie_streaming() with fallback web search
- Updated authentication flow to use SessionManager
- Improved route handling for session management

### Technical Details
- `SessionManager` class handles all user and session operations
- User data stored in `data/users.json`
- Individual sessions stored in `data/sessions/*.json`
- Password hashing using werkzeug.security
- Session IDs generated using UUID4

### Dependencies
- Using Ollama's tool calling feature (no additional dependencies required)
- Added `qrcode==8.2` and `pillow==12.0.0` for QR code generation support
- Removed `duckduckgo-search` dependency

## Notes
- All data is stored locally in JSON format
- Session history is automatically loaded on page refresh
- Guest users can use the app but history is not persisted across browser sessions
- Auto-create accounts eliminates need for separate registration page
