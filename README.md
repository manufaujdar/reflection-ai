# Reflection AI

Read the [documentation map](docs/README.md) before changing consent, memory,
training, evaluation, or deployment behavior.

[![CI](https://github.com/manufaujdar/reflection-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/manufaujdar/reflection-ai/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

A standalone framework for building an AI that becomes more aligned with how an individual
communicates and works as conversations accumulate. It learns immediately from explicit preferences,
observable writing mechanics, and user corrections. With separate consent, positively rated examples
can later enter offline, evaluation-gated adapter training. Every layer is inspectable, reversible,
and subordinate to consent, safety, deletion, and rollback controls.

Reflection AI is an alpha, local-first research framework. It is not production-ready,
does not establish privacy or security compliance, and must not be used for
high-impact decisions. Personalization records are revisable hypotheses backed by
evidence—not authoritative facts about a person.

## Architecture

```text
Client -> FastAPI -> Evidence -> Proposal -> Typed/versioned memory
             |                                  |
             +-> bounded explainable retrieval -+-> Model provider -> Response
             |                                  |
             +-> retention and audit            +-> feedback/evidence loop
                         |
             evaluated training dataset -> trainer/evaluator/registry ports
```

The starter implements the complete local loop through evidence-backed memory and gated dataset preparation. Explicit preferences and corrections become immediately usable memories through an auditable proposal; inferred claims require a separate apply step. It deliberately does **not** fine-tune weights after every message: that is expensive, risks learning mistakes, and can cause regressions. A production trainer can attach LoRA adapters to an SLM, or call a hosted fine-tuning API only after evaluation.

## Quick start

```bash
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn --app-dir src reflection_ai.api:app --reload
```

Open `http://localhost:8000/docs` for the interactive API.

Open `http://localhost:8000/chat` for the adaptive chatbot. It walks through a
consent-gated onboarding flow, learns explicit preferences and low-risk observable
writing mechanics, persists conversation history, accepts feedback/corrections,
and exposes a personalization inspector with memory provenance and agent traces.
See [docs/adaptive-chatbot.md](docs/adaptive-chatbot.md) for the architecture and
production boundaries.

Open `http://localhost:8000/` for a minimal synthetic research console that can
create, exercise, and delete a local test subject. It is intentionally labeled as
unauthenticated and must never receive real personal or confidential information.

Integrations can inspect `GET /v1/capabilities` for the framework’s explicit
privacy invariants: consent-gated storage and training, evidence-linked memory,
deletion support, and the fact that this starter is not production-ready.

```bash
curl -X POST http://localhost:8000/v1/users \
  -H 'content-type: application/json' \
  -d '{"external_id":"demo-user","consent":true}'
```

Use the returned ID to post preferences, generate responses, refresh the profile, or prepare a training run. Set `REFLECTION_MODEL_PROVIDER=openai-compatible` and a base URL to connect any OpenAI-compatible local or hosted LLM.

For Ollama on the same machine, no cloud key is needed:

```bash
REFLECTION_MODEL_PROVIDER=openai-compatible \
REFLECTION_MODEL_BASE_URL=http://127.0.0.1:11434 \
REFLECTION_MODEL_NAME=gemma3:1b \
uvicorn --app-dir src reflection_ai.api:app --reload
```

This localhost path was smoke-tested with the existing provider adapter. Keep the
mock provider as the reproducible default and never expose an unauthenticated Ollama
port to other machines.

## Learning loop

1. Capture interactions only after user consent.
2. Attach explicit preferences, topics, ratings, or corrections as events.
3. Refresh the transparent per-user profile every few events.
4. Inject that profile at inference time for immediate personalization.
5. Select positively rated examples into a versioned dataset.
6. Train an adapter/SLM, evaluate it against the current version, and deploy only if it wins.
7. Keep rollback, deletion, audit, and per-user isolation available.

## Project map

- `api.py`: HTTP endpoints and orchestration
- `db.py`: users, profiles, events, and training-run records
- `providers.py`: mock and OpenAI-compatible inference adapters
- `services.py`: profile learning, prompt personalization, dataset preparation
- `personalization.py`: immutable evidence, proposals, typed memory, retrieval, context compilation, retention and redaction
- `chat/`: onboarding, chat persistence, observable-style learning, schemas, agent harness and API routes
- `frontend/`: responsive chatbot, onboarding flow, feedback controls and personalization inspector
- `slm/`: optional causal reference model, byte tokenizer, low-rank adapters and local experimental trainer
- `domain/`: framework-independent memory, evidence, artifact, temporal and policy models
- `engine/`: runnable local job, vector, graph, consolidation, retrieval, evaluation, registry and training baselines
- `adapters/`: infrastructure-to-domain translators, beginning with SQLAlchemy
- `ports.py`: stable extension boundaries for memory, extraction, training, evaluation, and registry implementations
- `tests/`: consent and core-loop checks
- `docs/architecture.md`: production roadmap and safety boundaries
- `docs/open-source-landscape.md`: research review and prioritized design lessons
- `docs/implementation-roadmap.md`: phased plan for memory, reflection, evaluation, and model learning
- `docs/personalization-core.md`: implemented trust, lifecycle and API invariants
- `docs/adaptive-chatbot.md`: chatbot layers, agent harness, immediate/memory/training loops and API
- `docs/reference-slm.md`: supplied-model assessment, enhanced reference architecture and safe training boundary
- `docs/authentication-tenant-contract.md`: Privacy- and Security-accepted fail-closed
  identity, tenant, consent, deletion, and abuse-test contract; not yet implemented
- `docs/engine-building-blocks.md`: original local baselines and production replacement contracts
- `docs/agent-team.md`: explicit AI delivery gears, project skills, and release gates
- `.agents/skills/`: validated Planner, Builder, Engineer, Reviewer, QA, Release, Documentation, R&D, Marketing, Design, Privacy, Security, Evaluation, and Retro skills
- `memory.py`: optional adapters that reuse maintained Mem0 and Hindsight clients
- `THIRD_PARTY_NOTICES.md`: dependency, license, and reuse inventory
- `VALIDATION_PROTOCOL.md`: minimum evidence and release gates for personalization changes
- `MODEL_CARD_TEMPLATE.md` and `DATASET_CARD_TEMPLATE.md`: provenance-first review templates
- `COMPLIANCE_AND_DEPLOYMENT.md`: explicit research and production boundary
- `PROVENANCE.md`: source, model, dataset, service, and artifact traceability rules
- `tools/project_agent/`: deterministic local repository and console audit
- `archive/`: inactive integration research retained for possible future use

Install an optional open-source memory backend without copying its internal implementation:

```bash
pip install -e '.[memory-mem0]'
# or
pip install -e '.[memory-hindsight]'
```

Install the experimental local SLM components separately:

```bash
pip install -e '.[slm]'
```

The reference SLM is not automatically routed to the chatbot. Adapter artifacts
must still pass the existing consent, evaluation, registry, promotion, and rollback gates.

Reflection AI runs independently. Its HTTP and Python boundaries remain generic so future clients can be added without coupling the core to any particular application.

## Open-source governance

Source code is licensed under Apache-2.0. See [LICENSE](LICENSE), [NOTICE](NOTICE),
and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Public source availability
does not license external datasets, model weights, hosted services, or optional
provider assets.

Contributions must use synthetic fixtures and preserve consent, isolation,
deletion, provenance, evaluation, and rollback invariants. See
[CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md),
[GOVERNANCE.md](GOVERNANCE.md), and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
The source-only privacy and self-hosting boundary is in
[PRIVACY_AND_DATA_BOUNDARY.md](PRIVACY_AND_DATA_BOUNDARY.md).

Run the complete local validation gate with:

```bash
make validate
```

## Production next steps

Add authentication and tenant isolation, encrypt sensitive data, redact PII before storage, move jobs to a queue, add evaluation/rollback gates, and implement a trainer adapter (for example PEFT/LoRA on a small model). Never train directly on secrets or unreviewed model output, and give users export/delete/opt-out controls.
