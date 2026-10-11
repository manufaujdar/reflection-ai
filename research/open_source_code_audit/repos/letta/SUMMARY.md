# Letta source review

Snapshot: `b76da9092518cbaa2d09042e52fdcbde69243e18` (2026-07-03), Apache-2.0. Inventory: 1,156 files, 367,689 text lines, 8,820 declarations. The README identifies this repository as the legacy V1 server, so its patterns are useful but it should not be treated as the current Letta product architecture.

## Architecture and execution path

Letta distinguishes memory by where it lives. **Core memory** is a list of bounded `Block` records rendered into the system context. Blocks can represent the human, persona and other stable sections; they carry descriptions, character limits and read-only state. **Recall memory** is conversation/message history. **Archival memory** is embedded `Passage` data retrieved with tools. A context-window overview accounts separately for system prompt, core memory, summary memory, functions, messages and external-memory metadata.

`letta/schemas/memory.py` renders blocks into structured XML-like prompt sections, including line-numbered and git-backed forms. Block services maintain shared blocks and rebuild affected agent prompts. Passage services create chunks, generate embeddings concurrently, manage tags, and persist/search archival content. Agent loops expose explicit tools such as core-memory replace/insert and archival-memory search/insert, letting the model manage its working state. Message managers preserve recall history while summarization prevents context overflow.

## Important files

| Path | Responsibility | Reflection AI use |
|---|---|---|
| `letta/schemas/memory.py` | Core-memory model, rendering and context accounting | Adopt typed, bounded profile blocks and explicit token accounting in the context compiler. |
| `letta/schemas/block.py` | Block identity, value, limit and metadata | Inform `ProfileSection`, but add provenance/confidence and avoid making prompt format the storage schema. |
| `letta/services/block_manager.py` | Block CRUD, sharing and prompt rebuild | Reference dependency invalidation when a profile summary changes. |
| `letta/services/passage_manager.py` | Archival passage CRUD, tags and embeddings | Reference ingestion adapter behavior and batch embedding. |
| `letta/agents/*` | Agent loops, summarization and tool execution | Do not couple Reflection AI to an agent loop; expose these operations through an API/tool facade. |
| `letta/services/memory_repo/*` | Git-backed memory projection | Consider later for human-auditable profile exports, not baseline storage. |

## Strengths, gaps and decision

The strongest idea is a visible, bounded “working self” separated from large external memory. Reflection AI should compile a small user model—identity, stable preferences, current goals and behavioral policies—then supplement it with retrieved evidence. Character/token limits and explicit editing operations prevent silent prompt growth.

Letta is an agent server, not a neutral personalization engine, and the audited branch is legacy. Do not copy its service graph. Adapt the block and context-budget concepts into provider-neutral domain records; keep any Letta integration as a future adapter.
