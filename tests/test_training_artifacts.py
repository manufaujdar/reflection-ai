import asyncio
from hashlib import sha256
from pathlib import Path

import pytest

from reflection_ai.db import TrainingRun, User
from reflection_ai.engine.artifacts import LocalArtifactStore
from reflection_ai.engine.training import TrainingOutcome
from reflection_ai.slm.system import PersonalizationModelSystem


def test_local_artifact_store_scopes_hashes_and_deletes_subject(tmp_path):
    store = LocalArtifactStore(tmp_path)
    artifact = store.write_training_dataset(
        "subject-visible-id",
        "01234567-89ab-cdef-0123-456789abcdef",
        [{"prompt": "hello", "completion": "concise answer"}],
        [{"prompt": "later", "completion": "short answer"}],
    )
    assert "subject-visible-id" not in artifact.dataset_uri
    assert len(artifact.dataset_hash) == 64
    assert len(artifact.holdout_hash) == 64
    assert Path(artifact.dataset_uri).is_file()
    assert Path(artifact.manifest_uri).is_file()
    assert store.delete_subject("subject-visible-id") is True
    assert not Path(artifact.dataset_uri).exists()
    assert store.delete_subject("subject-visible-id") is False


class RecordingPipeline:
    def __init__(self):
        self.request = None

    async def run(self, request):
        self.request = request
        return TrainingOutcome(status="rejected", reason="synthetic-evaluation")


def test_model_system_connects_prepared_data_without_bypassing_pipeline(tmp_path):
    dataset = tmp_path / "train.jsonl"
    holdout = tmp_path / "holdout.jsonl"
    dataset.write_text("{}\n", encoding="utf-8")
    holdout.write_text("{}\n", encoding="utf-8")
    user = User(id="user-1", external_id="local", consent=True, training_consent=True)
    run = TrainingRun(
        id="run-1",
        user_id=user.id,
        status="dataset_ready",
        artifact_uri=str(dataset),
        metrics={
            "dataset_hash": sha256(dataset.read_bytes()).hexdigest(),
            "holdout_hash": sha256(holdout.read_bytes()).hexdigest(),
            "holdout_uri": str(holdout),
            "examples": 20,
        },
    )
    pipeline = RecordingPipeline()
    system = PersonalizationModelSystem(pipeline, "file:///base-model.pt")
    prepared = system.prepare(user, run)
    outcome = asyncio.run(system.train(prepared))
    assert outcome.status == "rejected"
    assert pipeline.request.subject_id == user.id
    assert pipeline.request.training_consent is True

    other = User(id="user-2", external_id="other", consent=True, training_consent=True)
    with pytest.raises(PermissionError, match="another subject"):
        system.prepare(other, run)
