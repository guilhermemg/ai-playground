from __future__ import annotations

import json
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Agent, Questionnaire, PromptVersion
from app.agents.standard_template import generate_prompt_v1, generate_prompt

logger = logging.getLogger(__name__)

SEED_AGENTS = [
    {
        "name": "Physics Expert",
        "domain": "physics",
        "description": "Evaluates questions about classical mechanics, thermodynamics, electromagnetism, and modern physics.",
        "enabled_tools": ["calculator", "wikipedia"],
        "additional_instructions": "Use the calculator for any numerical verification. Cross-check physical constants on Wikipedia when needed.",
    },
    {
        "name": "Math Expert",
        "domain": "math",
        "description": "Evaluates questions about algebra, calculus, geometry, and general mathematics.",
        "enabled_tools": ["calculator"],
        "additional_instructions": "Always verify numerical answers using the calculator tool before scoring.",
    },
    {
        "name": "Medicine Expert",
        "domain": "medicine",
        "description": "Evaluates questions about anatomy, physiology, pharmacology, and clinical sciences.",
        "enabled_tools": ["wikipedia"],
        "additional_instructions": "Use Wikipedia to verify medical facts and drug information when needed.",
    },
    {
        "name": "General Knowledge Expert",
        "domain": "general knowledge",
        "description": "Evaluates questions about history, geography, literature, arts, and general trivia.",
        "enabled_tools": ["wikipedia", "web_search"],
        "additional_instructions": "Use Wikipedia and web search to fact-check answers about historical events, geography, and cultural topics.",
    },
]

SEED_QUESTIONNAIRES = [
    {
        "title": "General Knowledge Quiz",
        "questions": [
            {"question": "What is the capital of France?", "answer": "Paris"},
            {"question": "Who wrote Hamlet?", "answer": "Shakespeare"},
            {"question": "What is the chemical symbol for gold?", "answer": "Ag"},
            {"question": "Who painted the Mona Lisa?", "answer": "Michelangelo"},
            {"question": "What is the largest planet in our solar system?", "answer": "Pluto"},
            {"question": "Who is the author of 'To Kill a Mockingbird'?", "answer": "Harper Lee"},
        ],
    },
    {
        "title": "Physics & Math Quiz",
        "questions": [
            {"question": "What is Newton's second law of motion?", "answer": "F = ma"},
            {"question": "What is the speed of light in vacuum (m/s)?", "answer": "3 x 10^8 m/s"},
            {"question": "What is the square root of 144?", "answer": "13"},
            {"question": "What is the formula for the area of a circle?", "answer": "πr^2"},
            {"question": "What is the boiling point of water in Fahrenheit?", "answer": "212 F"},
            {"question": "What is the derivative of x^2?", "answer": "2x"},
        ],
    },
    {
        "title": "Medicine Basics Quiz",
        "questions": [
            {"question": "What organ produces insulin?", "answer": "Liver"},
            {"question": "What is the largest organ of the human body?", "answer": "Skin"},
            {"question": "What does DNA stand for?", "answer": "Deoxyribonucleic acid"},
            {"question": "What type of blood cells fight infection?", "answer": "White blood cells"},
            {"question": "What is the normal resting heart rate for adults (bpm)?", "answer": "60-100 bpm"},
        ],
    },
]


async def seed_database(db: AsyncSession) -> None:
    result = await db.execute(select(Agent).limit(1))
    if result.scalar_one_or_none() is not None:
        logger.info("Database already seeded, skipping")
        return

    logger.info("Seeding database with sample agents and questionnaires...")

    for agent_data in SEED_AGENTS:
        agent = Agent(
            name=agent_data["name"],
            domain=agent_data["domain"],
            description=agent_data["description"],
            enabled_tools=agent_data["enabled_tools"],
            is_active=True,
        )
        db.add(agent)
        await db.flush()

        extra = agent_data.get("additional_instructions", "")

        v1_data = generate_prompt_v1(agent_data["name"], agent_data["domain"], extra)
        v1_prompt = PromptVersion(
            agent_id=agent.id,
            version=1,
            system_message=v1_data["system_message"],
            full_prompt=v1_data["full_prompt"],
        )
        db.add(v1_prompt)
        await db.flush()

        v2_data = generate_prompt(agent_data["name"], agent_data["domain"], extra)
        v2_prompt = PromptVersion(
            agent_id=agent.id,
            version=2,
            system_message=v2_data["system_message"],
            full_prompt=v2_data["full_prompt"],
        )
        db.add(v2_prompt)
        await db.flush()

        agent.active_prompt_version_id = v2_prompt.id

    for q_data in SEED_QUESTIONNAIRES:
        content = json.dumps(q_data["questions"])
        questionnaire = Questionnaire(title=q_data["title"], content=content)
        db.add(questionnaire)

    await db.commit()
    logger.info("Database seeded successfully with %d agents and %d questionnaires",
                len(SEED_AGENTS), len(SEED_QUESTIONNAIRES))
