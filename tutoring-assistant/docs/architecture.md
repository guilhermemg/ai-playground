# Architecture

## System Overview

The Tutoring Assistant is a microservices-based platform built around **dynamic expert agents**. Unlike traditional multi-agent systems with hardcoded roles, this system allows professors to create, configure, and manage domain-specific expert agents at runtime through a web UI.

## Core Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    React Admin Frontend                       │
│  ┌──────────┐ ┌────────────┐ ┌───────┐ ┌────┐ ┌──────────┐ │
│  │Dashboard │ │Questionnaire│ │Agents │ │Docs│ │Chat│Eval │ │
│  └────┬─────┘ └─────┬──────┘ └──┬────┘ └──┬─┘ └──┬──┬────┘ │
└───────┼──────────────┼──────────┼─────────┼──────┼──┼───────┘
        │  REST API    │          │         │   WS │  │
┌───────┼──────────────┼──────────┼─────────┼──────┼──┼───────┐
│       ▼              ▼          ▼         ▼      ▼  ▼       │
│                    FastAPI Backend                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │            LangGraph StateGraph (Dynamic)             │   │
│  │                                                       │   │
│  │  ┌────────────────┐     ┌──────────────────────┐     │   │
│  │  │ Router Node    │────►│ Dynamic Expert Agent  │     │   │
│  │  │ (gpt-4o-mini)  │     │ (gpt-4o)             │     │   │
│  │  │                │     │ - Medicine Expert     │     │   │
│  │  │ Classifies     │     │ - Law Expert          │     │   │
│  │  │ questions by   │     │ - Physics Expert      │     │   │
│  │  │ domain         │     │ - Math Expert         │     │   │
│  │  │                │     │ - ...any domain       │     │   │
│  │  └────────────────┘     └──────────────────────┘     │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ RAG Engine  │  │ Prompt       │  │ Observability     │  │
│  │ (Pinecone)  │  │ Versioning   │  │ OTEL + LangSmith  │  │
│  └─────────────┘  └──────────────┘  └───────────────────┘  │
└──────────────────────────┬───────────────────────────────────┘
                           │
       ┌───────────────────┼───────────────────┐
       ▼                   ▼                   ▼
  ┌──────────┐     ┌────────────┐      ┌────────────┐
  │PostgreSQL│     │  Pinecone  │      │  Jaeger    │
  │          │     │  (Vector)  │      │  Prometheus│
  │  Agents  │     │            │      │  Grafana   │
  │  Prompts │     │  Embeddings│      │            │
  │  Quests  │     │  per agent │      │  Traces    │
  │  Docs    │     │  namespace │      │  Metrics   │
  └──────────┘     └────────────┘      └────────────┘
```

## Data Flow: Questionnaire Evaluation

1. Professor submits a questionnaire (list of Q&A pairs) via the UI
2. Backend stores it in PostgreSQL with status `pending`
3. Professor clicks "Evaluate" — triggers a background task
4. The task loads all **active agents** from the database
5. A LangGraph `StateGraph` is built dynamically with one node per active agent + the router
6. For each question in the questionnaire:
   - The **Router** (gpt-4o-mini) receives the question + list of available agents (name, domain, description)
   - The router selects the best-fit agent
   - The question is forwarded to that agent's node
   - The agent evaluates the answer using its configured prompt and tools
7. Results are aggregated and stored per-question in `questionnaire_results`
8. Status is updated to `completed`

## Data Flow: Chat Streaming

1. Professor opens the Chat page — WebSocket connection established
2. Professor types a question
3. Backend routes the question through the same LangGraph router
4. The selected agent streams its response token-by-token via WebSocket
5. Frontend displays tokens in real-time with the agent name badge

## Dynamic Agent Lifecycle

```
Professor creates agent via UI
        │
        ▼
┌─────────────────────────┐
│ POST /api/agents        │
│ {name, domain,          │
│  description, tools}    │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Standard template       │     ┌──────────────────────────┐
│ generates initial       │────►│ PromptVersion v1 stored  │
│ system_message +        │     │ in PostgreSQL            │
│ full_prompt             │     └──────────────────────────┘
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Agent record created    │
│ in PostgreSQL with      │
│ active_prompt_version   │
│ = v1                    │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Professor edits prompt  │     ┌──────────────────────────┐
│ in the UI prompt editor │────►│ PromptVersion v2 created │
│                         │     │ (v1 preserved)           │
└─────────────────────────┘     └──────────────────────────┘
```

## Agent Instantiation at Runtime

When a request comes in (evaluation or chat), agents are loaded from the DB:

1. Query all `agents` where `is_active = True`
2. For each agent, load the active `prompt_version`
3. Instantiate a `DynamicExpertAgent` with:
   - The stored system message and full prompt
   - Tools assembled from `tools_registry` based on `enabled_tools`
   - A RAG retrieval tool scoped to the agent's Pinecone namespace (if documents are assigned)
4. The graph is built with these agent instances as nodes

## RAG Pipeline

```
Upload Document
      │
      ▼
┌─────────────────┐
│ Document Parser  │  (PyPDF, docx2txt, TextLoader)
│ Detect file type │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Text Splitter    │  (RecursiveCharacterTextSplitter)
│ chunk_size=1000  │
│ overlap=200      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Embedding        │  (text-embedding-3-small)
│ OpenAI API       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Pinecone Upsert  │  namespace = "agent_{agent_id}"
│ Vectors + meta   │
└─────────────────┘
```

Each agent has an isolated Pinecone namespace. When the `rag_retrieval` tool is invoked, it queries only that agent's namespace, ensuring document isolation.

## Observability Architecture

### LangSmith (LLM-level)
- Traces every LangChain/LangGraph call automatically
- Captures: prompt inputs, model outputs, token usage, latency
- Custom metadata: agent name, domain, prompt version, questionnaire ID

### Jaeger (Service-level)
- OpenTelemetry auto-instrumentation on FastAPI, httpx, SQLAlchemy
- Full request traces: HTTP → Router → Agent → LLM → Tools → DB
- Span hierarchy shows exactly where time is spent

### Prometheus + Grafana (Metrics)
- `questionnaire_evaluation_duration_seconds` - histogram
- `agent_invocations_total{agent_name, domain}` - counter
- `llm_tokens_used_total{model, type}` - counter
- `rag_retrieval_latency_seconds` - histogram
- `routing_decisions_total{selected_domain}` - counter

## Database Schema

| Table | Purpose |
| --- | --- |
| `agents` | Agent configs: name, domain, tools, active prompt version |
| `prompt_versions` | Immutable prompt history per agent |
| `questionnaires` | Submitted questionnaires with status |
| `questionnaire_results` | Per-question evaluation results |
| `documents` | Uploaded files with Pinecone namespace mapping |
| `evaluation_runs` | RAGAS evaluation run results |
