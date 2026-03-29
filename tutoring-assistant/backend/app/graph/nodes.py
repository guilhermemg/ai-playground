from __future__ import annotations

import json
import logging
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config.settings import get_settings
from app.graph.state import GraphState, ChatState
from app.observability.metrics import LLM_TOKENS_USED

logger = logging.getLogger(__name__)


def _record_token_usage(response, model: str) -> None:
    usage = getattr(response, "usage_metadata", None) or {}
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)
    if input_tokens:
        LLM_TOKENS_USED.labels(model=model, type="input").inc(input_tokens)
    if output_tokens:
        LLM_TOKENS_USED.labels(model=model, type="output").inc(output_tokens)


async def router_node(state: GraphState) -> dict:
    """Routes each question to the most appropriate active agent."""
    settings = get_settings()
    llm = ChatOpenAI(model=settings.openai_router_model, temperature=0.0, api_key=settings.openai_api_key)

    active_agents = state["active_agents"]
    idx = state["current_question_index"]
    questions = state["questions"]

    if idx >= len(questions):
        return {"routing_decisions": [], "current_question_index": idx}

    q = questions[idx]
    agent_descriptions = "\n".join(
        f'- "{agent_id}": {info["name"]} (domain: {info["domain"]}) — {info.get("description", "")}'
        for agent_id, info in active_agents.items()
    )

    system_prompt = f"""You are a routing classifier. Given a question, determine which expert agent is best suited to answer it.

Available agents:
{agent_descriptions}

Respond with ONLY the agent_id string (e.g., "abc123"). If no agent is a good fit, respond with "fallback"."""

    response = await llm.ainvoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Question: {q['question']}\nStudent Answer: {q['answer']}"),
    ])

    _record_token_usage(response, settings.openai_router_model)

    selected = response.content.strip().strip('"')
    if selected not in active_agents:
        selected = next(iter(active_agents)) if active_agents else "fallback"

    decision = {
        "question_index": idx,
        "question": q["question"],
        "answer": q["answer"],
        "selected_agent": selected,
    }

    return {"routing_decisions": [decision], "current_question_index": idx + 1}


def _parse_agent_output(raw_output: str) -> tuple[str, bool | None, str | None]:
    """Extract feedback, is_correct flag, and correct_answer from agent output.

    Supports v2 (is_correct boolean) and falls back to v1 (score 0-100).
    Returns (feedback, is_correct, correct_answer).
    """
    text = raw_output.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

    try:
        parsed = json.loads(text)
        feedback = parsed.get("feedback", "")
        correct_answer = parsed.get("correct_answer")

        if "is_correct" in parsed:
            is_correct = bool(parsed["is_correct"])
        elif "score" in parsed:
            try:
                is_correct = float(parsed["score"]) >= 50
            except (ValueError, TypeError):
                is_correct = None
        else:
            is_correct = None

        return feedback, is_correct, correct_answer
    except (json.JSONDecodeError, ValueError, TypeError):
        return raw_output, None, None


async def agent_node(state: GraphState, agent_callable: Any) -> dict:
    """Executes the selected agent on the routed question."""
    decisions = state["routing_decisions"]
    responses = []

    for decision in decisions:
        if decision.get("question_index") != state["current_question_index"] - 1:
            continue
        try:
            result = await agent_callable.ainvoke(decision["question"], decision["answer"])
            feedback, is_correct, correct_answer = _parse_agent_output(result["output"])

            response_data = {
                "question_index": decision["question_index"],
                "agent_id": result["agent_id"],
                "agent_name": result["agent_name"],
                "domain": result["domain"],
                "feedback": feedback,
                "is_correct": is_correct,
                "correct_answer": correct_answer,
            }
            responses.append(response_data)
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            responses.append({
                "question_index": decision["question_index"],
                "agent_id": str(agent_callable.agent_id),
                "agent_name": agent_callable.name,
                "domain": agent_callable.domain,
                "feedback": f"Error during evaluation: {str(e)}",
                "is_correct": None,
                "correct_answer": None,
            })

    return {"agent_responses": responses}


async def chat_router_node(state: ChatState) -> dict:
    """Routes a chat message to the best agent."""
    settings = get_settings()
    llm = ChatOpenAI(model=settings.openai_router_model, temperature=0.0, api_key=settings.openai_api_key)

    active_agents = state["active_agents"]
    agent_descriptions = "\n".join(
        f'- "{agent_id}": {info["name"]} (domain: {info["domain"]})'
        for agent_id, info in active_agents.items()
    )

    response = await llm.ainvoke([
        SystemMessage(content=f"""Route this question to the best agent.

Available agents:
{agent_descriptions}

Respond with ONLY the agent_id string."""),
        HumanMessage(content=state["message"]),
    ])

    _record_token_usage(response, settings.openai_router_model)

    selected = response.content.strip().strip('"')
    if selected not in active_agents:
        selected = next(iter(active_agents)) if active_agents else "fallback"

    agent_info = active_agents.get(selected, {})
    return {
        "routing_decision": selected,
        "agent_name": agent_info.get("name", "General Agent"),
    }
