# Governance

Reflection AI is currently maintainer-led. Decisions prioritize user agency,
consent, tenant isolation, deletion, evidence provenance, evaluation, and
rollback over feature velocity or benchmark claims.

## Decision process

Small, reversible changes may be accepted after tests and review. Changes to
identity, authorization, consent, sensitive-data handling, retention, training,
model promotion, or deployment require explicit privacy and security review and
must preserve the invariants in `AGENTS.md`.

Material architecture decisions should document:

- the user or research problem;
- considered alternatives and why they were rejected;
- affected evidence, memory, training, and deployment boundaries;
- new failure modes and abuse cases;
- validation evidence and rollback procedure;
- third-party code, service, model, and dataset provenance.

## Releases

Releases require a clean repository audit, passing tests and lint, an updated
changelog, reviewed dependency/provenance changes, and no unresolved
release-blocking privacy or security finding. A public release does not imply
production readiness, privacy compliance, or suitability for high-impact use.

## Contributions and ownership

Contributions are accepted under Apache-2.0 unless explicitly stated otherwise.
The maintainer may request narrower changes, additional tests, or independent
review. Governance may evolve as maintainers and reviewers join; changes to this
document should be discussed publicly unless doing so would disclose a security
or privacy issue.
