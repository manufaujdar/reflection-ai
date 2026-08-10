# Reflection AI project context

## Mission

Build a provider-agnostic personalization framework that turns consented evidence and corrections into inspectable memory, bounded retrieval, and gated training/evaluation workflows.

## Source map

- Human entry: `START_HERE.txt`
- Architecture and policies: `docs/`
- Implementation: `src/reflection_ai/`
- Verification: `tests/`
- External-system research: `research/`
- Inactive retained work: `archive/`
- Generated local artifacts: `artifacts/`

## Invariants

Consent, user isolation, provenance, deletion, audit, and rollback are mandatory. Explicit evidence and inference are different. Training/deployment requires evaluation. Real user data never belongs in Git.
