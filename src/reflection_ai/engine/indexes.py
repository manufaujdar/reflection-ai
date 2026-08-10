"""Dependency-free embedding and vector-index baselines for local development."""

from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Sequence
from datetime import datetime
from threading import RLock

from reflection_ai.domain.models import MemoryAssertion, RetrievalCandidate


TOKEN_RE = re.compile(r"[a-z0-9]+")


class HashingEmbedder:
    """Deterministic feature hashing; useful for tests, not a semantic production model."""

    def __init__(self, dimensions: int = 256) -> None:
        if dimensions < 8:
            raise ValueError("dimensions must be at least 8")
        self._dimensions = dimensions

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in TOKEN_RE.findall(text.lower()):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            slot = int.from_bytes(digest, "big") % self.dimensions
            sign = 1.0 if digest[0] & 1 else -1.0
            vector[slot] += sign
        norm = math.sqrt(sum(value * value for value in vector))
        return [value / norm for value in vector] if norm else vector


def cosine(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise ValueError("Vector dimensions do not match")
    return sum(a * b for a, b in zip(left, right, strict=True))


class InMemoryVectorIndex:
    def __init__(self, dimensions: int) -> None:
        self.dimensions = dimensions
        self._rows: dict[str, tuple[MemoryAssertion, tuple[float, ...]]] = {}
        self._lock = RLock()

    def upsert(self, memories: Sequence[MemoryAssertion], vectors: Sequence[list[float]]) -> None:
        if len(memories) != len(vectors):
            raise ValueError("Every memory requires one vector")
        with self._lock:
            for memory, vector in zip(memories, vectors, strict=True):
                if len(vector) != self.dimensions:
                    raise ValueError("Vector dimensions do not match the index")
                self._rows[memory.id] = (memory, tuple(vector))

    def delete(self, memory_ids: Sequence[str]) -> None:
        with self._lock:
            for memory_id in memory_ids:
                self._rows.pop(memory_id, None)

    def search(
        self,
        subject_id: str,
        vector: list[float],
        limit: int,
        at: datetime | None = None,
    ) -> list[RetrievalCandidate]:
        if len(vector) != self.dimensions:
            raise ValueError("Vector dimensions do not match the index")
        with self._lock:
            ranked = []
            for memory, stored in self._rows.values():
                if memory.subject_id != subject_id or not memory.usable_at(at):
                    continue
                similarity = max(cosine(vector, stored), 0.0)
                confidence = memory.confidence
                score = similarity * 0.8 + confidence * 0.2
                ranked.append(
                    RetrievalCandidate(
                        memory=memory,
                        score=round(score, 6),
                        score_components={
                            "vector_similarity": round(similarity, 6),
                            "confidence": round(confidence, 6),
                        },
                        ranker="hashing-cosine-v1",
                    )
                )
        return sorted(ranked, key=lambda item: item.score, reverse=True)[: max(limit, 0)]
