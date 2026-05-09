# Table for Three AI

A multi-model AI conversation platform for structured interaction experiments, including the "AI Mafia" role-playing game experiment.

## Architecture

- **Backend**: FastAPI (Python) running on port 5000
- **Frontend**: Single-page HTML/JS app served as static files by the FastAPI server
- **AI Integration**: Google Generative AI (Gemini models) via `google-generativeai`
- **Real-time**: WebSocket support for live AI conversation streaming

## Project Structure

```
├── main.py                     # App entry point, mounts static files
├── models.py                   # Pydantic data models
├── requirements.txt            # Python dependencies
├── api/
│   └── routes.py               # REST and WebSocket API routes
├── services/
│   ├── ai_service.py           # Google AI SDK integration
│   └── conversation_manager.py # Conversation state management
├── utils/
│   └── buffer.py               # Streaming response buffer
├── config/
│   ├── models.json             # AI model configurations
│   ├── mafia_prompt.md         # System prompts for AI Mafia roles
│   └── workflow.json           # Workflow config
└── static/
    └── index.html              # Frontend SPA
```

## Key Features

- **Parallel mode**: All AI participants respond simultaneously to a user message
- **Sequential mode**: AI participants respond in turn, each seeing the previous response
- **AI Mafia experiment**: Role-based game with Detective, Innocent, and Mafia roles
- **WebSocket streaming**: Real-time AI response delivery

## Environment Variables

- `GOOGLE_API_KEY`: Required for Google Generative AI (Gemini) access

## Running

The app runs via the "Start application" workflow:
```
python main.py
```
Server starts on `0.0.0.0:5000`.
