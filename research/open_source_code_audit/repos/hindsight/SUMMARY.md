# Hindsight source review

Snapshot: `395823f7b6611a08a777d3c03414a3270ec54d18` (2026-07-14), MIT. Inventory: 3,294 files, 910,507 text lines, 27,434 declarations. Much of the volume is integrations, generated clients, docs, migrations, benchmarks and fixtures; the principal engine is under `hindsight-api-slim/hindsight_api/engine`.

## Architecture and execution path

Hindsight exposes three explicit operations. **Retain** accepts content/documents, chunks and embeds them, extracts facts/entities/temporal information, stores memory units and schedules maintenance. **Recall** analyzes a query, executes multiple retrieval strategies, fuses/reranks results, expands connected evidence and applies a token budget. **Reflect** runs a bounded tool-using agent that can search mental models, observations and recall results before producing a final or structured answer.

Background consolidation converts retained units into denser observations. `consolidator.py` groups by scope/tags, filters deleted sources, asks the LLM for create/update/delete actions, adjudicates duplicates, limits scope growth, preserves observation history and creates links. Mental models are materialized, refreshable summaries with staleness checks and history. The engine also includes bank/tenant isolation, disposition and mission settings, directives, async operation records, webhooks, retries, audit logs and health checks.

## Important files

| Path | Responsibility | Reflection AI use |
|---|---|---|
| `engine/memory_engine.py` | Public orchestration for retain, recall, reflect, documents, banks, observations and mental models | Use the operation boundaries as API inspiration; integrate through the existing optional adapter before reimplementation. |
| `engine/consolidation/consolidator.py` | Scoped batch consolidation with history, dedup and limits | Reimplement a smaller state machine with evidence-first proposals and idempotent jobs. |
| `engine/reflect/agent.py` | Bounded search/tool loop, structured output, token and overflow handling | Adapt tool restrictions, iteration limits and trace collection. |
| `engine/retrieval/*` | Query analysis, candidate retrieval and scoring | Inform hybrid retrieval and explainable score components. |
| `engine/embeddings.py` | Embedding lifecycle/configuration | Keep behind Reflection AI's embedding port. |
| `engine/temporal/*` and migrations | Temporal parsing/storage evolution | Adopt valid-time plus ingestion-time and test backdated evidence. |
| `tests` and `dev/benchmarks` | Behavior, migration and long-memory evaluation | Select scenarios for Reflection AI's replay and benchmark suite. |

## Strengths, gaps and decision

Hindsight is the closest conceptual match to Reflection AI: it treats reflection as an evidence-seeking operation, separates raw memory from consolidated observations, and makes mental models refreshable instead of pretending a single prompt is the user. It also demonstrates the operational cost: a very large coordinator, deep PostgreSQL schema, migrations and many deployment concerns.

Use Hindsight via a backend adapter now. Port only domain concepts that remain valuable without its infrastructure: retain/recall/reflect verbs, observation history, scoped consolidation, mental-model staleness and explicit directives. Do not fork its database engine into the core.
