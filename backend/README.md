# NeetCode SRS Backend

FastAPI backend for NeetCode 250 spaced repetition, daily email delivery, completion sync, and internship job radar.

## Setup

```bash
uv sync
cp .env.example .env
uv run uvicorn app.main:app --reload
```

## Internship Job Radar

Config:
- [`config/jobs.config.yaml`](config/jobs.config.yaml) — terms, locations, categories, ranking weights, email slots
- [`data/profile.json`](data/profile.json) — skills, preferred companies, BM25 query context

Cron (separate Railway service): [`railway.send-jobs.toml`](railway.send-jobs.toml) polls every 15 minutes and sends up to 3 digests per day (9am, 12pm, 3pm local) **only when new matching roles appear**.

```bash
# Preview filtered/ranked listings without sending
uv run python -m app.jobs.send_job_digest --dry-run

# Force a slot during testing
uv run python -m app.jobs.send_job_digest --dry-run --force-slot 1
```

Apply migration 003 before first run:

```bash
uv run alembic upgrade head
```

## Dashboard

Static dashboard at `/dashboard` (same API key as the browser extension).

### Local development

```bash
# Terminal 1 — API
uv run uvicorn app.main:app --reload

# Terminal 2 — dashboard dev server (proxyless; set API URL in login UI)
cd ../dashboard
npm install
npm run dev
```

For the integrated path served by FastAPI:

```bash
cd ../dashboard
npm install
npm run build
# then open http://127.0.0.1:8000/dashboard/
```

### Production Docker image

Railway builds from `backend/` only. Bundle the dashboard before deploy:

```bash
./scripts/prepare_dashboard.sh
docker build -t neetcode-auto .
```

`prepare_dashboard.sh` builds `../dashboard` and copies output to `backend/dashboard_dist/`, which the Dockerfile includes and `app.main` mounts at `/dashboard`.

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
