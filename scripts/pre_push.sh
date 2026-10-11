#!/usr/bin/env bash
# Existing quality checks followed by bounded synthetic/tooling gates.
set -euo pipefail
cd "$(dirname "$0")/.."
python -m pytest
ruff check .
node --check src/reflection_ai/frontend/chat.js
python scripts/validate_team.py
python tools/project_agent/review_agent.py audit --json
python -m compileall -q src tools scripts
python -m unittest discover -s tools -p 'test_*.py'
python -m pip check
python -m pip_audit --local
python scripts/browser_regressions.py
python scripts/engineering_checks.py "$@"
