from __future__ import annotations
from typing import TypedDict, Annotated
import operator


class QuestionInput(TypedDict):
    question: str
    answer: str


class RoutingDecision(TypedDict):
    question_index: int
    question: str
    answer: str
    selected_agent: str


class AgentResponse(TypedDict):
    question_index: int
    agent_id: str
    agent_name: str
    domain: str
    feedback: str
    score: float | None


class GraphState(TypedDict):
    questions: list[QuestionInput]
    routing_decisions: Annotated[list[RoutingDecision], operator.add]
    agent_responses: Annotated[list[AgentResponse], operator.add]
    current_question_index: int
    active_agents: dict[str, dict]
    error: str | None


class ChatState(TypedDict):
    message: str
    routing_decision: str
    agent_response: str
    agent_name: str
    active_agents: dict[str, dict]
