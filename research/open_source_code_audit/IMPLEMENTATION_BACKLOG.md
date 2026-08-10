# Reflection AI implementation backlog

## Phase 1 — trustworthy memory substrate

- Add immutable `InteractionEvent` and `Evidence` records with tenant, user, source, timestamps, consent basis, sensitivity, retention policy and content hash.
- Define typed derived memories: fact, preference, episode, procedure, goal, relationship and behavior rule.
- Add confidence, evidence links, valid-time, transaction-time, status, supersession and expiry to every memory.
- Implement user APIs for list, explain, correct, delete, export, disable learning and retention configuration.
- Put ingestion, embedding, vector store, graph store, reranker and model calls behind ports.

**Exit gate:** isolation, deletion, provenance and deterministic history tests pass before any automatic personalization is enabled.

## Phase 2 — retrieval personalization baseline

- Extract candidate facts/preferences with structured output and evidence spans.
- Deduplicate exact/near duplicates; create explicit supersession rather than destructive overwrite.
- Retrieve in parallel using semantic similarity, lexical match, recency, entity overlap and memory type.
- Fuse scores, apply policy filters, reserve recent-context budget and compile a bounded context package.
- Log which memories affected each answer.

**Exit gate:** offline tests show improvement over a non-personalized baseline without regression in privacy or factual consistency.

## Phase 3 — reflection and consolidation

- Add an idempotent background job queue with retry, dead-letter, cancellation and per-user serialization.
- Give the reflector read-only search tools and explicit proposal tools: create, revise, supersede, expire and no-op.
- Require evidence, confidence, reason and affected-memory IDs on every proposal.
- Add consolidation limits per memory scope and refresh materialized profile summaries only when source memories change.
- Add contradiction, stale-memory and unresolved-conflict queues.

**Exit gate:** replaying a job produces the same committed state; every mutation is explainable and reversible.

## Phase 4 — evaluation and feedback

- Create synthetic and consented evaluation personas with hidden ground truth.
- Measure retrieval recall/nDCG, answer correctness, preference adherence, contradiction rate, stale-memory use, deletion compliance, latency, tokens and cost.
- Compare no personalization, recent-context only, retrieval, retrieval + reflection and model-adapter variants.
- Capture explicit feedback separately from inferred behavioral signals; weight them differently.

**Exit gate:** a versioned evaluation report and promotion threshold are mandatory for releases.

## Phase 5 — gated personal model adaptation

- Build de-identified, versioned training examples from approved evidence and feedback.
- Begin with shared SLM classification/extraction models; later test per-user or cohort LoRA adapters where data volume justifies it.
- Train asynchronously, never inside the request path. Track base model, adapter, dataset, code and prompt versions.
- Run privacy leakage, catastrophic forgetting, safety, preference adherence and holdout tests.
- Promote through shadow/canary stages and retain one-click rollback.

**Exit gate:** adapters must beat retrieval-only personalization on held-out data by a defined margin and pass deletion/retraining policy.

## Near-term file changes in Reflection AI

1. `domain/events.py`, `domain/memories.py`, `domain/policies.py` — provider-neutral records.
2. `ports/evidence.py`, `ports/vector.py`, `ports/graph.py`, `ports/jobs.py`, `ports/training.py` — integration seams.
3. `services/ingestion.py`, `services/consolidation.py`, `services/retrieval.py`, `services/context_compiler.py`, `services/reflection.py`.
4. `evaluation/` — fixtures, metrics, baselines and promotion reports.
5. `adapters/` — optional Mem0, Hindsight, Graphiti and local implementations.

The existing CDSS and MasterLLM examples remain archived. Future integrations should call stable Reflection AI APIs and never reach directly into a chosen memory backend.
