# Compliance and deployment boundary

Reflection AI is an alpha research framework, not a production identity,
authorization, privacy-compliance, clinical, employment, financial, or other
high-impact decision system. The local console is deliberately synthetic and
unauthenticated. Do not expose it to a network or enter real personal data.

## Current boundary

The repository demonstrates consent-aware evidence capture, typed and
versioned memory, policy filtering, retention, deletion, evaluation gates, and
rollback contracts. These controls are research prototypes. They do not by
themselves establish legal compliance, security certification, or safe
deployment.

## Required before real-user deployment

- Implement authenticated principals and fail-closed tenant authorization as
  specified in `docs/authentication-tenant-contract.md`.
- Encrypt data in transit and at rest with managed keys and rotation.
- Separate identity, raw evidence, derived memory, datasets, artifacts, audit
  logs, and backups with least-privilege access.
- Complete a data inventory, purpose/consent analysis, retention schedule,
  deletion verification, incident response plan, and applicable DPIA/PIA.
- Add durable queues, transactional outbox/idempotency, rate limiting, abuse
  controls, monitoring, backup/restore, and disaster recovery.
- Validate extraction, retrieval, temporal correctness, prompt-injection
  resistance, privacy leakage, subgroup behavior, safety regression, and model
  rollback on representative approved data.
- Review every external model, memory provider, dataset, weight, and hosted
  service for license, privacy, residency, logging, retention, and subprocessors.
- Obtain independent legal, privacy, security, human-factors, and domain review
  appropriate to the intended use and jurisdiction.

## Prohibited claims

Do not describe this code as self-improving intelligence, a faithful digital
twin, privacy-compliant, secure, unbiased, clinically safe, or production-ready
without scoped evidence. Personalization signals are revisable hypotheses, not
ground truth about a person.

## High-impact and sensitive contexts

Personalized output must never silently override system or safety policy. In
healthcare, employment, education, credit, insurance, legal, public-sector, or
other high-impact settings, keep personalization out of decision criteria until
the intended use, lawful basis, human oversight, validation, appeal, and audit
requirements have been independently approved.
