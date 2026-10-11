# Experimental personalization SLM

The optional `reflection_ai.slm` package turns the supplied educational GPT example into a safer,
adapter-oriented research component. It is deliberately not the live chatbot provider. Installing
it, preparing data, or producing an artifact never authorizes promotion or routing.

```bash
pip install -e '.[dev,slm]'
pytest tests/test_slm.py
```

## Assessment of the supplied architecture

### Advantages

- A decoder-only transformer is transparent, compact, locally runnable, and easy to instrument.
- Causal self-attention is a valid foundation for next-token generation.
- A small model can support offline experiments, deterministic tests, distillation, and narrow
  preference tasks without sending data to a hosted provider.
- Owning the architecture makes checkpoint, deletion, provenance, and adapter boundaries explicit.

### Disadvantages and risks

- Training a useful language model from scratch needs far more diverse data and compute than one
  person's conversations can safely provide. A tiny personal dataset mainly causes memorization.
- The supplied loss compares each token with itself when callers pass `targets=input_tokens`; causal
  language modeling must predict the next token using shifted labels.
- It stores a device string inside the model, has no padding mask, repeats attention modules per head,
  lacks weight tying and artifact provenance, and mutates sampling logits in place.
- It has no tokenizer contract, EOS handling, deterministic generation option, adapter isolation,
  evaluation, incumbent comparison, promotion, or rollback.
- Updating full model weights continuously creates poisoning, catastrophic-forgetting, privacy,
  deletion, latency, and per-user storage problems. Model output can reinforce its own mistakes.

## Reflection AI enhancements

`SLMConfig` validates architecture and produces a stable configuration fingerprint. `ByteTokenizer`
provides a dependency-free UTF-8 contract for reproducible experiments; production checkpoints must
use their original tokenizer.

`ReflectionSLM` adds:

- combined multi-head QKV projections and an explicit causal/padding mask;
- pre-normalized residual blocks, GELU feed-forward layers, dropout, and tied token/output weights;
- internally shifted causal loss with an ignore index for prompt and padding tokens;
- device-agnostic tensors and validated greedy, temperature, top-k, nucleus, repetition-penalty, EOS,
  and seeded sampling controls;
- a zero-initialized low-rank personalization adapter in each block;
- a runtime personalization-strength control for base-versus-personalized evaluation and gradual rollout;
- a freeze operation that makes only adapters trainable and transactionally rejects incomplete,
  malformed, or base-weight-containing adapter artifacts.

`ReferenceSLMTrainingBackend` implements the existing `TrainingBackend` protocol for local research.
It requires an existing local base checkpoint, a caller-supplied opaque artifact scope, redacted JSONL
examples, and exports only adapter weights plus the base identifier, dataset hash, configuration
fingerprint, and metrics. It cannot promote itself. The existing `GatedTrainingPipeline` still checks
both consents and minimum data, evaluates against the incumbent, registers the candidate, and promotes
only a passing result with rollback preserved.

`save_base_checkpoint` creates the canonical, versioned base envelope with a model identifier,
configuration fingerprint, restrictive file permissions, and a checkpoint hash. It writes atomically
and refuses overwrite. The trainer rejects unversioned or fingerprint-mismatched base checkpoints.

`PersonalizationModelSystem` is the missing orchestration bridge between a persisted `TrainingRun`
and the gated pipeline. It verifies subject ownership, dataset state, hashes, holdout availability,
and both consent values before delegating to the trainer/evaluator/registry sequence. It is not called
from the chat request path.

## Data saving and training status

The data-saving system exists. SQLAlchemy stores subjects, consent, chat sessions, messages, events,
evidence, typed memory, style profiles, traces, and training-run metadata in SQLite by default. The
new `LocalArtifactStore` saves redacted train/holdout JSONL under a hashed subject scope with restrictive
file permissions, SHA-256 hashes, and a manifest. Full subject deletion removes that scoped directory.
Production deployments still need encrypted managed Postgres/object storage and authenticated tenant
repositories.

The training system also exists as composable layers: dataset preparation, `TrainingBackend`,
`GatedTrainingPipeline`, evaluator, registry, promotion, and rollback. The reference adapter trainer
can execute locally when the `slm` extra and a valid base checkpoint are supplied. What is intentionally
not enabled is automatic scheduling or live routing: a durable queue, real benchmark evaluator,
persistent registry, approved pretrained base checkpoint/tokenizer, and independent release approval
are still required.

## Recommended product strategy

Use retrieval, explicit memory, and observable style guidance as the default immediate loop. Train a
small reranker next. Prefer a pretrained SLM plus cohort or task adapters when evaluation demonstrates
a gain. Consider a per-user adapter only with sufficient diverse, positively rated, consented examples
and only if it beats retrieval-only personalization on chronological holdout, safety, privacy leakage,
general capability, latency, and deletion tests.

The reference byte-level SLM is suitable for architecture tests and controlled experiments, not a
claim that training from scratch will produce a capable assistant.
