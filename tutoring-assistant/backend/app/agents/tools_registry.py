from __future__ import annotations

from typing import TYPE_CHECKING
from langchain_community.tools import DuckDuckGoSearchRun, WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_core.tools import Tool

if TYPE_CHECKING:
    from app.rag.embeddings import PineconeRetriever

TOOL_DEFINITIONS: dict[str, dict] = {
    "calculator": {
        "description": "Useful for mathematical computations and arithmetic",
    },
    "web_search": {
        "description": "Search the web for current information using DuckDuckGo",
    },
    "wikipedia": {
        "description": "Look up factual information on Wikipedia",
    },
    "rag_retrieval": {
        "description": "Retrieve relevant content from uploaded documents assigned to this agent",
    },
}


def _build_calculator() -> Tool:
    from langchain_community.tools import ShellTool
    import numexpr

    def _safe_calc(expression: str) -> str:
        try:
            result = numexpr.evaluate(expression.strip())
            return str(result)
        except Exception as e:
            return f"Error evaluating expression: {e}"

    return Tool(
        name="calculator",
        func=_safe_calc,
        description="Evaluate a mathematical expression. Input must be a valid numeric expression (e.g. '2 + 3 * 4').",
    )


def _build_web_search() -> Tool:
    search = DuckDuckGoSearchRun()
    return Tool(
        name="web_search",
        func=search.run,
        description="Search the web for current information. Input should be a search query string.",
    )


def _build_wikipedia() -> Tool:
    wiki = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper(top_k_results=2, doc_content_chars_max=2000))
    return Tool(
        name="wikipedia",
        func=wiki.run,
        description="Look up factual information on Wikipedia. Input should be a topic or concept to search.",
    )


def _build_rag_retrieval(retriever: PineconeRetriever, namespace: str) -> Tool:
    def _retrieve(query: str) -> str:
        docs = retriever.retrieve(query, namespace=namespace)
        if not docs:
            return "No relevant documents found."
        return "\n\n---\n\n".join(
            f"[Source: {d.metadata.get('source', 'unknown')}]\n{d.page_content}" for d in docs
        )

    return Tool(
        name="rag_retrieval",
        func=_retrieve,
        description="Retrieve relevant content from uploaded documents. Input should be a question or topic to search for in the knowledge base.",
    )


def build_tools(
    enabled_tools: list[str],
    retriever: PineconeRetriever | None = None,
    agent_namespace: str | None = None,
) -> list[Tool]:
    tools = []
    for tool_name in enabled_tools:
        if tool_name == "calculator":
            tools.append(_build_calculator())
        elif tool_name == "web_search":
            tools.append(_build_web_search())
        elif tool_name == "wikipedia":
            tools.append(_build_wikipedia())
        elif tool_name == "rag_retrieval" and retriever and agent_namespace:
            tools.append(_build_rag_retrieval(retriever, agent_namespace))
    return tools


def list_available_tools() -> list[dict]:
    return [{"name": k, **v} for k, v in TOOL_DEFINITIONS.items()]
