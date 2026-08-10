from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    external_id: str = Field(min_length=1, max_length=200)
    application_id: str = Field(default="generic", min_length=1, max_length=100)
    tenant_id: str = Field(default="default", min_length=1, max_length=200)
    consent: bool = False
    training_consent: bool = False
    attributes: dict[str, Any] = Field(default_factory=dict)


class UserView(BaseModel):
    id: str
    application_id: str
    tenant_id: str
    external_id: str
    consent: bool
    training_consent: bool
    preferences: dict[str, Any]


class UserPolicyUpdate(BaseModel):
    learning_enabled: bool | None = None
    default_retention_days: int | None = Field(default=None, ge=1, le=3650)


class UserPolicyView(BaseModel):
    personalization_consent: bool
    training_consent: bool
    learning_enabled: bool
    default_retention_days: int | None


class EventCreate(BaseModel):
    kind: Literal["interaction", "feedback", "preference", "correction"]
    input_text: str | None = None
    output_text: str | None = None
    feedback: float | None = Field(default=None, ge=-1, le=1)
    idempotency_key: str | None = Field(default=None, max_length=300)
    session_id: str | None = Field(default=None, max_length=300)
    message_id: str | None = Field(default=None, max_length=300)
    model: str | None = Field(default=None, max_length=200)
    source: str = Field(default="api", min_length=1, max_length=100)
    attributes: dict[str, Any] = Field(default_factory=dict)


class EventView(BaseModel):
    id: str
    created_at: datetime
    duplicate: bool = False


class EvidenceKind(StrEnum):
    USER_ASSERTION = "user_assertion"
    USER_CORRECTION = "user_correction"
    EXPLICIT_FEEDBACK = "explicit_feedback"
    INTERACTION = "interaction"
    MODEL_OUTPUT = "model_output"
    EXTERNAL_DOCUMENT = "external_document"


class MemoryType(StrEnum):
    FACT = "fact"
    PREFERENCE = "preference"
    EPISODE = "episode"
    PROCEDURE = "procedure"
    GOAL = "goal"
    RELATIONSHIP = "relationship"
    BEHAVIOR_RULE = "behavior_rule"


class EvidenceCreate(BaseModel):
    kind: EvidenceKind
    content: str = Field(min_length=1, max_length=50_000)
    source: str = Field(default="api", min_length=1, max_length=100)
    source_reference: str | None = Field(default=None, max_length=500)
    idempotency_key: str | None = Field(default=None, max_length=300)
    sensitivity: Literal["normal", "sensitive", "restricted"] = "normal"
    observed_at: datetime | None = None
    retention_days: int | None = Field(default=None, ge=1, le=3650)
    attributes: dict[str, Any] = Field(default_factory=dict)


class EvidenceView(BaseModel):
    id: str
    kind: str
    source: str
    sensitivity: str
    content_hash: str
    observed_at: datetime
    expires_at: datetime | None
    created_at: datetime
    duplicate: bool = False


class MemoryCreate(BaseModel):
    memory_type: MemoryType
    content: str = Field(min_length=1, max_length=10_000)
    evidence_ids: list[str] = Field(min_length=1, max_length=50)
    normalized_key: str | None = Field(default=None, max_length=300)
    confidence: float = Field(default=1.0, ge=0, le=1)
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    expires_at: datetime | None = None
    sensitivity: Literal["normal", "sensitive", "restricted"] = "normal"
    attributes: dict[str, Any] = Field(default_factory=dict)


class MemoryView(BaseModel):
    id: str
    memory_type: str
    content: str
    normalized_key: str
    status: str
    confidence: float
    explicit: bool
    sensitivity: str
    valid_from: datetime | None
    valid_to: datetime | None
    expires_at: datetime | None
    supersedes_id: str | None
    evidence_ids: list[str] = Field(default_factory=list)
    created_at: datetime


class MemorySearchResponse(BaseModel):
    memory: MemoryView
    score: float
    explanation: dict[str, float | str | bool]


class ProposalCreate(BaseModel):
    action: Literal["create", "supersede", "expire", "revoke"]
    memory_type: MemoryType
    content: str = Field(min_length=1, max_length=10_000)
    evidence_ids: list[str] = Field(min_length=1, max_length=50)
    target_memory_id: str | None = None
    normalized_key: str | None = Field(default=None, max_length=300)
    confidence: float = Field(default=0.5, ge=0, le=1)
    reason: str = Field(min_length=3, max_length=2_000)


class ProposalView(BaseModel):
    id: str
    action: str
    target_memory_id: str | None
    memory_type: str
    content: str
    normalized_key: str
    confidence: float
    reason: str
    evidence_ids: list[str]
    status: str
    created_at: datetime
    decided_at: datetime | None


class ReflectionAnalyzeRequest(BaseModel):
    evidence_ids: list[str] = Field(default_factory=list, max_length=100)
    limit: int = Field(default=25, ge=1, le=100)


class ReflectionAnalyzeResponse(BaseModel):
    proposals: list[ProposalView]
    inspected_evidence: int
    skipped_evidence: int


class RetentionResult(BaseModel):
    evidence_deleted: int
    memories_revoked: int


class ContextMemoryTrace(BaseModel):
    memory_id: str
    score: float
    memory_type: str
    evidence_ids: list[str]
    truncated: bool = False


class SubjectResolveRequest(UserCreate):
    """Creates a subject or returns the existing app/tenant-scoped subject."""


class SafetyContext(BaseModel):
    mode: str = Field(default="standard", max_length=100)
    high_risk: bool = False
    allow_personalization: bool = True
    immutable_instructions: list[str] = Field(default_factory=list)


class ContextRequest(BaseModel):
    application_id: str = Field(min_length=1, max_length=100)
    tenant_id: str = Field(default="default", min_length=1, max_length=200)
    external_user_id: str = Field(min_length=1, max_length=200)
    session_id: str | None = Field(default=None, max_length=300)
    request_id: str | None = Field(default=None, max_length=300)
    base_system_prompt: str | None = None
    host_personalization: dict[str, Any] = Field(default_factory=dict)
    memory_context: str | None = None
    feedback_analysis: dict[str, Any] = Field(default_factory=dict)
    memory_query: str | None = Field(default=None, max_length=10_000)
    memory_limit: int = Field(default=8, ge=0, le=25)
    memory_char_budget: int = Field(default=3000, ge=0, le=20_000)
    safety: SafetyContext = Field(default_factory=SafetyContext)


class PromptContext(BaseModel):
    system_prompt: str
    system_prompt_addendum: str
    instructions: list[str]


class ContextResponse(BaseModel):
    subject_id: str
    application_id: str
    tenant_id: str
    profile_version: int
    personalization_applied: bool
    personalization_reason: str
    prompt: PromptContext
    preferences: dict[str, Any]
    routing_hints: dict[str, Any]
    trace: dict[str, Any]


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1)
    system_prompt: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class GenerateResponse(BaseModel):
    text: str
    applied_profile_version: int
    event_id: str | None = None
    memory_trace: list[ContextMemoryTrace] = Field(default_factory=list)


class TrainingView(BaseModel):
    id: str
    status: str
    event_count: int
    artifact_uri: str | None
    metrics: dict[str, Any]
