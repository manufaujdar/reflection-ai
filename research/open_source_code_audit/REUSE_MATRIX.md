# Reuse matrix

“Adapt” means implement the pattern behind Reflection AI's own ports and schemas. “Vendor” means copying source is technically plausible but still requires file-level license notices, dependency review, security review, and pinned tests. This document is engineering guidance, not legal advice.

| Capability | Strongest reference | Decision | Why / boundary |
|---|---|---|---|
| Memory provider abstraction | Mem0 factories and Reflection AI's existing `MemoryBackend` | Adapt | Preserve vendor independence; do not import Mem0's large configuration surface into the domain core. |
| Add/search/history operations | Mem0 `mem0/memory/main.py` | Adapt | Useful scoping, expiration, entity boost and history patterns; its sync/async duplication should not be copied. |
| Core user/persona context | Letta `schemas/memory.py` and block services | Adapt | Typed, size-bounded blocks are ideal for the context compiler; keep storage independent of agent runtime. |
| Background reflection | LangMem `knowledge/extraction.py` + `reflection.py` | Adapt or optional dependency | Clean runnable boundary and namespace model; Reflection AI should not require LangGraph. |
| Retain/recall/reflect | Hindsight `memory_engine.py` | Integrate through adapter first | Very complete but operationally large. Use its API as an optional backend before reproducing selected concepts. |
| Consolidation | Hindsight consolidator | Reimplement narrowly | Adopt batch state machine, dedup, scope limits and history; avoid copying its database-specific 2k+ line implementation. |
| Temporal provenance graph | Graphiti core | Optional adapter | Mature graph ingestion and invalidation. Do not make Neo4j/FalkorDB/Kuzu a mandatory baseline dependency. |
| Personal document ingestion | Supermemory and Khoj processors | Adapt interfaces | Useful product patterns, but both bring a large application stack. Build connectors behind an ingestion port. |
| User memory controls | Khoj memory API/settings | Adapt | Explicit enable/disable, list, update and delete controls should be baseline behavior. AGPL makes direct copying unsuitable for a permissively licensed core unless obligations are accepted. |
| Memory graph visualization | Supermemory `packages/memory-graph` | Optional later vendor/adaptation | MIT and well tested, but it is UI—not the memory engine. Keep it in a separate frontend package. |
| Profile-item ranking | LaMP `rank_profiles.py` | Reimplement + test | Algorithms are standard and the root has no detected license. Do not copy source until licensing is clarified. |
| Personalization evaluation | LaMP metrics/task design | Adapt concepts | Establish personalized versus non-personalized, retrieval-only, adapter-only and combined baselines. |
| Online model training | None is a safe turnkey answer | Build gated pipeline | Continuous raw weight updates create privacy, poisoning, forgetting and rollback risks. Use dataset versions and promotion gates. |

## Safe copying procedure

Before any upstream file enters Reflection AI:

1. Record repository URL, pinned commit, original path, license and copyright.
2. Confirm the license is compatible with Reflection AI's intended distribution and network deployment.
3. Copy the smallest cohesive unit, preserving required notices.
4. Add an entry to `THIRD_PARTY_NOTICES.md` and a source-level attribution header where required.
5. Add characterization tests before modifying behavior.
6. Maintain a patch log so upstream security fixes can be compared.

At this audit stage, no upstream implementation file has been silently copied into the runtime. The generated TSV indexes and original analysis are safe project artifacts; upstream source remains in temporary clones.
