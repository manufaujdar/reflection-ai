# Reflection AI project review agent

This local deterministic tool checks repository governance, release metadata,
privacy boundaries, CI safeguards, tracked sensitive artifact types, and the
synthetic browser console. It makes no network or model calls and never edits
source files.

```bash
python3 tools/project_agent/review_agent.py audit
python3 tools/project_agent/review_agent.py audit --json
```

The audit is a release hygiene gate, not a penetration test, accessibility
certification, legal review, privacy impact assessment, or model evaluation.
