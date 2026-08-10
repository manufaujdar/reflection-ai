---
name: reflection-security
description: Perform a release-blocking security review of Reflection AI trust boundaries. Use for authentication, tenant authorization, encryption, secrets, external services, uploads, queues, callbacks, deployment, or changes that alter data access or execution boundaries.
---

# Reflection Security

Read `AGENTS.md`, `.ai/TEAM.md`, `.ai/HANDOFF.md`, architecture, configuration,
affected code, deployment files, and tests. Treat the shared invariant in
`.ai/TEAM.md` as release-blocking.

1. Identify assets, actors, entry points, trust boundaries, and attacker abilities.
2. Trace identity and tenant authorization on every affected read, write, export,
   deletion, background job, adapter, and artifact operation.
3. Check secrets, injection, deserialization, SSRF, path/data access, replay,
   idempotency, encryption, logging, failure recovery, and least privilege.
4. Require reproducible abuse cases and isolation/deletion tests for findings.
5. Return severity-ranked findings, mitigations, residual risk, and gate result.

Remain report-only and do not fix or deploy. Security approval does not replace
Privacy, Evaluation, QA, or explicit release authority.
