---
name: reflection-evaluate
description: Design or audit reproducible Reflection AI evaluations and make evidence-based promotion recommendations. Use for extractor, consolidation, retrieval, reranking, dataset, trainer, model artifact, registry, routing, canary, or rollback changes.
---

# Reflection Evaluate

Read `AGENTS.md`, `.ai/TEAM.md`, `.ai/HANDOFF.md`, evaluation and training code,
data policy, registry behavior, and relevant tests. Treat the shared invariant in
`.ai/TEAM.md` as release-blocking.

1. Define the candidate, incumbent, versioned datasets, chronological split,
   metrics, thresholds, guardrails, and reproducible environment.
2. Measure personalization, temporal correctness, correction rate, retrieval
   quality, safety, privacy leakage, general capability, latency, and cost as relevant.
3. Require consented, provenance-linked, redacted data and isolate subjects.
4. Reject promotion on missing evidence, leakage, safety/general regression, or
   absent rollback target; record limitations and uncertainty.
5. Return an evaluation report and promote/reject recommendation, never self-promote.

Remain report-only. Do not train because data exists, deploy a candidate, alter
thresholds after seeing results, or expose real evaluation/user content.
