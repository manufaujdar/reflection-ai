---
name: reflection-document
description: Update Reflection AI human, architecture, API, operational, research, and rollback documentation to match verified behavior. Use after behavioral, interface, deployment, or workflow changes and before release.
---

# Reflection Documentation

Read `AGENTS.md`, `.ai/TEAM.md`, `.ai/HANDOFF.md`, the verified diff, tests, and
existing documentation. Treat the shared invariant in `.ai/TEAM.md` as
release-blocking.

1. Establish behavior from code and test evidence, not aspiration.
2. Update only affected human entrypoints, architecture, API, operations,
   migrations, limitations, provenance, and rollback guidance.
3. Preserve the distinction between implemented, experimental, and future work.
4. Never include real user data, raw interactions, secrets, or unsupported claims.
5. Check links/commands and return files changed plus evidence used.

Documentation may edit project documentation within assigned scope, but cannot
change runtime behavior to make prose true. Run `pytest` and `ruff check .` when
documentation touches executable examples or project validation.
