---
name: reflection-release
description: Apply the final mechanical release gate to a reviewed and tested Reflection AI change. Use only when implementation, independent review, QA, applicable trust/evaluation approvals, documentation, and rollback evidence are complete.
---

# Reflection Release

Read `AGENTS.md`, `.ai/TEAM.md`, `.ai/HANDOFF.md`, the diff, test evidence,
review findings, applicable gate reports, docs, migrations, and rollback notes.
Treat the shared invariant in `.ai/TEAM.md` as release-blocking.

1. Confirm scope matches the accepted contract and all blocking findings closed.
2. Re-run `pytest` and `ruff check .`; verify migrations and operational checks.
3. Require consent/isolation/deletion coverage for affected flows.
4. For any extractor, retriever, dataset, model, or routing change, require
   candidate-versus-incumbent evaluation, safety/general-capability evidence,
   approval, and an identified tested rollback target.
5. Return a signed checklist, release decision, known limitations, and rollback.

Do not decide product scope during release. Do not push, publish, deploy, train,
or promote without explicit user authority. Data availability is never release
authority; a failed or missing gate blocks release.
