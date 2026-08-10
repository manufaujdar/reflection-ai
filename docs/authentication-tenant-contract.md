# Authentication and tenant authorization contract

Status: **proposed contract for Privacy and Security review**. This document does
not describe implemented behavior. Every `/v1` route remains unsuitable for a
networked or multi-tenant deployment until this contract is accepted, built, and
verified.

## Outcome and smallest safe slice

An authenticated host can operate only on subjects owned by its verified
application and tenant. Identity, authorization, personalization consent, training
consent, and artifact promotion remain separate decisions. The first slice adds a
provider-neutral authenticator and tenant-scoped repository boundary; it does not
add login UI, model training, artifact promotion, or a production auth bypass.

An immutable request principal contains `actor_type`, opaque `actor_id`, one
allowlisted `role`, `application_id`, `tenant_id`, optional `bound_subject_id`,
explicit scopes, delegation issuer/audience/version, credential and token IDs,
issued/not-before/expiry times, and authenticator name. Authorization requires
`scope AND role allowlist AND subject binding`; credentials carrying a scope outside
their role template are rejected, not narrowed. Application, tenant, role, and
subject binding always come from verified claims. Body and path values may select a
resource only after they match that principal.

Only a separately governed identity broker, not a tenant runtime credential, may
issue `subject_delegate` assertions after subject authentication and an explicit
grant/revoke confirmation. The assertion is audience-bound to this API, subject-
bound, single-purpose, expires within five minutes, and carries a monotonic
delegation version checked against revocation state on every use. Broker trust and
tenant administration are separate. Privacy-operator forced revocation is limited
to a versioned, human-approved emergency/privacy policy identified in the audit;
it can never grant or issue subject delegation.

## Roles and scopes

There are no implicit permissions and no wildcard scope in the first slice.

| Role | Allowed scope set | Important exclusions |
|---|---|---|
| `runtime_service` | `subject:create`, `subject:read`, `context:read`, `event:write`, `generate:execute`, `evidence:write`, `memory:read`, `profile:refresh`, `retention:purge` | Cannot write memory directly, change consent or policy, delete a subject, prepare training data, or promote artifacts. |
| `subject_delegate` | `subject:read`, `policy:read`, `policy:write`, `consent:grant`, `consent:revoke`, `memory:read`, `memory:revoke`, `subject:delete`, `deletion:read` | Must carry subject-bound delegation issued by the independent identity broker; cannot act on another subject or start training. |
| `training_operator` | `subject:read`, `training:prepare` | Requires both stored consents after authorization; cannot change either consent or deploy an artifact. |
| `privacy_operator` | `subject:read`, `policy:read`, `consent:revoke`, `subject:delete`, `retention:purge`, `deletion:read` | May force revocation under recorded policy but can never grant consent; cannot create evidence, generate, train, or promote. |
| `memory_curator` | `subject:read`, `memory:write`, `memory:revoke` | Subject-bound and limited to reviewed explicit memory; cannot create inferred or prohibited memory, change consent, or train. |

Roles are credential templates only. Authorization checks the actual scope list,
tenant, application, and any subject binding. A tenant-wide credential is never a
subject delegate. No role in this slice can promote a model artifact.

## Deny-by-default route matrix

`/health` is public. `/v1/capabilities` is authenticated because it may later
expose deployment configuration. Every other route requires the scope below plus
an application/tenant-scoped subject lookup. Missing and foreign resources return
the same `404`; missing/invalid credentials return `401`; insufficient scope
returns `403` without revealing resource existence.

| Route/action | Required scope | Additional gate |
|---|---|---|
| `GET /v1/capabilities` | `subject:read` | None. |
| `POST /v1/users`, `POST /v1/subjects/resolve` | `subject:create` | Application/tenant fields are removed from public input or must exactly equal verified claims; initial consents are always false. Resolve never mutates consent or attributes. |
| `POST /v1/context` | `context:read` | Subject lookup uses principal application/tenant plus external ID; personalization consent and request safety flag gate memory use. |
| `GET /v1/users/{id}` | `subject:read` | Scoped subject lookup. |
| `GET /v1/users/{id}/policy` | `policy:read` | Scoped subject lookup. |
| `PATCH /v1/users/{id}/policy` | `policy:write` | Learning and default-retention fields only; mixed consent fields are rejected. Subject-bound delegation required. |
| `PUT /v1/users/{id}/consents/{personalization\|training}` | `consent:grant` for `false→true`; `consent:revoke` for `true→false` | Grant always requires subject-bound delegation. A privacy operator may revoke but never grant. Expected policy version, idempotency key, purpose, and payload hash are required. |
| `DELETE /v1/users/{id}` | `subject:delete` | Subject-bound delegation or privacy operator, idempotency key, purpose, complete cascade, and deletion receipt. |
| `POST /v1/users/{id}/events` | `event:write` | Personalization consent, learning switch, and prohibited-content/attribute check before storage. |
| `POST /v1/users/{id}/generate` | `generate:execute` | Prohibited-input check before retrieval/provider call and prohibited-output check before disclosure or event storage. |
| `POST /v1/users/{id}/profile/refresh` | `profile:refresh` | Personalization consent after authorization. |
| `POST /v1/users/{id}/training-runs` | `training:prepare` | Personalization and training consent after authorization; dataset path is tenant scoped. |
| `POST /v1/users/{id}/evidence` | `evidence:write` | Scoped subject, personalization consent, learning enabled, and prohibited-content check. |
| `POST /v1/users/{id}/memories` | `memory:write` | Subject-bound curator, reviewed explicit evidence, and prohibited-content check. |
| `GET /v1/users/{id}/memories` | `memory:read` | Scoped subject and personalization consent. |
| `DELETE /v1/users/{id}/memories/{memory_id}` | `memory:revoke` | Memory must belong to scoped subject; idempotent revocation. |
| `POST /v1/users/{id}/reflection/proposals` | `profile:refresh` | Scoped subject, consent, evidence ownership, and prohibited-content check. |
| `GET /v1/users/{id}/reflection/proposals` | `subject:read` | Scoped subject; results cannot include another subject. |
| `POST /v1/users/{id}/reflection/proposals/{proposal_id}/apply` | `memory:write` | Subject-bound curator; proposal ownership, evidence, and prohibited-content check. |
| `POST /v1/users/{id}/reflection/analyze` | `profile:refresh` | Scoped subject; prohibited-inference check before proposal creation. |
| `POST /v1/users/{id}/retention/purge` | `retention:purge` | Subject-scoped purge and receipt. |
| `GET /v1/deletions/{receipt_id}` | `deletion:read` | Receipt principal must match its application, tenant, and bound subject unless it is a same-tenant privacy operator. |

FastAPI documentation routes (`/openapi.json`, `/docs`, `/docs/oauth2-redirect`,
and `/redoc`) are disabled in production. Development documentation is loopback-
only. Unsupported methods and unknown `/v1` paths receive generic denials.

Unknown routes and actions are denied. Workers and adapters do not inherit the API
principal. The API-side queue authorization service is the sole worker-envelope
issuer; workers, brokers, adapters, and queue infrastructure cannot sign envelopes.
It signs a fresh envelope for every fenced execution attempt, including retries,
only after re-reading current policy, consent, delegation, cancellation, and key
epochs. Each attempt receives a new `jti`, incremented attempt number, and current
fencing token; an earlier attempt's envelope is never reused. A queued authorization
envelope contains actor/role, credential ID,
scopes, application, tenant, bound subject, operation, job and token IDs,
issued/not-before/expiry times, policy/consent/delegation/cancellation epochs,
attempt number, and a canonical payload hash. It is signed with a separately
rotated Ed25519 worker key. The signed member set is exactly the protected header
(`alg=EdDSA`, `typ=reflection-worker+jws`, `kid`) and every envelope member named
above plus `issuer`, `aud=reflection-worker`, and unique `jti`; both are encoded as
RFC 8785 canonical JSON and the detached signature is base64url without padding.
No unsigned member influences authorization. Envelopes have a maximum five-minute
lifetime. During an explicitly bounded rotation overlap, an old `kid` remains valid
for envelopes issued before issuance switched to the new key, until the earlier of
that envelope's expiry or the overlap deadline; the old key cannot sign new
envelopes after the switch and explicit revocation invalidates it immediately.
Worker trust maps each issuer/key to allowed queues, operations, applications and
tenants; key/revocation state is durable, overlapping rotation is supported, and
unknown/revoked/cache-unavailable keys fail closed. Queue state uses compare-and-set leases and attempt fencing;
each irreversible result is accepted once only for the current attempt. Cancellation
increments the epoch, and stale or replayed workers cannot commit.

## Explicit consent mutation

Subject resolution creates or finds identity only and is idempotent by
`(application_id, tenant_id, external_id)`; it never changes consent or arbitrary
attributes. Consent changes use the dedicated consent endpoint with:

- a subject-bound `subject_delegate` for grants or revocations; a
  `privacy_operator` may perform revocation only under recorded policy;
- an `Idempotency-Key` unique within application/tenant/subject/action;
- `purpose`, requested values, `expected_policy_version`, actor type and opaque actor ID;
- previous and new monotonic consent versions and server timestamp in a metadata-only audit;
- revocation taking effect before the response and invalidating queued work whose
  consent version is stale.

Personalization and training consent are mutated independently. Consent state,
version, provenance audit, idempotency key, and payload hash commit atomically in
one transaction with database uniqueness on `(application, tenant, subject, action,
idempotency_key)`. Repeating the same key and payload returns the original result;
reusing a key with another payload is `409`. Concurrent mutations compare-and-set
the expected version; only one commits, so a delayed grant cannot overwrite a newer
revocation. Policy PATCH requests containing consent fields or a mixture of fields
with different authority are rejected. Revocation is never converted to grant by
retry, subject resolution, import, migration, or rollback.

### Revocation effects

| Change | Required lifecycle effect |
|---|---|
| Learning disabled | Stop new evidence, events, proposals, profile refresh, indexing, dataset preparation, and training; approved retrieval may continue only while personalization consent remains. |
| Personalization consent revoked | Immediately block and quarantine all evidence, events, profiles, memories, proposals, indexes and caches; cancel work and purge active stores/adapters within 24 hours. Backup copies remain inaccessible and expire within the documented 30-day backup window. Re-grant starts empty at a new version and never reactivates quarantined data or stale work. |
| Training consent revoked | Cancel training/evaluation; immediately disable every subject-contributed candidate, rejected, promoted, superseded, rolled-back or cohort artifact; route to a verified-clean base; purge datasets, holdouts, evaluations, registry mappings and artifact versions within 24 hours, with inaccessible backups expiring within 30 days. |
| Memory revoked | Remove it from retrieval, indexes, caches, proposals and future datasets while retaining only privacy-approved provenance. |
| Subject deleted | Apply the complete cascade below; re-grant is impossible because the subject no longer exists. |

Every worker, provider, trainer, evaluator, registry, and external-memory operation
checks authorization, credential status, tombstone, policy version, and consent
immediately before external disclosure and before each write. Responses returning
after revocation are discarded and cannot create events, memories, datasets,
evaluations, or artifacts.

## Tenant-scoped data and jobs

One repository method must load a subject using application, tenant, and subject ID
in the same query. Downstream keys and paths begin with an opaque hash of
`application_id/tenant_id/subject_id`; raw external IDs are not file names or log
labels. The same scope is mandatory for SQL rows, queue messages, locks, vector and
graph namespaces, external-memory adapters, dataset and holdout files, caches,
registry mappings, evaluation records, and artifact routes. Every adapter must
provide scoped `enumerate`, `cancel`, `revoke/delete`, `purge`, `status`, and
deletion-verification operations with a metadata-only receipt. An adapter that
cannot express all three boundaries, cancel running work, delete, or attest a
pending deletion is incompatible and fails closed for that lifecycle.

Queues expose scoped cancellation and purge for queued, running, completed, failed,
and dead-letter payloads, results, errors, and authorization envelopes. Workers
re-authorize the signed job envelope and current consent version before the first
read, before external disclosure, and before each irreversible write. Expired,
revoked, foreign-tenant, or unknown jobs fail closed and produce a metadata-only
audit event.

## Deletion cascade and receipt

Deletion first records a tombstone and blocks new work and subject resolution. Its
anti-resurrection key is an HMAC over the UTF-8 NFC-normalized, whitespace-trimmed
tuple of exact application ID, exact tenant ID, and identity-broker canonical
external ID, with length-prefixed fields. A separately rotated deletion key is
used; raw identity is not retained. Tombstones and their verification key versions
remain for the service lifetime. Re-enrollment requires a future, separately
approved subject-authenticated flow and is not available in this slice. Only a
subject-bound delegate or same-tenant privacy operator may read the receipt.

Deletion then cancels and purges queued, running, completed, failed, and dead-letter
job payloads, results, errors, and envelopes. It removes SQL evidence links,
proposals, memories, events, profiles, training runs, datasets/holdouts, external
memories, vector/graph indexes, caches, evaluation outputs, registry mappings, and
every subject-derived candidate, rejected, promoted, superseded, rolled-back, or
cohort artifact version. Routing falls back to a non-personalized base artifact or
a provenance-verified artifact with no contribution from the subject; otherwise
generation fails closed. Third-party processors must support contracted deletion
and attestation or cannot receive subject data. Backup expiry is tracked rather than
falsely reported as immediate physical erasure.

The response is a privacy-safe receipt containing opaque receipt ID, subject-scope
hash, request/idempotency IDs, actor type, reason code, start/completion timestamps,
per-store status and counts, outstanding backup expiry dates, rollback target ID,
and overall `logically_deleted`, `pending_physical_expiry`, or
`physically_deleted` state. `logically_deleted` means inaccessible in every active
system, not erased from backups. `physically_deleted` requires attestation from
every store and backup; each pending store and retry state remains explicit. The
receipt never contains external IDs, memory content, prompts, credentials, paths,
or deleted values. Retrying returns the same receipt or advances pending work; it
cannot recreate the subject. Receipts, tombstones, and minimal metadata-only audits
have explicit access and retention. Receipt detail expires after 90 days; the
minimal anti-resurrection tombstone remains for service lifetime and its key is not
destroyed while any tombstone references that version. No undefined audit subset
may be silently retained.

## Prohibited inference and storage

No role, consent state, sensitivity label, tenant setting, or administrator may
authorize inferring or storing sensitive traits, diagnoses, protected
characteristics, emotions, or unrelated private facts. A deterministic policy
boundary runs before evidence ingestion, extraction, proposal creation, direct
memory creation, proposal application, consolidation, profile refresh,
retrieval/indexing, dataset preparation, import/migration, queueing, and every
external-adapter write. Unknown classifications fail closed to review or rejection;
they are never silently relabeled `normal`.

Negative tests cover each prohibited category at every entry and derivation stage,
including euphemisms, arbitrary attributes, quoted third-party claims, model output,
imports, retries, and cross-tenant adapters. Rejection occurs before persistence,
indexing, provider calls, queueing, or audit content that repeats the prohibited
value; only a reason code and content hash may be recorded.

## Production configuration and credential lifecycle

The first production authenticator is a compact signed JWT carried only in the
`Authorization: Bearer` header and verified with pinned Ed25519 keys (`alg=EdDSA`;
algorithm substitution is rejected). Required claims are issuer, audience,
application, tenant, actor, allowlisted role, exact scopes, credential ID, unique
`jti`, `iat`, `nbf`, and `exp`, plus subject/delegation claims where required.
Ordinary tokens live at most 15 minutes; consent and deletion tokens are single-use
and live at most five minutes. Privileged `jti` values are atomically consumed with
their idempotent mutation. Credential and delegation revocation epochs are checked
from durable storage; cache failure fails closed.

Token class is derived only from the verified trust-registry entry for `(issuer,
kid)` plus the route/action; an untrusted claim cannot select a more permissive
class. Reusable access tokens are intentionally reusable until expiry/revocation; a repeat
read receives the same authorization decision and is not called an attack replay.
Every non-idempotent write additionally requires an idempotency key bound atomically
to issuer, credential ID, token ID, route/action, subject, and canonical payload
hash, so retry cannot duplicate side effects. Consent/deletion tokens and worker
envelopes are single-use. For an HTTP consent/deletion request, the sole operation
permitted before replay denial is a constant-scope idempotency-record lookup keyed
by the verified issuer, credential ID, `jti`, route/action, subject, and idempotency
key. If its stored canonical payload hash matches, return the stored result without
reauthorizing or mutating; a hash mismatch is a conflict. If no record exists, an
atomic consume-and-mutate transaction consumes `jti` and stores the result; an
already-consumed `jti` is denied. Worker envelopes have no HTTP retry exception:
any second `jti` use is denied before job or result lookup or mutation. Tests assert
these different outcomes by registry-derived token class; sender constraints are
not silently implied.

Production startup fails unless deployment mode is explicit, issuer/audience/EdDSA
and maximum lifetimes are pinned, active verification keys are present, revocation
storage is reachable, and default application/tenant fallbacks are disabled. The
backend does not trust public forwarded identity headers. If an ingress terminates
identity, it must use mutually authenticated TLS and a signed short-lived assertion,
strip inbound identity headers, and network policy must deny direct public paths.
Ingress identity, direct-path denial, spoofed-header, key-cache failure, and replay
are acceptance tests. A local development authenticator causes production startup
rejection.

The trust registry binds `(issuer, kid)` to allowed audiences, applications,
tenants, actor types, roles, maximum scopes, subject-delegation authority, token
lifetimes, and whether single-use is mandatory. Verification rejects any signed
claim outside that key's authority. Only identity-broker keys explicitly marked for
subject delegation may mint `subject_delegate`; runtime or tenant-administrator keys
cannot. Negative tests cover cross-issuer, cross-tenant/application, role escalation,
scope escalation, delegation forgery, and a valid signature from the wrong key.

Credential IDs support overlapping rotation windows: add new, verify both, switch
issuance, then revoke old. Unknown algorithms, missing expiry, clock-skew violations,
revoked IDs, malformed claims, and stale subject delegations fail closed. Secrets
are never returned, logged, stored in database rows, or placed in tests. Security
audits contain request ID, credential ID, actor type, scope decision, route template,
tenant/application hashes, result, reason code, and timestamp—never raw content.

Rollback restores the previous code and key set but cannot restore anonymous access,
default tenancy, revoked consent, deleted subjects, or expired credentials.

## Migration, recovery, and rollback

An explicit migration framework replaces `create_all`. A staged forward migration
adds tenant-aware identities, policy versions, provenance audits, idempotency rows,
credential/delegation revocations, job fencing, tombstones, deletion receipts and
scoped downstream mappings before auth enforcement is enabled. Preflight rejects
duplicate identities, uniqueness conflicts, missing mappings, partial schema
versions and `generic/default` rows; ambiguous rows are quarantined, never assigned.
Each stage is restart-safe and records completion without private content.

Tombstone creation, deletion state, and receipt creation commit atomically before
cleanup. A durable worker resumes pending deletion after crash. Restored backups
reapply tombstones and revocation epochs before any data becomes readable.
Production startup checks a minimum security-schema version. Rollback is permitted
only to an auth-capable release that understands that schema, behind independently
enforced authenticated ingress; rollback to the current anonymous release is
mechanically refused.

## Abuse and failure matrix

The implementation generates a parameterized matrix for **every route listed
above**, including documentation, unknown `/v1` paths and unsupported methods,
against anonymous, malformed, expired/not-yet-valid and revoked tokens; permitted
reusable-token retries, idempotent write retries, forbidden single-use-token replay;
wrong role/scope/application/tenant/subject; stale delegation/policy/consent/job
epochs; and denial-before-side-effect. The cases below add lifecycle-specific rows.

| Case | Required observable result | Side-effect assertion |
|---|---|---|
| Anonymous or invalid credential on `/v1/*` | Uniform `401` | No DB/provider/queue/artifact call. |
| Valid credential, missing scope | `403` | No resource lookup that reveals existence and no mutation. |
| Wrong tenant/application/subject | Uniform `404` after scoped lookup | No unscoped fallback query. |
| Body tenant differs from principal | `403` or validation rejection | No subject create/resolve. |
| Consent forged through resolve/import | Request rejected or consent fields ignored as contract specifies | Consent version unchanged. |
| Idempotency retry | Original result | Exactly one consent/deletion mutation. |
| Same key, different payload | `409` | Original state unchanged. |
| Stale policy version or concurrent grant/revoke | `409`; newer version wins | Atomic state/audit/idempotency; delayed grant cannot overwrite revocation. |
| Mixed consent and learning/retention PATCH | Validation rejection | No partial mutation. |
| Consent revoked before worker executes | Job rejected as stale | No dataset, memory, provider, or artifact write. |
| Consent revoked during provider/trainer/adapter call | Result discarded and cleanup queued | No post-revocation event, dataset, evaluation, disclosure, or artifact write. |
| Deletion during running job | Tombstone blocks writes; receipt is `pending` until cancellation/cleanup | Subject cannot be resolved or recreated by retry. |
| Resolve deleted external ID with a new request key | Tombstoned response | HMAC anti-resurrection lookup blocks recreation. |
| Adapter deletion unsupported or partially fails | Receipt names pending store; lifecycle fails closed | No false completion; retry is idempotent. |
| Foreign tenant reads receipt or purges adapter namespace | Uniform denial | No receipt disclosure or cross-tenant deletion. |
| Foreign memory/proposal ID under owned subject | Uniform `404` | No cross-subject read or write. |
| Prohibited trait at ingestion, inference, apply, import, job, or adapter boundary | Rejected with reason code | No persistence, indexing, provider call, queue, dataset, or artifact. |
| Migration finds `generic/default` rows | Quarantine and operator report | Never silently assign a production tenant. |
| Authenticator/ingress/key unavailable | Startup or request fails closed | No anonymous fallback. |
| Rollback to older release | Deployment refused unless auth invariant remains | No consent resurrection or reopened access. |

## Acceptance and validation

The Builder may start only after Privacy and Security accept this contract. The
implementation must add unit, API, repository, worker, migration, and adapter
contract tests for every matrix row; prove denial happens before side effects with
spies/fakes; run existing consent/isolation/deletion tests; and pass `pytest`, Ruff,
and the team validator. A production-readiness claim additionally requires an
external deployment review, encryption/key management, operational recovery tests,
and explicit release authority.
