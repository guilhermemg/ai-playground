# Deployment Guide

## Local Development (Docker Compose)

### Prerequisites

- Docker Engine 24+
- Docker Compose v2+
- API keys: OpenAI, Pinecone, (optional) LangSmith

### Steps

```bash
# 1. Configure environment
cp .env.template .env
# Edit .env with your API keys

# 2. Build and start all services
docker-compose up --build

# 3. Verify services are running
curl http://localhost:8000/api/health
# → {"status": "healthy"}
```

### Service Ports

| Service | Port | URL |
| --- | --- | --- |
| Frontend | 3000 | http://localhost:3000 |
| Backend API | 8000 | http://localhost:8000 |
| Swagger Docs | 8000 | http://localhost:8000/docs |
| PostgreSQL | 5432 | - |
| Jaeger UI | 16686 | http://localhost:16686 |
| Prometheus | 9090 | http://localhost:9090 |
| Grafana | 3001 | http://localhost:3001 |

## Production Deployment

### Docker Image Versioning

Images follow the convention `{semver}-prompt-v{N}`:

```bash
# Build with version tags
docker build -t tutoring-backend:1.0.0-prompt-v1 ./backend
docker build -t tutoring-frontend:1.0.0 ./frontend

# The backend Dockerfile includes a LABEL for traceability
# LABEL prompt_version="v1"
```

When prompt templates change significantly, increment the prompt version in the tag and Dockerfile LABEL. This creates a clear link between Docker images and the prompt versions they ship with.

### Production Compose

```bash
# Set production secrets
export POSTGRES_PASSWORD=<strong-password>
export GRAFANA_PASSWORD=<strong-password>

# Create .env.prod with production API keys
cp .env.template .env.prod
# Edit .env.prod

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

### Production Checklist

- [ ] Set strong passwords for PostgreSQL and Grafana
- [ ] Configure CORS to allow only your frontend domain (update `main.py`)
- [ ] Set up persistent volume mounts for PostgreSQL and uploads
- [ ] Configure Pinecone for your production index
- [ ] Set up LangSmith project for production tracing
- [ ] Configure resource limits in `docker-compose.prod.yml`
- [ ] Set up a reverse proxy (nginx/Traefik) with HTTPS
- [ ] Configure log aggregation

### Database Migrations

```bash
# Generate a new migration
cd backend
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

### Scaling Considerations

- **Backend**: Increase `--workers` in the Dockerfile CMD or use multiple replicas
- **Database**: Consider connection pooling (PgBouncer) for high concurrency
- **Pinecone**: Choose an appropriate pod type for your document volume
- **Frontend**: Static files served by nginx; trivially horizontally scalable

## Monitoring

### Grafana Setup

1. Access Grafana at http://localhost:3001 (admin/admin)
2. Add Prometheus as a data source: URL = `http://prometheus:9090`
3. Import or create dashboards for the custom metrics:
   - `questionnaire_evaluation_duration_seconds`
   - `agent_invocations_total`
   - `rag_retrieval_latency_seconds`
   - `routing_decisions_total`

### Jaeger Traces

Access Jaeger at http://localhost:16686. Select service `tutoring-backend` to see:
- Full request traces with span hierarchy
- Latency distributions
- Error traces

### LangSmith

Access at https://smith.langchain.com. Your project will show:
- Every LLM call with full prompt and response
- Token usage and latency per call
- Agent reasoning traces from LangGraph
