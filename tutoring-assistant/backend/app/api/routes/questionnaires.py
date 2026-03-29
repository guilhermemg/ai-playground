from __future__ import annotations

import json
import logging
import time
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db, AsyncSessionLocal
from app.db.models import Questionnaire, QuestionnaireResult, QuestionnaireStatus
import asyncio

from app.graph.router import load_agents_from_db
from app.graph.nodes import _parse_agent_output
from app.observability.metrics import QUESTIONNAIRE_EVAL_DURATION, AGENT_INVOCATIONS, ROUTING_DECISIONS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/questionnaires", tags=["questionnaires"])


class QuestionItem(BaseModel):
    question: str
    answer: str


class QuestionnaireCreate(BaseModel):
    title: str
    questions: list[QuestionItem]


class QuestionnaireResponse(BaseModel):
    id: UUID
    title: str
    content: str
    status: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class ResultResponse(BaseModel):
    id: UUID
    question_text: str
    answer_text: str
    agent_domain: str
    feedback: str
    score: Optional[float] = None
    is_correct: Optional[bool] = None
    correct_answer: Optional[str] = None

    model_config = {"from_attributes": True}


class QuestionnaireDetailResponse(BaseModel):
    id: UUID
    title: str
    status: str
    created_at: str
    results: list[ResultResponse]


@router.post("", status_code=status.HTTP_201_CREATED, response_model=QuestionnaireResponse)
async def create_questionnaire(body: QuestionnaireCreate, db: AsyncSession = Depends(get_db)):
    content = json.dumps([q.model_dump() for q in body.questions])
    questionnaire = Questionnaire(title=body.title, content=content)
    db.add(questionnaire)
    await db.commit()
    await db.refresh(questionnaire)
    return _to_response(questionnaire)


@router.get("", response_model=list[QuestionnaireResponse])
async def list_questionnaires(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Questionnaire).order_by(Questionnaire.created_at.desc()))
    return [_to_response(q) for q in result.scalars().all()]


@router.get("/{questionnaire_id}", response_model=QuestionnaireDetailResponse)
async def get_questionnaire(questionnaire_id: UUID, db: AsyncSession = Depends(get_db)):
    questionnaire = await _get_or_404(questionnaire_id, db)
    result = await db.execute(
        select(QuestionnaireResult)
        .where(QuestionnaireResult.questionnaire_id == questionnaire_id)
        .order_by(QuestionnaireResult.created_at)
    )
    results = result.scalars().all()
    return QuestionnaireDetailResponse(
        id=questionnaire.id,
        title=questionnaire.title,
        status=questionnaire.status.value,
        created_at=questionnaire.created_at.isoformat(),
        results=[
            ResultResponse(
                id=r.id,
                question_text=r.question_text,
                answer_text=r.answer_text,
                agent_domain=r.agent_domain or "",
                feedback=r.feedback or "",
                score=r.score,
                is_correct=r.is_correct,
                correct_answer=r.correct_answer,
            )
            for r in results
        ],
    )


@router.post("/{questionnaire_id}/evaluate")
async def evaluate_questionnaire(
    questionnaire_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    questionnaire = await _get_or_404(questionnaire_id, db)
    if questionnaire.status == QuestionnaireStatus.EVALUATING:
        raise HTTPException(status_code=409, detail="Evaluation already in progress")

    await db.execute(
        delete(QuestionnaireResult)
        .where(QuestionnaireResult.questionnaire_id == questionnaire_id)
    )
    questionnaire.status = QuestionnaireStatus.EVALUATING
    await db.commit()

    return StreamingResponse(
        _stream_evaluation(questionnaire_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _evaluate_single_question(
    idx: int,
    question: dict,
    agents: dict,
    active_agents_info: dict,
) -> dict:
    """Route and evaluate a single question in isolation."""
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage
    from app.config.settings import get_settings

    settings = get_settings()
    llm = ChatOpenAI(model=settings.openai_router_model, temperature=0.0, api_key=settings.openai_api_key)

    agent_descriptions = "\n".join(
        f'- "{agent_id}": {info["name"]} (domain: {info["domain"]}) — {info.get("description", "")}'
        for agent_id, info in active_agents_info.items()
    )

    response = await llm.ainvoke([
        SystemMessage(content=f"""You are a routing classifier. Given a question, determine which expert agent is best suited to answer it.

Available agents:
{agent_descriptions}

Respond with ONLY the agent_id string (e.g., "abc123"). If no agent is a good fit, respond with "fallback"."""),
        HumanMessage(content=f"Question: {question['question']}\nStudent Answer: {question['answer']}"),
    ])

    selected = response.content.strip().strip('"')
    if selected not in agents:
        selected = next(iter(agents))

    agent = agents[selected]
    try:
        result = await agent.ainvoke(question["question"], question["answer"])
        feedback, is_correct, correct_answer = _parse_agent_output(result["output"])
        return {
            "question_index": idx,
            "agent_id": result["agent_id"],
            "agent_name": result["agent_name"],
            "domain": result["domain"],
            "feedback": feedback,
            "is_correct": is_correct,
            "correct_answer": correct_answer,
            "question_text": question["question"],
            "answer_text": question["answer"],
        }
    except Exception as e:
        logger.error(f"Agent execution failed for Q{idx + 1}: {e}")
        return {
            "question_index": idx,
            "agent_id": str(agent.agent_id),
            "agent_name": agent.name,
            "domain": agent.domain,
            "feedback": f"Error during evaluation: {str(e)}",
            "is_correct": None,
            "correct_answer": None,
            "question_text": question["question"],
            "answer_text": question["answer"],
        }


async def _stream_evaluation(questionnaire_id: UUID):
    """Run evaluation with all questions in parallel, streaming each result via SSE as it completes."""
    start = time.time()
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(Questionnaire).where(Questionnaire.id == questionnaire_id)
            )
            questionnaire = result.scalar_one()
            questions = json.loads(questionnaire.content)

            agents = await load_agents_from_db(db)
            if not agents:
                questionnaire.status = QuestionnaireStatus.FAILED
                await db.commit()
                yield f"data: {json.dumps({'type': 'error', 'message': 'No active agents available'})}\n\n"
                return

            active_agents_info = {
                aid: {"name": a.name, "domain": a.domain, "description": ""}
                for aid, a in agents.items()
            }

            yield f"data: {json.dumps({'type': 'start', 'total': len(questions)})}\n\n"

            pending = {
                asyncio.create_task(
                    _evaluate_single_question(idx, q, agents, active_agents_info)
                ): idx
                for idx, q in enumerate(questions)
            }

            completed = 0
            while pending:
                done, _ = await asyncio.wait(pending.keys(), return_when=asyncio.FIRST_COMPLETED)
                for task in done:
                    resp = task.result()
                    completed += 1

                    AGENT_INVOCATIONS.labels(
                        agent_name=resp.get("agent_name", ""),
                        domain=resp.get("domain", ""),
                    ).inc()
                    ROUTING_DECISIONS.labels(selected_domain=resp.get("domain", "")).inc()

                    is_correct = resp.get("is_correct")
                    score = 100.0 if is_correct else 0.0 if is_correct is not None else None

                    db_result = QuestionnaireResult(
                        questionnaire_id=questionnaire_id,
                        question_text=resp.get("question_text", ""),
                        answer_text=resp.get("answer_text", ""),
                        agent_id=UUID(resp["agent_id"]) if resp.get("agent_id") else None,
                        agent_domain=resp.get("domain", ""),
                        feedback=resp.get("feedback", ""),
                        score=score,
                        is_correct=is_correct,
                        correct_answer=resp.get("correct_answer"),
                    )
                    db.add(db_result)
                    await db.flush()
                    await db.refresh(db_result)

                    event_data = {
                        "type": "result",
                        "completed": completed,
                        "total": len(questions),
                        "result": {
                            "id": str(db_result.id),
                            "question_index": resp["question_index"],
                            "question_text": resp.get("question_text", ""),
                            "answer_text": resp.get("answer_text", ""),
                            "agent_domain": resp.get("domain", ""),
                            "feedback": resp.get("feedback", ""),
                            "is_correct": is_correct,
                            "correct_answer": resp.get("correct_answer"),
                            "score": score,
                        },
                    }
                    yield f"data: {json.dumps(event_data)}\n\n"

                    del pending[task]

            questionnaire.status = QuestionnaireStatus.COMPLETED
            await db.commit()

            elapsed = time.time() - start
            QUESTIONNAIRE_EVAL_DURATION.observe(elapsed)
            logger.info(f"Evaluation of {questionnaire_id} completed in {elapsed:.2f}s")

            yield f"data: {json.dumps({'type': 'done', 'elapsed': round(elapsed, 2)})}\n\n"

        except Exception as e:
            logger.exception(f"Evaluation failed for {questionnaire_id}: {e}")
            questionnaire.status = QuestionnaireStatus.FAILED
            await db.commit()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


async def _get_or_404(questionnaire_id: UUID, db: AsyncSession) -> Questionnaire:
    result = await db.execute(select(Questionnaire).where(Questionnaire.id == questionnaire_id))
    q = result.scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=404, detail="Questionnaire not found")
    return q


def _to_response(q: Questionnaire) -> QuestionnaireResponse:
    return QuestionnaireResponse(
        id=q.id,
        title=q.title,
        content=q.content,
        status=q.status.value,
        created_at=q.created_at.isoformat() if q.created_at else "",
        updated_at=q.updated_at.isoformat() if q.updated_at else "",
    )
