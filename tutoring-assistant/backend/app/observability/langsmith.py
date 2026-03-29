import os
import logging

from app.config.settings import get_settings

logger = logging.getLogger(__name__)


def setup_langsmith():
    """Configure LangSmith tracing via environment variables.

    LangChain/LangGraph automatically pick up these env vars
    and send traces to LangSmith.
    """
    settings = get_settings()

    os.environ["LANGCHAIN_TRACING_V2"] = str(settings.langchain_tracing_v2).lower()
    os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project

    if settings.langchain_api_key:
        logger.info(f"LangSmith tracing enabled for project: {settings.langchain_project}")
    else:
        logger.warning("LangSmith API key not set, tracing will be disabled")
