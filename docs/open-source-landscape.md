# Open-source personalization landscape

Reviewed July 2026. Popularity is useful for finding mature projects, but design choices below are based on architecture, license, evaluation discipline, and fit—not stars alone.

## Projects worth tracking

| Project | Primary strength | What Reflection AI should learn | Adoption stance |
|---|---|---|---|
| [Mem0](https://github.com/mem0ai/mem0) | Production-oriented user/session/agent memory with hybrid and temporal retrieval | Multi-scope memory, bounded retrieval, reproducible memory evaluation | Study and benchmark; keep behind `MemoryStore` |
| [Letta](https://github.com/letta-ai/letta) | Stateful agents with explicit human/persona memory blocks and background learning | Separate user model from assistant persona; introduce sleep-time consolidation | Study concepts; do not couple core to an agent runtime |
| [Hindsight](https://github.com/vectorize-io/hindsight) | Retain/recall/reflect model with experiences and mental models | Add explicit reflection jobs and distinguish raw experiences from derived beliefs | Strong conceptual fit for the reflection layer |
| [Graphiti](https://github.com/getzep/graphiti) | Temporal facts, provenance, contradiction history, hybrid graph retrieval | Valid-time/supersession and evidence lineage for changing preferences | Optional advanced memory backend, not the default database |
| [Supermemory](https://github.com/supermemoryai/supermemory) | Context engine with profiles, contradiction handling, expiry, and local operation | Forgetting/expiry policies and fast profile context | Track architecture and benchmarks; verify OSS boundaries before reuse |
| [LangMem](https://github.com/langchain-ai/langmem) | Storage-independent memory primitives and hot/background paths | Keep protocols small and support both synchronous and background memory updates | Useful reference; avoid mandatory LangGraph dependency |
| [Khoj](https://github.com/khoj-ai/khoj) | Self-hosted personal assistant and second-brain product | Local-first privacy, document ingestion, user-controlled personas and knowledge | Product/UX reference; AGPL requires care for code reuse |
| [LaMP](https://github.com/LaMP-Benchmark/LaMP) | Personalization datasets, RAG, retriever optimization, and per-user LoRA evaluation | Build measurable retrieval and PEFT experiments before claiming improvement | Adopt benchmark ideas and experiment formats |

## Current Reflection AI assessment

### Working now

- Consent-gated users, profiles, interaction events, feedback, corrections, and deletion.
- Application/tenant-scoped identity and idempotent event ingestion.
- Transparent deterministic profile extraction with evidence IDs and confidence metadata.
- Profile-based prompt adaptation and a protected-mode policy boundary.
- Replaceable inference provider and versioned training-dataset preparation.
- Explicit protocol boundaries for memory, extraction, training, evaluation, and artifact resolution.

### Important gaps

1. No semantic or hybrid recall; all profile extraction scans recent events.
2. No episodic/semantic/procedural memory separation.
3. No temporal validity, contradiction resolution, expiry, or forgetting.
4. No background worker for consolidation and reflection.
5. No learned retrieval/reranking or query-specific profile selection.
6. No holdout evaluator, benchmark harness, artifact registry, or rollback implementation.
7. Dataset selection treats positive ratings as sufficient quality evidence.
8. No PII classification/redaction, retention jobs, export, or consent audit history.
9. No real SLM/LoRA trainer despite the training-run boundary.

## Recommended build order

1. Add immutable evidence records with provenance, sensitivity, timestamps, validity, and confidence.
2. Implement a local memory backend with lexical + embedding retrieval behind `MemoryStore`.
3. Add background extraction/consolidation with contradiction and expiry rules.
4. Retrieve only task-relevant memories and expose citations back to evidence.
5. Build memory and personalization evaluation using LoCoMo/LongMemEval ideas and LaMP-style task splits.
6. Add a reflection job that forms revisable higher-level user models from evidence.
7. Add a preference reranker before considering weight updates.
8. Add LoRA/SLM training only after dataset curation, holdout comparison, and rollback exist.

The goal is not merely recall. Reflection AI should learn a revisable model of how the user communicates, decides, works, and changes over time—while always showing what evidence produced that model and allowing the user to correct or delete it.
