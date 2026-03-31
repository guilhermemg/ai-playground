# Tutoring Assistant

A production-ready, AI-powered tutoring platform where professors can create dynamic expert agents for any knowledge domain, evaluate student questionnaires, and interact through a streaming chatbot -- all managed via a modern React admin UI.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     React Frontend (Vite)                       │
│  Dashboard │ Questionnaires │ Agents │ Documents │ Chat │ Eval │
└──────────────────────────┬──────────────────────────────────────┘
                           │ REST + WebSocket
┌──────────────────────────┴──────────────────────────────────────┐
│                    FastAPI Backend                               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              LangGraph Orchestration                     │    │
│  │   Router (gpt-4o-mini) → Dynamic Expert Agents (gpt-4o) │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌──────────┐ ┌───────────┐ ┌──────────┐ ┌────────────────┐   │
│  │ RAG      │ │ Prompt    │ │ RAGAS    │ │ Observability  │   │
│  │ Pinecone │ │ Versioning│ │ Eval     │ │ OTEL+LangSmith │   │
│  └──────────┘ └───────────┘ └──────────┘ └────────────────┘   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
  ┌────────┐ ┌──────────┐ ┌────────┐ ┌───────────┐ ┌─────────┐
  │Postgres│ │ Pinecone │ │ Jaeger │ │Prometheus │ │ Grafana │
  └────────┘ └──────────┘ └────────┘ └───────────┘ └─────────┘
```

## Key Features

- **Dynamic Expert Agents**: Professors create agents for any domain (Medicine, Law, Physics, Math, Engineering, etc.) through the UI with customizable prompts and tools
- **LangGraph Routing**: A lightweight router model (gpt-4o-mini) classifies each question and routes it to the most suitable expert agent
- **RAG with Pinecone**: Upload documents per agent; chunks are embedded and stored in agent-specific Pinecone namespaces
- **Prompt Versioning**: Every prompt edit creates a new version; professors can switch between versions and track changes
- **Streaming Chatbot**: WebSocket-based chat with real-time token streaming, showing which agent is responding
- **RAGAS Evaluation**: Full-system evaluation with golden datasets measuring faithfulness, answer relevancy, context precision/recall, correctness, and routing accuracy
- **Observability**: LangSmith for LLM traces, Jaeger for distributed tracing, Prometheus + Grafana for metrics
- **Docker Compose**: One-command deployment with all services

## Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI API key
- Pinecone API key (free tier works)
- LangSmith API key (optional, for LLM tracing)

### 1. Clone and configure

```bash
cd tutoring-assistant
cp .env.template .env
# Edit .env with your API keys
```

### 2. Start all services

```bash
docker-compose up --build
```

### 3. Access the application

| Service          | URL                        |
| ---------------- | -------------------------- |
| Frontend UI      | http://localhost:3000       |
| Backend API      | http://localhost:8000       |
| API Docs (Swagger) | http://localhost:8000/docs |
| Jaeger UI        | http://localhost:16686      |
| Prometheus       | http://localhost:9090       |
| Grafana          | http://localhost:3001       |

### 4. First steps in the UI

1. Go to **Agents** and create your first expert agent (e.g., "Physics Expert" with domain "Physics")
2. Optionally enable tools (calculator, web_search, wikipedia) for the agent
3. Upload documents in **Documents** and assign them to agents for RAG
4. Go to **Questionnaires**, create a quiz, and hit **Evaluate**
5. Use the **Chat** to ask questions interactively
6. Run evaluations in the **Evaluation** dashboard

## Development Setup

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# Start PostgreSQL locally or via Docker
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=tutoring postgres:16-alpine

# Run the backend
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
cd backend
pytest -v
pytest --cov=app tests/
```

## Environment Variables

See [`.env.template`](.env.template) for all available configuration options. Key variables:

| Variable | Description | Required |
| --- | --- | --- |
| `OPENAI_API_KEY` | OpenAI API key | Yes |
| `PINECONE_API_KEY` | Pinecone API key | Yes |
| `LANGCHAIN_API_KEY` | LangSmith API key | No |
| `OPENAI_MODEL` | Model for expert agents (default: gpt-4o) | No |
| `OPENAI_ROUTER_MODEL` | Model for routing (default: gpt-4o-mini) | No |

## API Reference

See full interactive docs at `http://localhost:8000/docs` when the backend is running.

Key endpoints:

- `POST /api/agents` - Create a new expert agent
- `GET /api/agents` - List all agents
- `PATCH /api/agents/{id}` - Update agent (toggle, tools, name)
- `PUT /api/agents/{id}/prompt` - Update agent prompt (creates new version)
- `POST /api/questionnaires` - Submit a questionnaire
- `POST /api/questionnaires/{id}/evaluate` - Trigger evaluation
- `POST /api/documents` - Upload a document
- `POST /api/documents/{id}/assign/{agent_id}` - Assign document to agent
- `POST /api/evaluation/run` - Run RAGAS evaluation
- `WS /ws/chat` - Streaming chatbot

## Documentation

- [Architecture](docs/architecture.md) - Detailed system architecture and data flows
- [Deployment](docs/deployment.md) - Docker build, versioning, production deployment
- [Prompt Versioning](docs/prompt-versioning.md) - How prompt versioning works
- [Evaluation](docs/evaluation.md) - RAGAS evaluation setup and golden datasets

## Project Structure

```
tutoring-assistant/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI entrypoint
│   │   ├── api/routes/                # REST + WebSocket endpoints
│   │   ├── agents/                    # DynamicExpertAgent + tools registry
│   │   ├── graph/                     # LangGraph router + nodes
│   │   ├── rag/                       # Pinecone embeddings + doc processor
│   │   ├── prompts/                   # Prompt versioning registry
│   │   ├── config/                    # Pydantic Settings
│   │   ├── observability/             # OTEL + LangSmith + Prometheus
│   │   ├── evaluation/               # RAGAS evaluator + golden datasets
│   │   └── db/                        # SQLAlchemy models + migrations
│   ├── tests/                         # pytest test suite
│   └── test_documents/                # Sample docs for RAG testing
├── frontend/
│   └── src/
│       ├── components/                # React components
│       └── services/                  # API + WebSocket clients
├── docs/                              # Architecture + deployment docs
├── docker-compose.yml                 # Local development
├── docker-compose.prod.yml            # Production
└── prometheus.yml                     # Prometheus config
```

## Tech Stack

**Backend**: Python, FastAPI, LangChain, LangGraph, OpenAI, Pinecone, SQLAlchemy, PostgreSQL

**Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Recharts

**Observability**: LangSmith, OpenTelemetry, Jaeger, Prometheus, Grafana

**Evaluation**: RAGAS

**Infrastructure**: Docker, Docker Compose, nginx
