import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_upload_unsupported_file(client: AsyncClient):
    response = await client.post(
        "/api/documents",
        files={"file": ("test.exe", b"binary content", "application/octet-stream")},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_list_documents_empty(client: AsyncClient):
    response = await client.get("/api/documents")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_delete_nonexistent_document(client: AsyncClient):
    import uuid
    response = await client.delete(f"/api/documents/{uuid.uuid4()}")
    assert response.status_code == 404
