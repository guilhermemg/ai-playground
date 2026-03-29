import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Float, DateTime,
    ForeignKey, Enum, JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class QuestionnaireStatus(str, enum.Enum):
    PENDING = "pending"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    FAILED = "failed"


class EvaluationRunStatus(str, enum.Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Agent(Base):
    __tablename__ = "agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    domain = Column(String(255), nullable=False)
    description = Column(Text, default="")
    is_active = Column(Boolean, default=True)
    enabled_tools = Column(JSON, default=list)
    active_prompt_version_id = Column(
        UUID(as_uuid=True),
        ForeignKey("prompt_versions.id", use_alter=True),
        nullable=True,
    )
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    prompt_versions = relationship(
        "PromptVersion",
        back_populates="agent",
        foreign_keys="PromptVersion.agent_id",
        cascade="all, delete-orphan",
    )
    active_prompt = relationship(
        "PromptVersion",
        foreign_keys=[active_prompt_version_id],
        post_update=True,
    )
    documents = relationship("Document", back_populates="assigned_agent")
    questionnaire_results = relationship("QuestionnaireResult", back_populates="agent")


class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False)
    system_message = Column(Text, nullable=False)
    full_prompt = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    agent = relationship("Agent", back_populates="prompt_versions", foreign_keys=[agent_id])


class Questionnaire(Base):
    __tablename__ = "questionnaires"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(Enum(QuestionnaireStatus), default=QuestionnaireStatus.PENDING)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    results = relationship("QuestionnaireResult", back_populates="questionnaire", cascade="all, delete-orphan")


class QuestionnaireResult(Base):
    __tablename__ = "questionnaire_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    questionnaire_id = Column(UUID(as_uuid=True), ForeignKey("questionnaires.id", ondelete="CASCADE"), nullable=False)
    question_text = Column(Text, nullable=False)
    answer_text = Column(Text, nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)
    agent_domain = Column(String(255), default="")
    feedback = Column(Text, default="")
    score = Column(Float, nullable=True)
    is_correct = Column(Boolean, nullable=True)
    correct_answer = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    questionnaire = relationship("Questionnaire", back_populates="results")
    agent = relationship("Agent", back_populates="questionnaire_results")


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_type = Column(String(50), nullable=False)
    pinecone_namespace = Column(String(255), nullable=True)
    assigned_agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)
    chunk_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    assigned_agent = relationship("Agent", back_populates="documents")


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    triggered_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    status = Column(Enum(EvaluationRunStatus), default=EvaluationRunStatus.RUNNING)
    dataset_domain = Column(String(255), nullable=True)
    results = Column(JSON, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
