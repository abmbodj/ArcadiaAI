<p align="center">
  <img src="/templates/imgs/Mini Knight Laptop.svg" alt="ArchieAI Logo" width="150"/>
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

## Setup

1. Install [Ollama](https://ollama.ai/) on your system
2. Pull a model: `ollama pull llama2` (or another supported model)
3. Copy `.env.example` to `.env` and configure your model:
   ```bash
   cp .env.example .env
   ```
4. Edit `.env` and set your preferred model (e.g., `OLLAMA_MODEL=llama2`)
5. Install Python dependencies (you may need to create a requirements.txt)
6. Run the application: `python src/app.py`

## Usage
To use ArchieAI, simply interact with it through your preferred messaging platform or web interface. Ask questions, request assistance, or provide instructions, and ArchieAI will respond accordingly with streaming support for real-time responses.
