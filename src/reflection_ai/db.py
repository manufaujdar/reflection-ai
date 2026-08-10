from collections.abc import Generator
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    sessionmaker,
)

from reflection_ai.config import get_settings


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("application_id", "tenant_id", "external_id", name="uq_subject"),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    application_id: Mapped[str] = mapped_column(String, default="generic", index=True)
    tenant_id: Mapped[str] = mapped_column(String, default="default", index=True)
    external_id: Mapped[str] = mapped_column(String, index=True)
    consent: Mapped[bool] = mapped_column(Boolean, default=False)
    training_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    attributes: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    profile: Mapped["Profile"] = relationship(back_populates="user", uselist=False)


class Profile(Base):
    __tablename__ = "profiles"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    preferences: Mapped[dict] = mapped_column(JSON, default=dict)
    version: Mapped[int] = mapped_column(default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    user: Mapped[User] = relationship(back_populates="profile")


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        UniqueConstraint("user_id", "idempotency_key", name="uq_user_event_idempotency"),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    kind: Mapped[str] = mapped_column(String, index=True)
    idempotency_key: Mapped[str | None] = mapped_column(String, nullable=True)
    session_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    message_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    model: Mapped[str | None] = mapped_column(String, nullable=True)
    source: Mapped[str] = mapped_column(String, default="api")
    input_text: Mapped[str | None] = mapped_column(Text)
    output_text: Mapped[str | None] = mapped_column(Text)
    feedback: Mapped[float | None] = mapped_column(Float)
    attributes: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Evidence(Base):
    """Immutable source material from which personalization may be derived."""

    __tablename__ = "evidence"
    __table_args__ = (
        UniqueConstraint("user_id", "idempotency_key", name="uq_user_evidence_idempotency"),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    event_id: Mapped[str | None] = mapped_column(ForeignKey("events.id"), nullable=True, index=True)
    kind: Mapped[str] = mapped_column(String, index=True)
    content: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String, default="api")
    source_reference: Mapped[str | None] = mapped_column(String, nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String, nullable=True)
    sensitivity: Mapped[str] = mapped_column(String, default="normal", index=True)
    consent_basis: Mapped[str] = mapped_column(String, default="personalization")
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attributes: Mapped[dict] = mapped_column(JSON, default=dict)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class MemoryRecord(Base):
    """A versioned, derived assertion. Evidence remains the source of truth."""

    __tablename__ = "memory_records"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    memory_type: Mapped[str] = mapped_column(String, index=True)
    content: Mapped[str] = mapped_column(Text)
    normalized_key: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String, default="active", index=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    explicit: Mapped[bool] = mapped_column(Boolean, default=False)
    sensitivity: Mapped[str] = mapped_column(String, default="normal", index=True)
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    supersedes_id: Mapped[str | None] = mapped_column(
        ForeignKey("memory_records.id"), nullable=True, index=True
    )
    extractor: Mapped[str] = mapped_column(String, default="explicit-v1")
    attributes: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class MemoryEvidence(Base):
    __tablename__ = "memory_evidence"
    memory_id: Mapped[str] = mapped_column(ForeignKey("memory_records.id"), primary_key=True)
    evidence_id: Mapped[str] = mapped_column(ForeignKey("evidence.id"), primary_key=True)
    relation: Mapped[str] = mapped_column(String, default="supports")


class ReflectionProposal(Base):
    """A reviewable proposal; reflection cannot mutate memory without applying one."""

    __tablename__ = "reflection_proposals"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String, index=True)
    target_memory_id: Mapped[str | None] = mapped_column(
        ForeignKey("memory_records.id"), nullable=True
    )
    memory_type: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    normalized_key: Mapped[str] = mapped_column(String, index=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    reason: Mapped[str] = mapped_column(Text)
    evidence_ids: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String, default="pending", index=True)
    proposal_hash: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MemoryAudit(Base):
    __tablename__ = "memory_audit"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    memory_id: Mapped[str | None] = mapped_column(
        ForeignKey("memory_records.id"), nullable=True, index=True
    )
    proposal_id: Mapped[str | None] = mapped_column(
        ForeignKey("reflection_proposals.id"), nullable=True
    )
    action: Mapped[str] = mapped_column(String)
    before: Mapped[dict] = mapped_column(JSON, default=dict)
    after: Mapped[dict] = mapped_column(JSON, default=dict)
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class TrainingRun(Base):
    __tablename__ = "training_runs"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(String, default="queued")
    event_count: Mapped[int] = mapped_column(default=0)
    artifact_uri: Mapped[str | None] = mapped_column(String)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


def make_engine(url: str | None = None):
    target = url or get_settings().database_url
    args = {"check_same_thread": False} if target.startswith("sqlite") else {}
    return create_engine(target, connect_args=args)


engine = make_engine()
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db() -> None:
    Base.metadata.create_all(engine)


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
