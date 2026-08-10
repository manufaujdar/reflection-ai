# AI delivery team

Reflection AI uses an explicit-gear delivery system inspired by the useful
workflow separation in [gstack](https://github.com/manufaujdar/gstack), adapted
in original language for Codex and this project's trust requirements. The team
is not a collection of agents that all run for every task. It is a roster of
validated project skills, selected when their gate or expertise is relevant.

The canonical roster and rules are in [`.ai/TEAM.md`](../.ai/TEAM.md). Active
work is coordinated through [`.ai/HANDOFF.md`](../.ai/HANDOFF.md). Skill contracts
are under [`.agents/skills/`](../.agents/skills/).

## Why explicit gears

Product judgment, architecture, implementation, review, QA, release, and
marketing optimize for different outcomes. Keeping them separate makes stop
conditions and authority visible. Reflection AI adds mandatory privacy, security,
and evaluation gates because generic software workflow roles do not cover its
personalization lifecycle.

## Typical feature workflow

1. `reflection-plan` defines the smallest safe user outcome and acceptance tests.
2. `reflection-research` or `reflection-design` resolves uncertainty when needed.
3. `reflection-engineer` defines boundaries, state transitions, failures and tests.
4. `reflection-privacy`, `reflection-security`, and `reflection-evaluate` review
   the plan when their triggers apply.
5. `reflection-build` implements only the accepted slice.
6. `reflection-review` reports code findings; the Builder fixes and re-enters review.
7. `reflection-qa` independently runs verification and trust-invariant scenarios.
8. `reflection-document` aligns documentation with verified behavior.
9. `reflection-release` checks evidence and rollback before any authorized release.
10. `reflection-market` and `reflection-retro` communicate facts and improve the loop.

## Invocation examples

Use a skill explicitly when you want a particular gear:

```text
Use $reflection-plan to scope tenant-scoped authentication.
Use $reflection-privacy to audit the deletion cascade in this plan.
Use $reflection-review to review the current diff without editing it.
Use $reflection-qa to verify this branch against the handoff contract.
```

For idea-to-release work, the Coordinator may create bounded sub-agents for
independent roles. In the shared checkout, only agents with disjoint file
ownership may write concurrently. Reviewers, QA, and trust-gate agents are
report-only unless the user starts a separate fix gear.

## Validation

Run `python3 scripts/validate_team.py` to validate role coverage and contracts.
Each skill is also compatible with the standard Codex skill validator. The full
project gate remains `pytest` followed by `ruff check .`.

The adaptation uses architectural ideas from gstack rather than vendored prompt
or source text. External research records should continue to include source URL,
version or commit, access date, license, reusable lessons, and rejected patterns.
