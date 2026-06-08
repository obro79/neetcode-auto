# Deployment — Neon + Railway

## Neon Postgres

1. Create a Neon project and database.
2. Copy the connection string and convert to async SQLAlchemy format:

```text
postgresql+asyncpg://USER:PASSWORD@HOST/DB?sslmode=require
```

3. Set `DATABASE_URL` in Railway.

## Railway API service

1. Create a new Railway service from this repo (`backend/` as root or monorepo with start command).
2. Set environment variables:

```text
APP_NAME=NeetCode SRS
ENVIRONMENT=production
DATABASE_URL=postgresql+asyncpg://...
API_KEY=<strong-random-key>
RESEND_API_KEY=re_...
EMAIL_FROM=NeetCode SRS <you@yourdomain.com>
EMAIL_TO=owenfisher46@gmail.com
TIMEZONE=America/Vancouver
```

3. Deploy command:

```bash
uv sync
uv run alembic upgrade head
uv run python scripts/seed_problems.py
uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

`backend/Procfile` is included for Railway.

## Railway cron jobs

Create two cron triggers in Railway (America/Vancouver):

| Schedule | Command |
|----------|---------|
| `0 7 * * *` | `uv run python -m app.jobs.send_daily --attempt 1` |
| `30 7 * * *` | `uv run python -m app.jobs.send_daily --attempt 2` |

Cron jobs need the same env vars as the API service.

## Chrome extension cutover

1. Open extension popup.
2. Set API base URL to your Railway URL.
3. Set the production `API_KEY`.
4. Enable auto-sync.

## Disable old Notion automations

After verifying 2–3 days of emails and sync:

- Disable Codex automations `daily-neetcode-retry-7-00` and `daily-neetcode-retry-7-30`
- Keep Notion tracker read-only until optional migration is done

## Optional Notion progress migration

Export tracker rows from Notion and map to `user_progress` updates:

- `Solved on NeetCode` → `solved`
- `Review Stage` → `review_stage`
- `Next Review` → `next_review`
- `Last Practiced` → `last_practiced`
- `Confidence` → `confidence`

A one-off script can be added under `backend/scripts/migrate_notion.py` when export data is available.
