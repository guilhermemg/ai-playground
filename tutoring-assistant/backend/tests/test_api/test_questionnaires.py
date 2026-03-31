import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_questionnaire(client: AsyncClient):
    response = await client.post("/api/questionnaires", json={
        "title": "Physics Quiz 1",
        "questions": [
            {"question": "What is Newton's first law?", "answer": "An object at rest stays at rest"},
            {"question": "What is F=ma?", "answer": "Force equals mass times acceleration"},
        ],
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Physics Quiz 1"
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_list_questionnaires(client: AsyncClient):
    await client.post("/api/questionnaires", json={
        "title": "Quiz 1",
        "questions": [{"question": "Q1", "answer": "A1"}],
    })
    await client.post("/api/questionnaires", json={
        "title": "Quiz 2",
        "questions": [{"question": "Q2", "answer": "A2"}],
    })

    response = await client.get("/api/questionnaires")
    assert response.status_code == 200
    assert len(response.json()) >= 2


@pytest.mark.asyncio
async def test_get_questionnaire_detail(client: AsyncClient):
    create_resp = await client.post("/api/questionnaires", json={
        "title": "Detail Quiz",
        "questions": [{"question": "Q1", "answer": "A1"}],
    })
    qid = create_resp.json()["id"]

    response = await client.get(f"/api/questionnaires/{qid}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Detail Quiz"
    assert data["results"] == []


@pytest.mark.asyncio
async def test_questionnaire_not_found(client: AsyncClient):
    import uuid
    response = await client.get(f"/api/questionnaires/{uuid.uuid4()}")
    assert response.status_code == 404
