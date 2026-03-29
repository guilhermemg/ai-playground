import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from app.agents.dynamic_expert import DynamicExpertAgent
from app.agents.standard_template import generate_prompt


def test_generate_prompt():
    result = generate_prompt("Physics Expert", "Physics", "Focus on mechanics")
    assert "Physics" in result["system_message"]
    assert "Focus on mechanics" in result["system_message"]
    assert "Physics Expert" in result["full_prompt"]


def test_generate_prompt_no_additional():
    result = generate_prompt("Math Expert", "Mathematics")
    assert "Mathematics" in result["system_message"]
    assert "Math Expert" in result["full_prompt"]


@patch("app.agents.dynamic_expert.get_settings")
def test_agent_creation_without_tools(mock_settings):
    mock_settings.return_value = MagicMock(
        openai_api_key="test-key",
        openai_model="gpt-4o",
    )

    prompt = generate_prompt("Test Agent", "Test Domain")

    agent = DynamicExpertAgent(
        agent_id="test-id",
        name="Test Agent",
        domain="Test Domain",
        system_message=prompt["system_message"],
        full_prompt=prompt["full_prompt"],
        enabled_tools=[],
    )

    assert agent.name == "Test Agent"
    assert agent.domain == "Test Domain"
    assert agent.tools == []
    assert agent.executor is None


@patch("app.agents.dynamic_expert.get_settings")
def test_agent_creation_with_calculator(mock_settings):
    mock_settings.return_value = MagicMock(
        openai_api_key="test-key",
        openai_model="gpt-4o",
    )

    prompt = generate_prompt("Math Agent", "Math")

    agent = DynamicExpertAgent(
        agent_id="math-id",
        name="Math Agent",
        domain="Math",
        system_message=prompt["system_message"],
        full_prompt=prompt["full_prompt"],
        enabled_tools=["calculator"],
    )

    assert len(agent.tools) == 1
    assert agent.tools[0].name == "calculator"
    assert agent.executor is not None
