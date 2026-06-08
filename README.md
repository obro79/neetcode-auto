# NeetCode Auto

FastAPI spaced-repetition backend with daily email delivery and a Chrome extension that auto-syncs accepted LeetCode/NeetCode submissions.

## Structure

- `backend/` — FastAPI app (uv, async Postgres, Alembic, Resend email)
- `extension/` — Chrome MV3 extension for submission sync
- `data/neetcode_250.json` — NeetCode 250 problem catalog seed

## Quick start (local)

```bash
cd backend
cp .env.example .env
uv sync
uv run alembic upgrade head
uv run python scripts/seed_problems.py
uv run uvicorn app.main:app --reload
```

Load the extension from `extension/` via `chrome://extensions` → Load unpacked.

## Daily workflow

1. Cron (or manual call) hits `POST /daily-sets/today/send?attempt=1` at 7:00 AM Vancouver
2. Retry at 7:30 AM with `attempt=2` if needed
3. Solve problems on LeetCode/NeetCode — extension POSTs to `/completions`
4. SRS stages advance automatically

## API

All protected routes require `X-API-Key`.

- `GET /health`
- `GET /daily-sets/today`
- `POST /daily-sets/today/send?attempt=1`
- `POST /completions`
- `GET /problems`

## Deployment

See [docs/deployment.md](docs/deployment.md) for Neon + Railway setup and Notion cutover notes.
