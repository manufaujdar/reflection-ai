# Archived: CDSS and MasterLLM integration

This is a preserved research and integration proof of concept. It is not part of the active Reflection AI roadmap or required runtime.

This design was based on the local `healthunited-in/CDSS` and `Stardustpaaji/master-ai-hub` repositories. Both hosts already expose a compatible chat shape with `userId`, `sessionId`, `systemPrompt`, `personalization`, `memoryContext`, and `feedbackAnalysis`. Both also use Supabase user profiles, feedback, memory services, and consolidated chat handlers.

## Ownership boundary

Reflection AI owns profile learning, preference versions, event lineage, context compilation, and training-dataset preparation. The host continues to own authentication, clinical policy, RAG, citations, model routing, provider calls, response streaming, and final safety enforcement.

The host should call `POST /v1/context` immediately before its model-routing/provider boundary. Reflection returns a structured context and composed system prompt. If Reflection is unavailable, the TypeScript adapter fails open to the original host request so chat availability is not coupled to personalization.

## Required flow

1. Resolve a subject after login or anonymous-session creation with `POST /v1/subjects/resolve`.
2. Request context before inference with the host's current personalization, memory, and feedback summaries.
3. Keep `deep_analysis`, `dims`, `clinical_protocol`, and `emergency` modes protected. Reflection returns the base prompt unchanged for these modes.
4. Dispatch to the host's existing model router.
5. Capture the final interaction asynchronously with a stable idempotency key such as `sessionId:messageId:completed`.
6. Capture user ratings/corrections as separate events.

## Existing field mapping

| Host field | Reflection field | Notes |
|---|---|---|
| `userId` | `external_user_id` | Scoped by application and tenant |
| `sessionId` | `session_id` | Trace and learning context |
| message ID | `message_id` | Needed to join later feedback |
| `systemPrompt` | `base_system_prompt` | Host policy remains first |
| `personalization` | `host_personalization` | Merged with learned preferences |
| `memoryContext` | `memory_context` | Treated as untrusted data |
| `feedbackAnalysis` | `feedback_analysis` | Bounded improvement hints |
| selected model | event `model` | Used for evaluation and routing research |

## Supabase deployment

SQLite remains the local development default. Production should implement the same repository boundary with Postgres/Supabase and reuse the host Supabase project where operationally appropriate. Keep Reflection tables in a separate schema, enable RLS/tenant checks, use service-to-service authentication, and do not expose the service role key to either frontend.

Do not copy raw clinical records into training events. Redact or tokenize identifiers before ingestion, store references to host-owned memory when possible, and separate personalization consent from model-training consent.

## Rollout

Start in shadow mode: request context and log the result without changing prompts. Next, enable explicit settings only, then learned profiles for a small non-clinical cohort. Weight training comes last and requires offline holdout evaluation, safety/regression gates, versioned deployment, and rollback.
