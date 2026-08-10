"""Gated training orchestration; actual model training remains an adapter."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from reflection_ai.domain.models import EvaluationReport, ModelArtifact
from reflection_ai.ports import ModelRegistry, PromotionEvaluator, TrainingBackend


@dataclass(frozen=True)
class TrainingRequest:
    subject_id: str
    dataset_uri: str
    dataset_hash: str
    holdout_uri: str
    base_model: str
    example_count: int
    personalization_consent: bool
    training_consent: bool
    minimum_examples: int = 20


@dataclass(frozen=True)
class TrainingOutcome:
    status: str
    artifact: ModelArtifact | None = None
    evaluation: EvaluationReport | None = None
    reason: str | None = None


class GatedTrainingPipeline:
    def __init__(
        self,
        backend: TrainingBackend,
        evaluator: PromotionEvaluator,
        registry: ModelRegistry,
    ) -> None:
        self.backend = backend
        self.evaluator = evaluator
        self.registry = registry

    async def run(self, request: TrainingRequest) -> TrainingOutcome:
        if not request.personalization_consent or not request.training_consent:
            return TrainingOutcome("skipped", reason="consent_missing")
        if request.example_count < request.minimum_examples:
            return TrainingOutcome("skipped", reason="insufficient_examples")
        incumbent = self.registry.resolve_artifact(request.subject_id)
        result = await self.backend.train(
            request.dataset_uri,
            request.base_model,
            incumbent.uri if incumbent else None,
        )
        artifact = ModelArtifact(
            id=str(result.get("id") or uuid4()),
            subject_id=request.subject_id,
            base_model=request.base_model,
            uri=str(result["artifact_uri"]),
            dataset_hash=request.dataset_hash,
            version=(incumbent.version + 1) if incumbent else 1,
            metrics={str(key): float(value) for key, value in result.get("metrics", {}).items()},
        )
        self.registry.register(artifact)
        report = await self.evaluator.evaluate(artifact, incumbent, request.holdout_uri)
        if not report.passed:
            return TrainingOutcome("rejected", artifact=artifact, evaluation=report)
        self.registry.promote(request.subject_id, artifact.id, report)
        return TrainingOutcome(
            "promoted",
            artifact=self.registry.resolve_artifact(request.subject_id),
            evaluation=report,
        )
