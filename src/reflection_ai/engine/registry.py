"""Versioned model/adapter registry with promotion and rollback."""

from dataclasses import replace
from threading import RLock

from reflection_ai.domain.models import EvaluationReport, ModelArtifact


class InMemoryModelRegistry:
    def __init__(self) -> None:
        self._artifacts: dict[str, ModelArtifact] = {}
        self._history: dict[str, list[str]] = {}
        self._active: dict[str, str] = {}
        self._lock = RLock()

    def register(self, artifact: ModelArtifact) -> None:
        with self._lock:
            if artifact.id in self._artifacts:
                if self._artifacts[artifact.id] != artifact:
                    raise ValueError("Artifact ID already exists with different content")
                return
            subject_versions = [
                item.version
                for item in self._artifacts.values()
                if item.subject_id == artifact.subject_id
            ]
            if artifact.version in subject_versions:
                raise ValueError("Artifact version already exists for this subject")
            self._artifacts[artifact.id] = artifact

    def promote(self, subject_id: str, artifact_id: str, report: EvaluationReport) -> None:
        with self._lock:
            artifact = self._artifacts.get(artifact_id)
            if not artifact or artifact.subject_id != subject_id:
                raise KeyError(artifact_id)
            if report.candidate_id != artifact_id or not report.passed:
                raise ValueError("Only a passing evaluation can be promoted")
            incumbent_id = self._active.get(subject_id)
            if report.incumbent_id != incumbent_id:
                raise ValueError("Evaluation incumbent does not match the active artifact")
            if incumbent_id:
                self._artifacts[incumbent_id] = replace(
                    self._artifacts[incumbent_id], status="superseded"
                )
            self._artifacts[artifact_id] = replace(
                artifact, status="active", metrics={**report.metrics}
            )
            self._active[subject_id] = artifact_id
            self._history.setdefault(subject_id, []).append(artifact_id)

    def resolve_artifact(self, subject_id: str) -> ModelArtifact | None:
        with self._lock:
            artifact_id = self._active.get(subject_id)
            return self._artifacts.get(artifact_id) if artifact_id else None

    def rollback(self, subject_id: str) -> ModelArtifact | None:
        with self._lock:
            history = self._history.get(subject_id, [])
            if len(history) < 2:
                return self.resolve_artifact(subject_id)
            current_id = history.pop()
            previous_id = history[-1]
            self._artifacts[current_id] = replace(self._artifacts[current_id], status="rolled_back")
            self._artifacts[previous_id] = replace(self._artifacts[previous_id], status="active")
            self._active[subject_id] = previous_id
            return self._artifacts[previous_id]

    def get(self, artifact_id: str) -> ModelArtifact | None:
        with self._lock:
            return self._artifacts.get(artifact_id)
