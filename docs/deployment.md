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

`RESEND_API_KEY` is required for email; set it in Railway (**Variables**) before cron jobs can send mail.

3. Deploy command:

```bash
uv sync
uv run alembic upgrade head
uv run python scripts/seed_problems.py
uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

`backend/Procfile` is included for Railway.

## Railway cron jobs

Railway has no `railway cron` subcommand. Schedules are configured per **service** (dashboard **Settings → Cron Schedule**) or via **Railway Functions** (`railway functions new --cron "..."`).

**Important:** Do not attach a cron schedule to the main API service (its start command runs Uvicorn). Use **two additional services** from the same `backend/` root (duplicate the service or `railway add --service <name> --repo obro79/neetcode-auto` and set the root directory to `backend`).

1. Copy all environment variables from the API service (`DATABASE_URL`, `API_KEY`, `RESEND_API_KEY`, email settings, `TIMEZONE`, etc.).
2. Override **Start Command** (Settings → Deploy) for each cron service:

| Service (suggested name) | Start command | Cron (UTC) |
|--------------------------|---------------|------------|
| `send-daily-attempt-1` | `python -m app.jobs.send_daily --attempt 1` | `0 14 * * *` |
| `send-daily-attempt-2` | `python -m app.jobs.send_daily --attempt 2` | `30 14 * * *` |

Cron expressions use **UTC**. For `TIMEZONE=America/Vancouver`, 7:00 / 7:30 AM local time is **14:00 / 14:30 UTC** during PDT (roughly March–November) and **15:00 / 15:30 UTC** during PST. Adjust when daylight saving changes.

For local/Nixpacks deploys without Docker, use `uv run python -m app.jobs.send_daily --attempt N` instead of `python -m ...`.

Cron containers must **exit** when the job finishes (the `send_daily` job does). If a run stays **Active**, Railway skips the next run.

### Optional: Railway Functions (Bun/TypeScript)

```bash
railway functions new --path ./railway/send-daily-attempt-1.ts --name send-daily-attempt-1 --cron "0 14 * * *"
```

Set `API_BASE_URL` and `API_KEY` on the function service and POST to `/daily-sets/today/send?attempt=N`. Prefer duplicate Python cron services unless you want a lightweight HTTP trigger.

## Chrome extension cutover

See `extension/README.md` for load-unpacked steps.

1. Load the extension from `extension/` in `chrome://extensions`.
2. Open the popup — API URL defaults to `https://neetcode-auto-production.up.railway.app`.
3. Paste the production `API_KEY` from Railway (not stored in git).
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
