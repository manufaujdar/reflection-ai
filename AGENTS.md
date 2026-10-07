# Reflection AI agent guide

Read `START_HERE.txt`, `.ai/CONTEXT.md`, `.ai/MEMORY.md`, `README.md`, `docs/architecture.md`, `docs/personalization-core.md`, and relevant tests before substantial changes.

- Consent, per-user isolation, deletion, provenance, auditability, and rollback are invariants.
- Treat explicit user statements and corrections as evidence; inferred memories require gated review and must carry confidence and provenance.
- Never infer or store sensitive traits, diagnoses, protected characteristics, emotions, or unrelated private facts.
- Keep evidence, proposals, typed memory, retrieval, training data, evaluation, and deployment as separate stages.
- Do not train or deploy a personalized model merely because data exists; require evaluation against the current version and preserve rollback.
- Keep core behavior provider-agnostic and offline-testable. External memory/model systems belong behind adapters.
- Never commit real user data, database files, credentials, or unredacted interaction logs.

Validate Python changes with `pytest` and `ruff check .`; include consent, isolation, and deletion tests for affected flows.

Use `.ai/HANDOFF.md` only for active project work. `.ai/MEMORY.md` stores project decisions, never actual personalized user memories or interaction content.

## Startup team

Read `.ai/TEAM.md` before multi-role or idea-to-release work. Use its explicit
gears and keep the task contract in `.ai/HANDOFF.md`; consent, isolation,
deletion, evaluation, and rollback invariants remain authoritative.

## Shared AI-agent resources

When a task needs a shared role or resource, read [MASTER_AI_AGENTS.md](MASTER_AI_AGENTS.md).
Select only the relevant definition. Existing project roles, scoped instructions,
data boundaries, source-of-truth records, and release gates retain authority.
