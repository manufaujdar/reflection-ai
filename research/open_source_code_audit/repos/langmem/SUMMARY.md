# LangMem source review

Snapshot: `a2d580946465137c89162e67dc0b18108bd4850c` (2026-07-14), MIT. Inventory: 91 files, 36,064 text lines, 319 declarations. This is the smallest focused library in the audit. Test cassettes account for a notable part of its line count.

## Architecture and execution path

LangMem supports two complementary paths. In the **hot path**, `create_manage_memory_tool()` gives an agent explicit create/update/delete access and `create_search_memory_tool()` searches a namespaced LangGraph store during a conversation. Namespace placeholders bind memory to a runtime user/team scope. In the **background path**, `MemoryManager` reflects over messages and existing memories, then uses structured tools to create, patch or delete semantic, episodic and procedural memories.

The default reflection instructions prioritize surprising and persistent information, compare it with existing memory, compress redundancy, qualify uncertain conclusions and preserve internal consistency. `ReflectionExecutor` can submit local or remote background jobs and search their store. Thread extractors build schema-constrained summaries. The library leans on LangGraph stores, LangChain runnables and Trustcall for extraction/patch behavior.

## Important files

| Path | Responsibility | Reflection AI use |
|---|---|---|
| `src/langmem/knowledge/tools.py` | Agent-facing memory create/update/delete/search tools | Mirror the narrow operations in Reflection AI's tool API, with consent and evidence requirements. |
| `src/langmem/knowledge/extraction.py` | Structured thread extraction and `MemoryManager` consolidation | Adapt typed extraction and compare/update phases; retain our own schemas and audit ledger. |
| `src/langmem/reflection.py` | Local/remote reflection executor and store search | Reference background-job separation and namespace binding. |
| `src/langmem/prompts.py` | Default memory-management instructions | Use only as test/research input; Reflection AI prompts must be versioned and evaluated. |
| `tests/*` | Tool validation, extraction and executor behavior | Inform contracts for create/update/delete and local job execution. |

## Strengths, gaps and decision

LangMem has clean composable boundaries and explicitly recognizes semantic, episodic and procedural memory. It is an excellent prototype reference for splitting immediate agent tools from delayed consolidation. Its default prompt also highlights confidence and surprising/persistent evidence.

It assumes the LangChain/LangGraph runtime and leaves governance, provenance, temporal truth and end-user controls to the host application. Reflection AI should adapt its functional boundaries and can offer a LangMem adapter, but the core must remain usable by any LLM/tool stack.
