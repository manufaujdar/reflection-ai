.PHONY: install dev test lint audit validate

install:
	python -m pip install -e '.[dev]'

dev:
	uvicorn --app-dir src reflection_ai.api:app --reload

test:
	pytest

lint:
	ruff check .

audit:
	python tools/project_agent/review_agent.py audit

validate:
	pytest
	ruff check .
	python -m compileall -q src tools scripts
	python scripts/validate_team.py
	python tools/project_agent/review_agent.py audit --json
