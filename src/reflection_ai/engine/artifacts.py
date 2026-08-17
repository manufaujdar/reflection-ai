"""Subject-scoped local artifact storage with hashes, manifests, and deletion."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
from uuid import uuid4


@dataclass(frozen=True)
class TrainingDatasetArtifact:
    dataset_uri: str
    holdout_uri: str
    manifest_uri: str
    dataset_hash: str
    holdout_hash: str
    scope: str


class LocalArtifactStore:
    """Store redacted training material under an opaque per-subject scope."""

    def __init__(self, root: str | Path = "artifacts") -> None:
        self.root = Path(root)

    @staticmethod
    def scope_for_subject(subject_id: str) -> str:
        if not subject_id.strip():
            raise ValueError("subject_id is required")
        return sha256(f"reflection-ai:subject:{subject_id}".encode()).hexdigest()[:32]

    @staticmethod
    def _jsonl(rows: list[dict]) -> bytes:
        if not rows:
            raise ValueError("A training split cannot be empty")
        return ("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n").encode(
            "utf-8"
        )

    @staticmethod
    def _atomic_write(path: Path, payload: bytes) -> None:
        temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
        try:
            temporary.write_bytes(payload)
            os.chmod(temporary, 0o600)
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)

    def write_training_dataset(
        self,
        subject_id: str,
        run_id: str,
        train_rows: list[dict],
        holdout_rows: list[dict],
    ) -> TrainingDatasetArtifact:
        if not run_id.strip() or any(character not in "0123456789abcdef-" for character in run_id):
            raise ValueError("run_id must be an opaque UUID-like identifier")
        scope = self.scope_for_subject(subject_id)
        target = self.root / scope / run_id
        target.mkdir(parents=True, exist_ok=False, mode=0o700)
        os.chmod(target.parent, 0o700)
        os.chmod(target, 0o700)

        train_payload = self._jsonl(train_rows)
        holdout_payload = self._jsonl(holdout_rows)
        dataset_hash = sha256(train_payload).hexdigest()
        holdout_hash = sha256(holdout_payload).hexdigest()
        dataset = target / "train.jsonl"
        holdout = target / "holdout.jsonl"
        manifest = target / "manifest.json"
        self._atomic_write(dataset, train_payload)
        self._atomic_write(holdout, holdout_payload)
        self._atomic_write(
            manifest,
            (
                json.dumps(
                    {
                        "format": "reflection-ai-training-dataset-v1",
                        "scope": scope,
                        "run_id": run_id,
                        "dataset_hash": dataset_hash,
                        "holdout_hash": holdout_hash,
                        "training_examples": len(train_rows),
                        "holdout_examples": len(holdout_rows),
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            ).encode("utf-8"),
        )
        return TrainingDatasetArtifact(
            dataset_uri=str(dataset),
            holdout_uri=str(holdout),
            manifest_uri=str(manifest),
            dataset_hash=dataset_hash,
            holdout_hash=holdout_hash,
            scope=scope,
        )

    def delete_subject(self, subject_id: str) -> bool:
        target = self.root / self.scope_for_subject(subject_id)
        if not target.exists():
            return False
        if target.is_symlink() or not target.is_dir():
            target.unlink()
            return True
        shutil.rmtree(target)
        return True
