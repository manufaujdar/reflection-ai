# Provenance policy

Every external dependency, code fragment, model, adapter, dataset, prompt set,
benchmark, evaluation result, and generated artifact must be traceable.

## Required record

Document the name, source URL, exact version or commit, license/terms,
copyright, purpose, integrity hash where applicable, modification history,
known limitations, security status, and redistribution constraints.

## Repository rules

- Do not copy upstream source merely because it is public. Confirm compatibility
  and preserve notices before reuse.
- Do not commit downloaded model weights, private prompts, user data, service
  responses, or benchmark datasets without explicit approval and provenance.
- Keep optional providers behind ports. Hosted-service terms and data handling
  remain separate from the repository's Apache-2.0 license.
- Record training dataset hashes, chronological splits, base model, code and
  prompt version, evaluator version, metrics, approval, and rollback target.
- Treat AI-generated code like any contribution: review behavior, authorship
  constraints, security, tests, and license risk before acceptance.

Current upstream research and optional client dependencies are inventoried in
`THIRD_PARTY_NOTICES.md` and `research/open_source_code_audit/`.
