# Changelog

## Unreleased

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
