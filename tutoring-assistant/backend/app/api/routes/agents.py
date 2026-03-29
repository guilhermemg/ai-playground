from __future__ import annotations

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models import Agent, PromptVersion
from app.prompts.registry import (
    create_initial_prompt,
    create_new_version,
    get_prompt_versions,
    activate_prompt_version,
)
from app.agents.tools_registry import list_available_tools

router = APIRouter(prefix="/api/agents", tags=["agents"])


class AgentCreate(BaseModel):
    name: str
    domain: str
    description: str = ""
    enabled_tools: list[str] = []
    additional_instructions: str = ""


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    enabled_tools: Optional[list[str]] = None


class PromptUpdate(BaseModel):
    system_message: str
    full_prompt: str


class AgentResponse(BaseModel):
    id: UUID
    name: str
    domain: str
    description: str
    is_active: bool
    enabled_tools: list[str]
    active_prompt_version_id: Optional[UUID] = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class PromptVersionResponse(BaseModel):
    id: UUID
    agent_id: UUID
    version: int
    system_message: str
    full_prompt: str
    created_at: str

    model_config = {"from_attributes": True}


@router.post("", status_code=status.HTTP_201_CREATED, response_model=AgentResponse)
async def create_agent(body: AgentCreate, db: AsyncSession = Depends(get_db)):
    agent = Agent(
        name=body.name,
        domain=body.domain,
        description=body.description,
        enabled_tools=body.enabled_tools,
    )
    db.add(agent)
    await db.flush()

    prompt = await create_initial_prompt(
        db, agent.id, body.name, body.domain, body.additional_instructions
    )
    agent.active_prompt_version_id = prompt.id
    await db.commit()
    await db.refresh(agent)

    return _to_response(agent)


@router.get("", response_model=list[AgentResponse])
async def list_agents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).order_by(Agent.created_at.desc()))
    agents = result.scalars().all()
    return [_to_response(a) for a in agents]


@router.get("/tools")
async def get_available_tools():
    return list_available_tools()


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: UUID, db: AsyncSession = Depends(get_db)):
    agent = await _get_agent_or_404(agent_id, db)
    return _to_response(agent)


@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: UUID, body: AgentUpdate, db: AsyncSession = Depends(get_db)):
    agent = await _get_agent_or_404(agent_id, db)

    if body.name is not None:
        agent.name = body.name
    if body.domain is not None:
        agent.domain = body.domain
    if body.description is not None:
        agent.description = body.description
    if body.is_active is not None:
        agent.is_active = body.is_active
    if body.enabled_tools is not None:
        agent.enabled_tools = body.enabled_tools

    await db.commit()
    await db.refresh(agent)
    return _to_response(agent)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(agent_id: UUID, db: AsyncSession = Depends(get_db)):
    agent = await _get_agent_or_404(agent_id, db)

    if "rag_retrieval" in (agent.enabled_tools or []):
        try:
            from app.rag.embeddings import get_retriever
            retriever = get_retriever()
            retriever.delete_namespace(f"agent_{agent_id}")
        except Exception:
            pass

    await db.delete(agent)
    await db.commit()


@router.get("/{agent_id}/prompt", response_model=PromptVersionResponse)
async def get_agent_prompt(agent_id: UUID, db: AsyncSession = Depends(get_db)):
    agent = await _get_agent_or_404(agent_id, db)
    if not agent.active_prompt_version_id:
        raise HTTPException(status_code=404, detail="No active prompt version")

    result = await db.execute(
        select(PromptVersion).where(PromptVersion.id == agent.active_prompt_version_id)
    )
    prompt = result.scalar_one_or_none()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt version not found")
    return _prompt_to_response(prompt)


@router.put("/{agent_id}/prompt", response_model=PromptVersionResponse)
async def update_agent_prompt(agent_id: UUID, body: PromptUpdate, db: AsyncSession = Depends(get_db)):
    await _get_agent_or_404(agent_id, db)
    prompt = await create_new_version(db, agent_id, body.system_message, body.full_prompt)
    await activate_prompt_version(db, agent_id, prompt.id)
    await db.commit()
    await db.refresh(prompt)
    return _prompt_to_response(prompt)


@router.get("/{agent_id}/prompt/versions", response_model=list[PromptVersionResponse])
async def list_prompt_versions(agent_id: UUID, db: AsyncSession = Depends(get_db)):
    await _get_agent_or_404(agent_id, db)
    versions = await get_prompt_versions(db, agent_id)
    return [_prompt_to_response(v) for v in versions]


@router.put("/{agent_id}/prompt/versions/{version_id}/activate")
async def activate_version(agent_id: UUID, version_id: UUID, db: AsyncSession = Depends(get_db)):
    await _get_agent_or_404(agent_id, db)
    success = await activate_prompt_version(db, agent_id, version_id)
    if not success:
        raise HTTPException(status_code=404, detail="Prompt version not found or does not belong to agent")
    await db.commit()
    return {"status": "activated"}


async def _get_agent_or_404(agent_id: UUID, db: AsyncSession) -> Agent:
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


def _to_response(agent: Agent) -> AgentResponse:
    return AgentResponse(
        id=agent.id,
        name=agent.name,
        domain=agent.domain,
        description=agent.description or "",
        is_active=agent.is_active,
        enabled_tools=agent.enabled_tools or [],
        active_prompt_version_id=agent.active_prompt_version_id,
        created_at=agent.created_at.isoformat() if agent.created_at else "",
        updated_at=agent.updated_at.isoformat() if agent.updated_at else "",
    )


def _prompt_to_response(p: PromptVersion) -> PromptVersionResponse:
    return PromptVersionResponse(
        id=p.id,
        agent_id=p.agent_id,
        version=p.version,
        system_message=p.system_message,
        full_prompt=p.full_prompt,
        created_at=p.created_at.isoformat() if p.created_at else "",
    )
