# Documentation index

Reflection AI is a consent-aware personalization and memory research
framework. It separates immediate evidence-backed personalization from slower,
evaluated model training. The local starter is not a production multi-tenant
service.

## Authoritative documents

- README.md: learning loop, quick start, project map, and production gaps.
- docs/architecture.md: core boundaries and extension points.
- docs/personalization-core.md and docs/engine-building-blocks.md: implemented invariants and baselines.
- docs/authentication-tenant-contract.md: proposed Privacy/Security contract; not implemented behavior.
- docs/open-source-landscape.md and docs/implementation-roadmap.md: research and phased work.
- docs/agent-team.md, AGENTS.md, .ai/, and .agents/skills/: delivery controls.
- docs/technical-overview.md: code, technology, lifecycle, and validation baseline.

## Initial documentation set

| Area | Status |
| --- | --- |
| Product/research scope | Present |
| Architecture and data lifecycle | Present |
| Codebase and extension points | Added |
| Technology and local operations | Added |
| Auth/tenant/privacy contract | Proposed, not implemented |
| Security and deletion boundary | Present as contract/research gate |
| Tests and release workflow | Present |
| License and provenance | Human follow-up; no GitHub license metadata |

Use Mem0, LangMem, Letta, Hindsight, and OpenTelemetry as comparison points.
Keep evidence and policy canonical; vector/graph indexes and model adapters
remain replaceable.

