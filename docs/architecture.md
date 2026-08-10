# Standalone architecture and extension points

Reflection AI is developed as an independent personalization engine. External application adapters are optional and are not part of the active runtime. The domain layer must remain usable from the HTTP API, a Python process, a worker, or a future adapter without importing host-specific code.

## Core boundaries

- **Event ingestion** accepts interactions, explicit preferences, corrections, and normalized feedback.
- **Profile extraction** turns evidence into inspectable preferences. The starter uses deterministic aggregation; an extractor SLM can implement the same boundary.
- **Evidence and memory** separate immutable source material from typed facts, preferences, episodes, procedures, goals, relationships, behavior rules, and reviewable reflection proposals. Retrieval is query-relevant and fully attributed rather than injecting an entire profile.
- **Inference provider** supports any service implementing OpenAI-compatible chat completions. Add another `ModelProvider` for other protocols.
- **Training service** selects positive examples and versions the dataset. A production `Trainer` should accept that artifact and return adapter/model metadata plus evaluation metrics.
- **Model registry/router** is the next deployment component: map a user or cohort to an approved adapter and fall back to the base model.

## Recommended production loop

Use two cadences. Update profile and retrieval memory after a small number of events for immediate learning. Trigger weight training less often, only when there is enough high-quality data. Split data chronologically, compare the candidate with the deployed version on personalization, safety, and general-capability suites, then canary and roll back automatically on regression.

Use three learning paths:

1. **Hot path:** retrieve a small amount of relevant, trusted context before inference.
2. **Background path:** extract, consolidate, expire, contradict, and summarize memories after interactions.
3. **Training path:** build reviewed datasets and update a reranker, adapter, SLM, or LLM only after evaluation.

Every derived preference retains evidence IDs, confidence, extractor version, timestamps, temporal validity and supersession history. User assertions, model outputs, inferred traits, explicit feedback and external documents remain distinct evidence classes. These invariants are implemented in `personalization.py`; vector and graph systems are optional indexes, never the canonical source of truth.

Per-user adapters provide the strongest isolation but are costly at scale. Cohort adapters plus per-user profiles are a practical default. A small preference model or reranker can often improve selection before full fine-tuning is justified.

## Privacy and safety invariants

- Consent is required for event storage and training.
- Users can delete their stored profile, events, and training history.
- Separate identity from training content and use tenant-scoped authorization.
- Redact PII/secrets and define retention before accepting production traffic.
- Treat learned preferences as lower priority than system and safety policy.
- Maintain data lineage, dataset/model versions, evaluation results, and rollback targets.
- Protect against prompt injection in stored memory and poisoning through adversarial feedback.

## Suggested next interfaces

```python
class ProfileExtractor:
    def extract(self, events, previous_profile): ...

class Trainer:
    def train(self, dataset_uri, base_model, previous_adapter=None): ...

class Evaluator:
    def compare(self, candidate, incumbent, holdout): ...

class ModelRouter:
    def resolve(self, user_id, cohort_id=None): ...
```

The executable protocol definitions live in `reflection_ai/ports.py`. Implementations
may use SQLite/Postgres, vector search, a temporal graph, local models, or hosted
services. Before multi-tenant use, current subject-only ports must change to carry
application, tenant, subject, policy version, and scoped lifecycle operations;
preserving an unsafe domain signature is not a compatibility goal.

## Future integration rule

Future adapters belong outside `reflection_ai` and translate an external contract
into core commands. Authentication, authorization, consent, tenant isolation,
deletion, prohibited inference, and external disclosure always fail closed.
Optional non-personal enrichment may degrade only when it cannot change access,
storage, output safety, or lifecycle guarantees. Adapters are versioned independently
and prohibited from adding host-specific fields to domain models. Archived
prototypes are reference material only.
