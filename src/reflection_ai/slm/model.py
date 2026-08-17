from __future__ import annotations

from math import isfinite, sqrt
from typing import Any

import torch
from torch import nn
from torch.nn import functional as F

from reflection_ai.slm.config import GenerationConfig, SLMConfig


class CausalSelfAttention(nn.Module):
    def __init__(self, config: SLMConfig) -> None:
        super().__init__()
        self.heads = config.attention_heads
        self.head_dim = config.embedding_dim // config.attention_heads
        self.qkv = nn.Linear(config.embedding_dim, 3 * config.embedding_dim, bias=False)
        self.output = nn.Linear(config.embedding_dim, config.embedding_dim, bias=False)
        self.attention_dropout = nn.Dropout(config.dropout)
        self.residual_dropout = nn.Dropout(config.dropout)
        self.register_buffer(
            "causal_mask",
            torch.tril(torch.ones(config.context_length, config.context_length, dtype=torch.bool)),
            persistent=False,
        )

    def forward(
        self, x: torch.Tensor, attention_mask: torch.Tensor | None = None
    ) -> torch.Tensor:
        batch, length, width = x.shape
        qkv = self.qkv(x).chunk(3, dim=-1)
        query, key, value = (
            item.view(batch, length, self.heads, self.head_dim).transpose(1, 2)
            for item in qkv
        )
        scores = query @ key.transpose(-2, -1) / sqrt(self.head_dim)
        scores = scores.masked_fill(~self.causal_mask[:length, :length], torch.finfo(x.dtype).min)
        if attention_mask is not None:
            if attention_mask.shape != (batch, length):
                raise ValueError("attention_mask must have shape (batch, sequence)")
            scores = scores.masked_fill(
                ~attention_mask[:, None, None, :].to(dtype=torch.bool),
                torch.finfo(x.dtype).min,
            )
        weights = F.softmax(scores.float(), dim=-1).to(dtype=x.dtype)
        weights = self.attention_dropout(weights)
        attended = weights @ value
        attended = attended.transpose(1, 2).contiguous().view(batch, length, width)
        return self.residual_dropout(self.output(attended))


class FeedForward(nn.Module):
    def __init__(self, config: SLMConfig) -> None:
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(config.embedding_dim, 4 * config.embedding_dim, bias=False),
            nn.GELU(approximate="tanh"),
            nn.Linear(4 * config.embedding_dim, config.embedding_dim, bias=False),
            nn.Dropout(config.dropout),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x)


class PersonalizationAdapter(nn.Module):
    """Small zero-initialized residual adapter; only these weights need user training."""

    def __init__(self, config: SLMConfig) -> None:
        super().__init__()
        self.scale = config.personalization_alpha / config.personalization_rank
        self.down = nn.Linear(config.embedding_dim, config.personalization_rank, bias=False)
        self.up = nn.Linear(config.personalization_rank, config.embedding_dim, bias=False)
        self.dropout = nn.Dropout(config.dropout)
        nn.init.zeros_(self.up.weight)

    def forward(self, x: torch.Tensor, strength: float = 1.0) -> torch.Tensor:
        if not isfinite(strength) or not 0 <= strength <= 2:
            raise ValueError("personalization strength must be finite and between 0 and 2")
        return self.up(self.dropout(F.gelu(self.down(x)))) * self.scale * strength


class TransformerBlock(nn.Module):
    def __init__(self, config: SLMConfig) -> None:
        super().__init__()
        self.attention_norm = nn.LayerNorm(config.embedding_dim)
        self.attention = CausalSelfAttention(config)
        self.feed_forward_norm = nn.LayerNorm(config.embedding_dim)
        self.feed_forward = FeedForward(config)
        self.adapter_norm = nn.LayerNorm(config.embedding_dim)
        self.adapter = PersonalizationAdapter(config)

    def forward(
        self,
        x: torch.Tensor,
        attention_mask: torch.Tensor | None = None,
        personalization_strength: float = 1.0,
    ) -> torch.Tensor:
        x = x + self.attention(self.attention_norm(x), attention_mask)
        x = x + self.feed_forward(self.feed_forward_norm(x))
        return x + self.adapter(self.adapter_norm(x), personalization_strength)


class ReflectionSLM(nn.Module):
    """Compact causal transformer for offline, evaluation-gated experiments.

    It is deliberately not registered as the live chat provider. A candidate must
    pass the project's evaluator and registry promotion boundary before routing.
    """

    def __init__(self, config: SLMConfig) -> None:
        super().__init__()
        self.config = config
        self.token_embedding = nn.Embedding(config.vocab_size, config.embedding_dim)
        self.position_embedding = nn.Embedding(config.context_length, config.embedding_dim)
        self.embedding_dropout = nn.Dropout(config.dropout)
        self.blocks = nn.ModuleList(TransformerBlock(config) for _ in range(config.layers))
        self.final_norm = nn.LayerNorm(config.embedding_dim)
        self.language_head = nn.Linear(config.embedding_dim, config.vocab_size, bias=False)
        self.apply(self._initialize)
        for block in self.blocks:
            nn.init.zeros_(block.adapter.up.weight)
        self.language_head.weight = self.token_embedding.weight

    @staticmethod
    def _initialize(module: nn.Module) -> None:
        if isinstance(module, (nn.Linear, nn.Embedding)):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)
        if isinstance(module, nn.LayerNorm):
            nn.init.ones_(module.weight)
            nn.init.zeros_(module.bias)

    def forward(
        self,
        input_ids: torch.Tensor,
        labels: torch.Tensor | None = None,
        attention_mask: torch.Tensor | None = None,
        personalization_strength: float = 1.0,
    ) -> tuple[torch.Tensor, torch.Tensor | None]:
        if input_ids.ndim != 2:
            raise ValueError("input_ids must have shape (batch, sequence)")
        _, length = input_ids.shape
        if length > self.config.context_length:
            raise ValueError("sequence exceeds the configured context length")
        if labels is not None and labels.shape != input_ids.shape:
            raise ValueError("labels must match input_ids")
        positions = torch.arange(length, device=input_ids.device)
        x = self.token_embedding(input_ids) + self.position_embedding(positions)
        x = self.embedding_dropout(x)
        for block in self.blocks:
            x = block(x, attention_mask, personalization_strength)
        logits = self.language_head(self.final_norm(x))
        loss = None
        if labels is not None:
            if length < 2:
                raise ValueError("at least two tokens are required for causal loss")
            loss = F.cross_entropy(
                logits[:, :-1, :].contiguous().view(-1, self.config.vocab_size),
                labels[:, 1:].contiguous().view(-1),
                ignore_index=self.config.ignore_index,
            )
        return logits, loss

    def freeze_base_for_personalization(self) -> dict[str, int]:
        for parameter in self.parameters():
            parameter.requires_grad = False
        for block in self.blocks:
            for parameter in block.adapter.parameters():
                parameter.requires_grad = True
        return self.parameter_summary()

    def parameter_summary(self) -> dict[str, int]:
        total = sum(parameter.numel() for parameter in self.parameters())
        trainable = sum(
            parameter.numel() for parameter in self.parameters() if parameter.requires_grad
        )
        return {"total": total, "trainable": trainable, "frozen": total - trainable}

    def adapter_state_dict(self) -> dict[str, torch.Tensor]:
        return {
            name: value.detach().cpu()
            for name, value in self.state_dict().items()
            if ".adapter." in name
        }

    def load_adapter_state_dict(self, state: dict[str, Any]) -> None:
        unexpected = [name for name in state if ".adapter." not in name]
        if unexpected:
            raise ValueError("Adapter artifact contains non-adapter weights")
        expected_state = self.adapter_state_dict()
        if set(state) != set(expected_state):
            raise ValueError("Adapter artifact is incomplete")
        for name, value in state.items():
            expected = expected_state[name]
            if not isinstance(value, torch.Tensor) or value.shape != expected.shape:
                raise ValueError(f"Adapter weight has an invalid shape: {name}")
        incompatible = self.load_state_dict(state, strict=False)
        if incompatible.unexpected_keys:
            raise ValueError("Adapter artifact contains unknown weights")

    @torch.inference_mode()
    def generate(
        self,
        input_ids: torch.Tensor,
        config: GenerationConfig | None = None,
        *,
        generator: torch.Generator | None = None,
        personalization_strength: float = 1.0,
    ) -> torch.Tensor:
        generation = config or GenerationConfig(eos_token_id=self.config.eos_token_id)
        if input_ids.ndim != 2 or input_ids.shape[1] == 0:
            raise ValueError("input_ids must be a non-empty batch of token sequences")
        eos_id = (
            generation.eos_token_id
            if generation.eos_token_id is not None
            else self.config.eos_token_id
        )
        output = input_ids
        finished = torch.zeros(input_ids.shape[0], dtype=torch.bool, device=input_ids.device)
        was_training = self.training
        self.eval()
        try:
            for _ in range(generation.max_new_tokens):
                cropped = output[:, -self.config.context_length :]
                logits, _ = self(
                    cropped, personalization_strength=personalization_strength
                )
                next_logits = logits[:, -1, :].clone()
                if generation.repetition_penalty != 1:
                    seen = torch.zeros_like(next_logits, dtype=torch.bool)
                    seen.scatter_(1, cropped, True)
                    adjusted = torch.where(
                        next_logits < 0,
                        next_logits * generation.repetition_penalty,
                        next_logits / generation.repetition_penalty,
                    )
                    next_logits = torch.where(seen, adjusted, next_logits)
                if generation.temperature == 0:
                    next_token = next_logits.argmax(dim=-1, keepdim=True)
                else:
                    next_logits /= generation.temperature
                    if generation.top_k is not None:
                        threshold = torch.topk(
                            next_logits,
                            min(generation.top_k, next_logits.shape[-1]),
                        ).values[:, -1:]
                        next_logits = next_logits.masked_fill(
                            next_logits < threshold, float("-inf")
                        )
                    if generation.top_p is not None and generation.top_p < 1:
                        sorted_logits, sorted_indices = torch.sort(
                            next_logits, descending=True
                        )
                        sorted_probabilities = F.softmax(sorted_logits, dim=-1)
                        cumulative = sorted_probabilities.cumsum(dim=-1)
                        remove = cumulative - sorted_probabilities > generation.top_p
                        sorted_logits = sorted_logits.masked_fill(remove, float("-inf"))
                        next_logits = torch.full_like(next_logits, float("-inf"))
                        next_logits.scatter_(1, sorted_indices, sorted_logits)
                    probabilities = F.softmax(next_logits, dim=-1)
                    next_token = torch.multinomial(
                        probabilities, num_samples=1, generator=generator
                    )
                next_token = torch.where(
                    finished[:, None],
                    torch.full_like(next_token, self.config.pad_token_id),
                    next_token,
                )
                output = torch.cat((output, next_token), dim=1)
                finished |= next_token.squeeze(1).eq(eos_id)
                if finished.all():
                    break
        finally:
            self.train(was_training)
        return output
