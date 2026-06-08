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

Railway has no `railway cron` subcommand. Cron schedules are set per **service** via dashboard **Settings → Deploy → Cron Schedule** or via config-as-code (`deploy.cronSchedule` in `railway.toml` / `railway.json`). See [Cron jobs](https://docs.railway.com/cron-jobs).

**Do not** attach a cron schedule to the main API service (`neetcode-auto`); its image runs Uvicorn via `scripts/start.sh`. Use **two extra services** from the same `backend/` root.

### Production layout (neetcode-auto project)

| Service | Start command | Cron (UTC) | Config file |
|---------|---------------|------------|-------------|
| `neetcode-auto` | Dockerfile `CMD` → `start.sh` (API) | *(none)* | `backend/railway.toml` |
| `send-daily-1` | `python -m app.jobs.send_daily --attempt 1` | `0 14 * * *` | `backend/railway.send-daily-1.toml` |
| `send-daily-2` | `python -m app.jobs.send_daily --attempt 2` | `30 14 * * *` | `backend/railway.send-daily-2.toml` |

Cron expressions are **UTC**. With `TIMEZONE=America/Vancouver`, 7:00 / 7:30 AM local is **14:00 / 14:30 UTC** during PDT (UTC−7, roughly March–November) and **15:00 / 15:30 UTC** during PST. Adjust schedules when daylight saving changes.

Copy the same app env vars as the API service: `DATABASE_URL`, `API_KEY`, `RESEND_API_KEY`, `EMAIL_FROM`, `EMAIL_TO`, `TIMEZONE`, `APP_NAME`, `ENVIRONMENT`, etc. Omit `PORT` on cron services.

### CLI setup (what works today)

```bash
cd backend
railway link  # project neetcode-auto, environment production

# Create empty services (no cron flag on `railway add`)
railway add --service send-daily-1 --json
railway add --service send-daily-2 --json

# Copy variables from API → each cron service (keys only shown)
railway variable list --service neetcode-auto --kv | rg -v '^RAILWAY_' | rg -v '^PORT=' | rg -v '^NIXPACKS_'
# For each KEY=VALUE line, per target service:
#   printf '%s' "$value" | railway variable set KEY --stdin --service send-daily-1 --skip-deploys

# Deploy with per-service config-as-code (cron + start command)
cp railway.toml railway.toml.api
cp railway.send-daily-1.toml railway.toml && railway up --service send-daily-1 --detach -y
cp railway.send-daily-2.toml railway.toml && railway up --service send-daily-2 --detach -y
mv railway.toml.api railway.toml
```

`railway service source connect --repo owner/repo` failed from this environment (“User does not have access to the repo”); connect GitHub in the dashboard if you want autodeploys on push.

### Dashboard steps (if not using CLI deploy swap)

1. Open project **neetcode-auto** → service **send-daily-1**.
2. **Settings → Source**: connect repo `obro79/neetcode-auto`, branch `main`, root directory **`backend`** (match the API service).
3. **Settings → Config-as-code**: set config file path to **`railway.send-daily-1.toml`** (repo-relative under `backend/`), *or* paste **Start command** and **Cron schedule** under **Deploy** manually.
4. **Variables**: ensure they match the API service (Shared Variables or duplicate keys).
5. Repeat for **send-daily-2** with `railway.send-daily-2.toml` and cron `30 14 * * *`.
6. **Deploy** each service once; confirm deployment details show `cronSchedule` and `startCommand`.

Cron containers must **exit** when the job finishes (`app/jobs/send_daily.py` does). If a run stays **Active**, Railway skips the next scheduled run.

### Railway pricing (2026)

- **Free trial**: one-time **$5** usage credit for new accounts (expires in **30 days**); no card required to start trial per [pricing FAQ](https://railway.com/pricing).
- **Hobby**: **$5/month** subscription; includes **$5/month** of usage (does not roll over). Usage above that is billed on top of the subscription.
- Each cron service counts as its own service toward usage (short-lived cron runs are usually cheap vs. a 24/7 API).

### Optional: Railway Functions

```bash
railway functions new --path ./railway/send-daily-attempt-1.ts --name send-daily-attempt-1 --cron "0 14 * * *"
```

Prefer duplicate Python cron services unless you want a lightweight HTTP trigger to `/daily-sets/today/send?attempt=N`.

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
