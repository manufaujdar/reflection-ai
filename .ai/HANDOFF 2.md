# Current handoff

## Status

- Task: establish the AI delivery team and start the next production-hardening slice
- Team scaffold: complete
- Current gear: Planning handoff after Security and Privacy gates
- Gate result: Privacy accepted revision three and Security accepted revision four
  for Builder. The contract gate is complete; authentication code is not yet
  implemented and no release is authorized.
- Coordinator: lead agent

## Completed outcome

The repository now has an explicit-gear delivery team, fourteen repository-local
Codex skills, a human workflow guide, a portable validator, and regression tests.
Planning, implementation, independent review, QA, and release remain separate.
Privacy, Security, and Evaluation are conditional release-blocking gates.

## Evidence log

- `python3 scripts/validate_team.py`: passed for all 14 skills and roster.
- Standard Codex `quick_validate.py`: all 14 skills passed using a temporary
  environment with PyYAML. The upstream validator's PyYAML dependency is not a
  project runtime requirement; the stdlib repository validator is the portable gate.
- `pytest -q`: 42 passed in the current Python 3.13 environment (including
  5 team-structure tests); one upstream Starlette TestClient deprecation warning.
- `ruff check .`: passed.
- A clearly labeled synthetic local browser console exercises create/event/delete;
  it does not weaken or satisfy the production authentication gate.
- `git diff --check`: passed.
- Independent QA found and resolved an Engineer UI prompt/authority mismatch,
  strict UI metadata parsing, and negative validator fixtures.
- The existing workspace `.venv` initially stalled while importing pytest modules;
  a clean temporary environment produced the authoritative full-suite result.

## Active next objective

Add provider-neutral, fail-closed authentication and tenant-scoped authorization
before any networked or multi-tenant release.

User outcome: an authenticated host application can access only subjects owned by
its verified application and tenant, while consent, learning, deletion, memory,
training, evaluation, and rollback gates remain independent.

## Accepted scope direction

- Keep `/health` public and authenticate every `/v1` operation.
- Introduce an immutable request principal and a provider-neutral authenticator port.
- Derive application and tenant from verified credentials, never trusted JSON.
- Replace unscoped `db.get(User, user_id)` with a single SQL query scoped by
  principal application, tenant, and subject ID.
- Return uniform 404 responses for missing and foreign resources.
- Authorize before database mutation, retrieval, provider calls, queueing, or
  artifact writes; never log credentials or private content.
- Preserve consent and training consent as separate gates after authentication.
- Support rotation and a rollback that never reopens anonymous production access.

## Accepted contract requirements

Privacy and Security accepted the following requirements as the minimum Builder
contract. The earlier static hashed service-token proposal is superseded:

1. Define a deny-by-default route/action/role matrix. A tenant-wide credential
   cannot implicitly grant training, deletion, or consent-management authority.
2. Remove consent mutation as a side effect of subject resolution. Define an
   explicit subject-authorized consent operation with actor/purpose provenance,
   idempotency, and revocation behavior.
3. Scope repository/service loaders and downstream jobs, external memory
   namespaces, datasets, indexes, and registry mappings by application and tenant,
   not only the subject UUID.
4. Make deletion cover queued jobs, dataset/holdout files, external memories,
   indexes, caches, and active artifacts; define a privacy-safe deletion receipt.
5. Define production fail-closed configuration, credential verification/rotation,
   trusted ingress, non-sensitive security audit events, and startup rejection of
   anonymous/default-tenant production mode.
6. Add a route-by-route abuse matrix for anonymous, wrong-tenant, wrong-application,
   insufficient-scope, consent-forgery, denial-before-side-effect, deletion, worker,
   migration, and rollback behavior.

## Lifecycle impact

- Directly affected: identity, authorization, consent provenance, audit, and tenant isolation boundary.
- Transitively gated: evidence, proposals, memory, retrieval/context, retention,
  deletion, jobs, datasets, training, artifacts, routing, export, and external adapters.
- Unchanged invariant: authentication never implies personalization or training consent.
- No real user data, credentials, database files, or raw logs may enter Git or tests.

## Non-goals for the first Builder slice

Do not implement login UI or passwords, silently assign existing `generic/default`
rows, add a production auth bypass, change personalization semantics, train or
promote models, deploy, publish, push, or make production-readiness claims.

## Exact next action

Builder may now implement the smallest provider-neutral principal, deny-by-default
route/action policy, and tenant-scoped repository boundary specified in
`docs/authentication-tenant-contract.md`. Use synthetic fixtures only. Then hand off
to independent Security, Privacy, Reviewer, QA, Documentation, and Release gates;
none of those later gates or the human release decision is pre-approved.
