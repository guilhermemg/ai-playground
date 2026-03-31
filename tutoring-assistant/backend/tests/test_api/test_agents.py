import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_agent(client: AsyncClient):
    response = await client.post("/api/agents", json={
        "name": "Physics Expert",
        "domain": "physics",
        "description": "Expert in classical and modern physics",
        "enabled_tools": ["calculator", "wikipedia"],
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Physics Expert"
    assert data["domain"] == "physics"
    assert data["is_active"] is True
    assert "calculator" in data["enabled_tools"]


@pytest.mark.asyncio
async def test_list_agents(client: AsyncClient):
    await client.post("/api/agents", json={"name": "Agent 1", "domain": "math"})
    await client.post("/api/agents", json={"name": "Agent 2", "domain": "physics"})

    response = await client.get("/api/agents")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_update_agent(client: AsyncClient):
    create_resp = await client.post("/api/agents", json={"name": "Test Agent", "domain": "test"})
    agent_id = create_resp.json()["id"]

    response = await client.patch(f"/api/agents/{agent_id}", json={
        "is_active": False,
        "enabled_tools": ["calculator"],
    })
    assert response.status_code == 200
    assert response.json()["is_active"] is False


@pytest.mark.asyncio
async def test_delete_agent(client: AsyncClient):
    create_resp = await client.post("/api/agents", json={"name": "Temp Agent", "domain": "temp"})
    agent_id = create_resp.json()["id"]

    response = await client.delete(f"/api/agents/{agent_id}")
    assert response.status_code == 204

    get_response = await client.get(f"/api/agents/{agent_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_get_agent_prompt(client: AsyncClient):
    create_resp = await client.post("/api/agents", json={"name": "Law Expert", "domain": "law"})
    agent_id = create_resp.json()["id"]

    response = await client.get(f"/api/agents/{agent_id}/prompt")
    assert response.status_code == 200
    data = response.json()
    assert "law" in data["system_message"].lower()
    assert data["version"] == 1


@pytest.mark.asyncio
async def test_update_agent_prompt(client: AsyncClient):
    create_resp = await client.post("/api/agents", json={"name": "Med Expert", "domain": "medicine"})
    agent_id = create_resp.json()["id"]

    response = await client.put(f"/api/agents/{agent_id}/prompt", json={
        "system_message": "Updated system message",
        "full_prompt": "Updated full prompt",
    })
    assert response.status_code == 200
    assert response.json()["version"] == 2


@pytest.mark.asyncio
async def test_list_prompt_versions(client: AsyncClient):
    create_resp = await client.post("/api/agents", json={"name": "Eng Expert", "domain": "engineering"})
    agent_id = create_resp.json()["id"]

    await client.put(f"/api/agents/{agent_id}/prompt", json={
        "system_message": "v2 system",
        "full_prompt": "v2 full",
    })

    response = await client.get(f"/api/agents/{agent_id}/prompt/versions")
    assert response.status_code == 200
    versions = response.json()
    assert len(versions) == 2


@pytest.mark.asyncio
async def test_get_available_tools(client: AsyncClient):
    response = await client.get("/api/agents/tools")
    assert response.status_code == 200
    tools = response.json()
    tool_names = [t["name"] for t in tools]
    assert "calculator" in tool_names
    assert "web_search" in tool_names
    assert "wikipedia" in tool_names
    assert "rag_retrieval" in tool_names
