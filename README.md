# NeetCode Auto

Self-hostable spaced-repetition system for NeetCode/LeetCode practice: daily problem sets by email, SRS stage tracking, and a Chrome extension that syncs accepted submissions.

## What's included

| Path | Purpose |
|------|---------|
| `backend/` | FastAPI API, Alembic migrations, Resend email, cron job |
| `extension/` | Chrome MV3 extension (auto-sync + confidence picker) |
| `config/srs.config.yaml` | Behavior config (SRS rules, email schedule, slug aliases) |
| `data/neetcode_250.json` | Default 250-problem catalog |

Secrets live in `.env` / Railway variables only. YAML controls behavior without code changes.

## Quick start (local)

```bash
# 1. Clone and configure
git clone https://github.com/obro79/neetcode-auto.git
cd neetcode-auto
cp config/srs.config.example.yaml config/srs.config.yaml
cd backend && cp .env.example .env

# 2. Install and migrate
uv sync
uv run alembic upgrade head
uv run python scripts/seed_problems.py

# 3. Run API
uv run uvicorn app.main:app --reload
```

Load the extension from `extension/` via `chrome://extensions` → **Load unpacked**.

## Configuration

Edit `config/srs.config.yaml` to customize:

- **Daily set size** — `daily_set.review_count`, `focused_new_count`, `random_new_count`
- **Pattern focus** — `daily_set.focus_pattern_order`, `excluded_patterns`
- **SRS intervals** — `srs.stages`, `srs.intervals_days`, `srs.struggling_interval_days`
- **Email schedule** — `email.anchor_time`, `email.backoff_minutes`, `email.max_attempts_per_day`
- **Slug aliases** — map LeetCode URL slugs to catalog slugs (`two-sum` → `two-integer-sum`)

Regenerate slug aliases after changing the catalog:

```bash
cd backend
PYTHONPATH=. uv run python scripts/audit_slug_aliases.py
```

Override config path with `SRS_CONFIG_PATH` in `.env`.

## Daily workflow

1. Cron polls every 15 minutes and sends email when the backoff slot is due (default: 7:00, 7:30, 8:30, 10:30 Vancouver)
2. Solve problems on LeetCode/NeetCode — extension shows a confidence picker after **Accepted**, then POSTs to `/completions`
3. SRS stages advance automatically; completed items are marked in the daily email

## API

Protected routes require header `X-API-Key`.

| Method | Path | Auth |
|--------|------|------|
| GET | `/health` | No |
| GET | `/config/public` | No |
| GET | `/daily-sets/today` | Yes |
| POST | `/daily-sets/today/send` | Yes |
| POST | `/completions` | Yes |
| GET | `/problems` | Yes |

`POST /daily-sets/today/send` is schedule-aware. Optional `?attempt=N` still works for manual retries.

## Chrome extension

1. Load unpacked from `extension/`
2. Set API URL and API key in the popup
3. Enable auto-sync
4. After an accepted submission, pick **Struggling / Getting There / Solid** (or **Skip**)

The extension fetches `GET /config/public` for slug aliases.

## Production deployment

See [docs/self-host.md](docs/self-host.md) for the full Neon + Railway + Resend checklist, or [docs/deployment.md](docs/deployment.md) for ops notes.

## Optional Notion import

```bash
cd backend
uv run python scripts/migrate_notion.py --file data/notion_export.json
```

## Development

```bash
cd backend
make test    # pytest
make lint    # ruff check + format
make ci      # both
```

CI runs on every push/PR to `main` via `.github/workflows/ci.yml` (ruff + pytest on Python 3.12).
