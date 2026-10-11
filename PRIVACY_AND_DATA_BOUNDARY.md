# Privacy and data boundary

Status: research alpha and local synthetic demonstration only. This file is a
technical privacy boundary, not a jurisdiction-specific privacy policy for a
deployed personalization service.

## Current distribution

The local demo is unauthenticated and intended for synthetic subjects only. It
uses local research storage and exposes create/event/delete behavior to make the
framework inspectable. It is not a tenant-secure service and must not receive
real conversations, profiles, identifiers, health data, credentials, private
databases, or raw interaction logs.

Optional memory backends, model providers, queues, databases, and telemetry may
send or retain data under their own terms when an integrator enables them. The
repository's Apache-2.0 license does not license those services, models,
datasets, outputs, or training data.

## Deployment responsibility

Before processing personal or sensitive data, an operator must implement and
review authentication, tenant and subject isolation, consent and lawful-basis
records, access/export/correction/deletion controls, retention and revocation,
encryption and key management, worker isolation, provider terms and regions,
incident response, and applicable contracts or institutional approvals. A
deployed service must publish its own privacy notice and terms of service with
the actual controller, contact, purposes, recipients, retention, rights, and
transfer information. This repository does not provide those notices.

## Legal and compliance boundary

The Apache-2.0 `LICENSE` governs the source code. It is not a consent record,
privacy policy, security certification, HIPAA/DPDP/GDPR compliance statement,
or authorization to train on user data. See `COMPLIANCE_AND_DEPLOYMENT.md`,
`SECURITY.md`, `PROVENANCE.md`, and `VALIDATION_PROTOCOL.md`.

Reviewed: 2026-08-14.
