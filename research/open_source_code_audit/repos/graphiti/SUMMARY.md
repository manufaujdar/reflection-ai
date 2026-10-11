# Graphiti source review

Snapshot: `526dcad7a300f3c5c506ff96a68bcdc7ca9f97ed` (2026-07-09), Apache-2.0. Inventory: 352 files, 156,973 text lines, 2,539 declarations. A large portion of test lines is evaluation data; the reusable library lives in `graphiti_core`.

## Architecture and execution path

Graphiti represents incoming content as `EpisodicNode`s, extracted concepts as `EntityNode`s, statements as `EntityEdge`s, and clusters as communities. An episode keeps raw provenance and reference time. `Graphiti.add_episode()` retrieves prior episodes, extracts nodes/edges through LLM clients, resolves entity duplicates, resolves edge duplicates/contradictions, invalidates superseded facts, creates embeddings and persists nodes plus provenance edges. Bulk ingestion follows the same phases with batch deduplication.

Entity edges carry temporal fields including `valid_at`, `invalid_at`, `expired_at` and creation time. This separates when a claim was true from when it was learned. Search can combine full-text/BM25, cosine similarity, graph distance and cross-encoder reranking across edges, nodes, episodes and communities. Database-driver interfaces support multiple graph engines; search recipes package common retrieval configurations.

## Important files

| Path | Responsibility | Reflection AI use |
|---|---|---|
| `graphiti_core/graphiti.py` | Episode ingestion, entity/edge extraction, resolution, search and saga summaries | Reference the staged ingestion pipeline and optional `GraphStorePort` adapter. |
| `graphiti_core/nodes.py` | Episodic, entity, community and saga models | Adopt separate evidence/event and entity concepts, not its database models verbatim. |
| `graphiti_core/edges.py` | Provenance and typed/temporal relationships | Adopt valid/invalid time and source attribution for relationships. |
| `graphiti_core/search/search.py` | Multi-channel search and reranking | Inform hybrid retrieval and per-channel explanations. |
| `graphiti_core/utils/maintenance/*` | Extraction, dedup, invalidation, communities | Reference contradiction and graph-maintenance tests. |
| `graphiti_core/driver/*` | Neo4j/FalkorDB/Kuzu abstractions | Keep graph persistence optional; avoid making a graph server necessary for basic personalization. |

## Strengths, gaps and decision

Graphiti gives Reflection AI the best model for claims that change over time: retain old truth, mark its validity interval, preserve the episode that supported it, and retrieve the correct state for the question's time. This is more defensible than overwriting “user likes X.”

It is a temporal knowledge-graph library, not a preference policy, consent system or training loop. Add a future Graphiti adapter behind `GraphStorePort`; first implement the same temporal/provenance fields in the canonical relational domain so the rest of Reflection AI does not depend on graph infrastructure.
