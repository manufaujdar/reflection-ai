---
name: reflection-build
description: Implement an accepted Reflection AI task slice with tests while preserving provider-neutral boundaries and personalization trust invariants. Use after the handoff contains approved scope, acceptance criteria, file ownership, and applicable trust-gate decisions.
---

# Reflection Build

Read `AGENTS.md`, `.ai/TEAM.md`, `.ai/HANDOFF.md`, architecture, personalization
core, and relevant tests before editing. Treat the shared invariant in
`.ai/TEAM.md` as release-blocking.

1. Confirm the active contract, owned files, non-goals, and rollback plan.
2. Implement the smallest complete slice; keep providers and infrastructure
   behind adapters and preserve evidence-to-deployment stage separation.
3. Add targeted tests. For affected flows include consent, cross-user isolation,
   deletion, provenance, evaluation, and rollback cases.
4. Run targeted tests, then `pytest` and `ruff check .`.
5. Return files changed, behavior, commands/results, risks, and next review gear.

Do not silently expand scope, edit another agent's owned files, use real user
data, or train/deploy merely because data exists. Stop for Coordinator review if
the contract or architecture must change.
