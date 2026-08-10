# Adaptive chatbot

The adaptive chatbot is a complete local research path from consent and onboarding to
provider-neutral generation, feedback, explainable memory, and evaluation-gated training data.
It is available at `/chat`; its JSON API is under `/v1/chat`.

This is not an impersonation engine. It adapts how an assistant communicates and which explicit
user context it recalls. It must not infer identity, diagnoses, emotions, protected traits, beliefs,
or unrelated private facts. The local site has no authentication, encryption, rate limiting, CSRF
protection, or production tenant boundary, so it must not be exposed or used with real sensitive data.

## Runtime layers

```text
Browser UI
  -> FastAPI chat router
  -> consent guard + session boundary
  -> chat orchestrator / agent harness
       -> observable style learner
       -> evidence-backed typed memory retrieval
       -> bounded context compiler
       -> provider-neutral response agent
       -> interaction/evidence recorder
  -> SQLite through SQLAlchemy
  -> feedback/correction loop
  -> existing evaluation-gated dataset/training/registry ports
```

The implementation uses FastAPI for the HTTP boundary, Pydantic for input/output contracts,
SQLAlchemy for persistence, and the existing `ModelProvider` interface for either the reproducible
mock or an OpenAI-compatible hosted/local LLM. It intentionally avoids a heavyweight agent framework:
the internal harness is explicit, offline-testable, and does not hide consent or memory mutations.

## Agent harness

Each response records an `AgentRun` with a prompt hash and non-content trace:

1. `consent-guard-agent` fails closed when storage consent is missing.
2. `style-learning-agent` updates running aggregates of observable mechanics only.
3. `memory-retrieval-agent` retrieves active user-scoped memory with an attribution score.
4. `context-planner-agent` compiles selected records as bounded, inert data.
5. `response-agent` calls the configured model provider.

The provider receives a bounded window of the current session transcript as structured
user/assistant messages (`REFLECTION_CHAT_HISTORY_MESSAGES`, default 20). Transcript contents are
not copied into the agent trace; only the count and a one-way prompt hash are retained there.

The onboarding path is the explicit preference acquisition agent. Every non-skipped answer is
stored as evidence, converted to a typed memory, and linked through `MemoryEvidence`. Corrections
use the same explicit evidence-backed path. Ordinary conversation never silently becomes a fact.

## Learning loops

### Immediate communication loop

After each user message, the style learner updates running averages for message length, sentence
length, question/exclamation frequency, bullet use, and emoji frequency. It emits instructions only
after `REFLECTION_CHAT_STYLE_MIN_SAMPLES` samples (default three). These are low-risk writing
mechanics, not psychological or demographic inference.

### Explicit memory loop

Onboarding answers and corrections create typed, versioned memory with source evidence. Retrieval is
user-scoped and produces an explanation trace. Supersession, revocation, retention, and full subject
deletion reuse the core memory lifecycle.

### Feedback and model-improvement loop

Helpful/unhelpful ratings attach to the original complete interaction event. Positively rated,
complete interactions can enter the existing versioned training-dataset builder only when separate
training consent exists. Training stays asynchronous and promotion-gated: a future SLM/LoRA adapter
must train on a split dataset, beat the current candidate on personalization and safety evaluations,
and retain rollback. No request fine-tunes model weights inline.

## Database tables

- `chat_sessions`: onboarding and active conversation lifecycle.
- `onboarding_answers`: explicit answer record and resulting memory ID.
- `chat_messages`: redacted user/assistant transcript and event link.
- `chat_style_profiles`: running observable-style aggregates and derived instructions.
- `chat_agent_runs`: stage trace, provider/model, prompt hash, status, and timestamps.

Core tables continue to hold the subject, evidence, versioned memory, provenance links, audit records,
reflection proposals, interaction events, and training runs.

## API

- `POST /v1/chat/sessions` — resolve a local subject and begin onboarding.
- `GET /v1/chat/sessions/{id}/onboarding` — obtain current progress/question.
- `POST /v1/chat/sessions/{id}/onboarding` — submit or skip the current question.
- `POST /v1/chat/sessions/{id}/messages` — run the adaptive agent harness.
- `GET /v1/chat/sessions/{id}/messages` — load the persisted transcript.
- `POST /v1/chat/messages/{id}/feedback` — rate or explicitly correct an answer.
- `GET /v1/chat/sessions/{id}/personalization` — inspect style, memory, provenance, and traces.
- `DELETE /v1/users/{id}` — delete the subject and every chatbot/core learning layer.
- `GET /v1/chat/capabilities` — inspect implemented features and explicit limitations.

## Production integration boundary

Before deployment, put the router behind the documented authenticated principal/tenant contract,
replace direct database access with tenant-scoped repositories, enable encryption and managed secrets,
add rate/abuse controls, migrate background work to a queue, and run security/privacy reviews. The
provider and memory ports let a host project integrate the engine without coupling its own UI or LLM.
