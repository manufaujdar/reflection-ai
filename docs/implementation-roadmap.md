# Roadmap to a highly personalized AI engine

The target is a revisable user model, not a chatbot that merely remembers messages. Every behavior change must be traceable to evidence, confidence-scored, correctable by the user, and evaluated against safety and general capability.

## Phase 1: evidence and memory foundation

Build immutable evidence records with source type, timestamps, sensitivity, consent scope, confidence, validity window, and supersession. Add a `MemoryService` that uses the `MemoryStore` port and supports retain, recall, forget, and evidence citation.

Start with Mem0 or Hindsight as an optional backend and maintain a simple local development backend. Evaluate both on latency, relevance, contradiction handling, deletion, isolation, and operating cost before selecting a default.

Exit gate: relevant memories can be retrieved for a query, every result cites evidence, and deletion/consent tests pass.

## Phase 2: reflection and user model

Separate four memory classes:

- Episodic: what happened in an interaction.
- Semantic: stable or time-bounded facts and preferences.
- Procedural: how the user prefers work to be performed.
- Reflective: higher-level, revisable patterns inferred across evidence.

Run extraction and consolidation in background jobs. Add contradiction detection, temporal supersession, confidence decay, expiry, and explicit user corrections. Keep the user's model separate from the assistant's persona.

Exit gate: profile changes show evidence, confidence, extractor version, and history; contradictory preferences resolve without deleting history.

## Phase 3: personalization runtime

Build a query-aware context planner that selects only relevant memories within token, latency, sensitivity, and policy budgets. Add a preference reranker trained from corrections and ratings. Support per-task modes such as writing, research, planning, coding, and decision support.

Exit gate: offline evaluation shows improvement over no-personalization and whole-profile baselines without increasing safety violations or hallucinations.

## Phase 4: evaluation system

Create chronological train/validation/test splits and evaluate:

- Memory recall and temporal correctness.
- Preference adherence and style similarity.
- Task success and correction rate.
- General-capability regression.
- Safety, privacy leakage, and prompt-injection resistance.
- Latency, token cost, and retrieval precision.

Adapt LoCoMo/LongMemEval-style memory tests and LaMP-style personalization tasks. Maintain an incumbent-versus-candidate registry with automatic rejection and rollback.

Exit gate: every deployed profile extractor, retriever, prompt policy, or adapter has reproducible evaluation results.

## Phase 5: model learning

Begin with learned retrieval and reranking. Then experiment with cohort LoRA adapters. Use per-user LoRA only for users with enough diverse, high-quality, consented examples and a clear gain over retrieval-based personalization. Never train on raw model output solely because the model produced it.

Exit gate: a candidate adapter beats retrieval-only personalization on holdout tasks and passes safety/general-capability regression tests.

## Phase 6: user control and production hardening

Add a profile inspector where users can view, correct, pin, expire, export, or delete memories and inferred traits. Add encryption, tenant authorization, retention jobs, audit trails, rate limits, worker queues, observability, backup/restore, and disaster recovery.

Exit gate: privacy deletion is verifiable end to end, users can understand why behavior changed, and every deployed artifact can be rolled back.

## Immediate implementation sequence

Implemented foundations:

1. Evidence and typed/versioned memory database models.
2. Retain/recall/revoke APIs, retention enforcement and a leased background-job interface.
3. Optional Mem0/Hindsight client adapters plus a dependency-free local vector contract baseline.
4. Temporal relationship graph and deterministic contradiction/consolidation tests.
5. Evidence-linked reflection proposals, automatic explicit-preference flow and audit history.
6. Personalization metrics, promotion thresholds and a versioned rollback registry.
7. Query-aware selection, multi-channel fusion and bounded inert context compilation.
8. Consent/data/evaluation-gated training orchestration interfaces.
9. An optional adapter-oriented reference SLM, byte tokenizer, local experimental
   training backend, and transparent chatbot learning-readiness controls.

Next implementation work is operational: persist the queue and registry, build real
embedding/graph adapters, run the benchmark matrix, add authentication/encryption,
implement holdout inference evaluators, and validate a pretrained SLM/PEFT backend.
The reference SLM remains unrouted until those gates pass.
