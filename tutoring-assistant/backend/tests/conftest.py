import os
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.db.models import Base
from app.db.session import get_db


os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("DATABASE_URL_SYNC", "sqlite:///./test.db")
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("PINECONE_API_KEY", "test-key")
os.environ.setdefault("LANGCHAIN_API_KEY", "test-key")
os.environ.setdefault("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")


TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session():
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session):
    with patch("app.observability.tracing.setup_tracing"):
        from app.main import create_app

        app = create_app()

        async def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c


@pytest.fixture
def mock_llm():
    llm = MagicMock()
    llm.ainvoke = AsyncMock(return_value=MagicMock(content='{"feedback": "Good answer", "score": 85}'))
    return llm


@pytest.fixture
def mock_retriever():
    retriever = MagicMock()
    retriever.retrieve = MagicMock(return_value=[])
    retriever.upsert = MagicMock(return_value=5)
    retriever.delete_namespace = MagicMock()
    return retriever
