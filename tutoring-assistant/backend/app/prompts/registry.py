from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PromptVersion, Agent
from app.agents.standard_template import generate_prompt, generate_prompt_v1

logger = logging.getLogger(__name__)


async def create_initial_prompt(
    db: AsyncSession,
    agent_id: UUID,
    agent_name: str,
    domain: str,
    additional_instructions: str = "",
) -> PromptVersion:
    v1_data = generate_prompt_v1(agent_name, domain, additional_instructions)
    v1 = PromptVersion(
        agent_id=agent_id,
        version=1,
        system_message=v1_data["system_message"],
        full_prompt=v1_data["full_prompt"],
    )
    db.add(v1)
    await db.flush()

    v2_data = generate_prompt(agent_name, domain, additional_instructions)
    v2 = PromptVersion(
        agent_id=agent_id,
        version=2,
        system_message=v2_data["system_message"],
        full_prompt=v2_data["full_prompt"],
    )
    db.add(v2)
    await db.flush()
    return v2


async def create_new_version(
    db: AsyncSession,
    agent_id: UUID,
    system_message: str,
    full_prompt: str,
) -> PromptVersion:
    max_version = await db.execute(
        select(func.max(PromptVersion.version)).where(PromptVersion.agent_id == agent_id)
    )
    current_max = max_version.scalar() or 0

    prompt = PromptVersion(
        agent_id=agent_id,
        version=current_max + 1,
        system_message=system_message,
        full_prompt=full_prompt,
    )
    db.add(prompt)
    await db.flush()
    return prompt


async def get_prompt_versions(db: AsyncSession, agent_id: UUID) -> list[PromptVersion]:
    result = await db.execute(
        select(PromptVersion)
        .where(PromptVersion.agent_id == agent_id)
        .order_by(PromptVersion.version.desc())
    )
    return list(result.scalars().all())


async def get_prompt_version(db: AsyncSession, prompt_id: UUID) -> PromptVersion | None:
    result = await db.execute(select(PromptVersion).where(PromptVersion.id == prompt_id))
    return result.scalar_one_or_none()


async def activate_prompt_version(
    db: AsyncSession, agent_id: UUID, prompt_version_id: UUID
) -> bool:
    prompt = await get_prompt_version(db, prompt_version_id)
    if not prompt or prompt.agent_id != agent_id:
        return False

    agent_result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = agent_result.scalar_one_or_none()
    if not agent:
        return False

    agent.active_prompt_version_id = prompt_version_id
    await db.flush()
    return True
