from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from hashlib import sha256


@dataclass(frozen=True)
class SLMConfig:
    """Validated architecture for the experimental causal personalization model."""

    vocab_size: int = 259
    context_length: int = 512
    embedding_dim: int = 256
    attention_heads: int = 8
    layers: int = 6
    dropout: float = 0.1
    personalization_rank: int = 8
    personalization_alpha: float = 16.0
    ignore_index: int = -100
    pad_token_id: int = 0
    eos_token_id: int = 2

    def __post_init__(self) -> None:
        if self.vocab_size < 4:
            raise ValueError("vocab_size must include special and content tokens")
        if self.context_length < 2:
            raise ValueError("context_length must be at least 2")
        if self.attention_heads < 1:
            raise ValueError("attention_heads must be positive")
        if self.embedding_dim < 8 or self.embedding_dim % self.attention_heads:
            raise ValueError("embedding_dim must be divisible by attention_heads")
        if self.layers < 1:
            raise ValueError("layers must be positive")
        if not 0 <= self.dropout < 1:
            raise ValueError("dropout must be in [0, 1)")
        if self.personalization_rank < 1:
            raise ValueError("personalization_rank must be positive")
        if self.personalization_rank > self.embedding_dim:
            raise ValueError("personalization_rank cannot exceed embedding_dim")
        if self.personalization_alpha <= 0:
            raise ValueError("personalization_alpha must be positive")
        if not 0 <= self.pad_token_id < self.vocab_size:
            raise ValueError("pad_token_id must be in the vocabulary")
        if not 0 <= self.eos_token_id < self.vocab_size:
            raise ValueError("eos_token_id must be in the vocabulary")

    @property
    def fingerprint(self) -> str:
        payload = json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))
        return sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class GenerationConfig:
    max_new_tokens: int = 128
    temperature: float = 0.8
    top_k: int | None = 40
    top_p: float | None = 0.95
    repetition_penalty: float = 1.0
    eos_token_id: int | None = None

    def __post_init__(self) -> None:
        if self.max_new_tokens < 0:
            raise ValueError("max_new_tokens cannot be negative")
        if self.temperature < 0:
            raise ValueError("temperature cannot be negative")
        if self.top_k is not None and self.top_k < 1:
            raise ValueError("top_k must be positive")
        if self.top_p is not None and not 0 < self.top_p <= 1:
            raise ValueError("top_p must be in (0, 1]")
        if self.repetition_penalty <= 0:
            raise ValueError("repetition_penalty must be positive")
