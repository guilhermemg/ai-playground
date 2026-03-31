import pytest


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_observability_links(client):
    response = await client.get("/api/config/observability")
    assert response.status_code == 200
    data = response.json()
    assert "jaeger_url" in data
    assert "grafana_url" in data
    assert "langsmith_url" in data
