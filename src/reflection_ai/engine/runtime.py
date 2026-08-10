"""Composition root for dependency-free local development."""

from dataclasses import dataclass

from reflection_ai.engine.graph import TemporalRelationshipGraph
from reflection_ai.engine.indexes import HashingEmbedder, InMemoryVectorIndex
from reflection_ai.engine.jobs import InMemoryJobQueue
from reflection_ai.engine.registry import InMemoryModelRegistry


@dataclass
class LocalPersonalizationRuntime:
    embedder: HashingEmbedder
    vector_index: InMemoryVectorIndex
    graph: TemporalRelationshipGraph
    jobs: InMemoryJobQueue
    registry: InMemoryModelRegistry

    @classmethod
    def create(cls, embedding_dimensions: int = 256) -> "LocalPersonalizationRuntime":
        embedder = HashingEmbedder(embedding_dimensions)
        return cls(
            embedder=embedder,
            vector_index=InMemoryVectorIndex(embedder.dimensions),
            graph=TemporalRelationshipGraph(),
            jobs=InMemoryJobQueue(),
            registry=InMemoryModelRegistry(),
        )
