# Deployment — Neon + Railway

## Neon Postgres

1. Create a Neon project and database.
2. Copy the connection string and convert to async SQLAlchemy format:

```text
postgresql+asyncpg://USER:PASSWORD@HOST/DB?sslmode=require
```

3. Set `DATABASE_URL` in Railway.

## Railway API service

1. Create a new Railway service from this repo with root directory **`backend/`**.
2. Set environment variables:

```text
APP_NAME=NeetCode SRS
ENVIRONMENT=production
DATABASE_URL=postgresql+asyncpg://...
API_KEY=<strong-random-key>
RESEND_API_KEY=re_...
EMAIL_FROM=NeetCode SRS <you@yourdomain.com>
EMAIL_TO=you@example.com
TIMEZONE=America/Vancouver
SRS_CONFIG_PATH=config/srs.config.yaml
```

`RESEND_API_KEY` is required for email. Email schedule and SRS rules come from `config/srs.config.yaml` (bundled in the Docker image at `backend/config/`).

3. Deploy uses Dockerfile + `scripts/start.sh` (migrate, seed, uvicorn).

## Railway cron — single 15-minute poller

Replace the legacy two-service 7:00/7:30 UTC crons with **one** poller:

| Service | Start command | Cron (UTC) | Config file |
|---------|---------------|------------|-------------|
| `neetcode-auto` | Dockerfile `CMD` → `start.sh` | *(none)* | `backend/railway.toml` |
| `send-daily` | `python -m app.jobs.send_daily` | `*/15 * * * *` | `backend/railway.send-daily.toml` |

The job reads `email.anchor_time` and `email.backoff_minutes` from YAML. Default backoff: 7:00, 7:30, 8:30, 10:30 in `America/Vancouver` — no manual UTC edits when DST changes.

Copy the same app env vars as the API service. Omit `PORT` on cron services.

### Migrating from send-daily-1 / send-daily-2

1. Create `send-daily` service with `railway.send-daily.toml`
2. Deploy and verify one test window sends email
3. Delete `send-daily-1` and `send-daily-2` services

Legacy files `railway.send-daily-1.toml` and `railway.send-daily-2.toml` remain for reference but are superseded.

### Dashboard steps

1. Open project → service **send-daily**
2. **Settings → Source**: repo `obro79/neetcode-auto`, branch `main`, root **`backend`**
3. **Config-as-code**: `railway.send-daily.toml`
4. **Variables**: match API service
5. Deploy; confirm `cronSchedule` is `*/15 * * * *`

Cron containers must **exit** when the job finishes. Skips (already sent, not yet time) exit 0.

## Migrations

After pulling updates with schema changes:

```bash
uv run alembic upgrade head
```

Revision `002` adds `email_log.success`, `email_log.resend_id`, and `user_progress.updated_at`.

## Chrome extension cutover

See `extension/README.md`.

1. Load unpacked from `extension/`
2. Set API URL and production `API_KEY`
3. Enable auto-sync; confidence picker appears after Accepted

Extension fetches `GET /config/public` for slug aliases.

## Disable old Notion automations

After verifying 2–3 days of emails and sync:

- Disable Codex automations `daily-neetcode-retry-7-00` and `daily-neetcode-retry-7-30`
- Keep Notion tracker read-only until optional re-import

## Optional Notion progress migration

```bash
cd backend
uv run python scripts/migrate_notion.py --file data/notion_export.json
```

Maps Notion fields to `user_progress` (solved, review_stage, next_review, last_practiced, confidence).

## Slug alias audit

After catalog changes:

```bash
cd backend
PYTHONPATH=. uv run python scripts/audit_slug_aliases.py
```

Update `slug_aliases` in `config/srs.config.yaml` and redeploy.
