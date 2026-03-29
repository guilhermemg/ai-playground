from __future__ import annotations

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.db.session import AsyncSessionLocal
from app.graph.router import load_agents_from_db, build_chat_graph

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


@router.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket):
    await websocket.accept()

    try:
        async with AsyncSessionLocal() as db:
            agents = await load_agents_from_db(db)

        if not agents:
            await websocket.send_json({"type": "error", "content": "No active agents available"})
            await websocket.close()
            return

        active_agents_info = {
            aid: {"name": a.name, "domain": a.domain}
            for aid, a in agents.items()
        }

        await websocket.send_json({
            "type": "system",
            "content": "Connected to tutoring assistant",
            "agents": [
                {"id": aid, "name": info["name"], "domain": info["domain"]}
                for aid, info in active_agents_info.items()
            ],
        })

        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                user_message = message.get("message", data)
            except json.JSONDecodeError:
                user_message = data

            selected_agent_id = None
            selected_agent = None

            # Route the message
            from app.graph.nodes import chat_router_node
            from app.graph.state import ChatState

            route_state: ChatState = {
                "message": user_message,
                "routing_decision": "",
                "agent_response": "",
                "agent_name": "",
                "active_agents": active_agents_info,
            }
            route_result = await chat_router_node(route_state)
            selected_agent_id = route_result["routing_decision"]
            agent_name = route_result["agent_name"]

            if selected_agent_id in agents:
                selected_agent = agents[selected_agent_id]

            if not selected_agent:
                selected_agent = next(iter(agents.values()))
                agent_name = selected_agent.name

            await websocket.send_json({
                "type": "routing",
                "agent_name": agent_name,
                "domain": selected_agent.domain,
            })

            # Stream response
            async for token in selected_agent.astream(user_message):
                await websocket.send_json({
                    "type": "token",
                    "content": token,
                    "agent_name": agent_name,
                })

            await websocket.send_json({
                "type": "done",
                "agent_name": agent_name,
            })

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.exception(f"WebSocket error: {e}")
        try:
            await websocket.send_json({"type": "error", "content": str(e)})
        except Exception:
            pass
