## Summary

Describe the change, the user/research problem, and why it belongs in Reflection AI.

## Validation

- [ ] `.venv/bin/pytest -q`
- [ ] `.venv/bin/ruff check .`
- [ ] `python3 scripts/validate_team.py`
- [ ] `python3 tools/project_agent/review_agent.py audit --json`
- [ ] Documentation and changelog updated when behavior or release scope changed

## Trust, safety and provenance

- [ ] No real user data, conversations, identifiers, credentials, private databases or model weights included
- [ ] Consent, tenant isolation, deletion, provenance, evaluation and rollback invariants preserved
- [ ] Inferred memory remains reviewable and cannot silently become user truth
- [ ] Third-party code, models, services and datasets have documented versions and terms
- [ ] Model/data changes include cards, validation results and a rollback target
- [ ] Deployment or privacy claims are scoped and evidence-backed
