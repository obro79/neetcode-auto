#!/usr/bin/env sh
set -eu

PORT="${PORT:-8000}"

alembic upgrade head
python scripts/seed_problems.py
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
