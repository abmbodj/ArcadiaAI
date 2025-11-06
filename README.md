<p align="center">
  <img src="/static/imgs/Mini Knight Laptop.svg" alt="ArchieAI Logo" width="150"/>
</p>

<h1 align="center">ArchieAI</h1>

<p align="center">
  Archie AI is an AI-powered assistant designed to help users and students with a variety of tasks, from answering questions to providing recommendations and generating content. Built on Ollama for local LLM inference, ArchieAI aims to enhance productivity and make your experience at Arcadia University more efficient and enjoyable.
</p>

## Features
- **Natural Language Understanding:** Communicates in a human-like manner.  
- **Contextual Awareness:** Remembers previous interactions for better responses.  
- **Streaming Responses:** See the AI "thinking" in real-time with token-by-token streaming.
- **Local LLM Inference:** Uses Ollama for privacy-focused, local AI processing.
- **Multi-Tasking:** Handles a wide range of tasks including writing, research, and data analysis.  
- **Customizable:** Tailor responses and functionalities to suit individual needs.  
- **Integration:** Easily integrates with various platforms and applications.
- **Tool-Based Web Search:** Uses Ollama's tool calling to intelligently search the web when needed.
- **Session Management:** Persistent chat history with support for multiple sessions per user.
- **Account System:** User authentication with password hashing for secure login.
- **Chat History:** View, load, and delete previous conversations.
- **Web Scraping:** Automated scraping of Arcadia University resources for up-to-date information.  

## Setup

1. Install [Ollama](https://ollama.ai/) on your system
2. Pull a model that supports tool calling: `ollama pull qwen3` (recommended for tool calling support)
3. Copy `.env.example` to `.env` and configure your model:
   ```bash
   cp .env.example .env
   ```
4. Edit `.env` and set your preferred model (e.g., `MODEL=qwen3`)
5. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
6. Initialize data directories:
   ```bash
   mkdir -p data/sessions
   echo '{}' > data/qna.json
   ```
7. Run the application:
   ```bash
   python src/app.py
   ```
8. Access the web interface at `http://localhost:5000`

## Usage

### Getting Started
1. Visit `http://localhost:5000` in your web browser
2. Choose to login with an account or continue as a guest
3. Start chatting with ArchieAI!

### Features Guide

#### Chat History
- Click the history icon (clock) in the chat interface to view previous conversations
- Click "Load" to switch to a previous chat session
- Click "Delete" to remove a chat session permanently
- Click "+ New Chat" to start a fresh conversation

#### Account Management
- First-time users: Enter email and password to create an account automatically
- Returning users: Login with your credentials to access your chat history
- Guest users: Continue without an account (history not saved across sessions)

#### Web Search
ArchieAI uses Ollama's tool calling feature to intelligently search the web when:
- The scraped university data doesn't contain the answer
- The query requires current/real-time information
- The AI determines additional information is needed
- **Note:** Requires a model with tool calling support (e.g., qwen3)

#### Session Context
- Each conversation maintains context within the session
- Recent messages (last 5) are used to provide context for responses
- Context is preserved when loading previous sessions

## API Endpoints

### Chat Endpoints
- `POST /api/archie` - Send a question (non-streaming)
- `POST /api/archie/stream` - Send a question (streaming response)

### Session Management
- `GET /api/sessions/history` - Get current session history
- `GET /api/sessions/list` - List all user sessions (requires login)
- `GET /api/sessions/<id>` - Get specific session details
- `DELETE /api/sessions/<id>` - Delete a session
- `POST /api/sessions/new` - Create new session
- `POST /api/sessions/switch/<id>` - Switch to different session

## Data Storage

All data is stored locally in JSON files:
- `data/users.json` - User accounts with hashed passwords
- `data/sessions/*.json` - Individual chat sessions
- `data/scrape_results.json` - Cached university data from web scraping
- `data/qna.json` - Question-answer pairs (legacy storage)

## Development

To run the web scraper manually:
```bash
python src/helpers/scraper.py
```

The scraper runs in a loop and updates university data every hour.
