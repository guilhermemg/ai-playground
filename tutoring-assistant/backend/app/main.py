import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.config.settings import get_settings
from app.db.session import init_db, sync_engine, AsyncSessionLocal
from app.db.seed import seed_database
from app.observability.langsmith import setup_langsmith
from app.observability.tracing import setup_tracing

from app.api.routes import agents, questionnaires, documents, chat, prompts, evaluation
from app.db.models import Questionnaire, QuestionnaireStatus

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def _reset_stuck_evaluations(db) -> None:
    """Reset any questionnaires stuck in EVALUATING from a previous crash."""
    from sqlalchemy import update
    result = await db.execute(
        update(Questionnaire)
        .where(Questionnaire.status == QuestionnaireStatus.EVALUATING)
        .values(status=QuestionnaireStatus.PENDING)
    )
    if result.rowcount:
        await db.commit()
        logger.info("Reset %d stuck evaluations to PENDING", result.rowcount)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info(f"Starting {settings.app_name}")

    setup_langsmith()
    await init_db()

    async with AsyncSessionLocal() as db:
        await seed_database(db)
        await _reset_stuck_evaluations(db)

    yield

    logger.info("Shutting down")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    setup_tracing(app=app, engine=sync_engine)

    Instrumentator().instrument(app).expose(app)

    app.include_router(agents.router)
    app.include_router(questionnaires.router)
    app.include_router(documents.router)
    app.include_router(chat.router)
    app.include_router(prompts.router)
    app.include_router(evaluation.router)

    @app.get("/api/health")
    async def health():
        return {"status": "healthy"}

    @app.get("/api/config/observability")
    async def observability_links():
        return {
            "jaeger_url": settings.jaeger_ui_url,
            "grafana_url": settings.grafana_ui_url,
            "langsmith_url": settings.langsmith_ui_url,
        }

    return app


app = create_app()
