import pytest
from unittest.mock import AsyncMock, MagicMock

from app.graph.nodes import agent_node


@pytest.mark.asyncio
async def test_agent_node_success():
    mock_agent = MagicMock()
    mock_agent.agent_id = "test-agent"
    mock_agent.name = "Test Agent"
    mock_agent.domain = "test"
    mock_agent.ainvoke = AsyncMock(return_value={
        "agent_id": "test-agent",
        "agent_name": "Test Agent",
        "domain": "test",
        "output": '{"feedback": "Good", "score": 90}',
        "intermediate_steps": [],
    })

    state = {
        "questions": [{"question": "Q1", "answer": "A1"}],
        "routing_decisions": [
            {"question_index": 0, "question": "Q1", "answer": "A1", "selected_agent": "test-agent"},
        ],
        "agent_responses": [],
        "current_question_index": 1,
        "active_agents": {},
        "error": None,
    }

    result = await agent_node(state, agent_callable=mock_agent)
    assert len(result["agent_responses"]) == 1
    assert result["agent_responses"][0]["score"] == 90.0


@pytest.mark.asyncio
async def test_agent_node_error_handling():
    mock_agent = MagicMock()
    mock_agent.agent_id = "err-agent"
    mock_agent.name = "Error Agent"
    mock_agent.domain = "error"
    mock_agent.ainvoke = AsyncMock(side_effect=Exception("LLM failed"))

    state = {
        "questions": [{"question": "Q1", "answer": "A1"}],
        "routing_decisions": [
            {"question_index": 0, "question": "Q1", "answer": "A1", "selected_agent": "err-agent"},
        ],
        "agent_responses": [],
        "current_question_index": 1,
        "active_agents": {},
        "error": None,
    }

    result = await agent_node(state, agent_callable=mock_agent)
    assert len(result["agent_responses"]) == 1
    assert "Error" in result["agent_responses"][0]["feedback"]
