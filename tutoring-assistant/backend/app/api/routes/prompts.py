from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models import PromptVersion

router = APIRouter(prefix="/api/prompts", tags=["prompts"])


@router.get("/versions")
async def list_all_prompt_versions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PromptVersion).order_by(PromptVersion.created_at.desc())
    )
    versions = result.scalars().all()
    return [
        {
            "id": str(v.id),
            "agent_id": str(v.agent_id),
            "version": v.version,
            "system_message": v.system_message,
            "full_prompt": v.full_prompt,
            "created_at": v.created_at.isoformat() if v.created_at else "",
        }
        for v in versions
    ]
