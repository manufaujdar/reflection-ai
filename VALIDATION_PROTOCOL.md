# Validation protocol

This protocol defines the minimum evidence needed before a personalization
component can move from local experiment to candidate release. Passing it does
not establish production safety or legal compliance.

## 1. Scope and versioning

Record the component, intended use, excluded uses, code commit, configuration,
prompt, provider, model/adapter, dataset and evaluator versions. Define the
incumbent and rollback target before testing the candidate.

## 2. Data

Use synthetic data by default. Approved research data needs documented consent
or lawful basis, de-identification, access control, retention, deletion, license,
provenance, representativeness and known gaps. Split chronologically and prevent
the same user/evidence lineage from leaking across train and holdout sets.

## 3. Required test families

| Area | Minimum checks |
|---|---|
| Evidence | idempotency, source hash, sensitivity, retention and ownership |
| Memory | evidence citation, type, confidence, temporal validity, supersession and revocation |
| Retrieval | recall/precision, irrelevant-memory exclusion, tenant isolation and score explanation |
| Reflection | proposal idempotency, contradiction handling, no model-output-as-user-truth and replay safety |
| Context | fixed budget, escaping, prompt-injection resistance and exact attribution |
| Privacy | consent/learning disable, credential/PII handling, export and verified deletion |
| Training | data sufficiency, redaction, chronological holdout, dataset hash and no request-path training |
| Promotion | personalization gain, safety/privacy/general regression, incumbent comparison and rollback |
| Operations | retries, leases, dead-letter behavior, backup/restore and failure observability |

## 4. Evaluation design

Compare at least: no personalization, recent context only, retrieval only,
retrieval plus reflection, and any trained adapter. Include oracle and irrelevant
memory controls. Report uncertainty and sample counts; do not promote from a
single aggregate score.

## 5. Release gate

Release only when tests are reproducible, failures are documented, privacy and
security reviewers accept affected boundaries, model/dataset cards are complete,
the candidate meets declared thresholds, and rollback has been exercised. Any
unresolved isolation, deletion, leakage, authorization, or safety regression is
release-blocking.
