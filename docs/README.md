# Reflection AI documentation

Recommended reading order:

1. [`../README.md`](../README.md) — local loop, quick start, and explicit limits.
2. [`architecture.md`](architecture.md), [`personalization-core.md`](personalization-core.md),
   and [`authentication-tenant-contract.md`](authentication-tenant-contract.md) —
   system and privacy/security contracts.
3. [`adaptive-chatbot.md`](adaptive-chatbot.md), [`engine-building-blocks.md`](engine-building-blocks.md),
   and [`implementation-roadmap.md`](implementation-roadmap.md) — product and engineering scope.
4. [`../PRIVACY_AND_DATA_BOUNDARY.md`](../PRIVACY_AND_DATA_BOUNDARY.md),
   [`../PROVENANCE.md`](../PROVENANCE.md), and [`../THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md)
   — data, provenance, and external rights.

## Release boundary

The local loop is an alpha research framework, not a production personal-data
service. Authentication, tenant isolation, encryption, durable deletion,
retention controls, evaluation promotion, rollback, and operational incident
handling remain release gates. The Apache-2.0 license covers repository code;
user data, model weights, datasets, providers, and hosted services retain their
own terms.
