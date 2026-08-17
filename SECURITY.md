# Security and privacy policy

Reflection AI is an alpha framework and is not production-ready for personal
or health data. Do not commit real conversations, identifiers, credentials,
private databases, or raw interaction logs.

Report suspected vulnerabilities privately to the project maintainer with a
synthetic reproduction, preferably through GitHub's private vulnerability
reporting/security-advisory channel when available. Do not open a public issue
containing exploit details, credentials, personal data, private prompts, or
provider responses.

Known production gaps include authentication and tenant authorization,
encryption/key management, durable queues and registries, rate limiting,
verified backup deletion, incident response, and deployment monitoring. The
presence of retention and rollback contracts does not mean those operations are
production-hardened. See `COMPLIANCE_AND_DEPLOYMENT.md`, `docs/architecture.md`,
and the implementation roadmap.
