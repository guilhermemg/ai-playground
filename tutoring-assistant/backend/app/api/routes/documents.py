from __future__ import annotations

import os
import logging
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models import Document, Agent
from app.config.settings import get_settings
from app.rag.document_processor import process_and_embed

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])


class DocumentResponse(BaseModel):
    id: UUID
    filename: str
    file_type: str
    assigned_agent_id: Optional[UUID] = None
    chunk_count: int
    created_at: str

    model_config = {"from_attributes": True}


@router.post("", status_code=status.HTTP_201_CREATED, response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    settings = get_settings()
    os.makedirs(settings.upload_dir, exist_ok=True)

    ext = os.path.splitext(file.filename or "")[-1].lower()
    if ext not in (".pdf", ".docx", ".doc", ".txt", ".md"):
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    file_path = os.path.join(settings.upload_dir, file.filename or "upload")
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    doc = Document(
        filename=file.filename or "upload",
        file_path=file_path,
        file_type=ext,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    return _to_response(doc)


@router.get("", response_model=list[DocumentResponse])
async def list_documents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).order_by(Document.created_at.desc()))
    return [_to_response(d) for d in result.scalars().all()]


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: UUID, db: AsyncSession = Depends(get_db)):
    doc = await _get_or_404(document_id, db)

    if doc.pinecone_namespace:
        try:
            from app.rag.embeddings import get_retriever
            retriever = get_retriever()
            retriever.delete_namespace(doc.pinecone_namespace)
        except Exception as e:
            logger.warning(f"Failed to delete embeddings: {e}")

    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    await db.delete(doc)
    await db.commit()


@router.post("/{document_id}/assign/{agent_id}", response_model=DocumentResponse)
async def assign_document_to_agent(
    document_id: UUID,
    agent_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    doc = await _get_or_404(document_id, db)

    agent_result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = agent_result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    namespace = f"agent_{agent_id}"

    if doc.pinecone_namespace and doc.pinecone_namespace != namespace:
        try:
            from app.rag.embeddings import get_retriever
            retriever = get_retriever()
            retriever.delete_namespace(doc.pinecone_namespace)
        except Exception:
            pass

    chunk_count = process_and_embed(doc.file_path, namespace)

    doc.assigned_agent_id = agent_id
    doc.pinecone_namespace = namespace
    doc.chunk_count = chunk_count

    if "rag_retrieval" not in (agent.enabled_tools or []):
        tools = list(agent.enabled_tools or [])
        tools.append("rag_retrieval")
        agent.enabled_tools = tools

    await db.commit()
    await db.refresh(doc)

    return _to_response(doc)


async def _get_or_404(document_id: UUID, db: AsyncSession) -> Document:
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


def _to_response(doc: Document) -> DocumentResponse:
    return DocumentResponse(
        id=doc.id,
        filename=doc.filename,
        file_type=doc.file_type,
        assigned_agent_id=doc.assigned_agent_id,
        chunk_count=doc.chunk_count or 0,
        created_at=doc.created_at.isoformat() if doc.created_at else "",
    )
