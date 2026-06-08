# Self-host guide — NeetCode Auto

Step-by-step setup for Neon Postgres, Railway, Resend, and the Chrome extension.

## Prerequisites

- GitHub account (for CI and optional Railway autodeploy)
- [Neon](https://neon.tech) account (free tier works)
- [Railway](https://railway.com) account (Hobby $5/mo)
- [Resend](https://resend.com) account + verified sender domain (or `onboarding@resend.dev` for testing)
- Chrome for the extension

---

## 1. Clone and configure

```bash
git clone https://github.com/obro79/neetcode-auto.git
cd neetcode-auto
cp config/srs.config.example.yaml config/srs.config.yaml
```

Edit `config/srs.config.yaml`:

| Key | What to change |
|-----|----------------|
| `email.to` | Your inbox |
| `email.from` | Resend-verified sender |
| `timezone` | Your local timezone (default `America/Vancouver`) |
| `daily_set.*` | Review/new counts, excluded patterns |
| `slug_aliases` | Run audit script after catalog changes (see README) |

Copy backend env template:

```bash
cd backend
cp .env.example .env
```

---

## 2. Local smoke test

```bash
uv sync
uv run alembic upgrade head
uv run python scripts/seed_problems.py
uv run uvicorn app.main:app --reload
```

Verify:

```bash
curl http://127.0.0.1:8000/health
# {"status":"ok","database":"ok"}
```

---

## 3. Neon Postgres

1. Create project → database `neetcode_auto`
2. Copy connection string
3. Convert to async format:

```text
postgresql+asyncpg://USER:PASSWORD@HOST/neetcode_auto?sslmode=require
```

Paste into `DATABASE_URL` (local `.env` and Railway later).

---

## 4. Resend email

1. Create API key → `RESEND_API_KEY`
2. Verify domain or use `onboarding@resend.dev` for testing
3. Set `EMAIL_FROM` and `EMAIL_TO` in `.env` (or rely on `config/srs.config.yaml` for addresses)

Test send locally:

```bash
curl -X POST "http://127.0.0.1:8000/daily-sets/today/send" \
  -H "X-API-Key: dev-api-key-change-me"
```

---

## 5. Railway — API service

1. New project → deploy from GitHub repo `obro79/neetcode-auto`
2. Set root directory to **`backend`**
3. Builder: Dockerfile (`backend/railway.toml`)

### Environment variables

| Variable | Example | Required |
|----------|---------|----------|
| `DATABASE_URL` | `postgresql+asyncpg://...` | Yes |
| `API_KEY` | random string | Yes |
| `RESEND_API_KEY` | `re_...` | Yes (for email) |
| `EMAIL_FROM` | `NeetCode SRS <you@domain.com>` | Optional if set in YAML |
| `EMAIL_TO` | `you@example.com` | Optional if set in YAML |
| `TIMEZONE` | `America/Vancouver` | Optional |
| `SRS_CONFIG_PATH` | `config/srs.config.yaml` | Optional (default auto-detected) |
| `ENVIRONMENT` | `production` | Recommended |

Deploy. Confirm:

```bash
curl https://YOUR-APP.up.railway.app/health
```

---

## 6. Railway — email cron (single poller)

Use **one** cron service instead of fixed 7:00/7:30 jobs.

| Setting | Value |
|---------|-------|
| Service name | `send-daily` |
| Root directory | `backend` |
| Config file | `railway.send-daily.toml` |
| Start command | `python -m app.jobs.send_daily` |
| Cron schedule | `*/15 * * * *` (every 15 min UTC) |

Copy the same env vars as the API service (except `PORT`).

The job checks `email.anchor_time` + `email.backoff_minutes` in YAML and sends at the correct local slots. Remove legacy `send-daily-1` / `send-daily-2` services if present.

---

## 7. Chrome extension

1. Open `chrome://extensions` → enable Developer mode
2. **Load unpacked** → select `extension/`
3. Popup: set production API URL + `API_KEY`
4. Enable auto-sync

After solving a problem, the extension shows a confidence picker. Aliases are fetched from `GET /config/public`.

---

## 8. Optional Notion import

Export your Notion tracker to JSON, then:

```bash
cd backend
uv run python scripts/migrate_notion.py --file data/notion_export.json
```

Re-run against production by setting `DATABASE_URL` to the Neon URL.

---

## 9. Customize behavior (no deploy needed for YAML-only changes)

| Goal | Config key |
|------|------------|
| More reviews per day | `daily_set.review_count` |
| Skip Linked List | `daily_set.excluded_patterns` |
| Change SRS intervals | `srs.intervals_days` |
| Earlier/later email | `email.anchor_time`, `email.backoff_minutes` |
| Custom problem list | `catalog.path` → your JSON file |

Catalog JSON format:

```json
{
  "problems": [
    {
      "slug": "two-integer-sum",
      "name": "Two Sum",
      "category": "Arrays & Hashing",
      "difficulty": "Easy",
      "leetcode_url": "https://leetcode.com/problems/two-sum/",
      "neetcode_url": "/problems/two-integer-sum"
    }
  ]
}
```

---

## Config reference (YAML)

```yaml
timezone: America/Vancouver

catalog:
  path: data/neetcode_250.json

daily_set:
  review_count: 4
  focused_new_count: 2
  random_new_count: 2
  excluded_patterns: [Linked List, "2-D Dynamic Programming"]
  focus_pattern_order: [Advanced Graphs, "Math & Geometry", Greedy, Tries]

srs:
  stages: [new, 1d, 3d, 7d, 14d, 30d, mastered]
  intervals_days: {1d: 1, 3d: 3, 7d: 7, 14d: 14, 30d: 30}
  struggling_interval_days: 1

email:
  to: you@example.com
  from: "NeetCode SRS <onboarding@resend.dev>"
  anchor_time: "07:00"
  backoff_minutes: [0, 30, 90, 210]
  max_attempts_per_day: 4

extension:
  sync_only_daily_set: false

slug_aliases:
  two-sum: two-integer-sum
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Empty Review section in email | Import progress or solve problems so reviews are due |
| Extension sync 404 | Check slug alias; run `audit_slug_aliases.py` |
| Email not sent at 7:00 | Cron must run every 15 min; check `email.backoff_minutes` |
| Health `database: error` | Verify `DATABASE_URL` and SSL (`sslmode=require`) |
| NeetCode run button broken | Reload extension (only submission URLs are hooked) |
