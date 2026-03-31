from __future__ import annotations

import logging
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db, AsyncSessionLocal
from app.db.models import EvaluationRun, EvaluationRunStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])


class EvalRunRequest(BaseModel):
    domain: Optional[str] = None


class EvalRunResponse(BaseModel):
    id: UUID
    status: str
    dataset_domain: Optional[str] = None
    results: Optional[dict] = None
    triggered_at: str
    completed_at: Optional[str] = None

    model_config = {"from_attributes": True}


@router.post("/run", response_model=EvalRunResponse)
async def trigger_evaluation(
    body: EvalRunRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    run = EvaluationRun(dataset_domain=body.domain)
    db.add(run)
    await db.commit()
    await db.refresh(run)

    background_tasks.add_task(_run_evaluation, run.id, body.domain)

    return _to_response(run)


@router.get("/results", response_model=list[EvalRunResponse])
async def list_evaluation_results(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(EvaluationRun).order_by(EvaluationRun.triggered_at.desc())
    )
    return [_to_response(r) for r in result.scalars().all()]


@router.get("/results/{run_id}", response_model=EvalRunResponse)
async def get_evaluation_result(run_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EvaluationRun).where(EvaluationRun.id == run_id))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Evaluation run not found")
    return _to_response(run)


async def _run_evaluation(run_id: UUID, domain: str | None):
    from datetime import datetime, timezone

    async with AsyncSessionLocal() as db:
        try:
            from app.evaluation.ragas_evaluator import run_ragas_evaluation

            results = await run_ragas_evaluation(db, domain)

            result = await db.execute(
                select(EvaluationRun).where(EvaluationRun.id == run_id)
            )
            run = result.scalar_one()
            run.status = EvaluationRunStatus.COMPLETED
            run.results = results
            run.completed_at = datetime.now(timezone.utc)
            await db.commit()

        except Exception as e:
            logger.exception(f"Evaluation run {run_id} failed: {e}")
            result = await db.execute(
                select(EvaluationRun).where(EvaluationRun.id == run_id)
            )
            run = result.scalar_one()
            run.status = EvaluationRunStatus.FAILED
            run.results = {"error": str(e)}
            run.completed_at = datetime.now(timezone.utc)
            await db.commit()


def _to_response(run: EvaluationRun) -> EvalRunResponse:
    return EvalRunResponse(
        id=run.id,
        status=run.status.value,
        dataset_domain=run.dataset_domain,
        results=run.results,
        triggered_at=run.triggered_at.isoformat() if run.triggered_at else "",
        completed_at=run.completed_at.isoformat() if run.completed_at else None,
    )
