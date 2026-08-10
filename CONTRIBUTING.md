# Contributing

Reflection AI handles consented personalization concepts. Keep evidence,
derived memory, retrieval, training, evaluation, and deployment as separate
boundaries.

Before opening a pull request:

```bash
python -m pytest
ruff check .
python scripts/validate_team.py
```

Use synthetic fixtures only. Changes involving consent, retention, deletion,
tenant isolation, authentication, training, evaluation, or model promotion need
the corresponding project review gate before release.
