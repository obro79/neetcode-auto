.PHONY: test lint format ci

test:
	uv run pytest -v --tb=short

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff format .

ci: lint test
