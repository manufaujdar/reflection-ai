.PHONY: install dev test lint

install:
	python -m pip install -e '.[dev]'

dev:
	uvicorn --app-dir src reflection_ai.api:app --reload

test:
	pytest

lint:
	ruff check .
