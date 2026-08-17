from __future__ import annotations

import json
import re
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

import torch

from reflection_ai.slm.config import SLMConfig
from reflection_ai.slm.model import ReflectionSLM
from reflection_ai.slm.tokenizer import ByteTokenizer

OPAQUE_SCOPE = re.compile(r"^[a-f0-9]{16,64}$")


class ReferenceSLMTrainingBackend:
    """Experimental adapter-only TrainingBackend for local research.

    The caller must provide an opaque scoped artifact namespace. Promotion remains
    the responsibility of ``GatedTrainingPipeline`` and its evaluator/registry.
    """

    def __init__(
        self,
        artifact_root: str | Path,
        artifact_scope: str,
        config: SLMConfig | None = None,
        *,
        epochs: int = 1,
        learning_rate: float = 3e-4,
        device: str | None = None,
    ) -> None:
        if not OPAQUE_SCOPE.fullmatch(artifact_scope):
            raise ValueError("artifact_scope must be an opaque lowercase hex identifier")
        if epochs < 1 or learning_rate <= 0:
            raise ValueError("epochs and learning_rate must be positive")
        self.artifact_root = Path(artifact_root)
        self.artifact_scope = artifact_scope
        self.config = config or SLMConfig()
        self.epochs = epochs
        self.learning_rate = learning_rate
        self.device = device or ("mps" if torch.backends.mps.is_available() else "cpu")
        self.tokenizer = ByteTokenizer()
        if self.config.vocab_size != self.tokenizer.vocab_size:
            raise ValueError("Reference backend requires the ByteTokenizer vocabulary")

    @staticmethod
    def _local_path(uri: str) -> Path:
        value = uri.removeprefix("file://")
        path = Path(value)
        if not path.is_file():
            raise FileNotFoundError(f"Required local artifact does not exist: {path}")
        return path

    def _load_base(self, base_model: str) -> ReflectionSLM:
        checkpoint = torch.load(
            self._local_path(base_model), map_location=self.device, weights_only=True
        )
        if checkpoint.get("format") != "reflection-ai-base-v1":
            raise ValueError("Unsupported base checkpoint format")
        if checkpoint.get("config") != asdict(self.config):
            raise ValueError("Base checkpoint configuration does not match the trainer")
        if checkpoint.get("config_fingerprint") != self.config.fingerprint:
            raise ValueError("Base checkpoint fingerprint does not match the trainer")
        model = ReflectionSLM(self.config).to(self.device)
        model.load_state_dict(checkpoint["model_state"], strict=True)
        model.freeze_base_for_personalization()
        return model

    def _examples(self, dataset_uri: str) -> tuple[list[tuple[list[int], list[int]]], str]:
        path = self._local_path(dataset_uri)
        raw = path.read_bytes()
        dataset_hash = sha256(raw).hexdigest()
        examples: list[tuple[list[int], list[int]]] = []
        for line_number, line in enumerate(raw.decode("utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                prompt = str(row["prompt"])
                completion = str(row["completion"])
            except (KeyError, TypeError, json.JSONDecodeError) as error:
                raise ValueError(f"Invalid training example on line {line_number}") from error
            prefix = self.tokenizer.encode(
                f"User:\n{prompt}\nAssistant:\n", add_bos=True
            )
            answer = self.tokenizer.encode(completion, add_eos=True)
            if len(answer) >= self.config.context_length:
                answer = answer[: self.config.context_length - 1] + [self.tokenizer.eos_token_id]
                prefix = [self.tokenizer.bos_token_id]
            available_prefix = self.config.context_length - len(answer)
            prefix = prefix[-available_prefix:] if available_prefix else []
            tokens = prefix + answer
            labels = [self.config.ignore_index] * len(prefix) + answer
            if len(tokens) < 2 or all(
                label == self.config.ignore_index for label in labels[1:]
            ):
                raise ValueError(f"Training example {line_number} has no usable completion")
            examples.append((tokens, labels))
        if not examples:
            raise ValueError("Training dataset is empty")
        return examples, dataset_hash

    def _batch(
        self, examples: list[tuple[list[int], list[int]]]
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        width = max(len(tokens) for tokens, _ in examples)
        input_ids = torch.full(
            (len(examples), width),
            self.config.pad_token_id,
            dtype=torch.long,
            device=self.device,
        )
        labels = torch.full(
            (len(examples), width),
            self.config.ignore_index,
            dtype=torch.long,
            device=self.device,
        )
        mask = torch.zeros((len(examples), width), dtype=torch.bool, device=self.device)
        for index, (tokens, targets) in enumerate(examples):
            length = len(tokens)
            input_ids[index, :length] = torch.tensor(tokens, device=self.device)
            labels[index, :length] = torch.tensor(targets, device=self.device)
            mask[index, :length] = True
        return input_ids, labels, mask

    async def train(
        self, dataset_uri: str, base_model: str, previous_artifact: str | None = None
    ) -> dict[str, object]:
        model = self._load_base(base_model)
        if previous_artifact:
            previous = torch.load(
                self._local_path(previous_artifact),
                map_location=self.device,
                weights_only=True,
            )
            if previous.get("base_model") != base_model:
                raise ValueError("Previous adapter was trained from another base model")
            model.load_adapter_state_dict(previous["adapter_state"])
        examples, dataset_hash = self._examples(dataset_uri)
        optimizer = torch.optim.AdamW(
            [parameter for parameter in model.parameters() if parameter.requires_grad],
            lr=self.learning_rate,
        )
        model.train()
        losses: list[float] = []
        input_ids, labels, attention_mask = self._batch(examples)
        for _ in range(self.epochs):
            optimizer.zero_grad(set_to_none=True)
            _, loss = model(input_ids, labels, attention_mask)
            if loss is None or not torch.isfinite(loss):
                raise RuntimeError("Training produced a non-finite loss")
            loss.backward()
            torch.nn.utils.clip_grad_norm_(
                [parameter for parameter in model.parameters() if parameter.requires_grad], 1.0
            )
            optimizer.step()
            losses.append(float(loss.detach().cpu()))

        artifact_id = str(uuid4())
        target = self.artifact_root / self.artifact_scope / artifact_id
        target.mkdir(parents=True, exist_ok=False)
        checkpoint = target / "adapter.pt"
        summary = model.parameter_summary()
        torch.save(
            {
                "format": "reflection-ai-adapter-v1",
                "base_model": base_model,
                "config": asdict(self.config),
                "config_fingerprint": self.config.fingerprint,
                "dataset_hash": dataset_hash,
                "adapter_state": model.adapter_state_dict(),
            },
            checkpoint,
        )
        metadata = {
            "artifact_id": artifact_id,
            "format": "reflection-ai-adapter-v1",
            "base_model": base_model,
            "config_fingerprint": self.config.fingerprint,
            "dataset_hash": dataset_hash,
            "examples": len(examples),
            "epochs": self.epochs,
            "training_loss": losses[-1],
            "trainable_parameters": summary["trainable"],
            "total_parameters": summary["total"],
            "promotion_required": True,
        }
        (target / "metadata.json").write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return {
            "id": artifact_id,
            "artifact_uri": str(checkpoint),
            "metrics": {
                "training_loss": losses[-1],
                "examples": float(len(examples)),
                "trainable_parameters": float(summary["trainable"]),
            },
        }
