# Supermemory source review

Snapshot: `ef0026a23c160e2976480352e5a6f58762d70d13` (2026-07-14), MIT. Inventory: 1,014 files, 190,912 text lines, 9,126 declarations. This is a TypeScript monorepo containing API services, web/docs applications, SDK/tooling, MCP support and a memory-graph visualization package.

## Architecture and execution path

Supermemory is primarily a productized document-to-memory platform. Its API accepts documents and connected content, processes/chunks it asynchronously, stores embeddings and exposes search/profile behavior. The data contracts include documents with derived memories and explicit memory-to-memory relations such as `updates`, `extends` and `derives`. Memory metadata also models latest-version state and forgetting/expiry fields. The user-profile surface separates relatively stable and dynamic profile material for prompt use.

`packages/memory-graph` is a standalone visualization layer, not the inference engine. It converts API documents/memories into graph nodes and relation edges, computes version chains, clusters nodes, applies deterministic layout and renders large graphs with level-of-detail behavior. Its tests are especially useful for update-chain direction, edge construction and dense-graph rendering.

## Important areas

| Path | Responsibility | Reflection AI use |
|---|---|---|
| `apps/api` | Document ingestion, processing, search and profile APIs | Reference asynchronous ingestion and API ergonomics; do not import the whole application. |
| `packages/memory-graph/src/api-types.ts` | Memory/document relation contracts | Adapt `updates`/`extends`/`derives`, expiry and latest-state semantics. |
| `packages/memory-graph/src/hooks/use-graph-data.ts` | API-to-graph conversion and edge computation | Potential future UI adapter for explaining memory lineage. |
| `packages/memory-graph/src/canvas/version-chain.ts` | Navigation through memory revisions | Use as a UI reference after the backend has real supersession history. |
| `packages/memory-graph/src/__tests__` | Relation, version-chain and rendering cases | Translate relation invariants into domain tests. |
| `packages/*` SDK/MCP/tooling | Client and tool integrations | Inform a thin Reflection AI SDK after API stabilization. |

## Strengths, gaps and decision

The strongest contribution is the product-level representation of memory lineage and its explainability UI. Relations are preferable to destructive replacement because a user can see why one memory superseded or extended another. Expiry/forgetting metadata also aligns with privacy requirements.

The repository's business logic is interwoven with a large web/API monorepo and managed-service concerns. Adapt the relation schema and user-profile contract. Consider reusing the MIT visualization package later as a separately attributed frontend dependency; it should not shape the core storage model prematurely.
