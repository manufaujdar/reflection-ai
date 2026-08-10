---
name: reflection-plan
description: Define the user outcome, smallest safe scope, non-goals, acceptance criteria, success metrics, and trust guardrails for Reflection AI work. Use for new features, substantial changes, ambiguous requests, or idea-to-release planning before architecture or implementation.
---

# Reflection Plan

Read `AGENTS.md`, `.ai/TEAM.md`, `.ai/HANDOFF.md`, `.ai/CONTEXT.md`,
`.ai/MEMORY.md`, the roadmap, and relevant product tests. Treat the shared invariant
in `.ai/TEAM.md` as release-blocking.

1. State the user job and evidence that the change is useful.
2. Choose the smallest complete safe loop; list non-goals and assumptions.
3. Mark affected lifecycle stages, consent scopes, tenant boundaries, deletion,
   provenance, evaluation, audit, and rollback requirements.
4. Write measurable acceptance criteria and guardrail metrics.
5. Identify required Research, Design, Privacy, Security, and Evaluation gears.
6. Return a structured contract update and exact next gear to the Coordinator.

Remain report-only. Do not edit code, authorize training, promote artifacts, or
deploy. Do not put real user data or interaction content in planning artifacts.
Exit only when scope and acceptance criteria are testable and unresolved choices
are explicit.
