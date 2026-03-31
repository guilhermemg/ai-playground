from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Tutoring Assistant"
    debug: bool = False

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_router_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    # PostgreSQL
    database_url: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/tutoring"
    database_url_sync: str = "postgresql://postgres:postgres@postgres:5432/tutoring"

    # Pinecone
    pinecone_api_key: str = ""
    pinecone_index_name: str = "tutoring-assistant"
    pinecone_environment: str = "us-east-1"
    pinecone_dimension: int = 512

    # LangSmith
    langchain_tracing_v2: bool = True
    langchain_api_key: str = ""
    langchain_project: str = "tutoring-assistant"

    # Jaeger / OpenTelemetry
    otel_exporter_otlp_endpoint: str = "http://jaeger:4317"
    otel_service_name: str = "tutoring-backend"

    # Observability UI links (for frontend dashboard)
    jaeger_ui_url: str = "http://localhost:16686"
    grafana_ui_url: str = "http://localhost:3001"
    langsmith_ui_url: str = "https://smith.langchain.com"

    # File storage
    upload_dir: str = "/app/uploads"
    max_upload_size_mb: int = 50

    # RAG
    chunk_size: int = 1000
    chunk_overlap: int = 200
    retrieval_top_k: int = 5

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
