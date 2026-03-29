from __future__ import annotations

import logging
from typing import Any
from functools import partial

from langgraph.graph import StateGraph, END

from app.agents.dynamic_expert import DynamicExpertAgent
from app.graph.state import GraphState, ChatState
from app.graph.nodes import router_node, agent_node, chat_router_node

logger = logging.getLogger(__name__)


def build_evaluation_graph(
    agents: dict[str, DynamicExpertAgent],
) -> StateGraph:
    """Build a LangGraph for questionnaire evaluation.

    The graph processes questions one at a time:
    START -> router -> selected_agent -> check_done -> router (loop) or END
    """
    workflow = StateGraph(GraphState)
    workflow.add_node("router", router_node)

    for agent_id, agent in agents.items():
        node_name = f"agent_{agent_id}"
        workflow.add_node(node_name, partial(agent_node, agent_callable=agent))

    def route_to_agent(state: GraphState) -> str:
        if state["current_question_index"] > len(state["questions"]):
            return END

        decisions = state["routing_decisions"]
        if not decisions:
            return END

        latest = decisions[-1]
        selected = latest["selected_agent"]
        node_name = f"agent_{selected}"

        if node_name not in [f"agent_{aid}" for aid in agents]:
            fallback_id = next(iter(agents))
            return f"agent_{fallback_id}"

        return node_name

    edge_map = {f"agent_{aid}": f"agent_{aid}" for aid in agents}
    edge_map[END] = END
    workflow.add_conditional_edges("router", route_to_agent, edge_map)

    def check_done(state: GraphState) -> str:
        if state["current_question_index"] >= len(state["questions"]):
            return END
        return "router"

    for agent_id in agents:
        node_name = f"agent_{agent_id}"
        workflow.add_conditional_edges(node_name, check_done, {"router": "router", END: END})

    workflow.set_entry_point("router")

    return workflow.compile()


def build_chat_graph(
    agents: dict[str, DynamicExpertAgent],
) -> StateGraph:
    """Build a LangGraph for the streaming chat interface."""
    workflow = StateGraph(ChatState)

    workflow.add_node("router", chat_router_node)

    for agent_id, agent in agents.items():
        node_name = f"agent_{agent_id}"

        async def _chat_agent_node(state: ChatState, _agent=agent) -> dict:
            result = await _agent.ainvoke(state["message"], "")
            return {"agent_response": result["output"]}

        workflow.add_node(node_name, _chat_agent_node)

    def route_chat(state: ChatState) -> str:
        selected = state.get("routing_decision", "")
        node_name = f"agent_{selected}"
        if node_name not in [f"agent_{aid}" for aid in agents]:
            fallback_id = next(iter(agents))
            return f"agent_{fallback_id}"
        return node_name

    edge_map = {f"agent_{aid}": f"agent_{aid}" for aid in agents}
    workflow.add_conditional_edges("router", route_chat, edge_map)

    for agent_id in agents:
        workflow.add_edge(f"agent_{agent_id}", END)

    workflow.set_entry_point("router")

    return workflow.compile()


async def load_agents_from_db(db_session) -> dict[str, DynamicExpertAgent]:
    """Load all active agents from the database and instantiate them."""
    from sqlalchemy import select
    from app.db.models import Agent, PromptVersion
    from app.rag.embeddings import get_retriever

    stmt = select(Agent).where(Agent.is_active.is_(True))
    result = await db_session.execute(stmt)
    db_agents = result.scalars().all()

    agents = {}
    retriever = None

    for db_agent in db_agents:
        prompt_stmt = select(PromptVersion).where(
            PromptVersion.id == db_agent.active_prompt_version_id
        )
        prompt_result = await db_session.execute(prompt_stmt)
        prompt = prompt_result.scalar_one_or_none()

        if not prompt:
            logger.warning(f"Agent {db_agent.name} has no active prompt, skipping")
            continue

        has_rag = "rag_retrieval" in (db_agent.enabled_tools or [])
        namespace = f"agent_{db_agent.id}" if has_rag else None

        if has_rag and retriever is None:
            retriever = get_retriever()

        agent = DynamicExpertAgent(
            agent_id=str(db_agent.id),
            name=db_agent.name,
            domain=db_agent.domain,
            system_message=prompt.system_message,
            full_prompt=prompt.full_prompt,
            enabled_tools=db_agent.enabled_tools or [],
            retriever=retriever if has_rag else None,
            agent_namespace=namespace,
        )
        agents[str(db_agent.id)] = agent

    return agents
