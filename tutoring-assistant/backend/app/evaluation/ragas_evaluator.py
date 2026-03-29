from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
    answer_correctness,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.graph.router import load_agents_from_db, build_evaluation_graph
from app.graph.state import GraphState

logger = logging.getLogger(__name__)

GOLDEN_DATASETS_DIR = Path(__file__).parent / "golden_datasets"


def load_golden_dataset(domain: str | None = None) -> list[dict]:
    datasets = []
    for f in GOLDEN_DATASETS_DIR.glob("*.json"):
        with open(f) as fh:
            data = json.load(fh)
            if domain and data.get("domain") != domain:
                continue
            for q in data.get("questions", []):
                q["domain"] = data.get("domain", "general")
            datasets.extend(data.get("questions", []))
    return datasets


async def run_ragas_evaluation(
    db: AsyncSession,
    domain: str | None = None,
) -> dict[str, Any]:
    golden = load_golden_dataset(domain)
    if not golden:
        return {"error": "No golden dataset found", "metrics": {}}

    agents = await load_agents_from_db(db)
    if not agents:
        return {"error": "No active agents", "metrics": {}}

    graph = build_evaluation_graph(agents)
    active_agents_info = {
        aid: {"name": a.name, "domain": a.domain, "description": ""}
        for aid, a in agents.items()
    }

    questions = []
    answers = []
    contexts_list = []
    ground_truths = []
    routing_correct = 0
    routing_total = 0

    for item in golden:
        q_input = [{"question": item["question"], "answer": item.get("ground_truth", "")}]

        state: GraphState = {
            "questions": q_input,
            "routing_decisions": [],
            "agent_responses": [],
            "current_question_index": 0,
            "active_agents": active_agents_info,
            "error": None,
        }

        try:
            final_state = await graph.ainvoke(state)
            responses = final_state.get("agent_responses", [])
            decisions = final_state.get("routing_decisions", [])

            answer = responses[0]["feedback"] if responses else "No response"
            agent_domain = responses[0].get("domain", "") if responses else ""

            questions.append(item["question"])
            answers.append(answer)
            ground_truths.append(item.get("ground_truth", ""))
            contexts_list.append(item.get("contexts", []))

            expected_agent = item.get("expected_agent", "")
            if expected_agent and decisions:
                routing_total += 1
                routed_agent_id = decisions[0].get("selected_agent", "")
                routed_agent = agents.get(routed_agent_id)
                if routed_agent and routed_agent.domain.lower() == expected_agent.lower():
                    routing_correct += 1

        except Exception as e:
            logger.error(f"Evaluation failed for question: {item['question']}: {e}")
            questions.append(item["question"])
            answers.append(f"Error: {e}")
            ground_truths.append(item.get("ground_truth", ""))
            contexts_list.append(item.get("contexts", []))

    dataset = Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts_list,
        "ground_truth": ground_truths,
    })

    ragas_result = evaluate(
        dataset,
        metrics=[
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
            answer_correctness,
        ],
    )

    metrics = {k: float(v) if v is not None else None for k, v in ragas_result.items()}
    metrics["routing_accuracy"] = (routing_correct / routing_total) if routing_total > 0 else None
    metrics["total_questions"] = len(questions)
    metrics["routing_total"] = routing_total

    per_question = []
    for i in range(len(questions)):
        per_question.append({
            "question": questions[i],
            "answer": answers[i],
            "ground_truth": ground_truths[i],
            "domain": golden[i].get("domain", ""),
        })

    return {
        "metrics": metrics,
        "per_question": per_question,
    }
