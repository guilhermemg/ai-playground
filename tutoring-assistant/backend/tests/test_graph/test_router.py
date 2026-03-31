import pytest
from unittest.mock import patch, AsyncMock, MagicMock


@pytest.mark.asyncio
@patch("app.graph.nodes.ChatOpenAI")
async def test_router_selects_correct_agent(mock_llm_class):
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=MagicMock(content="agent_physics"))
    mock_llm_class.return_value = mock_llm

    from app.graph.nodes import router_node

    state = {
        "questions": [{"question": "What is gravity?", "answer": "A force"}],
        "routing_decisions": [],
        "agent_responses": [],
        "current_question_index": 0,
        "active_agents": {
            "agent_physics": {"name": "Physics Expert", "domain": "physics", "description": ""},
            "agent_math": {"name": "Math Expert", "domain": "math", "description": ""},
        },
        "error": None,
    }

    result = await router_node(state)
    assert len(result["routing_decisions"]) == 1
    assert result["routing_decisions"][0]["selected_agent"] == "agent_physics"


@pytest.mark.asyncio
@patch("app.graph.nodes.ChatOpenAI")
async def test_router_fallback_on_unknown(mock_llm_class):
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=MagicMock(content="nonexistent_agent"))
    mock_llm_class.return_value = mock_llm

    from app.graph.nodes import router_node

    state = {
        "questions": [{"question": "Random question", "answer": "An answer"}],
        "routing_decisions": [],
        "agent_responses": [],
        "current_question_index": 0,
        "active_agents": {
            "agent_1": {"name": "Agent 1", "domain": "general", "description": ""},
        },
        "error": None,
    }

    result = await router_node(state)
    assert result["routing_decisions"][0]["selected_agent"] == "agent_1"


@pytest.mark.asyncio
@patch("app.graph.nodes.ChatOpenAI")
async def test_router_past_end_of_questions(mock_llm_class):
    from app.graph.nodes import router_node

    state = {
        "questions": [{"question": "Q1", "answer": "A1"}],
        "routing_decisions": [],
        "agent_responses": [],
        "current_question_index": 5,
        "active_agents": {"a1": {"name": "A1", "domain": "d", "description": ""}},
        "error": None,
    }

    result = await router_node(state)
    assert result["routing_decisions"] == []
