---
name: reflection-privacy
description: Perform a release-blocking privacy and personalization-lifecycle review for Reflection AI. Use for changes touching evidence, memory, retrieval, retention, user policy, training data, model personalization, exports, deletion, external data, or user-visible privacy claims.
---

# Reflection Privacy

Read `AGENTS.md`, `.ai/TEAM.md`, `.ai/HANDOFF.md`, affected data models, services,
APIs, tests, and policies. Treat the shared invariant in `.ai/TEAM.md` as
release-blocking.

1. Trace data from collection through storage, derivation, retrieval, training,
   evaluation, deployment, export, expiry, revocation, and deletion.
2. Verify purpose-specific consent, learning/training separation, per-user/tenant
   isolation, provenance, audit, retention, and complete deletion.
3. Reject sensitive-trait, diagnosis, protected-characteristic, emotion, or
   unrelated private-fact inference or storage.
4. Check memory as untrusted data, injection/poisoning controls, redaction, and
   correction/supersession behavior.
5. Return blocking/non-blocking findings, evidence, missing tests, and gate result.

Remain report-only and do not remediate findings. Privacy approval cannot grant
training, promotion, deployment, or publication authority.
