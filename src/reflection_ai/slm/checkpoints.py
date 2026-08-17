"""Canonical checkpoint envelope for the experimental reference SLM."""

from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
import os
from pathlib import Path
from uuid import uuid4

import torch

from reflection_ai.slm.model import ReflectionSLM


def save_base_checkpoint(
    model: ReflectionSLM,
    path: str | Path,
    *,
    base_model_id: str,
) -> dict[str, str]:
    """Atomically save a versioned base checkpoint and return its provenance."""
    if not base_model_id.strip():
        raise ValueError("base_model_id is required")
    target = Path(path)
    if target.exists():
        raise FileExistsError(f"Refusing to overwrite base checkpoint: {target}")
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = target.with_name(f".{target.name}.{uuid4().hex}.tmp")
    try:
        torch.save(
            {
                "format": "reflection-ai-base-v1",
                "base_model_id": base_model_id,
                "config": asdict(model.config),
                "config_fingerprint": model.config.fingerprint,
                "model_state": {
                    name: value.detach().cpu() for name, value in model.state_dict().items()
                },
            },
            temporary,
        )
        os.chmod(temporary, 0o600)
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    return {
        "uri": str(target),
        "base_model_id": base_model_id,
        "config_fingerprint": model.config.fingerprint,
        "checkpoint_hash": sha256(target.read_bytes()).hexdigest(),
    }
