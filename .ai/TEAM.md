# Reflection AI delivery team

Roles are explicit gears, not permanent personas. The Coordinator selects only
the gears required by a task. Planning, implementation, independent review, QA,
and release approval remain separate; no agent approves its own work at a gate.

## Shared invariant

Every gear preserves consent, per-user isolation, deletion, provenance,
auditability, and rollback. Explicit statements and corrections are evidence;
inferences require gated review and must never include sensitive traits,
diagnoses, protected characteristics, emotions, or unrelated private facts.
Evidence, proposals, typed memory, retrieval, training data, evaluation, and
deployment stay separate. Data availability never grants training or deployment
permission. Core behavior remains provider-agnostic and offline-testable. Never
place real user data, credentials, private databases, or raw interaction logs in
the repository or handoff.

## Roster

| Gear | Project skill | Accountable outcome | Mode |
|---|---|---|---|
| Product plan | `reflection-plan` | Safe user outcome, scope, acceptance and guardrail metrics | report-only |
| Research | `reflection-research` | Source- and license-backed options or experiment | report-only |
| Experience design | `reflection-design` | Understandable consent, memory and deletion experience | report-only by default |
| Engineering plan | `reflection-engineer` | Buildable architecture, failure modes and test matrix | report-only for planning |
| Build | `reflection-build` | Smallest complete accepted slice with tests | mutating |
| Privacy gate | `reflection-privacy` | Consent, lifecycle, tenant and deletion assurance | report-only, blocking |
| Security gate | `reflection-security` | Authentication, authorization and trust-boundary assurance | report-only, blocking when triggered |
| Evaluation gate | `reflection-evaluate` | Candidate-versus-incumbent evidence and rollback target | report-only, blocking when triggered |
| Code review | `reflection-review` | Severity-ranked, reproducible findings | report-only |
| QA | `reflection-qa` | Independent verification and ship-readiness result | report-only by default |
| Documentation | `reflection-document` | Documentation that matches verified behavior | mutating |
| Release | `reflection-release` | Mechanical release decision with rollback evidence | mutating only with explicit authority |
| Marketing | `reflection-market` | Accurate, evidence-linked positioning | report-only until publication is authorized |
| Retro | `reflection-retro` | Durable project decisions and process improvements | mutating only in project docs |

The Coordinator is the lead agent for the active task. It owns `.ai/HANDOFF.md`,
chooses gears, assigns disjoint file ownership, integrates results, and resolves
failed gates. Specialist agents return structured results to the Coordinator and
do not edit the handoff concurrently.

## Gear routing

```text
Intake -> Product plan -> [Research / Design] -> Engineering plan
       -> [Privacy / Security / Evaluation gates] -> Build
       -> Review -> Fix -> Review -> QA -> Documentation
       -> Release gate -> [Marketing] -> Retro
```

- Use Research for uncertain technology, evidence, licensing, or external systems.
- Use Design for user-visible consent, correction, inspection, export, or deletion.
- Privacy is required for any evidence, memory, retrieval, retention, training, or
  user-policy change.
- Security is required for identity, authorization, encryption, secrets, external
  services, or trust-boundary changes.
- Evaluation is required for extractors, retrieval/ranking changes, datasets,
  training, model artifacts, routing, promotion, or rollback.
- Reviewer and QA stay independent of the implementing agent. A fix returns to
  the relevant review gate.
- Documentation follows behavioral, interface, operational, or public changes.
- Marketing may start only from verified capabilities and never from aspiration.

Docs-only and research-only work may stop early. Tiny implementation fixes may
use a short plan, but cannot skip a triggered trust gate. Parallel agents are
used only for independent bounded work; concurrent writers must own disjoint
files or isolated worktrees.

## Task contract

Before substantial work, the Coordinator records in `.ai/HANDOFF.md`:

- objective, user outcome, scope and non-goals;
- current gear, owner, assignments and file ownership;
- affected lifecycle stages, consent scopes, data class and tenant boundary;
- interfaces, migrations, acceptance criteria and rollback plan;
- unit/API/integration tests plus consent, isolation, deletion, provenance,
  evaluation and rollback coverage where affected;
- evidence log, findings, gate status, blockers and exact next action.

Planning or review output that changes scope returns to the Coordinator for a
contract update. No specialist silently expands authority.

## Release gates

A releasable change has all applicable items below:

1. Accepted task contract and scoped implementation.
2. Independent code review with blocking findings resolved.
3. `pytest` and `ruff check .` passing, including affected trust-invariant tests.
4. Privacy/Security/Evaluation approvals when triggered.
5. Migrations, documentation, operational notes and provenance updated.
6. Candidate-versus-incumbent evidence and a tested rollback target for any
   personalized artifact promotion.
7. Explicit user authority for publishing, pushing, deploying, or messaging.

## Skill validation

Repository-local skills live in `.agents/skills/`. Run:

```bash
python3 scripts/validate_team.py
pytest
ruff check .
```

The validator checks roster completeness, skill metadata, UI metadata, shared
invariant references, report-only boundaries, and role-specific safety clauses.
