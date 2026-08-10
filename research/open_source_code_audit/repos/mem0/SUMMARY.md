# Mem0 source review

Snapshot: `633b0353422ff7634f8ec72daa4d1aed9e224983` (2026-07-15), Apache-2.0. Inventory: 1,803 files, 339,723 text lines, 14,217 declarations. The repository includes Python and TypeScript SDKs, a self-hosted server, integrations, CLI, UI and extensive provider adapters; those are distinct products around the same memory abstraction.

## Architecture and execution path

The OSS Python center is `mem0/memory/main.py`. `Memory` and `AsyncMemory` construct LLM, embedder, vector store, optional graph store, reranker, history database and a lazy entity collection from configuration factories. `add()` validates user/agent/run scope and delegates to `_add_to_vector_store()`. The latter normalizes messages, optionally bypasses inference, asks an LLM for standalone facts, embeds/inserts them, records ADD history and links extracted entities. In this snapshot the default extraction path is additive; explicit update/delete methods still exist for API operations and compatibility.

`search()` validates the query and scope, embeds it, runs vector search, filters expired records, optionally extracts query entities and boosts linked memories, then optionally reranks. CRUD methods keep the vector record, entity links and SQLite history aligned. `mem0/configs/*`, `embeddings/*`, `vector_stores/*`, `rerankers/*` and `llms/*` implement the provider matrix. The TypeScript implementation mirrors much of this design under `mem0-ts/src/oss`.

## Important files

| Path | Responsibility | Reflection AI use |
|---|---|---|
| `mem0/memory/main.py` | Scoped add/search/CRUD, expiration, entity linking, history, sync/async APIs | Adapt the lifecycle and filtering semantics behind our own ports; avoid copying the 3,777-line coordinator. |
| `mem0/memory/utils.py` | Message parsing, fact normalization, JSON recovery, vision conversion | Reuse concepts for robust structured extraction and normalization tests. |
| `mem0/configs/base.py` and factories | Provider selection/config validation | Keep Reflection AI's smaller port model; adapter-specific configuration should not leak into the domain. |
| `mem0/vector_stores/*` | Backend-specific insert/search/filter behavior | Reference for adapters and conformance tests. |
| `mem0/rerankers/*` | Cross-encoder, LLM and hosted rerankers | Add an optional `RerankerPort` with deterministic fallback. |
| `mem0/memory/storage.py` | Mutation history | Extend the idea to immutable evidence and complete audit provenance. |
| `tests/memory/*` | Validation, temporal/decay notices, CRUD and failure cases | Translate edge cases into provider-contract tests. |

## Strengths, gaps and decision

Mem0 is the best reference here for a practical, model-neutral memory SDK. Its strongest reusable ideas are mandatory identity scope, backend factories, metadata filters, entity-assisted retrieval, expiry, history and graceful optional features. Its main architectural weakness for Reflection AI is concentration of orchestration in one large file with duplicated sync/async implementations. “Memory” is also primarily a retrieved fact record, not a full typed user model with evidence, confidence, consent and temporal validity.

Use the existing Mem0 adapter as an optional backend. Implement Reflection AI's evidence ledger, typed profile and policy layer independently, and add contract tests that compare local and Mem0 behavior.
