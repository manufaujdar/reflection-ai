---
name: reflection-review
description: Independently review Reflection AI diffs for correctness, regressions, unsafe lifecycle shortcuts, and production failure modes. Use after implementation or fixes and before QA; report actionable findings without modifying files.
---

# Reflection Review

Read `AGENTS.md`, `.ai/TEAM.md`, `.ai/HANDOFF.md`, the complete diff, affected
architecture, and relevant tests. Treat the shared invariant in `.ai/TEAM.md` as
release-blocking.

1. Verify the change satisfies the contract and does not broaden scope.
2. Trace consent, ownership, deletion, provenance, retention, temporal validity,
   audit, evaluation, and rollback paths end to end.
3. Check authorization, cross-user leakage, idempotency, concurrency, failure
   recovery, prompt injection, poisoning, adapter leakage, and compatibility.
4. Check tests for meaningful failure detection, not only happy-path coverage.
5. Report only reproducible findings with severity, file/line, impact, evidence,
   and required fix; state explicitly when no findings remain.

Remain report-only: do not edit files or approve your own implementation. Do not
infer hidden intent without code evidence. Blocking findings return to Builder,
then re-enter review.
