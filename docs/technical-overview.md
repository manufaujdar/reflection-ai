# Technical overview

Status: research alpha; production hardening is blocked on the proposed
authentication/tenant implementation contract.

## Runtime and package map

- Python 3.11 or newer.
- FastAPI/Uvicorn expose the HTTP surface.
- SQLAlchemy provides the current persistence adapter.
- Pydantic Settings provides configuration.
- Optional Mem0 and Hindsight extras are adapters, not required core dependencies.
- Source is under src/reflection_ai and tests under tests/.

## Code responsibilities

- api.py and main.py: HTTP application and local entrypoint.
- db.py and adapters/sqlalchemy.py: persistence boundary.
- domain/: framework-independent models and policy.
- personalization.py and memory.py: evidence, memory, retrieval, retention, and adapters.
- services.py: profile learning, prompt personalization, and training preparation.
- providers.py: mock and OpenAI-compatible inference.
- engine/: jobs, graph/vector/consolidation/retrieval/evaluation/registry/training baselines.
- ports.py: extension interfaces for extraction, memory, training, evaluation, and registry.
- tests/: consent, deletion, API, engine, and team checks.

## Data lifecycle and operations

Consent-gated event -> evidence -> proposal/profile/memory -> bounded retrieval
-> provider response -> feedback/evaluation -> versioned dataset -> optional
trainer/evaluator/registry path.

Use the README virtualenv/Uvicorn flow and synthetic console only. The mock
provider is reproducible. Ollama is permitted only on literal loopback.

## Validation and human gates

The existing tests, Ruff, and team checks define the research baseline. Before
networked or multi-tenant use, implement and verify principal validation,
tenant-scoped repositories, deletion receipts, job fencing, prohibited-
inference checks, encryption/key management, retention, and rollback. No
license or production release should be inferred from repository visibility.

