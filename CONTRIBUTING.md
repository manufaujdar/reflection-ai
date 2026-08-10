# Contributing

Reflection AI handles consented personalization concepts. Keep evidence,
derived memory, retrieval, training, evaluation, and deployment as separate
boundaries.

Before opening a pull request:

```bash
python -m pytest
ruff check .
python scripts/validate_team.py
python tools/project_agent/review_agent.py audit --json
```

Use synthetic fixtures only. Changes involving consent, retention, deletion,
tenant isolation, authentication, training, evaluation, or model promotion need
the corresponding project review gate before release.

Do not commit real conversations, personal profiles, identifiers, private
databases, credentials, provider responses, model weights, or unapproved
datasets. New external code, models, datasets, prompts, benchmarks, services,
or generated artifacts require the record described in `PROVENANCE.md`.

Model or dataset changes must include the relevant card template and follow
`VALIDATION_PROTOCOL.md`. UI changes must preserve the visible synthetic-only,
unauthenticated boundary, keyboard focus, narrow-screen behavior, and safe text
rendering. Update `CHANGELOG.md` when public behavior or release scope changes.
