# Personalization engine building blocks

These modules are original Reflection AI implementations of architectural patterns found across the reviewed open-source landscape. No upstream implementation was copied. Every local component implements or anticipates a stable port so production infrastructure can replace it.

## Package map

```text
reflection_ai/
├── domain/
│   ├── models.py       # immutable provider-neutral records and temporal validity
│   └── policy.py       # store/retrieve/reflect/train/export/delete decisions
├── adapters/
│   └── sqlalchemy.py   # ORM-to-domain translation and active-memory reader
├── engine/
│   ├── consolidation.py # deterministic deduplication and unresolved conflicts
│   ├── evaluation.py    # retrieval/adherence metrics and promotion thresholds
│   ├── graph.py         # temporal relationships with evidence provenance
│   ├── indexes.py       # local hashing embedder and vector index
│   ├── jobs.py          # idempotency, leases, retries, dead-letter state
│   ├── registry.py      # versioned artifacts, promotion and rollback
│   ├── retrieval.py     # multi-channel reciprocal-rank fusion and policy filter
│   ├── runtime.py       # local composition root
│   ├── training.py      # consent/data/evaluation-gated training orchestration
│   └── worker.py        # replaceable local job handler loop
├── personalization.py   # persisted evidence/proposal/memory lifecycle
└── ports.py             # integration contracts
```

## Patterns adapted independently

| Architectural lesson | Reflection AI implementation | Why it is different |
|---|---|---|
| Scoped memory and vector retrieval | `HashingEmbedder`, `InMemoryVectorIndex`, `VectorIndex` port | Canonical memory remains evidence-backed SQL/domain data; vector rows are disposable indexes. |
| Bounded working memory | Existing `ContextCompiler` and `ContextBundle` | Stored text is escaped and explicitly treated as inert data, with exact memory/evidence attribution. |
| Retain–recall–reflect and background work | `InMemoryJobQueue`, `LocalWorker`, reflection proposals | Reflection cannot write directly; leases, idempotency and dead-letter state are explicit. |
| Temporal knowledge relationships | `TemporalRelationshipGraph` | Every edge requires evidence and can be invalidated without deleting its history. |
| Hot/background memory management | Event fast path plus proposal/analyzer/job contracts | Only explicit preferences/corrections auto-apply; inferred claims remain reviewable. |
| Memory lineage | Supersession fields, `MemoryAudit`, graph relations | Lineage is a backend invariant, not just a visualization concern. |
| Personal-assistant user controls | Policy API, learning switch, retention purge, deletion | “Use existing memory” and “continue learning” are separate decisions. |
| Personalization experiments and PEFT | `EvaluationGate`, `GatedTrainingPipeline`, registry | Weight updates require consent, minimum examples, holdout evaluation, incumbent comparison and rollback. |

## Local runtime example

```python
from reflection_ai.domain.models import MemoryAssertion, MemoryKind
from reflection_ai.engine import LocalPersonalizationRuntime

runtime = LocalPersonalizationRuntime.create(embedding_dimensions=256)

memory = MemoryAssertion(
    id="memory-1",
    subject_id="user-1",
    kind=MemoryKind.PREFERENCE,
    content="Prefers concise technical explanations",
    normalized_key="response-style",
    confidence=1.0,
    evidence_ids=("evidence-1",),
    explicit=True,
)
runtime.vector_index.upsert([memory], runtime.embedder.embed([memory.content]))
query_vector = runtime.embedder.embed(["How should this explanation be written?"])[0]
hits = runtime.vector_index.search("user-1", query_vector, limit=5)
```

The hashing embedder is deterministic and dependency-free. It is intended for development and contract tests, not as a claim of semantic-model quality. A production embedding adapter implements `EmbeddingProvider`; a production vector database implements `VectorIndex`.

## Replacement boundaries

- Replace `InMemoryJobQueue` with Postgres, Redis, SQS or another durable queue while preserving idempotency and lease behavior.
- Replace `HashingEmbedder` and `InMemoryVectorIndex` with an embedding model and vector store.
- Replace `TemporalRelationshipGraph` with Graphiti or another temporal graph through `RelationshipIndex`.
- Implement `TrainingBackend` for PEFT/LoRA or a hosted fine-tuning system.
- Implement `PromotionEvaluator` with real holdout inference and safety/privacy suites.
- Persist `ModelRegistry` in a transactional artifact registry before serving trained adapters.

Production adapters must pass the same tests for tenant isolation, temporal filtering, provenance, deletion, evaluation rejection and rollback.
