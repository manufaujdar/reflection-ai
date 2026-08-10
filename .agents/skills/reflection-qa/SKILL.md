---
name: reflection-qa
description: Independently verify a Reflection AI change against its handoff contract, regression suite, and trust-invariant scenarios. Use after code review or for QA-only audits; report failures and ship readiness without fixing unless a separate fix task is explicitly assigned.
---

# Reflection QA

Read `AGENTS.md`, `.ai/TEAM.md`, `.ai/HANDOFF.md`, acceptance criteria, changed
files, and relevant tests. Treat the shared invariant in `.ai/TEAM.md` as
release-blocking.

1. Derive a risk-based matrix from the diff and active task contract.
2. Run targeted tests, `pytest`, and `ruff check .`.
3. Exercise affected consent-denied, cross-user isolation, deletion/purge,
   provenance, inferred-memory gate, retention, failed evaluation, and rollback
   paths; mark non-applicable scenarios with reasons.
4. Record commands, environment, observed results, gaps, and reproduction steps.
5. Return pass/fail per acceptance criterion and a ship-readiness decision.

Remain report-only by default and do not edit files. A QA-fix request is a new
Builder assignment followed by fresh independent review and QA.
