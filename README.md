# Table for Three AI

Multi-model AI conversation platform with parallel/sequential modes, content moderation, and identity protection. Implements the "AI Mafia" experiment - integrating Google AI Studio prompts with production-ready architecture.

## 🎯 Features

- **Multi-Model Conversations**: Support for multiple AI models in a single conversation
- **Conversation Modes**: 
  - Parallel mode - all participants respond simultaneously
  - Sequential mode - participants take turns
- **Content Moderation**: Built-in safety checks for conversations
- **Identity Protection**: Masking of names, locations, and sensitive data
- **AI Mafia Experiment**: Role-based conversation simulation (Detective, Innocent, Mafia)
- **WebSocket Support**: Real-time bidirectional communication
- **Docker Ready**: Full containerization support

## 🏗️ Project Structure

```
table-for-three-ai/
├── main.py                 # FastAPI application entry point
├── models.py               # Pydantic data models
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose setup
├── api/
│   ├── __init__.py
│   └── routes.py          # API route handlers
├── config/
│   ├── mafia_prompt.md    # AI Mafia game prompts
│   ├── models.json        # Model configurations
│   ├── moderation.json    # Moderation settings
│   └── workflow.json      # Workflow definitions
├── services/
│   ├── __init__.py
│   ├── ai_service.py      # AI service integration
│   └── conversation_manager.py  # Conversation state management
├── utils/
│   ├── __init__.py
│   └── buffer.py          # Utility functions
└── static/
    └── index.html         # Frontend interface
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (optional)
- API keys for AI services (see Configuration)

### Running with Docker (Recommended)

```bash
# Build and run
docker-compose up --build

# Access the application
open http://localhost:8000
```

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Run the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_MODERATION_KEY` | OpenAI API key for content moderation | Optional |

Create a `.env` file in the project root:

```bash
OPENAI_MODERATION_KEY=your-api-key-here
```

### Configuration Files

- **config/models.json**: Define available AI models and their settings
- **config/moderation.json**: Configure content moderation rules
- **config/workflow.json**: Set up conversation workflows
- **config/mafia_prompt.md**: Customize AI Mafia game prompts

## 📡 API Endpoints

### REST API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check and API info |
| `/health` | GET | Detailed health status |

### WebSocket

| Endpoint | Description |
|----------|-------------|
| `/ws` | Real-time conversation WebSocket |

**Example WebSocket Message:**
```json
{
  "type": "user_input",
  "content": "Hello, let's start the game!"
}
```

## 🎮 AI Mafia Experiment

The platform implements a role-based conversation system inspired by the Mafia party game:

- **Detective**: Tries to identify the mafia through questioning
- **Innocent**: Regular player trying to survive
- **Mafia**: Secretly working to eliminate other players

Each role has unique system prompts and behavioral patterns configured in `config/mafia_prompt.md`.

## 🛡️ Safety Features

### Content Moderation
- Automatic detection of harmful content
- Configurable confidence thresholds
- Category-based filtering

### Identity Protection
- Name masking
- Location data filtering
- Sensitive information detection
- Custom pattern matching

## 🧪 Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=.
```

## 📦 Dependencies

- **FastAPI** (0.110.0): Modern web framework
- **Uvicorn** (0.29.0): ASGI server
- **Pydantic** (2.6.0): Data validation
- **Playwright** (1.42.0): Browser automation
- **WebSockets** (12.0): WebSocket support
- **HTTPX** (0.27.0): Async HTTP client

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Google AI Studio for prompt engineering inspiration
- FastAPI community for excellent documentation
- All contributors to this project

---

**Table for Three AI** - Where AI meets structured conversation experiments.
