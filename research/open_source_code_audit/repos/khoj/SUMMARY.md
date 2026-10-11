# Khoj source review

Snapshot: `1e30154d1070c7b132f389638c008b490be1481b` (2026-06-24), AGPL-3.0. Inventory: 701 files, 133,097 text lines, 3,613 declarations. Khoj is a complete personal assistant with backend, web interface, document processors, agents and delivery channels rather than a standalone memory library.

## Architecture and execution path

Khoj's conversation path combines distinct personalization inputs. Agent records provide an explicit personality and tools. Before a chat response, `api_chat.py` loads recent user memories and separately searches long-term memories relevant to the current query. Prompt helpers inject personality context and relevant memory into provider-specific system prompts.

After/around interactions, helper functions ask an LLM for structured memory changes: facts to create and facts to delete. `UserMemoryAdapters` persists and semantically searches the records. Users can enable or disable memory, list their memories, edit (implemented as replacement) and delete them through dedicated APIs/UI. Document processors and embeddings provide a wider “second brain” corpus that is separate from compact learned user facts.

## Important files

| Path | Responsibility | Reflection AI use |
|---|---|---|
| `src/khoj/routers/api_chat.py` | Chat orchestration, recent and relevant memory retrieval | Adopt the two-channel context strategy and fixed budget. |
| `src/khoj/routers/helpers.py` | Prompt construction, fact extraction and memory update flow | Adapt structured proposals; add evidence/confidence and never log sensitive memory text. |
| `src/khoj/database/adapters/*` | User memory save/search/delete | Reference tenant/agent scoping and database tests. |
| `src/khoj/database/models.py` | User, agent, conversation and memory records | Inform ownership relationships, not schema copying. |
| `src/khoj/routers/api_memories.py` | End-user memory inspection and mutation | Make equivalent controls mandatory in Reflection AI. |
| `src/khoj/processor/embeddings.py` | Search-model abstraction and embedding operations | Keep provider-specific behavior behind adapters. |
| `tests/test_memory_settings.py` | Memory enablement behavior | Translate privacy toggles into cross-backend contract tests. |

## Strengths, gaps and decision

Khoj demonstrates the whole product loop: explicit persona, personal documents, learned facts, recent context, semantic retrieval and visible user controls. The opt-out and memory-management UI are more important to Reflection AI than another extraction prompt.

Its AGPL license is a material integration constraint for network software. Do not copy Khoj implementation into a differently licensed core without accepting and reviewing those obligations. Reimplement the product patterns from independent specifications and keep Khoj interoperability optional.
