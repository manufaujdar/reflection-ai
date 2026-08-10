"""Stable extension boundaries for standalone development and future adapters."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol, Sequence

from reflection_ai.domain.models import (
    EvaluationReport,
    MemoryAssertion,
    ModelArtifact,
    RetrievalCandidate,
)


@dataclass(frozen=True)
class ProfileCandidate:
    preferences: dict[str, Any]
    evidence_event_ids: list[str] = field(default_factory=list)
    confidence: dict[str, float] = field(default_factory=dict)


class ProfileExtractor(Protocol):
    def extract(
        self, events: Sequence[Any], previous_profile: dict[str, Any]
    ) -> ProfileCandidate: ...


class MemoryStore(Protocol):
    """Semantic/episodic memory implementations can be added without changing the API."""

    async def retain(self, subject_id: str, content: str, metadata: dict[str, Any]) -> str: ...

    async def recall(self, subject_id: str, query: str, limit: int = 5) -> list[dict[str, Any]]: ...


class TrainingBackend(Protocol):
    async def train(
        self, dataset_uri: str, base_model: str, previous_artifact: str | None = None
    ) -> dict[str, Any]: ...


class Evaluator(Protocol):
    async def compare(
        self, candidate: str, incumbent: str | None, holdout_uri: str
    ) -> dict[str, float]: ...


class ArtifactRegistry(Protocol):
    async def approve(self, subject_id: str, artifact: str, metrics: dict[str, float]) -> None: ...

    async def resolve(self, subject_id: str) -> str | None: ...


class EmbeddingProvider(Protocol):
    @property
    def dimensions(self) -> int: ...

    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


class VectorIndex(Protocol):
    def upsert(
        self, memories: Sequence[MemoryAssertion], vectors: Sequence[list[float]]
    ) -> None: ...

    def delete(self, memory_ids: Sequence[str]) -> None: ...

    def search(
        self,
        subject_id: str,
        vector: list[float],
        limit: int,
        at: datetime | None = None,
    ) -> list[RetrievalCandidate]: ...


class RelationshipIndex(Protocol):
    def link(
        self,
        subject_id: str,
        source_id: str,
        target_id: str,
        relation: str,
        evidence_ids: Sequence[str],
        valid_from: datetime | None = None,
        valid_to: datetime | None = None,
    ) -> str: ...

    def neighbors(
        self,
        subject_id: str,
        node_id: str,
        depth: int = 1,
        at: datetime | None = None,
    ) -> list[dict[str, Any]]: ...


class JobQueue(Protocol):
    def enqueue(
        self,
        kind: str,
        subject_id: str,
        payload: dict[str, Any],
        idempotency_key: str,
    ) -> str: ...

    def claim(self, worker_id: str, lease_seconds: int = 60) -> Any | None: ...

    def complete(self, job_id: str, worker_id: str, result: dict[str, Any]) -> None: ...

    def fail(self, job_id: str, worker_id: str, error: str, retryable: bool = True) -> None: ...


class PromotionEvaluator(Protocol):
    async def evaluate(
        self,
        candidate: ModelArtifact,
        incumbent: ModelArtifact | None,
        holdout_uri: str,
    ) -> EvaluationReport: ...


class ModelRegistry(Protocol):
    def register(self, artifact: ModelArtifact) -> None: ...

    def promote(self, subject_id: str, artifact_id: str, report: EvaluationReport) -> None: ...

    def resolve_artifact(self, subject_id: str) -> ModelArtifact | None: ...

    def rollback(self, subject_id: str) -> ModelArtifact | None: ...
