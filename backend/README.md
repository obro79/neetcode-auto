# NeetCode SRS Backend

FastAPI backend for NeetCode 250 spaced repetition, daily email delivery, and completion sync.

## Setup

```bash
uv sync
cp .env.example .env
uv run uvicorn app.main:app --reload
```

## Checks

```bash
uv run pytest
uv run ruff check .
```

## Database

Set `DATABASE_URL` in `.env`, then create migrations with Alembic:

```bash
uv run alembic revision --autogenerate -m "initial"
uv run alembic upgrade head
```
