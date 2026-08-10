"""Canonical domain objects that do not depend on SQLAlchemy or an AI framework."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def ensure_aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


class Sensitivity(StrEnum):
    NORMAL = "normal"
    SENSITIVE = "sensitive"
    RESTRICTED = "restricted"


class MemoryKind(StrEnum):
    FACT = "fact"
    PREFERENCE = "preference"
    EPISODE = "episode"
    PROCEDURE = "procedure"
    GOAL = "goal"
    RELATIONSHIP = "relationship"
    BEHAVIOR_RULE = "behavior_rule"


@dataclass(frozen=True)
class TemporalWindow:
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    expires_at: datetime | None = None

    def active_at(self, moment: datetime | None = None) -> bool:
        point = ensure_aware(moment) or utcnow()
        start = ensure_aware(self.valid_from)
        end = ensure_aware(self.valid_to)
        expiry = ensure_aware(self.expires_at)
        return not (
            (start and point < start) or (end and point >= end) or (expiry and point >= expiry)
        )


@dataclass(frozen=True)
class EvidenceRecord:
    id: str
    subject_id: str
    kind: str
    content: str
    content_hash: str
    observed_at: datetime
    sensitivity: Sensitivity = Sensitivity.NORMAL
    source: str = "api"
    source_reference: str | None = None
    expires_at: datetime | None = None
    attributes: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id or not self.subject_id or not self.content:
            raise ValueError("Evidence requires id, subject_id, and content")
        if len(self.content_hash) != 64:
            raise ValueError("Evidence content_hash must be SHA-256")


@dataclass(frozen=True)
class MemoryAssertion:
    id: str
    subject_id: str
    kind: MemoryKind
    content: str
    normalized_key: str
    confidence: float
    evidence_ids: tuple[str, ...]
    temporal: TemporalWindow = field(default_factory=TemporalWindow)
    sensitivity: Sensitivity = Sensitivity.NORMAL
    status: str = "active"
    explicit: bool = False
    supersedes_id: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0 <= self.confidence <= 1:
            raise ValueError("Memory confidence must be between 0 and 1")
        if not self.evidence_ids:
            raise ValueError("A memory must cite at least one evidence record")

    def usable_at(self, moment: datetime | None = None) -> bool:
        return self.status == "active" and self.temporal.active_at(moment)


@dataclass(frozen=True)
class RetrievalCandidate:
    memory: MemoryAssertion
    score: float
    score_components: dict[str, float] = field(default_factory=dict)
    ranker: str = "unknown"


@dataclass(frozen=True)
class ContextBundle:
    text: str
    memory_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    chars_used: int
    truncated: bool = False


@dataclass(frozen=True)
class ModelArtifact:
    id: str
    subject_id: str
    base_model: str
    uri: str
    dataset_hash: str
    version: int
    status: str = "candidate"
    metrics: dict[str, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utcnow)


@dataclass(frozen=True)
class EvaluationReport:
    candidate_id: str
    incumbent_id: str | None
    metrics: dict[str, float]
    passed: bool
    failures: tuple[str, ...] = ()
