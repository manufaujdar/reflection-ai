"""Bridge prepared datasets to the evaluation-gated personalization pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from reflection_ai.db import TrainingRun, User
from reflection_ai.engine.training import GatedTrainingPipeline, TrainingOutcome, TrainingRequest


@dataclass(frozen=True)
class PreparedPersonalizationRun:
    request: TrainingRequest
    training_run_id: str


class PersonalizationModelSystem:
    """Run prepared data through trainer, evaluator, registry, and rollback boundaries.

    Dataset preparation remains a separate consent-aware database operation. This
    coordinator never creates consent, never trains inline with chat, and never
    promotes without the evaluator owned by ``GatedTrainingPipeline``.
    """

    def __init__(
        self,
        pipeline: GatedTrainingPipeline,
        base_model: str,
        minimum_examples: int = 20,
    ) -> None:
        if minimum_examples < 1:
            raise ValueError("minimum_examples must be positive")
        if not base_model:
            raise ValueError("base_model is required")
        self.pipeline = pipeline
        self.base_model = base_model
        self.minimum_examples = minimum_examples

    def prepare(self, user: User, run: TrainingRun) -> PreparedPersonalizationRun:
        if run.user_id != user.id:
            raise PermissionError("Training run belongs to another subject")
        if run.status != "dataset_ready" or not run.artifact_uri:
            raise ValueError("Training run does not contain a prepared dataset")
        holdout_uri = str(run.metrics.get("holdout_uri", ""))
        dataset_hash = str(run.metrics.get("dataset_hash", ""))
        holdout_hash = str(run.metrics.get("holdout_hash", ""))
        examples = int(run.metrics.get("examples", 0))
        if len(dataset_hash) != 64 or len(holdout_hash) != 64 or not holdout_uri:
            raise ValueError("Training run provenance is incomplete")
        dataset_path = Path(run.artifact_uri)
        holdout_path = Path(holdout_uri)
        if not dataset_path.is_file() or not holdout_path.is_file():
            raise FileNotFoundError("Prepared training material is missing")
        if sha256(dataset_path.read_bytes()).hexdigest() != dataset_hash:
            raise ValueError("Prepared training dataset hash does not match")
        if sha256(holdout_path.read_bytes()).hexdigest() != holdout_hash:
            raise ValueError("Prepared holdout dataset hash does not match")
        return PreparedPersonalizationRun(
            training_run_id=run.id,
            request=TrainingRequest(
                subject_id=user.id,
                dataset_uri=run.artifact_uri,
                dataset_hash=dataset_hash,
                holdout_uri=holdout_uri,
                base_model=self.base_model,
                example_count=examples,
                personalization_consent=user.consent,
                training_consent=user.training_consent,
                minimum_examples=self.minimum_examples,
            ),
        )

    async def train(self, prepared: PreparedPersonalizationRun) -> TrainingOutcome:
        return await self.pipeline.run(prepared.request)
