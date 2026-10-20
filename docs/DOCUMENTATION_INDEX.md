# Documentation index

Reflection AI separates immediate evidence-backed personalization from slower,
evaluated model training. The local starter remains an alpha research framework;
an accepted contract does not establish implemented production authentication.

## Find the right document

| Task | Read |
| --- | --- |
| Install and exercise the local loop | [Root README](../README.md) and [reading order](README.md) |
| Understand code and extension points | [Architecture](architecture.md), [technical overview](technical-overview.md) and [engine building blocks](engine-building-blocks.md) |
| Change evidence, memory or deletion | [Personalization core](personalization-core.md) and [validation protocol](../VALIDATION_PROTOCOL.md) |
| Change chat or optional model experiments | [Adaptive chatbot](adaptive-chatbot.md) and [reference SLM](reference-slm.md) |
| Plan authentication and tenant isolation | [Accepted identity contract](authentication-tenant-contract.md); implementation remains pending |
| Plan future work or compare approaches | [Implementation roadmap](implementation-roadmap.md) and [open-source landscape](open-source-landscape.md) |
| Contribute and run checks | [Contributing](../CONTRIBUTING.md), [validation commands](../Makefile) and [tooling](../TOOLING.md) |
| Check licensing, provenance or data limits | [License](../LICENSE), [third-party notices](../THIRD_PARTY_NOTICES.md), [provenance](../PROVENANCE.md) and [privacy boundary](../PRIVACY_AND_DATA_BOUNDARY.md) |
| Resume agent work | [Agent guide](../AGENTS.md), [delivery team](agent-team.md) and [active handoff](../.ai/HANDOFF.md) |

## File placement

| Location | Purpose |
| --- | --- |
| `src/reflection_ai/` | Runtime packages, adapters and bundled frontend |
| `tests/` | Synthetic behavior and trust-invariant fixtures |
| `docs/` | Maintained explanations, contracts and plans |
| `research/` | Reviewed external-system research with provenance |
| `tools/`, `scripts/` | Repository audits, checks and maintenance commands |
| `.ai/`, `.agents/` | Project continuity and scoped delivery roles |
| `archive/` | Retained inactive work; no runtime authority |
| `artifacts/` | Generated local output; never a place for real user data |

Keep implementation evidence in the active handoff and avoid duplicating the
roadmap in new task lists. Preserve generated audit indexes and canonical paths.
Apache-2.0 covers repository source; external data, weights and services retain
their own terms and review requirements.
