import pytest
from app.agents.tools_registry import build_tools, list_available_tools, TOOL_DEFINITIONS


def test_list_available_tools():
    tools = list_available_tools()
    assert len(tools) == len(TOOL_DEFINITIONS)
    names = [t["name"] for t in tools]
    assert "calculator" in names
    assert "web_search" in names
    assert "wikipedia" in names
    assert "rag_retrieval" in names


def test_build_calculator_tool():
    tools = build_tools(["calculator"])
    assert len(tools) == 1
    assert tools[0].name == "calculator"
    result = tools[0].func("2 + 3 * 4")
    assert "14" in result


def test_build_empty_tools():
    tools = build_tools([])
    assert tools == []


def test_build_unknown_tool():
    tools = build_tools(["nonexistent"])
    assert tools == []


def test_rag_tool_requires_retriever():
    tools = build_tools(["rag_retrieval"])
    assert tools == []
