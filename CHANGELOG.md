# Changelog

## Unreleased

- Added `PRIVACY_AND_DATA_BOUNDARY.md` to document the synthetic-only research boundary and distinguish the Apache-2.0 source license from deployment privacy obligations.
- Added a responsive adaptive chatbot at `/chat` with consent-gated onboarding,
  persistent history, feedback/corrections, and a transparent personalization inspector.
- Added user-scoped chat/session/style/agent-run database layers and an explicit
  five-agent response harness with prompt hashing and explainable memory traces.
- Added low-risk running style learning, evidence-backed onboarding and correction
  memories, secret redaction, and deletion coverage across every chat layer.
- Connected positive chat ratings to the existing consent- and evaluation-gated
  training dataset loop; model weights are never updated inline.
- Added Apache-2.0 licensing, NOTICE and citation metadata.
- Added governance, conduct, provenance, compliance/deployment, validation,
  model-card and dataset-card guidance for public research collaboration.
- Added issue/PR templates, Dependabot configuration and stronger CI release checks.
- Added a deterministic local repository/UI review agent with automated tests.
- Rebuilt the synthetic browser console with maintainable semantic markup,
  visible focus, responsive layout, clearer action hierarchy and trust boundaries.
- Added an explicitly synthetic local browser console for create/event/delete API
  testing; it does not change the production authentication blocker.
- Added `/v1/capabilities` to make consent, deletion, evidence-linking, and production-readiness boundaries explicit.
- Added a Privacy- and Security-accepted, fail-closed authentication and tenant
  implementation contract. The contract is documentation only; the production
  principal, authorization and tenant-scoped repository boundary are not implemented.
- Prepared contributor, security, and CI guidance for public review.

## 0.2.0

- Added consent-aware evidence and memory services, provider-neutral adapters,
  deterministic local engine building blocks, API routes, and tests.
