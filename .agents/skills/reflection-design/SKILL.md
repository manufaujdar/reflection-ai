---
name: reflection-design
description: Design user-facing Reflection AI consent, memory inspection, correction, confidence/provenance explanation, export, deletion, opt-out, and failure experiences. Use for UI, API ergonomics, workflows, or copy that changes user understanding or control.
---

# Reflection Design

Read `AGENTS.md`, `.ai/TEAM.md`, `.ai/HANDOFF.md`, product context,
personalization core, and relevant interfaces/tests. Treat the shared invariant
in `.ai/TEAM.md` as release-blocking.

1. Map the user's mental model, decisions, risks, and recovery paths.
2. Design explicit consent and separate personalization/training controls.
3. Show provenance, confidence, review state, validity, correction, expiry,
   export, deletion, and audit consequences in plain language.
4. Include empty, loading, error, revoked, expired, conflict, permission, keyboard,
   screen-reader, responsive, and destructive-confirmation states.
5. Return flows, state inventory, copy, acceptance criteria, and open questions.

Remain report-only unless an explicit design-fix build is assigned. Do not use
dark patterns, infer sensitive traits, hide deletion effects, or use real user data.
